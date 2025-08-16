"""Security middleware for FastAPI application."""

import time
import asyncio
from collections import defaultdict
from typing import Dict, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from app.utils.logger import app_logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse."""
    
    def __init__(self, app, calls_per_minute: int = 60, calls_per_hour: int = 1000):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first (for proxy/load balancer scenarios)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, requests_list: list, window_seconds: int):
        """Remove requests older than the time window."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Remove old requests
        while requests_list and requests_list[0] < cutoff_time:
            requests_list.pop(0)
    
    async def dispatch(self, request: Request, call_next):
        """Process rate limiting for incoming requests."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Clean up old requests
        self._cleanup_old_requests(self.minute_requests[client_ip], 60)
        self._cleanup_old_requests(self.hour_requests[client_ip], 3600)
        
        # Check minute limit
        if len(self.minute_requests[client_ip]) >= self.calls_per_minute:
            app_logger.warning(f"Rate limit exceeded for IP {client_ip}: {len(self.minute_requests[client_ip])} requests in last minute")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.calls_per_minute} requests per minute",
                headers={"Retry-After": "60"}
            )
        
        # Check hour limit
        if len(self.hour_requests[client_ip]) >= self.calls_per_hour:
            app_logger.warning(f"Hourly rate limit exceeded for IP {client_ip}: {len(self.hour_requests[client_ip])} requests in last hour")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.calls_per_hour} requests per hour",
                headers={"Retry-After": "3600"}
            )
        
        # Record this request
        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)
        
        # Process the request
        response = await call_next(request)
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """General security middleware for request validation and logging."""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_request_size = max_request_size
        self._advanced_defender = None  # Lazy initialization
    
    async def dispatch(self, request: Request, call_next):
        """Process security checks for incoming requests."""
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            app_logger.warning(f"Request size too large: {content_length} bytes from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=413,
                detail=f"Request too large. Maximum size: {self.max_request_size} bytes"
            )
        
        # Log security-relevant information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Check for suspicious patterns in User-Agent
        suspicious_patterns = ["sqlmap", "nikto", "nmap", "masscan", "zap"]
        if any(pattern in user_agent.lower() for pattern in suspicious_patterns):
            app_logger.warning(f"Suspicious User-Agent detected: {user_agent} from {client_ip}")
        
        # Add request ID for tracing
        request.state.request_id = f"req_{int(time.time() * 1000)}"
        
        # Validate request body with advanced defense (for critical endpoints)
        if request.url.path in ["/api/v1/sessions", "/api/v1/sessions/analyze"]:
            is_valid = await self._validate_request_body(request)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail="Request blocked by security system. Please ensure your request contains only legitimate business automation requirements."
                )
        
        # Process the request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add security headers to response
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def _get_advanced_defender(self):
        """Get the advanced prompt defender instance (lazy initialization)."""
        if self._advanced_defender is None:
            try:
                from app.security.advanced_prompt_defender import AdvancedPromptDefender
                self._advanced_defender = AdvancedPromptDefender()
                app_logger.info("AdvancedPromptDefender integrated with SecurityMiddleware")
            except ImportError as e:
                app_logger.warning(f"AdvancedPromptDefender not available: {e}")
                self._advanced_defender = False  # Mark as unavailable
        return self._advanced_defender if self._advanced_defender is not False else None
    
    async def _validate_request_body(self, request: Request) -> bool:
        """Validate request body for advanced prompt attacks."""
        defender = self._get_advanced_defender()
        if not defender:
            return True  # Skip validation if not available
        
        try:
            # Only validate POST requests with JSON bodies
            if request.method != "POST":
                return True
            
            content_type = request.headers.get("content-type", "")
            if "application/json" not in content_type:
                return True
            
            # Read and validate body
            body = await request.body()
            if not body:
                return True
            
            # Decode body as text for validation
            try:
                body_text = body.decode('utf-8')
            except UnicodeDecodeError:
                app_logger.warning("Request body contains invalid UTF-8")
                return False
            
            # Prepare metadata for security logging
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            session_id = getattr(request.state, 'request_id', 'middleware_unknown')
            
            metadata = {
                "source": "middleware",
                "client_ip": client_ip,
                "user_agent": user_agent,
                "endpoint": str(request.url.path),
                "method": request.method,
                "content_type": content_type
            }
            
            # Validate with advanced defender including comprehensive logging
            decision = await defender.validate_input(
                body_text, 
                session_id=session_id,
                metadata=metadata
            )
            
            if decision.action.value == "block":
                app_logger.warning(f"Request blocked by advanced defense: {decision.user_message}")
                return False
            elif decision.action.value == "flag":
                app_logger.info(f"Request flagged by advanced defense: {decision.user_message}")
                # Allow flagged requests to proceed but log them
                return True
            
            return True
            
        except Exception as e:
            app_logger.error(f"Error validating request body: {e}")
            return True  # Allow on error to avoid breaking functionality


def setup_cors_middleware(app, allowed_origins: Optional[list] = None):
    """Setup CORS middleware with secure defaults."""
    if allowed_origins is None:
        # Default to localhost for development
        allowed_origins = [
            "http://localhost:8501",  # Streamlit default
            "http://127.0.0.1:8501",
            "http://localhost:3000",  # Common React dev server
            "http://127.0.0.1:3000"
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,  # Don't allow credentials for security
        allow_methods=["GET", "POST"],  # Only allow necessary methods
        allow_headers=[
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization"
        ],
        max_age=600  # Cache preflight requests for 10 minutes
    )
    
    app_logger.info(f"CORS configured with origins: {allowed_origins}")