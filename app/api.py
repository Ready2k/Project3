"""FastAPI application for Automated AI Assessment (AAA)."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles



from pydantic import BaseModel, field_validator

from app.config import Settings, load_settings
from app.embeddings.factory import create_embedding_provider
from app.embeddings.index import FAISSIndex
from app.exporters.service import ExportService
from app.llm.openai_provider import OpenAIProvider
from app.llm.claude_provider import ClaudeProvider
from app.llm.bedrock_provider import BedrockProvider
from app.llm.internal_provider import InternalProvider
from app.llm.fakes import FakeLLM
from app.llm.model_discovery import model_discovery
from app.pattern.loader import PatternLoader
from app.pattern.matcher import PatternMatcher
from app.qa.question_loop import QuestionLoop, TemplateLoader
from app.services.agentic_recommendation_service import AgenticRecommendationService
from app.services.jira import JiraService, JiraError, JiraConnectionError, JiraTicketNotFoundError
from app.state.store import SessionState, Phase, DiskCacheStore
from app.utils.logger import app_logger
from app.utils.audit import log_pattern_match
from app.version import __version__, RELEASE_NAME
from app.security import SecurityMiddleware, InputValidator, SecurityValidator, SecurityHeaders
from app.middleware.rate_limiter import RateLimitMiddleware
from app.security.middleware import setup_cors_middleware




# Global validators
input_validator = InputValidator()
security_validator = SecurityValidator()

# Request/Response models with validation
class ProviderConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    bedrock_api_key: Optional[str] = None
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        if not input_validator.validate_provider_name(v):
            raise ValueError('Invalid provider name')
        return v.lower()
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        if not input_validator.validate_model_name(v):
            raise ValueError('Invalid model name')
        return v
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v, info):
        if v is not None:
            # Get provider from context if available
            provider = 'openai'  # Default fallback
            if hasattr(info, 'data') and 'provider' in info.data:
                provider = info.data['provider']
            is_valid, message = input_validator.validate_api_key(v, provider)
            if not is_valid:
                raise ValueError(message)
        return v


# Initialize FastAPI app with security configuration
app = FastAPI(
    title="Automated AI Assessment (AAA) API",
    description="API for assessing automation feasibility of requirements",
    version=f"AAA-{__version__}",
    docs_url="/docs",  # Explicitly set docs URL
    redoc_url="/redoc",  # Explicitly set redoc URL
    openapi_url="/openapi.json"  # Explicitly set OpenAPI URL
)


# Add security middleware (order matters!)
# 1. Trusted Host middleware (first)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "*"]  # Configure based on deployment
)

# 2. CORS middleware
setup_cors_middleware(app)

# 3. Rate limiting middleware
# Load system configuration for rate limiting
try:
    from app.config.system_config import SystemConfigurationManager
    system_config_manager = SystemConfigurationManager()
    rate_limit_config = system_config_manager.config.rate_limiting
    app_logger.info(f"Loaded rate limiting config: burst_limit={rate_limit_config.default_burst_limit}")
except Exception as e:
    app_logger.warning(f"Failed to load system config for rate limiting, using defaults: {e}")
    rate_limit_config = None

app.add_middleware(RateLimitMiddleware, settings=None, rate_limit_config=rate_limit_config)

# 4. General security middleware (last)
app.add_middleware(SecurityMiddleware, max_request_size=10 * 1024 * 1024)  # 10MB limit

# Mount static files for exports
app.mount("/exports", StaticFiles(directory="exports"), name="exports")

# Global dependencies
settings: Optional[Settings] = None
session_store: Optional[DiskCacheStore] = None
pattern_matcher: Optional[PatternMatcher] = None
question_loop: Optional[QuestionLoop] = None
# recommendation_service is now created per request with LLM provider
export_service: Optional[ExportService] = None
jira_service: Optional[JiraService] = None


# Global exception handler for security
@app.exception_handler(ValueError)
async def validation_exception_handler(request: Request, exc: ValueError):
    """Handle validation errors with security logging."""
    client_ip = request.client.host if request.client else "unknown"
    app_logger.warning(f"Validation error from {client_ip}: {str(exc)}")
    
    response = Response(
        content=f'{{"error": "Validation Error", "message": "{str(exc)}"}}',
        status_code=400,
        media_type="application/json"
    )
    return SecurityHeaders.add_security_headers(response)

# Custom exception handler for HTTP exceptions with enhanced security feedback
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with enhanced security feedback formatting."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Check if this is a security-related error that needs special formatting
    if exc.status_code == 400 and "🔒" in str(exc.detail):
        # This is our enhanced security feedback - return it as-is for proper formatting
        app_logger.warning(f"Security validation failed from {client_ip}")
        
        response = Response(
            content=f'{{"error": "Security Validation", "message": {json.dumps(str(exc.detail))}, "type": "security_feedback"}}',
            status_code=400,
            media_type="application/json"
        )
        return SecurityHeaders.add_security_headers(response)
    else:
        # Standard HTTP exception handling
        app_logger.warning(f"HTTP error {exc.status_code} from {client_ip}: {str(exc.detail)}")
        
        response = Response(
            content=f'{{"error": "HTTP Error", "message": "{str(exc.detail)}"}}',
            status_code=exc.status_code,
            media_type="application/json"
        )
        return SecurityHeaders.add_security_headers(response)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with security headers."""
    response = Response(
        content=f'{{"error": "HTTP Error", "message": "{exc.detail}"}}',
        status_code=exc.status_code,
        media_type="application/json"
    )
    return SecurityHeaders.add_security_headers(response)


# Health check endpoints (no authentication required)
@app.get("/health")
async def health_check(response: Response):
    """Basic health check endpoint for monitoring."""
    # Add security headers
    SecurityHeaders.add_security_headers(response)
    return {"status": "healthy", "version": f"AAA-{__version__}", "release_name": RELEASE_NAME}

@app.get("/health/detailed")
async def detailed_health_check(response: Response):
    """Detailed health check with all system components."""
    from app.health.health_checker import get_health_checker
    
    try:
        health_checker = get_health_checker(settings)
        system_health = await health_checker.check_health()
        
        SecurityHeaders.add_security_headers(response)
        return system_health.to_dict()
        
    except Exception as e:
        app_logger.error(f"Detailed health check failed: {e}")
        SecurityHeaders.add_security_headers(response)
        return {
            "status": "critical",
            "message": f"Health check system failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health/readiness")
async def readiness_check(response: Response):
    """Kubernetes readiness probe endpoint."""
    from app.health.health_checker import get_health_checker
    
    try:
        health_checker = get_health_checker(settings)
        # Only check critical components for readiness
        critical_checks = ["disk_cache", "pattern_library", "llm_providers"]
        system_health = await health_checker.check_health(critical_checks)
        
        SecurityHeaders.add_security_headers(response)
        
        if system_health.status in ["healthy", "degraded"]:
            return {"status": "ready", "checks": len(system_health.checks)}
        else:
            response.status_code = 503
            return {"status": "not_ready", "message": "Critical components unhealthy"}
            
    except Exception as e:
        app_logger.error(f"Readiness check failed: {e}")
        response.status_code = 503
        SecurityHeaders.add_security_headers(response)
        return {"status": "not_ready", "message": str(e)}

@app.get("/health/liveness")
async def liveness_check(response: Response):
    """Kubernetes liveness probe endpoint."""
    from app.health.health_checker import get_health_checker
    
    try:
        health_checker = get_health_checker(settings)
        # Only check basic system resources for liveness
        liveness_checks = ["system_resources", "disk_cache"]
        system_health = await health_checker.check_health(liveness_checks)
        
        SecurityHeaders.add_security_headers(response)
        
        if system_health.status != "critical":
            return {"status": "alive", "checks": len(system_health.checks)}
        else:
            response.status_code = 503
            return {"status": "dead", "message": "System resources critical"}
            
    except Exception as e:
        app_logger.error(f"Liveness check failed: {e}")
        response.status_code = 503
        SecurityHeaders.add_security_headers(response)
        return {"status": "dead", "message": str(e)}

@app.get("/security/scan")
async def run_security_scan(response: Response, scan_type: str = "full"):
    """Run security scan on the application."""
    from app.security.security_scanner import get_security_scanner
    
    try:
        scanner = get_security_scanner(settings)
        
        if scan_type == "full":
            results = await scanner.run_full_security_scan()
            SecurityHeaders.add_security_headers(response)
            return {
                "scan_type": "full",
                "results": {name: result.to_dict() for name, result in results.items()}
            }
        elif scan_type == "code":
            result = await scanner.scan_code_vulnerabilities()
        elif scan_type == "dependencies":
            result = await scanner.scan_dependencies()
        elif scan_type == "configuration":
            result = await scanner.scan_configuration_security()
        else:
            raise HTTPException(status_code=400, detail="Invalid scan type")
        
        SecurityHeaders.add_security_headers(response)
        return result.to_dict()
        
    except Exception as e:
        app_logger.error(f"Security scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Security scan failed: {str(e)}")

@app.get("/security/history")
async def get_security_scan_history(response: Response, limit: int = 10):
    """Get security scan history."""
    from app.security.security_scanner import get_security_scanner
    
    try:
        scanner = get_security_scanner(settings)
        history = await scanner.get_scan_history(limit)
        
        SecurityHeaders.add_security_headers(response)
        return {"history": history}
        
    except Exception as e:
        app_logger.error(f"Failed to get security scan history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_settings() -> Settings:
    """Get application settings."""
    global settings
    if settings is None:
        settings = load_settings()
    return settings


def get_session_store() -> DiskCacheStore:
    """Get session store instance."""
    global session_store
    if session_store is None:
        session_store = DiskCacheStore()
    return session_store


async def get_pattern_matcher() -> PatternMatcher:
    """Get pattern matcher instance with properly built FAISS index."""
    global pattern_matcher
    if pattern_matcher is None:
        app_logger.info("Initializing pattern matcher...")
        settings = get_settings()
        
        # Create LLM provider for embedding if needed
        temp_llm_provider = None
        if settings.embedding.provider.value == "llm_based":
            temp_llm_provider = create_llm_provider()
        
        # Initialize components
        pattern_loader = PatternLoader(str(settings.pattern_library_path))
        embedder = create_embedding_provider(settings, temp_llm_provider)
        faiss_index = FAISSIndex(embedder=embedder)
        
        # Build FAISS index from patterns
        patterns = pattern_loader.load_patterns()
        if patterns:
            descriptions = [p["description"] for p in patterns]
            app_logger.info(f"Building FAISS index from {len(patterns)} patterns")
            await faiss_index.build_from_texts(descriptions)
            app_logger.info("✅ FAISS index built successfully")
        else:
            app_logger.warning("No patterns found, FAISS index will be empty")
        
        pattern_matcher = PatternMatcher(
            pattern_loader=pattern_loader,
            embedding_provider=embedder,
            faiss_index=faiss_index
        )
        
        app_logger.info("✅ Pattern matcher initialized")
    
    return pattern_matcher


def create_llm_provider(provider_config: Optional[ProviderConfig] = None, session_id: str = "unknown"):
    """Create LLM provider based on configuration with audit logging."""
    from app.utils.audit_integration import create_audited_provider
    
    settings = get_settings()
    base_provider = None
    
    app_logger.info(f"Creating LLM provider for session {session_id}")
    app_logger.info(f"Provider config: {provider_config.model_dump() if provider_config else 'None'}")
    app_logger.info(f"Settings provider: {settings.provider}")
    
    if not provider_config:
        # Use settings default or fallback to fake
        app_logger.info(f"No provider config, using settings: provider={settings.provider}")
        
        if settings.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            base_provider = OpenAIProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=settings.model
            )
            app_logger.info(f"✅ Using OpenAI provider from environment: {settings.model}")
        
        elif settings.provider == "claude" and os.getenv("ANTHROPIC_API_KEY"):
            base_provider = ClaudeProvider(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=settings.model
            )
            app_logger.info(f"✅ Using Claude provider from environment: {settings.model}")
        
        elif settings.provider == "bedrock":
            base_provider = BedrockProvider(
                model=settings.model,
                region=settings.bedrock.region,
                aws_access_key_id=settings.bedrock.aws_access_key_id,
                aws_secret_access_key=settings.bedrock.aws_secret_access_key,
                aws_session_token=settings.bedrock.aws_session_token,
                bedrock_api_key=settings.bedrock.bedrock_api_key
            )
            app_logger.info(f"✅ Using Bedrock provider from environment: {settings.model}")
        
        elif settings.provider == "internal" and os.getenv("INTERNAL_ENDPOINT_URL"):
            base_provider = InternalProvider(
                endpoint_url=os.getenv("INTERNAL_ENDPOINT_URL"),
                model=settings.model,
                api_key=os.getenv("INTERNAL_API_KEY")
            )
            app_logger.info(f"✅ Using Internal provider from environment: {settings.model}")
        
        else:
            if settings.disable_fake_llm:
                raise ValueError("No valid LLM provider configuration found and FakeLLM is disabled")
            app_logger.warning("⚠️ No provider configuration found, using FakeLLM")
            # Create FakeLLM with default responses for agentic operations
            default_responses = {
                "12345678": '{"overall_complexity": "moderate", "autonomy_potential": 0.8, "reasoning_analysis": {"logical": "high", "causal": "medium"}, "required_types": ["logical", "causal"], "challenges": ["Integration complexity"], "frameworks": ["LangChain"]}',
                "87654321": '{"independence_level": "high", "independence_score": 0.8, "autonomous_decisions": ["Process standard requests", "Apply business rules"], "escalation_triggers": ["Complex edge cases"], "risk_factors": ["Data sensitivity"]}',
                "abcdef12": '{"coverage_percentage": 0.85, "exception_handling_score": 0.8, "learning_potential": 0.7, "self_monitoring_capability": 0.7, "automation_gaps": ["Complex edge cases"]}'
            }
            base_provider = FakeLLM(default_responses, seed=42)
    
    else:
        app_logger.info(f"Using provider config: {provider_config.provider}/{provider_config.model}")
        
        if provider_config.provider == "openai":
            if not provider_config.api_key:
                raise ValueError("OpenAI API key is required")
            base_provider = OpenAIProvider(
                api_key=provider_config.api_key,
                model=provider_config.model
            )
            app_logger.info(f"✅ Using OpenAI provider from config: {provider_config.model}")
        
        elif provider_config.provider == "claude":
            if not provider_config.api_key:
                raise ValueError("Claude API key is required")
            base_provider = ClaudeProvider(
                api_key=provider_config.api_key,
                model=provider_config.model
            )
            app_logger.info(f"✅ Using Claude provider from config: {provider_config.model}")
        
        elif provider_config.provider == "bedrock":
            region = provider_config.region or settings.bedrock.region
            base_provider = BedrockProvider(
                model=provider_config.model,
                region=region,
                aws_access_key_id=provider_config.aws_access_key_id,
                aws_secret_access_key=provider_config.aws_secret_access_key,
                aws_session_token=provider_config.aws_session_token,
                bedrock_api_key=getattr(provider_config, 'bedrock_api_key', None)
            )
            auth_method = "API key" if getattr(provider_config, 'bedrock_api_key', None) else "AWS credentials"
            app_logger.info(f"✅ Using Bedrock provider from config: {provider_config.model} in {region} with {auth_method}")
        
        elif provider_config.provider == "internal":
            if not provider_config.endpoint_url:
                raise ValueError("Internal provider endpoint URL is required")
            base_provider = InternalProvider(
                endpoint_url=provider_config.endpoint_url,
                model=provider_config.model,
                api_key=provider_config.api_key
            )
            app_logger.info(f"✅ Using Internal provider from config: {provider_config.model}")
        
        elif provider_config.provider == "fake":
            base_provider = FakeLLM({}, seed=42)
            app_logger.info("✅ Using FakeLLM provider from config")
        
        else:
            raise ValueError(f"Provider {provider_config.provider} not supported. Available: openai, claude, bedrock, internal, fake")
    
    # Log final provider info
    model_info = base_provider.get_model_info()
    app_logger.info(f"🚀 Created provider: {model_info['provider']}/{model_info['model']}")
    
    # Wrap with audit logging
    return create_audited_provider(base_provider, session_id)


def get_question_loop(provider_config: Optional[ProviderConfig] = None, session_id: str = "unknown") -> QuestionLoop:
    """Get question loop instance with provider configuration."""
    llm_provider = create_llm_provider(provider_config, session_id)
    template_loader = TemplateLoader()
    store = get_session_store()
    
    return QuestionLoop(
        llm_provider=llm_provider,
        template_loader=template_loader,
        session_store=store
    )


def get_recommendation_service(llm_provider=None) -> AgenticRecommendationService:
    """Get recommendation service instance with LLM provider."""
    settings = get_settings()
    # Create agentic service with LLM provider (required for initialization)
    return AgenticRecommendationService(
        llm_provider=llm_provider,
        pattern_library_path=settings.pattern_library_path
    )


def get_export_service(llm_provider=None) -> ExportService:
    """Get export service instance."""
    global export_service
    if export_service is None:
        settings = get_settings()
        export_service = ExportService(settings.export_path, base_url="/exports/", llm_provider=llm_provider)
    return export_service


def get_jira_service() -> JiraService:
    """Get Jira service instance."""
    global jira_service
    if jira_service is None:
        settings = get_settings()
        jira_service = JiraService(settings.jira)
    return jira_service


def validate_output_security(data: Any) -> bool:
    """Validate that output doesn't contain banned tools or malicious content."""
    try:
        # Convert data to string for validation
        if isinstance(data, dict):
            text_content = str(data)
        elif isinstance(data, list):
            text_content = " ".join(str(item) for item in data)
        else:
            text_content = str(data)
        
        # Check for banned tools
        if not security_validator.validate_no_banned_tools(text_content):
            app_logger.error("Output validation failed: banned tools detected")
            return False
        
        return True
    except Exception as e:
        app_logger.error(f"Error validating output security: {e}")
        return False


class IngestRequest(BaseModel):
    source: str  # "text", "file", "jira"
    payload: Dict[str, Any]
    provider_config: Optional[ProviderConfig] = None
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        allowed_sources = ["text", "file", "jira"]
        if v not in allowed_sources:
            raise ValueError(f'Invalid source. Must be one of: {allowed_sources}')
        return v
    
    @field_validator('payload')
    @classmethod
    def validate_payload(cls, v):
        # Sanitize the payload dictionary
        return security_validator.sanitize_dict(v)


class IngestResponse(BaseModel):
    session_id: str


class StatusResponse(BaseModel):
    phase: str
    progress: int
    missing_fields: List[str]
    requirements: Optional[Dict[str, Any]] = None


class QARequest(BaseModel):
    answers: Dict[str, str]
    
    @field_validator('answers')
    @classmethod
    def validate_answers(cls, v):
        # Sanitize answers and check for reasonable limits
        if len(v) > 20:  # Max 20 answers per request
            raise ValueError('Too many answers in single request')
        
        sanitized = {}
        for key, value in v.items():
            if not isinstance(value, str):
                raise ValueError('All answers must be strings')
            if len(value) > 5000:  # Max 5KB per answer
                raise ValueError('Answer too long')
            sanitized[security_validator.sanitize_string(key)] = security_validator.sanitize_string(value)
        
        return sanitized


class QAResponse(BaseModel):
    complete: bool
    next_questions: List[Dict[str, Any]]


class MatchRequest(BaseModel):
    session_id: str
    top_k: int = 5


class MatchResponse(BaseModel):
    candidates: List[Dict[str, Any]]


class RecommendRequest(BaseModel):
    session_id: str
    top_k: int = 3


class RecommendResponse(BaseModel):
    feasibility: str
    recommendations: List[Dict[str, Any]]
    tech_stack: List[str]
    reasoning: str


class ExportRequest(BaseModel):
    session_id: str
    format: str  # "json", "md", "markdown", "comprehensive", or "report"
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        if not input_validator.validate_session_id(v):
            raise ValueError('Invalid session ID format')
        return v
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if not input_validator.validate_export_format(v):
            raise ValueError('Invalid export format')
        return v.lower()


class ExportResponse(BaseModel):
    download_url: str
    file_path: str
    file_info: Dict[str, Any]


class ProviderTestRequest(BaseModel):
    provider: str
    model: str
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    bedrock_api_key: Optional[str] = None


class ProviderTestResponse(BaseModel):
    ok: bool
    message: str


class GenerateCredentialsRequest(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: Optional[str] = None
    region: Optional[str] = "us-east-1"
    duration_seconds: Optional[int] = 3600


class GenerateCredentialsResponse(BaseModel):
    ok: bool
    message: str
    credentials: Optional[Dict[str, str]] = None


class ModelDiscoveryRequest(BaseModel):
    """Request for discovering available models."""
    provider: str
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    bedrock_api_key: Optional[str] = None
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        if not input_validator.validate_provider_name(v):
            raise ValueError('Invalid provider name')
        return v.lower()


class ModelInfo(BaseModel):
    """Information about an available model."""
    id: str
    name: str
    description: Optional[str] = None
    context_length: Optional[int] = None
    capabilities: List[str] = []


class ModelDiscoveryResponse(BaseModel):
    """Response for model discovery."""
    ok: bool
    message: str
    models: List[ModelInfo] = []


class JiraTestRequest(BaseModel):
    base_url: str
    auth_type: Optional[str] = "api_token"  # api_token, pat, sso, basic
    
    # Existing authentication fields
    email: Optional[str] = None
    api_token: Optional[str] = None
    
    # New Data Center authentication fields
    username: Optional[str] = None
    password: Optional[str] = None
    personal_access_token: Optional[str] = None
    
    # Network configuration options
    verify_ssl: bool = True
    ca_cert_path: Optional[str] = None
    proxy_url: Optional[str] = None
    timeout: int = 30
    
    # SSO configuration
    use_sso: bool = False
    sso_session_cookie: Optional[str] = None
    
    # Data Center specific configuration
    context_path: Optional[str] = None
    custom_port: Optional[int] = None
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        """Validate and normalize base URL."""
        if v is not None:
            v = v.rstrip('/')
            if not v.startswith(('http://', 'https://')):
                raise ValueError('Base URL must start with http:// or https://')
        return v
    
    @field_validator('auth_type')
    @classmethod
    def validate_auth_type(cls, v):
        """Validate authentication type."""
        allowed_types = ["api_token", "pat", "sso", "basic"]
        if v not in allowed_types:
            raise ValueError(f'Invalid auth_type. Must be one of: {allowed_types}')
        return v
    
    @field_validator('custom_port')
    @classmethod
    def validate_custom_port(cls, v):
        """Validate custom port range."""
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Custom port must be between 1 and 65535')
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v < 1:
            raise ValueError('Timeout must be at least 1 second')
        return v
    
    def validate_auth_config(self) -> List[str]:
        """Validate authentication configuration and return any errors."""
        errors = []
        
        if self.auth_type == "api_token":
            if not self.email:
                errors.append("Email is required for API token authentication")
            if not self.api_token:
                errors.append("API token is required for API token authentication")
        
        elif self.auth_type == "pat":
            if not self.personal_access_token:
                errors.append("Personal access token is required for PAT authentication")
        
        elif self.auth_type == "basic":
            if not self.username:
                errors.append("Username is required for basic authentication")
            if not self.password:
                errors.append("Password is required for basic authentication")
        
        elif self.auth_type == "sso":
            if not self.use_sso:
                errors.append("SSO must be enabled for SSO authentication")
        
        return errors


class JiraErrorDetail(BaseModel):
    """Detailed error information with troubleshooting steps."""
    error_type: str
    error_code: Optional[str] = None
    message: str
    troubleshooting_steps: List[str]
    documentation_links: List[str] = []
    suggested_config_changes: Optional[Dict[str, Any]] = None


class JiraTestResponse(BaseModel):
    ok: bool
    message: str
    deployment_info: Optional[Dict[str, Any]] = None
    error_details: Optional[JiraErrorDetail] = None
    auth_methods_available: List[str] = []
    api_version_detected: Optional[str] = None
    ssl_configuration: Optional[Dict[str, Any]] = None


class JiraFetchRequest(JiraTestRequest):
    ticket_key: str
    
    @field_validator('ticket_key')
    @classmethod
    def validate_ticket_key(cls, v):
        """Validate Jira ticket key format."""
        if not v or not isinstance(v, str):
            raise ValueError('Ticket key is required and must be a string')
        
        # Basic validation for Jira ticket key format (PROJECT-123)
        import re
        if not re.match(r'^[A-Z][A-Z0-9]*-\d+$', v.upper()):
            raise ValueError('Invalid ticket key format. Expected format: PROJECT-123')
        
        return v.upper()


class JiraFetchResponse(BaseModel):
    ticket_data: Dict[str, Any]
    requirements: Dict[str, Any]
    deployment_info: Optional[Dict[str, Any]] = None
    api_version_used: Optional[str] = None


# API Endpoints
@app.post("/ingest", response_model=IngestResponse)
async def ingest_requirements(request: IngestRequest, http_request: Request, response: Response):
    """Ingest requirements and create a new session."""
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Debug logging
        app_logger.info(f"🔍 Ingest request for session {session_id}")
        app_logger.info(f"Source: {request.source}")
        app_logger.info(f"Provider config received: {request.provider_config.model_dump() if request.provider_config else 'None'}")
        
        # Extract and validate requirements from payload
        requirements = {}
        if request.source == "text":
            text_content = request.payload.get("text", "")
            
            # Validate requirements text
            is_valid, validation_message = input_validator.validate_requirements_text(text_content)
            if not is_valid:
                raise HTTPException(status_code=400, detail=validation_message)
            
            requirements = {
                "description": security_validator.sanitize_string(text_content),
                "domain": security_validator.sanitize_string(str(request.payload.get("domain", ""))),
                "pattern_types": [security_validator.sanitize_string(str(pt)) for pt in request.payload.get("pattern_types", [])]
            }
            
            # Extract constraints if provided
            if "constraints" in request.payload and request.payload["constraints"]:
                constraints = request.payload["constraints"]
                requirements["constraints"] = {
                    "banned_tools": [security_validator.sanitize_string(str(tool)) for tool in constraints.get("banned_tools", [])],
                    "required_integrations": [security_validator.sanitize_string(str(integration)) for integration in constraints.get("required_integrations", [])],
                    "compliance_requirements": [security_validator.sanitize_string(str(comp)) for comp in constraints.get("compliance_requirements", [])],
                    "data_sensitivity": security_validator.sanitize_string(str(constraints.get("data_sensitivity", ""))) if constraints.get("data_sensitivity") else None,
                    "budget_constraints": security_validator.sanitize_string(str(constraints.get("budget_constraints", ""))) if constraints.get("budget_constraints") else None,
                    "deployment_preference": security_validator.sanitize_string(str(constraints.get("deployment_preference", ""))) if constraints.get("deployment_preference") else None
                }
        elif request.source == "file":
            # Extract and validate file content
            file_content = request.payload.get("content", "")
            filename = request.payload.get("filename", "")
            
            # Validate file content
            is_valid, validation_message = input_validator.validate_requirements_text(file_content)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"File content validation failed: {validation_message}")
            
            requirements = {
                "description": security_validator.sanitize_string(file_content),
                "filename": security_validator.sanitize_string(filename)
            }
            
            # Extract constraints if provided
            if "constraints" in request.payload and request.payload["constraints"]:
                constraints = request.payload["constraints"]
                requirements["constraints"] = {
                    "banned_tools": [security_validator.sanitize_string(str(tool)) for tool in constraints.get("banned_tools", [])],
                    "required_integrations": [security_validator.sanitize_string(str(integration)) for integration in constraints.get("required_integrations", [])],
                    "compliance_requirements": [security_validator.sanitize_string(str(comp)) for comp in constraints.get("compliance_requirements", [])],
                    "data_sensitivity": security_validator.sanitize_string(str(constraints.get("data_sensitivity", ""))) if constraints.get("data_sensitivity") else None,
                    "budget_constraints": security_validator.sanitize_string(str(constraints.get("budget_constraints", ""))) if constraints.get("budget_constraints") else None,
                    "deployment_preference": security_validator.sanitize_string(str(constraints.get("deployment_preference", ""))) if constraints.get("deployment_preference") else None
                }
        elif request.source == "jira":
            # For Jira source, payload should contain ticket_key and credentials
            ticket_key = request.payload.get("ticket_key")
            base_url = request.payload.get("base_url")
            auth_type = request.payload.get("auth_type", "api_token")
            
            # Extract credentials based on auth type
            email = request.payload.get("email")
            api_token = request.payload.get("api_token")
            username = request.payload.get("username")
            password = request.payload.get("password")
            personal_access_token = request.payload.get("personal_access_token")
            
            if not ticket_key:
                raise HTTPException(status_code=400, detail="ticket_key is required for Jira source")
            
            # Validate Jira credentials based on auth type
            is_valid, validation_message = input_validator.validate_jira_credentials(
                base_url=base_url,
                email=email,
                api_token=api_token,
                username=username,
                password=password,
                personal_access_token=personal_access_token,
                auth_type=auth_type
            )
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Jira credentials validation failed: {validation_message}")
            
            # Create temporary Jira service with provided credentials
            from app.config import JiraConfig, JiraAuthType
            
            # Map string auth type to enum
            auth_type_mapping = {
                "api_token": JiraAuthType.API_TOKEN,
                "pat": JiraAuthType.PERSONAL_ACCESS_TOKEN,
                "sso": JiraAuthType.SSO,
                "basic": JiraAuthType.BASIC
            }
            
            jira_config = JiraConfig(
                base_url=base_url,
                auth_type=auth_type_mapping.get(auth_type, JiraAuthType.API_TOKEN),
                email=email,
                api_token=api_token,
                username=username,
                password=password,
                personal_access_token=personal_access_token
            )
            temp_jira_service = JiraService(jira_config)
            
            try:
                # Fetch ticket data
                ticket = await temp_jira_service.fetch_ticket(ticket_key)
                # Map to requirements format
                requirements = temp_jira_service.map_ticket_to_requirements(ticket)
                app_logger.info(f"Successfully fetched and mapped Jira ticket {ticket_key}")
            except JiraConnectionError as e:
                raise HTTPException(status_code=401, detail=f"Jira connection failed: {str(e)}")
            except JiraTicketNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except JiraError as e:
                raise HTTPException(status_code=400, detail=f"Jira error: {str(e)}")
            except Exception as e:
                app_logger.error(f"Unexpected error fetching Jira ticket {ticket_key}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to fetch Jira ticket: {str(e)}")
        
        # Create initial session state
        session_state = SessionState(
            session_id=session_id,
            phase=Phase.PARSING,
            progress=10,
            requirements=requirements,
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            provider_config=request.provider_config.model_dump() if request.provider_config else None
        )
        
        # Store provider configuration in session for later use
        if request.provider_config:
            app_logger.info(f"Stored provider config in session: {session_state.provider_config}")
        
        # Store session
        store = get_session_store()
        await store.update_session(session_id, session_state)
        
        # Immediately advance to VALIDATING phase (simulate processing)
        session_state.phase = Phase.VALIDATING
        session_state.progress = 30
        session_state.updated_at = datetime.now()
        await store.update_session(session_id, session_state)
        
        # Check if we need Q&A or can proceed to matching
        # Always go to Q&A phase to gather clarifying information
        # The Q&A system will determine if questions are actually needed
        session_state.phase = Phase.QNA
        session_state.progress = 40
        session_state.missing_fields = ["workflow_variability", "data_sensitivity", "human_oversight"]
        
        session_state.updated_at = datetime.now()
        await store.update_session(session_id, session_state)
        
        app_logger.info(f"Created new session: {session_id} in phase: {session_state.phase.value}")
        
        # Add security headers to response
        SecurityHeaders.add_security_headers(response)
        
        return IngestResponse(session_id=session_id)
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error in ingest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str, response: Response):
    """Get session status and progress."""
    try:
        # Validate session ID format
        if not input_validator.validate_session_id(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        store = get_session_store()
        session = await store.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Auto-advance phases if needed
        if session.phase == Phase.QNA:
            try:
                # Check if we have questions to ask
                provider_config = None
                if session.provider_config:
                    app_logger.info(f"Creating ProviderConfig from: {session.provider_config}")
                    provider_config = ProviderConfig(**session.provider_config)
                
                question_loop = get_question_loop(provider_config, session_id)
                questions = await question_loop.generate_questions(session_id, max_questions=5)
                
                if not questions:
                    # No questions needed, advance to matching
                    session.phase = Phase.MATCHING
                    session.progress = 60
                    session.updated_at = datetime.now()
                    await store.update_session(session_id, session)
                    app_logger.info(f"Advanced session {session_id} from QNA to MATCHING phase (no questions needed)")
            except Exception as e:
                app_logger.error(f"Error in QNA phase processing: {e}")
                # Continue without advancing phase
        
        elif session.phase == Phase.MATCHING and not session.matches:
            # Simulate pattern matching completion
            session.phase = Phase.RECOMMENDING
            session.progress = 80
            session.updated_at = datetime.now()
            await store.update_session(session_id, session)
            app_logger.info(f"Advanced session {session_id} to RECOMMENDING phase")
        
        elif session.phase == Phase.RECOMMENDING and not session.recommendations:
            # Simulate recommendation generation completion
            session.phase = Phase.DONE
            session.progress = 100
            session.updated_at = datetime.now()
            await store.update_session(session_id, session)
            app_logger.info(f"Advanced session {session_id} to DONE phase")
        
        status_response = StatusResponse(
            phase=session.phase.value,
            progress=session.progress,
            missing_fields=session.missing_fields,
            requirements=session.requirements
        )
        app_logger.info(f"Status response for {session_id}: {status_response.model_dump()}")
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting status for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/qa/{session_id}/questions")
async def get_qa_questions(session_id: str, response: Response):
    """Get Q&A questions for a session."""
    try:
        from datetime import datetime, timedelta
        
        app_logger.info(f"API: Getting Q&A questions for session {session_id}")
        app_logger.info(f"API: Question request timestamp: {datetime.now()}")
        
        # Debug: Check if we have cache
        if hasattr(get_qa_questions, '_api_question_cache'):
            app_logger.info(f"API: Cache has {len(get_qa_questions._api_question_cache)} entries")
        else:
            app_logger.info("API: No cache exists yet")
        
        # Get session to retrieve provider configuration
        store = get_session_store()
        session = await store.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.phase != Phase.QNA:
            app_logger.info(f"Session {session_id} not in QNA phase (current: {session.phase}), returning empty questions")
            return {"questions": []}
        
        # Create provider config from session
        provider_config = None
        if session.provider_config:
            app_logger.info(f"Retrieved provider config from session for questions: {session.provider_config}")
            provider_config = ProviderConfig(**session.provider_config)
        else:
            app_logger.warning("No provider config found in session for questions")
        
        # Check if questions were recently generated for this session
        # Use a more robust API-level cache
        if not hasattr(get_qa_questions, '_api_question_cache'):
            get_qa_questions._api_question_cache = {}
        
        # Create a stable cache key that includes session requirements
        requirements_hash = hash(str(sorted(session.requirements.items())))
        api_cache_key = f"{session_id}_{requirements_hash}_questions"
        
        if api_cache_key in get_qa_questions._api_question_cache:
            cached_result, cache_time = get_qa_questions._api_question_cache[api_cache_key]
            # Use cached result if it's less than 5 minutes old
            if datetime.now() - cache_time < timedelta(minutes=5):
                app_logger.info(f"Using API-level cached questions for session {session_id}")
                return cached_result
            else:
                # Remove expired cache entry
                del get_qa_questions._api_question_cache[api_cache_key]
        
        # Check for rapid-fire requests (prevent duplicate calls within 10 seconds)
        rapid_fire_key = f"{session_id}_rapid_fire"
        if rapid_fire_key in get_qa_questions._api_question_cache:
            _, last_request_time = get_qa_questions._api_question_cache[rapid_fire_key]
            if datetime.now() - last_request_time < timedelta(seconds=10):
                app_logger.info(f"Preventing rapid-fire question request for session {session_id}")
                return {"questions": []}
        
        # Mark this request time to prevent rapid-fire
        get_qa_questions._api_question_cache[rapid_fire_key] = (None, datetime.now())
        
        question_loop = get_question_loop(provider_config, session_id)
        questions = await question_loop.generate_questions(session_id, max_questions=5)
        
        # If no questions generated (agentic scope gate rejection), assess for traditional automation
        if not questions:
            app_logger.info(f"No agentic questions generated for session {session_id}, assessing traditional automation suitability")
            
            # Import and use automation suitability assessor
            from app.services.automation_suitability_assessor import AutomationSuitabilityAssessor
            
            # Create assessor with same LLM provider
            llm_provider = get_llm_provider(provider_config, session_id)
            assessor = AutomationSuitabilityAssessor(llm_provider)
            
            # Assess automation suitability
            assessment = await assessor.assess_automation_suitability(
                session.requirements, 
                agentic_rejected=True
            )
            
            # Store assessment in session for later use
            session.requirements['automation_suitability_assessment'] = {
                'suitability': assessment.suitability.value,
                'confidence': assessment.confidence,
                'reasoning': assessment.reasoning,
                'recommended_approach': assessment.recommended_approach,
                'challenges': assessment.challenges,
                'next_steps': assessment.next_steps,
                'user_choice_required': assessment.user_choice_required,
                'warning_message': assessment.warning_message
            }
            
            # Update session with assessment
            await store.update_session(session_id, session)
            
            # Determine next steps based on assessment
            if assessor.should_require_user_choice(assessment):
                # Return special response indicating user choice is needed
                result = {
                    "questions": [],
                    "session_id": session_id,
                    "phase": session.phase.value,
                    "automation_assessment": {
                        "suitability": assessment.suitability.value,
                        "confidence": assessment.confidence,
                        "reasoning": assessment.reasoning,
                        "recommended_approach": assessment.recommended_approach,
                        "challenges": assessment.challenges,
                        "next_steps": assessment.next_steps,
                        "user_choice_required": assessment.user_choice_required,
                        "warning_message": assessment.warning_message
                    },
                    "requires_user_decision": True
                }
            elif assessor.should_proceed_with_traditional_patterns(assessment):
                # Proceed to traditional pattern matching
                app_logger.info(f"Proceeding with traditional automation for session {session_id}")
                
                # Advance session to MATCHING phase for traditional patterns
                session.phase = Phase.MATCHING
                session.progress = 60
                session.updated_at = datetime.now()
                await store.update_session(session_id, session)
                
                result = {
                    "questions": [],
                    "session_id": session_id,
                    "phase": Phase.MATCHING.value,
                    "automation_assessment": {
                        "suitability": assessment.suitability.value,
                        "confidence": assessment.confidence,
                        "reasoning": assessment.reasoning,
                        "recommended_approach": assessment.recommended_approach
                    },
                    "proceeding_with_traditional": True
                }
            else:
                # Not suitable for automation - require user choice
                result = {
                    "questions": [],
                    "session_id": session_id,
                    "phase": session.phase.value,
                    "automation_assessment": {
                        "suitability": assessment.suitability.value,
                        "confidence": assessment.confidence,
                        "reasoning": assessment.reasoning,
                        "recommended_approach": assessment.recommended_approach,
                        "challenges": assessment.challenges,
                        "next_steps": assessment.next_steps,
                        "warning_message": assessment.warning_message or "This requirement may not be suitable for automation"
                    },
                    "requires_user_decision": True
                }
        else:
            # Normal Q&A flow - we have questions to ask
            result = {
                "questions": [q.to_dict() for q in questions],
                "session_id": session_id,
                "phase": session.phase.value
            }
        
        # Cache the API response
        if questions:
            get_qa_questions._api_question_cache[api_cache_key] = (result, datetime.now())
            app_logger.info(f"Cached {len(questions)} questions for session {session_id}")
        else:
            app_logger.info(f"No questions to cache for session {session_id} - assessment result returned")
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return result
        
    except Exception as e:
        app_logger.error(f"Error getting Q&A questions for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/force_advance")
async def force_advance_session(session_id: str, request: dict, response: Response):
    """Force advance a session to a specific phase (user override)."""
    try:
        target_phase = request.get('target_phase')
        user_override = request.get('user_override', False)
        
        if not target_phase:
            raise HTTPException(status_code=400, detail="target_phase is required")
        
        if not user_override:
            raise HTTPException(status_code=400, detail="user_override must be true for force advance")
        
        # Get session
        store = get_session_store()
        session = await store.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Map string to Phase enum
        from app.state.store import Phase
        phase_mapping = {
            'PARSING': Phase.PARSING,
            'VALIDATING': Phase.VALIDATING,
            'QNA': Phase.QNA,
            'MATCHING': Phase.MATCHING,
            'RECOMMENDING': Phase.RECOMMENDING,
            'DONE': Phase.DONE
        }
        
        new_phase = phase_mapping.get(target_phase)
        if not new_phase:
            raise HTTPException(status_code=400, detail=f"Invalid target_phase: {target_phase}")
        
        # Update session phase
        session.phase = new_phase
        session.progress = 60 if new_phase == Phase.MATCHING else 80 if new_phase == Phase.RECOMMENDING else 100
        session.updated_at = datetime.now()
        
        # Mark that this was a user override
        session.requirements['user_override'] = True
        session.requirements['override_reason'] = 'User chose to proceed despite automation suitability concerns'
        
        await store.update_session(session_id, session)
        
        app_logger.info(f"Force advanced session {session_id} to {target_phase} by user override")
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return {"success": True, "new_phase": target_phase, "message": "Session advanced successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error force advancing session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qa/{session_id}", response_model=QAResponse)
async def process_qa(session_id: str, request: QARequest, response: Response):
    """Process Q&A answers."""
    try:
        from datetime import datetime
        
        # Get session to retrieve provider configuration
        store = get_session_store()
        session = await store.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create provider config from session
        provider_config = None
        if session.provider_config:
            app_logger.info(f"Retrieved provider config from session: {session.provider_config}")
            provider_config = ProviderConfig(**session.provider_config)
        else:
            app_logger.warning("No provider config found in session")
        
        question_loop = get_question_loop(provider_config, session_id)
        result = await question_loop.process_answers(session_id, request.answers)
        
        # If Q&A is complete, advance to MATCHING phase and clear caches
        if result.complete:
            # Clear question caches when Q&A is complete
            if hasattr(get_qa_questions, '_api_question_cache'):
                api_cache_key = f"{session_id}_questions"
                if api_cache_key in get_qa_questions._api_question_cache:
                    del get_qa_questions._api_question_cache[api_cache_key]
            
            session = await store.get_session(session_id)  # Refresh session
            if session and session.phase == Phase.QNA:
                session.phase = Phase.MATCHING
                session.progress = 60
                session.updated_at = datetime.now()
                await store.update_session(session_id, session)
                app_logger.info(f"Advanced session {session_id} from QNA to MATCHING phase")
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return QAResponse(
            complete=result.complete,
            next_questions=[q.to_dict() for q in result.next_questions]
        )
        
    except Exception as e:
        app_logger.error(f"Error in Q&A for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/sessions/{session_id}/enhanced_data")
async def update_session_enhanced_data(session_id: str, enhanced_data: dict, response: Response):
    """Update session recommendations with enhanced tech stack and architecture explanation."""
    try:
        store = get_session_store()
        session = await store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update recommendations with enhanced data
        enhanced_tech_stack = enhanced_data.get('enhanced_tech_stack', [])
        architecture_explanation = enhanced_data.get('architecture_explanation', '')
        
        if enhanced_tech_stack or architecture_explanation:
            for recommendation in session.recommendations:
                recommendation.enhanced_tech_stack = enhanced_tech_stack
                recommendation.architecture_explanation = architecture_explanation
        
        session.updated_at = datetime.now()
        await store.update_session(session_id, session)
        
        app_logger.info(f"Updated session {session_id} with enhanced data: {len(enhanced_tech_stack)} tech items, {len(architecture_explanation)} chars explanation")
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return {"status": "success", "message": "Enhanced data updated"}
    except Exception as e:
        app_logger.error(f"Failed to update enhanced data for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match", response_model=MatchResponse)
async def match_patterns(request: MatchRequest, response: Response):
    """Match patterns against requirements."""
    try:
        store = get_session_store()
        session = await store.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        matcher = await get_pattern_matcher()
        # Get constraints from session requirements if available
        constraints = {
            "banned_tools": session.requirements.get("banned_tools", []),
            "required_integrations": session.requirements.get("required_integrations", []),
            "compliance_requirements": session.requirements.get("compliance_requirements", [])
        }
        
        matches = await matcher.match_patterns(
            session.requirements, 
            constraints, 
            top_k=request.top_k
        )
        
        # Log pattern matches for analytics
        for match in matches:
            try:
                await log_pattern_match(
                    session_id=request.session_id,
                    pattern_id=match.pattern_id,
                    score=match.blended_score,
                    accepted=None  # Will be updated later if user accepts/rejects
                )
                app_logger.debug(f"Logged pattern match: {match.pattern_id} (score: {match.blended_score:.3f})")
            except Exception as e:
                app_logger.error(f"Failed to log pattern match for {match.pattern_id}: {e}")
        
        # Update session with matches
        session.matches = [
            type('PatternMatch', (), {
                'pattern_id': m.pattern_id,
                'score': m.blended_score,
                'rationale': m.rationale,
                'confidence': m.confidence,
                'dict': lambda: {
                    'pattern_id': m.pattern_id,
                    'score': m.blended_score,
                    'rationale': m.rationale,
                    'confidence': m.confidence
                }
            })() for m in matches
        ]
        session.phase = Phase.MATCHING
        session.progress = 80
        await store.update_session(request.session_id, session)
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return MatchResponse(
            candidates=[m.to_dict() for m in matches]
        )
        
    except Exception as e:
        app_logger.error(f"Error in pattern matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend", response_model=RecommendResponse)
async def generate_recommendations(request: RecommendRequest, response: Response):
    """Generate automation recommendations."""
    try:
        store = get_session_store()
        session = await store.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # First get pattern matches if not already done
        if not session.matches:
            matcher = await get_pattern_matcher()
            constraints = {"banned_tools": []}
            matches = await matcher.match_patterns(
                session.requirements, 
                constraints, 
                top_k=request.top_k
            )
        else:
            # Convert stored matches back to MatchResult objects with proper data
            from app.pattern.matcher import MatchResult
            pattern_loader = PatternLoader(str(get_settings().pattern_library_path))
            patterns = pattern_loader.load_patterns()
            pattern_dict = {p["pattern_id"]: p for p in patterns}
            
            matches = []
            for m in session.matches:
                # Get pattern data for proper feasibility and tech stack
                pattern_data = pattern_dict.get(m.pattern_id, {})
                
                match_result = MatchResult(
                    pattern_id=m.pattern_id,
                    pattern_name=pattern_data.get("name", f"Pattern {m.pattern_id}"),
                    feasibility=pattern_data.get("feasibility", "Partially Automatable"),
                    tech_stack=pattern_data.get("tech_stack", ["Python", "FastAPI"]),
                    confidence=m.confidence,
                    tag_score=0.8,
                    vector_score=0.7,
                    blended_score=m.score,
                    rationale=m.rationale
                )
                matches.append(match_result)
        
        # Get provider config from session and create LLM provider
        provider_config = None
        if session.provider_config:
            provider_config = ProviderConfig(**session.provider_config)
        
        # Create LLM provider for agentic recommendation service
        llm_provider = create_llm_provider(provider_config, request.session_id)
        
        # Generate recommendations with LLM provider
        rec_service = get_recommendation_service(llm_provider)
        
        recommendations = await rec_service.generate_agentic_recommendations(session.requirements, request.session_id)
        
        # Update session
        session.recommendations = recommendations
        session.phase = Phase.DONE
        session.progress = 100
        await store.update_session(request.session_id, session)
        
        # Prepare response
        overall_feasibility = recommendations[0].feasibility if recommendations else "Unknown"
        all_tech_stack = []
        for rec in recommendations:
            all_tech_stack.extend(rec.tech_stack)
        unique_tech_stack = list(set(all_tech_stack))
        
        reasoning = recommendations[0].reasoning if recommendations else "No recommendations available"
        
        # Create response data
        response_data = RecommendResponse(
            feasibility=overall_feasibility,
            recommendations=[rec.to_dict() for rec in recommendations],
            tech_stack=unique_tech_stack,
            reasoning=reasoning
        )
        
        # Validate output for banned tools
        if not validate_output_security(response_data.model_dump()):
            app_logger.error(f"Security validation failed for recommendations in session {request.session_id}")
            raise HTTPException(
                status_code=500, 
                detail="Generated recommendations failed security validation"
            )
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return response_data
        
    except Exception as e:
        app_logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export", response_model=ExportResponse)
async def export_results(request: ExportRequest, response: Response):
    """Export session results with format validation."""
    try:
        store = get_session_store()
        session = await store.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create LLM provider for comprehensive exports
        llm_provider = None
        if request.format in ["comprehensive", "report"]:
            try:
                # Create provider config from session
                provider_config = None
                if session.provider_config:
                    provider_config = ProviderConfig(**session.provider_config)
                
                # Create LLM provider for comprehensive analysis
                llm_provider = create_llm_provider(provider_config, request.session_id)
                app_logger.info(f"Created LLM provider for comprehensive export: {session.provider_config}")
            except Exception as e:
                app_logger.warning(f"Could not create LLM provider for comprehensive export: {e}")
                # Continue without LLM provider - will use fallback analysis
        
        export_service = get_export_service(llm_provider)
        
        # Validate session is ready for export
        if not export_service.validate_session_for_export(session):
            raise HTTPException(
                status_code=400, 
                detail="Session is not ready for export. Ensure processing is complete."
            )
        
        # Validate format
        if request.format not in export_service.get_supported_formats():
            supported = ", ".join(export_service.get_supported_formats())
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid format '{request.format}'. Supported formats: {supported}"
            )
        
        # Export the session
        file_path, download_url, file_info = export_service.export_session(session, request.format)
        
        app_logger.info(f"Exported session {request.session_id} to {request.format} format")
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return ExportResponse(
            download_url=download_url,
            file_path=file_path,
            file_info=file_info
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        app_logger.error(f"Validation error exporting session {request.session_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error exporting session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/providers/bedrock/generate-credentials", response_model=GenerateCredentialsResponse)
async def generate_bedrock_credentials(request: GenerateCredentialsRequest, response: Response):
    """Generate short-term AWS credentials for Bedrock access."""
    try:
        app_logger.info(f"Generating short-term credentials for Bedrock in {request.region}")
        
        provider = BedrockProvider(
            model="anthropic.claude-3-haiku-20240307-v1:0",  # Dummy model for credential generation
            region=request.region,
            aws_access_key_id=request.aws_access_key_id,
            aws_secret_access_key=request.aws_secret_access_key,
            aws_session_token=request.aws_session_token
        )
        
        credentials = await provider.generate_short_term_credentials()
        
        return GenerateCredentialsResponse(
            ok=True,
            message="Short-term credentials generated successfully",
            credentials=credentials
        )
        
    except Exception as e:
        app_logger.error(f"Failed to generate credentials: {e}")
        return GenerateCredentialsResponse(
            ok=False,
            message=f"Failed to generate credentials: {str(e)}"
        )


@app.post("/providers/test", response_model=ProviderTestResponse)
async def test_provider(request: ProviderTestRequest, response: Response):
    """Test LLM provider connection."""
    try:
        app_logger.info(f"Testing provider: {request.provider} with model: {request.model}")
        
        if request.provider == "openai":
            if not request.api_key:
                return ProviderTestResponse(ok=False, message="API key required for OpenAI")
            
            provider = OpenAIProvider(api_key=request.api_key, model=request.model)
            success, error_msg = await provider.test_connection_detailed()
            
            return ProviderTestResponse(
                ok=success,
                message="Connection successful" if success else f"Connection failed: {error_msg}"
            )
            
        elif request.provider == "claude":
            if not request.api_key:
                return ProviderTestResponse(ok=False, message="API key required for Claude")
            
            provider = ClaudeProvider(api_key=request.api_key, model=request.model)
            success = await provider.test_connection()
            
            return ProviderTestResponse(
                ok=success,
                message="Connection successful" if success else "Connection failed: Unable to connect to Claude API"
            )
            
        elif request.provider == "bedrock":
            region = request.region or "us-east-1"
            provider = BedrockProvider(
                model=request.model, 
                region=region,
                aws_access_key_id=request.aws_access_key_id,
                aws_secret_access_key=request.aws_secret_access_key,
                aws_session_token=request.aws_session_token,
                bedrock_api_key=getattr(request, 'bedrock_api_key', None)
            )
            success = await provider.test_connection()
            
            auth_method = "API key" if getattr(request, 'bedrock_api_key', None) else "AWS credentials"
            return ProviderTestResponse(
                ok=success,
                message=f"Connection successful using {auth_method}" if success else f"Connection failed: Unable to connect to Bedrock in {region} using {auth_method}"
            )
            
        elif request.provider == "internal":
            if not request.endpoint_url:
                return ProviderTestResponse(ok=False, message="Endpoint URL required for internal provider")
            
            provider = InternalProvider(
                endpoint_url=request.endpoint_url,
                model=request.model,
                api_key=request.api_key
            )
            success = await provider.test_connection()
            
            return ProviderTestResponse(
                ok=success,
                message="Connection successful" if success else f"Connection failed: Unable to connect to {request.endpoint_url}"
            )
            
        elif request.provider == "fake":
            # FakeLLM always works
            return ProviderTestResponse(
                ok=True,
                message="FakeLLM connection successful (no real API call made)"
            )
            
        else:
            return ProviderTestResponse(
                ok=False, 
                message=f"Provider {request.provider} not supported. Available: openai, claude, bedrock, internal, fake"
            )
            
    except Exception as e:
        app_logger.error(f"Error testing provider {request.provider}: {e}")
        return ProviderTestResponse(ok=False, message=f"Unexpected error: {str(e)}")


@app.post("/providers/models", response_model=ModelDiscoveryResponse)
async def discover_models(request: ModelDiscoveryRequest, response: Response):
    """Discover available models for a provider."""
    try:
        app_logger.info(f"Discovering models for provider: {request.provider}")
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        models = []
        
        if request.provider == "openai":
            if not request.api_key:
                return ModelDiscoveryResponse(
                    ok=False, 
                    message="API key required for OpenAI model discovery",
                    models=[]
                )
            
            discovered_models = await model_discovery.get_available_models(
                "openai", 
                api_key=request.api_key
            )
            
            models = [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    description=model.description,
                    context_length=model.context_length,
                    capabilities=model.capabilities
                )
                for model in discovered_models
            ]
            
        elif request.provider == "claude":
            if not request.api_key:
                return ModelDiscoveryResponse(
                    ok=False, 
                    message="API key required for Claude model discovery",
                    models=[]
                )
            
            discovered_models = await model_discovery.get_available_models(
                "claude", 
                api_key=request.api_key
            )
            
            models = [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    description=model.description,
                    context_length=model.context_length,
                    capabilities=model.capabilities
                )
                for model in discovered_models
            ]
            
        elif request.provider == "bedrock":
            region = request.region or "us-east-1"
            discovered_models = await model_discovery.get_available_models(
                "bedrock", 
                region=region,
                aws_access_key_id=request.aws_access_key_id,
                aws_secret_access_key=request.aws_secret_access_key,
                aws_session_token=request.aws_session_token,
                bedrock_api_key=getattr(request, 'bedrock_api_key', None)
            )
            
            models = [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    description=model.description,
                    capabilities=model.capabilities
                )
                for model in discovered_models
            ]
            
        elif request.provider == "internal":
            if not request.endpoint_url:
                return ModelDiscoveryResponse(
                    ok=False, 
                    message="Endpoint URL required for internal provider model discovery",
                    models=[]
                )
            
            discovered_models = await model_discovery.get_available_models(
                "internal", 
                endpoint_url=request.endpoint_url,
                api_key=request.api_key
            )
            
            models = [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    description=model.description,
                    capabilities=model.capabilities
                )
                for model in discovered_models
            ]
            
        elif request.provider == "fake":
            # Return fake models for testing
            models = [
                ModelInfo(
                    id="fake-llm",
                    name="Fake LLM",
                    description="Deterministic fake model for testing",
                    capabilities=["text", "testing"]
                )
            ]
            
        else:
            return ModelDiscoveryResponse(
                ok=False, 
                message=f"Provider {request.provider} not supported. Available: openai, claude, bedrock, internal, fake",
                models=[]
            )
        
        app_logger.info(f"Discovered {len(models)} models for {request.provider}")
        
        return ModelDiscoveryResponse(
            ok=True,
            message=f"Successfully discovered {len(models)} models",
            models=models
        )
        
    except Exception as e:
        app_logger.error(f"Error discovering models for provider {request.provider}: {e}")
        return ModelDiscoveryResponse(
            ok=False,
            message=f"Failed to discover models: {str(e)}",
            models=[]
        )


@app.post("/jira/test", response_model=JiraTestResponse)
async def test_jira_connection(request: JiraTestRequest, response: Response):
    """Test Jira connection with enhanced Data Center support and authentication fallback."""
    try:
        # Validate authentication configuration first
        auth_errors = request.validate_auth_config()
        if auth_errors:
            error_detail = JiraErrorDetail(
                error_type="configuration_error",
                message="Invalid authentication configuration",
                troubleshooting_steps=[
                    "Review authentication requirements for selected auth type",
                    "Ensure all required fields are provided"
                ] + auth_errors,
                documentation_links=[
                    "https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/",
                    "https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html"
                ]
            )
            
            SecurityHeaders.add_security_headers(response)
            return JiraTestResponse(
                ok=False,
                message="Authentication configuration validation failed",
                error_details=error_detail
            )
        
        # Create JiraConfig from request
        from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
        
        # Map string auth type to enum
        auth_type_mapping = {
            "api_token": JiraAuthType.API_TOKEN,
            "pat": JiraAuthType.PERSONAL_ACCESS_TOKEN,
            "sso": JiraAuthType.SSO,
            "basic": JiraAuthType.BASIC
        }
        
        jira_config = JiraConfig(
            base_url=request.base_url,
            auth_type=auth_type_mapping.get(request.auth_type, JiraAuthType.API_TOKEN),
            
            # Authentication fields
            email=request.email,
            api_token=request.api_token,
            username=request.username,
            password=request.password,
            personal_access_token=request.personal_access_token,
            
            # Network configuration
            verify_ssl=request.verify_ssl,
            ca_cert_path=request.ca_cert_path,
            proxy_url=request.proxy_url,
            timeout=request.timeout,
            
            # SSO configuration
            use_sso=request.use_sso,
            sso_session_cookie=request.sso_session_cookie,
            
            # Data Center configuration
            context_path=request.context_path,
            custom_port=request.custom_port,
            
            # Retry configuration
            max_retries=request.max_retries,
            retry_delay=request.retry_delay
        )
        
        # Create Jira service with enhanced configuration
        jira_service = JiraService(jira_config)
        
        # Perform auto-configuration to detect deployment type
        try:
            auto_config = await jira_service.auto_configure()
            jira_service.config = auto_config
            app_logger.info(f"Auto-detected deployment type: {auto_config.deployment_type}")
        except Exception as e:
            app_logger.warning(f"Auto-configuration failed, using provided config: {e}")
        
        # Test connection with fallback authentication
        try:
            connection_result = await jira_service.test_connection_with_fallback()
            
            if connection_result.success:
                # Prepare successful response with deployment info
                deployment_info = None
                if connection_result.deployment_info:
                    deployment_info = {
                        "deployment_type": connection_result.deployment_info.deployment_type.value,
                        "version": connection_result.deployment_info.version,
                        "build_number": connection_result.deployment_info.build_number,
                        "base_url_normalized": connection_result.deployment_info.base_url_normalized,
                        "context_path": connection_result.deployment_info.context_path,
                        "supports_sso": connection_result.deployment_info.supports_sso,
                        "supports_pat": connection_result.deployment_info.supports_pat
                    }
                
                # Determine available auth methods
                auth_methods = ["api_token"]  # Always available
                if connection_result.deployment_info:
                    if connection_result.deployment_info.supports_pat:
                        auth_methods.append("pat")
                    if connection_result.deployment_info.supports_sso:
                        auth_methods.append("sso")
                    # Basic auth is typically available for Data Center
                    if connection_result.deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER:
                        auth_methods.append("basic")
                
                # Detect API version
                api_version = None
                try:
                    api_version = await jira_service.detect_and_set_api_version()
                except Exception as e:
                    app_logger.warning(f"API version detection failed: {e}")
                
                SecurityHeaders.add_security_headers(response)
                return JiraTestResponse(
                    ok=True,
                    message="Jira connection successful",
                    deployment_info=deployment_info,
                    auth_methods_available=auth_methods,
                    api_version_detected=api_version,
                    ssl_configuration=connection_result.ssl_configuration
                )
            
            else:
                # Connection failed, provide detailed error information
                error_detail = None
                if connection_result.error_details:
                    error_detail = JiraErrorDetail(
                        error_type=connection_result.error_details.get("error_type", "connection_error"),
                        error_code=connection_result.error_details.get("error_code"),
                        message=connection_result.error_details.get("message", "Connection failed"),
                        troubleshooting_steps=connection_result.troubleshooting_steps,
                        documentation_links=connection_result.error_details.get("documentation_links", []),
                        suggested_config_changes=connection_result.error_details.get("suggested_config_changes")
                    )
                
                SecurityHeaders.add_security_headers(response)
                return JiraTestResponse(
                    ok=False,
                    message=connection_result.error_details.get("message", "Connection failed") if connection_result.error_details else "Connection failed",
                    error_details=error_detail,
                    ssl_configuration=connection_result.ssl_configuration
                )
        
        except JiraConnectionError as e:
            error_detail = JiraErrorDetail(
                error_type="connection_error",
                message=str(e),
                troubleshooting_steps=[
                    "Verify the base URL is correct and accessible",
                    "Check network connectivity to the Jira instance",
                    "Ensure firewall rules allow access to Jira",
                    "For Data Center: verify custom port and context path if used"
                ],
                documentation_links=[
                    "https://confluence.atlassian.com/jirakb/unable-to-connect-to-jira-applications-due-to-network-or-firewall-issues-203394974.html"
                ]
            )
            
            SecurityHeaders.add_security_headers(response)
            return JiraTestResponse(
                ok=False,
                message=f"Connection failed: {str(e)}",
                error_details=error_detail
            )
        
        except JiraError as e:
            error_detail = JiraErrorDetail(
                error_type="authentication_error",
                message=str(e),
                troubleshooting_steps=[
                    "Verify authentication credentials are correct",
                    "Check if the user account has necessary permissions",
                    "For API tokens: ensure token is not expired",
                    "For PAT: verify token has required scopes",
                    "For SSO: check if session is still valid"
                ],
                documentation_links=[
                    "https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/",
                    "https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html"
                ]
            )
            
            SecurityHeaders.add_security_headers(response)
            return JiraTestResponse(
                ok=False,
                message=f"Authentication failed: {str(e)}",
                error_details=error_detail
            )
        
    except Exception as e:
        app_logger.error(f"Unexpected error testing Jira connection: {e}")
        
        error_detail = JiraErrorDetail(
            error_type="unexpected_error",
            message=f"Unexpected error: {str(e)}",
            troubleshooting_steps=[
                "Check application logs for detailed error information",
                "Verify all required configuration fields are provided",
                "Try with a simpler configuration first",
                "Contact system administrator if the issue persists"
            ]
        )
        
        SecurityHeaders.add_security_headers(response)
        return JiraTestResponse(
            ok=False,
            message=f"Unexpected error: {str(e)}",
            error_details=error_detail
        )


@app.post("/jira/fetch", response_model=JiraFetchResponse)
async def fetch_jira_ticket(request: JiraFetchRequest, response: Response):
    """Fetch Jira ticket with enhanced Data Center support and API version detection."""
    try:
        # Validate authentication configuration first
        auth_errors = request.validate_auth_config()
        if auth_errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Authentication configuration validation failed: {'; '.join(auth_errors)}"
            )
        
        # Create JiraConfig from request
        from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
        
        # Map string auth type to enum
        auth_type_mapping = {
            "api_token": JiraAuthType.API_TOKEN,
            "pat": JiraAuthType.PERSONAL_ACCESS_TOKEN,
            "sso": JiraAuthType.SSO,
            "basic": JiraAuthType.BASIC
        }
        
        jira_config = JiraConfig(
            base_url=request.base_url,
            auth_type=auth_type_mapping.get(request.auth_type, JiraAuthType.API_TOKEN),
            
            # Authentication fields
            email=request.email,
            api_token=request.api_token,
            username=request.username,
            password=request.password,
            personal_access_token=request.personal_access_token,
            
            # Network configuration
            verify_ssl=request.verify_ssl,
            ca_cert_path=request.ca_cert_path,
            proxy_url=request.proxy_url,
            timeout=request.timeout,
            
            # SSO configuration
            use_sso=request.use_sso,
            sso_session_cookie=request.sso_session_cookie,
            
            # Data Center configuration
            context_path=request.context_path,
            custom_port=request.custom_port,
            
            # Retry configuration
            max_retries=request.max_retries,
            retry_delay=request.retry_delay
        )
        
        # Create Jira service with enhanced configuration
        jira_service = JiraService(jira_config)
        
        # Perform auto-configuration to detect deployment type and API version
        try:
            auto_config = await jira_service.auto_configure()
            jira_service.config = auto_config
            app_logger.info(f"Auto-detected deployment type: {auto_config.deployment_type}")
        except Exception as e:
            app_logger.warning(f"Auto-configuration failed, using provided config: {e}")
        
        # Detect and set API version
        api_version = None
        try:
            api_version = await jira_service.detect_and_set_api_version()
            app_logger.info(f"Using API version: {api_version}")
        except Exception as e:
            app_logger.warning(f"API version detection failed, using default: {e}")
            api_version = "3"  # Default fallback
        
        # Fetch ticket with API version support
        ticket = await jira_service.fetch_ticket(request.ticket_key)
        
        # Map to requirements
        requirements = jira_service.map_ticket_to_requirements(ticket)
        
        # Prepare deployment info
        deployment_info = None
        if hasattr(jira_service, 'deployment_info') and jira_service.deployment_info:
            deployment_info = {
                "deployment_type": jira_service.deployment_info.deployment_type.value,
                "version": jira_service.deployment_info.version,
                "build_number": jira_service.deployment_info.build_number,
                "base_url_normalized": jira_service.deployment_info.base_url_normalized
            }
        
        result = JiraFetchResponse(
            ticket_data=ticket.model_dump(),
            requirements=requirements,
            deployment_info=deployment_info,
            api_version_used=api_version
        )
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        return result
        
    except HTTPException:
        # Re-raise HTTPExceptions to preserve status codes
        raise
    except JiraConnectionError as e:
        app_logger.error(f"Jira connection failed for ticket {request.ticket_key}: {e}")
        raise HTTPException(
            status_code=401, 
            detail=f"Jira connection failed: {str(e)}. Please verify your credentials and network configuration."
        )
    except JiraTicketNotFoundError as e:
        app_logger.error(f"Jira ticket not found: {request.ticket_key}: {e}")
        raise HTTPException(
            status_code=404, 
            detail=f"Ticket {request.ticket_key} not found: {str(e)}"
        )
    except JiraError as e:
        app_logger.error(f"Jira error fetching ticket {request.ticket_key}: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"Jira error: {str(e)}. Check your authentication and permissions."
        )
    except Exception as e:
        app_logger.error(f"Unexpected error fetching Jira ticket {request.ticket_key}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch Jira ticket: {str(e)}. Check application logs for details."
        )


@app.post("/providers/test")
async def test_provider(request: dict, response: Response):
    """Test LLM provider connection."""
    try:
        provider = request.get("provider", "")
        model = request.get("model", "")
        api_key = request.get("api_key", "")
        
        app_logger.info(f"Testing provider: {provider} with model: {model}")
        
        if provider == "openai":
            if not api_key:
                result = {"ok": False, "message": "API key required for OpenAI"}
            else:
                # Validate model name
                valid_models = ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
                if model not in valid_models:
                    result = {
                        "ok": False, 
                        "message": f"Invalid model '{model}'. Valid models: {', '.join(valid_models)}"
                    }
                else:
                    provider_instance = OpenAIProvider(api_key=api_key, model=model)
                    success, error_msg = await provider_instance.test_connection_detailed()
                    
                    result = {
                        "ok": success,
                        "message": "Connection successful" if success else f"Connection failed: {error_msg}"
                    }
        elif provider == "fake":
            # FakeLLM always works
            result = {
                "ok": True,
                "message": "FakeLLM connection successful (no real API call made)"
            }
        else:
            result = {"ok": False, "message": f"Provider {provider} not implemented"}
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        return result
            
    except Exception as e:
        app_logger.error(f"Error testing provider {provider}: {e}")
        result = {"ok": False, "message": f"Unexpected error: {str(e)}"}
        SecurityHeaders.add_security_headers(response)
        return result






if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)