"""Advanced rate limiting middleware with per-user limits."""

import time
import hashlib
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque

import redis
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import app_logger
from app.config import Settings


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10  # Allow burst of requests
    burst_window_seconds: int = 60


@dataclass
class UserLimits:
    """Per-user rate limits."""

    user_id: str
    tier: str = "free"  # free, premium, enterprise
    custom_limits: Optional[RateLimitRule] = None

    def get_limits(self, rate_limit_config=None) -> RateLimitRule:
        """Get effective rate limits for this user."""
        if self.custom_limits:
            return self.custom_limits

        # Default limits by tier
        # Use rate limit config if available
        if rate_limit_config:
            config = rate_limit_config
            if self.tier == "enterprise":
                return RateLimitRule(
                    requests_per_minute=config.enterprise_requests_per_minute,
                    requests_per_hour=config.enterprise_requests_per_hour,
                    requests_per_day=config.enterprise_requests_per_day,
                    burst_limit=config.enterprise_burst_limit,
                    burst_window_seconds=60,
                )
            elif self.tier == "premium":
                return RateLimitRule(
                    requests_per_minute=config.premium_requests_per_minute,
                    requests_per_hour=config.premium_requests_per_hour,
                    requests_per_day=config.premium_requests_per_day,
                    burst_limit=config.premium_burst_limit,
                    burst_window_seconds=60,
                )
            else:  # free tier
                return RateLimitRule(
                    requests_per_minute=config.default_requests_per_minute,
                    requests_per_hour=config.default_requests_per_hour,
                    requests_per_day=config.default_requests_per_day,
                    burst_limit=config.default_burst_limit,
                    burst_window_seconds=config.default_burst_window_seconds,
                )
        else:
            # Fallback to hardcoded values
            if self.tier == "enterprise":
                return RateLimitRule(
                    requests_per_minute=300,
                    requests_per_hour=10000,
                    requests_per_day=100000,
                    burst_limit=100,  # Increased from 50 to 100
                    burst_window_seconds=60,
                )
            elif self.tier == "premium":
                return RateLimitRule(
                    requests_per_minute=120,
                    requests_per_hour=3000,
                    requests_per_day=30000,
                    burst_limit=40,  # Increased from 20 to 40
                    burst_window_seconds=60,
                )
            else:  # free tier
                return RateLimitRule(
                    requests_per_minute=60,
                    requests_per_hour=1000,
                    requests_per_day=10000,
                    burst_limit=25,  # Increased from 10 to 25 for Q&A interactions
                    burst_window_seconds=60,
                )


@dataclass
class RateLimitState:
    """Current rate limit state for a user."""

    requests_this_minute: deque = field(default_factory=deque)
    requests_this_hour: deque = field(default_factory=deque)
    requests_this_day: deque = field(default_factory=deque)
    last_request_time: float = 0
    burst_count: int = 0
    burst_window_start: float = 0


class RateLimiter:
    """Advanced rate limiter with Redis backend and memory fallback."""

    def __init__(self, settings: Settings, rate_limit_config=None) -> None:
        """Initialize rate limiter.

        Args:
            settings: Application settings
            rate_limit_config: Optional rate limit configuration
        """
        self.settings = settings
        self._redis: Optional[redis.Redis] = None
        self._memory_store: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._user_limits: Dict[str, UserLimits] = {}
        self._rate_limit_config = rate_limit_config

        # Initialize Redis if available
        self._init_redis()

        # Default rate limits - use config if available, otherwise defaults
        if rate_limit_config:
            self.default_limits = RateLimitRule(
                requests_per_minute=rate_limit_config.default_requests_per_minute,
                requests_per_hour=rate_limit_config.default_requests_per_hour,
                requests_per_day=rate_limit_config.default_requests_per_day,
                burst_limit=rate_limit_config.default_burst_limit,
                burst_window_seconds=rate_limit_config.default_burst_window_seconds,
            )
        else:
            # Fallback defaults with higher burst for Q&A
            self.default_limits = RateLimitRule(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_limit=25,  # Increased from default 10 to 25
                burst_window_seconds=60,
            )

        app_logger.info(
            f"Rate limiter initialized with Redis: {self._redis is not None}, burst_limit: {self.default_limits.burst_limit}"
        )

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            redis_url = (
                getattr(self.settings, "redis_url", None) or "redis://localhost:6379"
            )
            self._redis = redis.from_url(
                redis_url,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self._redis.ping()
            app_logger.info("Redis rate limiter backend initialized")
        except Exception as e:
            app_logger.warning(
                f"Redis unavailable for rate limiting, using memory: {e}"
            )
            self._redis = None

    def _get_user_id(self, request: Request) -> str:
        """Extract user ID from request.

        Args:
            request: FastAPI request

        Returns:
            User identifier
        """
        # Try to get user ID from various sources
        user_id = None

        # 1. From Authorization header (if JWT or API key)
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            # Simple hash of auth header for user identification
            user_id = hashlib.sha256(auth_header.encode()).hexdigest()[:16]

        # 2. From API key header
        api_key = request.headers.get("X-API-Key", "")
        if api_key and not user_id:
            user_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        # 3. From session ID in request body (for our specific API)
        if not user_id and hasattr(request, "session_id"):
            user_id = f"session_{request.session_id}"

        # 4. Fallback to IP address
        if not user_id:
            client_ip = request.client.host if request.client else "unknown"
            user_id = f"ip_{client_ip}"

        return user_id

    def set_user_limits(self, user_id: str, limits: UserLimits) -> None:
        """Set custom limits for a user.

        Args:
            user_id: User identifier
            limits: User limits configuration
        """
        self._user_limits[user_id] = limits
        app_logger.info(f"Set custom limits for user {user_id}: tier={limits.tier}")

    def update_default_limits(self, new_limits: RateLimitRule) -> None:
        """Update default rate limits.

        Args:
            new_limits: New default rate limit rules
        """
        self.default_limits = new_limits
        app_logger.info(
            f"Updated default rate limits: burst={new_limits.burst_limit}, per_minute={new_limits.requests_per_minute}"
        )

    def get_current_limits(self, user_id: str) -> RateLimitRule:
        """Get current rate limits for a user.

        Args:
            user_id: User identifier

        Returns:
            Current rate limit rules for the user
        """
        return self._get_user_limits(user_id)

    def _get_user_limits(self, user_id: str) -> RateLimitRule:
        """Get rate limits for a user.

        Args:
            user_id: User identifier

        Returns:
            Rate limit rules for the user
        """
        if user_id in self._user_limits:
            return self._user_limits[user_id].get_limits(self._rate_limit_config)

        # Default limits based on user ID pattern
        if user_id.startswith("session_"):
            # Session-based users get standard limits
            return self.default_limits
        elif user_id.startswith("ip_"):
            # IP-based users get more restrictive limits
            if self._rate_limit_config:
                return RateLimitRule(
                    requests_per_minute=self._rate_limit_config.ip_requests_per_minute,
                    requests_per_hour=self._rate_limit_config.ip_requests_per_hour,
                    requests_per_day=self._rate_limit_config.ip_requests_per_day,
                    burst_limit=self._rate_limit_config.ip_burst_limit,
                    burst_window_seconds=60,
                )
            else:
                return RateLimitRule(
                    requests_per_minute=30,
                    requests_per_hour=500,
                    requests_per_day=5000,
                    burst_limit=15,  # Increased from 5 to 15
                    burst_window_seconds=60,
                )
        else:
            # Authenticated users get standard limits
            return self.default_limits

    async def _check_redis_limits(
        self, user_id: str, limits: RateLimitRule
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limits using Redis backend.

        Args:
            user_id: User identifier
            limits: Rate limit rules

        Returns:
            Tuple of (allowed, limit_info)
        """
        if not self._redis:
            return True, {}

        try:
            current_time = time.time()
            pipe = self._redis.pipeline()

            # Keys for different time windows
            minute_key = f"rate_limit:{user_id}:minute:{int(current_time // 60)}"
            hour_key = f"rate_limit:{user_id}:hour:{int(current_time // 3600)}"
            day_key = f"rate_limit:{user_id}:day:{int(current_time // 86400)}"
            burst_key = f"rate_limit:{user_id}:burst"

            # Get current counts
            pipe.get(minute_key)
            pipe.get(hour_key)
            pipe.get(day_key)
            pipe.get(burst_key)

            results = pipe.execute()

            minute_count = int(results[0] or 0)
            hour_count = int(results[1] or 0)
            day_count = int(results[2] or 0)
            burst_info = results[3]

            # Parse burst info
            burst_count = 0
            burst_window_start = current_time
            if burst_info:
                try:
                    burst_data = burst_info.decode().split(":")
                    burst_count = int(burst_data[0])
                    burst_window_start = float(burst_data[1])
                except (ValueError, IndexError):
                    pass

            # Reset burst window if expired
            if current_time - burst_window_start > limits.burst_window_seconds:
                burst_count = 0
                burst_window_start = current_time

            # Check limits
            if minute_count >= limits.requests_per_minute:
                return False, {
                    "error": "Rate limit exceeded",
                    "limit_type": "per_minute",
                    "limit": limits.requests_per_minute,
                    "current": minute_count,
                    "reset_time": (int(current_time // 60) + 1) * 60,
                }

            if hour_count >= limits.requests_per_hour:
                return False, {
                    "error": "Rate limit exceeded",
                    "limit_type": "per_hour",
                    "limit": limits.requests_per_hour,
                    "current": hour_count,
                    "reset_time": (int(current_time // 3600) + 1) * 3600,
                }

            if day_count >= limits.requests_per_day:
                return False, {
                    "error": "Rate limit exceeded",
                    "limit_type": "per_day",
                    "limit": limits.requests_per_day,
                    "current": day_count,
                    "reset_time": (int(current_time // 86400) + 1) * 86400,
                }

            if burst_count >= limits.burst_limit:
                return False, {
                    "error": "Burst limit exceeded",
                    "limit_type": "burst",
                    "limit": limits.burst_limit,
                    "current": burst_count,
                    "reset_time": burst_window_start + limits.burst_window_seconds,
                }

            # Increment counters
            pipe = self._redis.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)  # Keep for 2 minutes
            pipe.incr(hour_key)
            pipe.expire(hour_key, 7200)  # Keep for 2 hours
            pipe.incr(day_key)
            pipe.expire(day_key, 172800)  # Keep for 2 days

            # Update burst counter
            burst_info = f"{burst_count + 1}:{burst_window_start}"
            pipe.set(burst_key, burst_info, ex=limits.burst_window_seconds + 60)

            pipe.execute()

            return True, {
                "requests_remaining_minute": limits.requests_per_minute
                - minute_count
                - 1,
                "requests_remaining_hour": limits.requests_per_hour - hour_count - 1,
                "requests_remaining_day": limits.requests_per_day - day_count - 1,
                "burst_remaining": limits.burst_limit - burst_count - 1,
            }

        except Exception as e:
            app_logger.error(f"Redis rate limit check error: {e}")
            return True, {}  # Allow on error

    def _check_memory_limits(
        self, user_id: str, limits: RateLimitRule
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limits using memory backend.

        Args:
            user_id: User identifier
            limits: Rate limit rules

        Returns:
            Tuple of (allowed, limit_info)
        """
        current_time = time.time()
        state = self._memory_store[user_id]

        # Clean old requests
        minute_cutoff = current_time - 60
        hour_cutoff = current_time - 3600
        day_cutoff = current_time - 86400

        # Remove old requests
        while (
            state.requests_this_minute and state.requests_this_minute[0] < minute_cutoff
        ):
            state.requests_this_minute.popleft()

        while state.requests_this_hour and state.requests_this_hour[0] < hour_cutoff:
            state.requests_this_hour.popleft()

        while state.requests_this_day and state.requests_this_day[0] < day_cutoff:
            state.requests_this_day.popleft()

        # Reset burst window if expired
        if current_time - state.burst_window_start > limits.burst_window_seconds:
            state.burst_count = 0
            state.burst_window_start = current_time

        # Check limits
        if len(state.requests_this_minute) >= limits.requests_per_minute:
            return False, {
                "error": "Rate limit exceeded",
                "limit_type": "per_minute",
                "limit": limits.requests_per_minute,
                "current": len(state.requests_this_minute),
            }

        if len(state.requests_this_hour) >= limits.requests_per_hour:
            return False, {
                "error": "Rate limit exceeded",
                "limit_type": "per_hour",
                "limit": limits.requests_per_hour,
                "current": len(state.requests_this_hour),
            }

        if len(state.requests_this_day) >= limits.requests_per_day:
            return False, {
                "error": "Rate limit exceeded",
                "limit_type": "per_day",
                "limit": limits.requests_per_day,
                "current": len(state.requests_this_day),
            }

        if state.burst_count >= limits.burst_limit:
            return False, {
                "error": "Burst limit exceeded",
                "limit_type": "burst",
                "limit": limits.burst_limit,
                "current": state.burst_count,
            }

        # Add current request
        state.requests_this_minute.append(current_time)
        state.requests_this_hour.append(current_time)
        state.requests_this_day.append(current_time)
        state.burst_count += 1
        state.last_request_time = current_time

        return True, {
            "requests_remaining_minute": limits.requests_per_minute
            - len(state.requests_this_minute),
            "requests_remaining_hour": limits.requests_per_hour
            - len(state.requests_this_hour),
            "requests_remaining_day": limits.requests_per_day
            - len(state.requests_this_day),
            "burst_remaining": limits.burst_limit - state.burst_count,
        }

    async def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits.

        Args:
            request: FastAPI request

        Returns:
            Tuple of (allowed, limit_info)
        """
        user_id = self._get_user_id(request)
        limits = self._get_user_limits(user_id)

        # Try Redis first, fallback to memory
        if self._redis:
            try:
                return await self._check_redis_limits(user_id, limits)
            except Exception as e:
                app_logger.warning(f"Redis rate limit check failed, using memory: {e}")

        return self._check_memory_limits(user_id, limits)

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            User rate limit statistics
        """
        limits = self._get_user_limits(user_id)

        if self._redis:
            try:
                current_time = time.time()
                minute_key = f"rate_limit:{user_id}:minute:{int(current_time // 60)}"
                hour_key = f"rate_limit:{user_id}:hour:{int(current_time // 3600)}"
                day_key = f"rate_limit:{user_id}:day:{int(current_time // 86400)}"

                pipe = self._redis.pipeline()
                pipe.get(minute_key)
                pipe.get(hour_key)
                pipe.get(day_key)
                results = pipe.execute()

                return {
                    "user_id": user_id,
                    "limits": {
                        "per_minute": limits.requests_per_minute,
                        "per_hour": limits.requests_per_hour,
                        "per_day": limits.requests_per_day,
                        "burst": limits.burst_limit,
                    },
                    "current_usage": {
                        "this_minute": int(results[0] or 0),
                        "this_hour": int(results[1] or 0),
                        "this_day": int(results[2] or 0),
                    },
                }
            except Exception as e:
                app_logger.error(f"Error getting user stats from Redis: {e}")

        # Fallback to memory stats
        state = self._memory_store.get(user_id, RateLimitState())
        return {
            "user_id": user_id,
            "limits": {
                "per_minute": limits.requests_per_minute,
                "per_hour": limits.requests_per_hour,
                "per_day": limits.requests_per_day,
                "burst": limits.burst_limit,
            },
            "current_usage": {
                "this_minute": len(state.requests_this_minute),
                "this_hour": len(state.requests_this_hour),
                "this_day": len(state.requests_this_day),
            },
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self, app, settings: Optional[Settings] = None, rate_limit_config=None
    ) -> None:
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            settings: Application settings
            rate_limit_config: Rate limiting configuration
        """
        super().__init__(app)

        if settings is None:
            from app.config import load_settings

            settings = load_settings()

        self.rate_limiter = RateLimiter(settings, rate_limit_config)

        # Exempt paths from rate limiting
        self.exempt_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
        }

    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response
        """
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Check rate limits
        allowed, limit_info = await self.rate_limiter.check_rate_limit(request)

        if not allowed:
            # Rate limit exceeded
            app_logger.warning(
                f"Rate limit exceeded for {self.rate_limiter._get_user_id(request)}: {limit_info}"
            )

            response_data = {
                "error": "Rate limit exceeded",
                "message": limit_info.get("error", "Too many requests"),
                "limit_type": limit_info.get("limit_type"),
                "limit": limit_info.get("limit"),
                "current": limit_info.get("current"),
                "reset_time": limit_info.get("reset_time"),
            }

            return JSONResponse(
                status_code=429,
                content=response_data,
                headers={
                    "Retry-After": str(
                        int(
                            limit_info.get("reset_time", time.time() + 60) - time.time()
                        )
                    ),
                    "X-RateLimit-Limit": str(limit_info.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(
                        int(limit_info.get("reset_time", time.time() + 60))
                    ),
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)

        if "requests_remaining_minute" in limit_info:
            response.headers["X-RateLimit-Limit"] = str(
                self.rate_limiter._get_user_limits(
                    self.rate_limiter._get_user_id(request)
                ).requests_per_minute
            )
            response.headers["X-RateLimit-Remaining"] = str(
                limit_info["requests_remaining_minute"]
            )
            response.headers["X-RateLimit-Reset"] = str(int(time.time() // 60 + 1) * 60)

        return response
