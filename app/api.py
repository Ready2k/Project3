"""FastAPI application for AgenticOrNot."""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from app.config import Settings, load_settings
from app.embeddings.engine import SentenceTransformerEmbedder
from app.embeddings.index import FAISSIndex
from app.exporters.service import ExportService
from app.llm.openai_provider import OpenAIProvider
from app.llm.fakes import FakeLLM
from app.pattern.loader import PatternLoader
from app.pattern.matcher import PatternMatcher
from app.qa.question_loop import QuestionLoop, TemplateLoader
from app.services.recommendation import RecommendationService
from app.state.store import SessionState, Phase, DiskCacheStore
from app.utils.logger import app_logger

# Initialize FastAPI app
app = FastAPI(
    title="AgenticOrNot API",
    description="API for assessing automation feasibility of requirements",
    version="1.3.2"
)

# Global dependencies
settings: Optional[Settings] = None
session_store: Optional[DiskCacheStore] = None
pattern_matcher: Optional[PatternMatcher] = None
question_loop: Optional[QuestionLoop] = None
recommendation_service: Optional[RecommendationService] = None
export_service: Optional[ExportService] = None


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


def get_pattern_matcher() -> PatternMatcher:
    """Get pattern matcher instance."""
    global pattern_matcher
    if pattern_matcher is None:
        settings = get_settings()
        
        # Initialize components
        pattern_loader = PatternLoader(str(settings.pattern_library_path))
        embedder = SentenceTransformerEmbedder()
        faiss_index = FAISSIndex(embedder=embedder)
        
        # Build FAISS index from patterns
        patterns = pattern_loader.load_patterns()
        if patterns:
            descriptions = [p["description"] for p in patterns]
            import asyncio
            asyncio.create_task(faiss_index.build_from_texts(descriptions))
        
        pattern_matcher = PatternMatcher(
            pattern_loader=pattern_loader,
            embedding_provider=embedder,
            faiss_index=faiss_index
        )
    
    return pattern_matcher


def create_llm_provider(provider_config: Optional[ProviderConfig] = None):
    """Create LLM provider based on configuration."""
    if not provider_config:
        # Use settings default or fallback to fake
        settings = get_settings()
        if settings.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            return OpenAIProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=settings.model
            )
        else:
            app_logger.warning("No provider configuration found, using FakeLLM")
            return FakeLLM({}, seed=42)
    
    if provider_config.provider == "openai":
        if not provider_config.api_key:
            app_logger.error("OpenAI API key is required")
            return FakeLLM({}, seed=42)
        
        return OpenAIProvider(
            api_key=provider_config.api_key,
            model=provider_config.model
        )
    else:
        app_logger.warning(f"Provider {provider_config.provider} not implemented, using FakeLLM")
        return FakeLLM({}, seed=42)


def get_question_loop(provider_config: Optional[ProviderConfig] = None) -> QuestionLoop:
    """Get question loop instance with provider configuration."""
    llm_provider = create_llm_provider(provider_config)
    template_loader = TemplateLoader()
    store = get_session_store()
    
    return QuestionLoop(
        llm_provider=llm_provider,
        template_loader=template_loader,
        session_store=store
    )


def get_recommendation_service() -> RecommendationService:
    """Get recommendation service instance."""
    global recommendation_service
    if recommendation_service is None:
        recommendation_service = RecommendationService()
    return recommendation_service


def get_export_service() -> ExportService:
    """Get export service instance."""
    global export_service
    if export_service is None:
        settings = get_settings()
        export_service = ExportService(settings.export_path)
    return export_service


# Request/Response models
class ProviderConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    region: Optional[str] = None


class IngestRequest(BaseModel):
    source: str  # "text", "file", "jira"
    payload: Dict[str, Any]
    provider_config: Optional[ProviderConfig] = None


class IngestResponse(BaseModel):
    session_id: str


class StatusResponse(BaseModel):
    phase: str
    progress: int
    missing_fields: List[str]


class QARequest(BaseModel):
    answers: Dict[str, str]


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
    format: str  # "json" or "md"


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


class ProviderTestResponse(BaseModel):
    ok: bool
    message: str


# API Endpoints
@app.post("/ingest", response_model=IngestResponse)
async def ingest_requirements(request: IngestRequest):
    """Ingest requirements and create a new session."""
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Extract requirements from payload
        requirements = {}
        if request.source == "text":
            requirements = {
                "description": request.payload.get("text", ""),
                "domain": request.payload.get("domain"),
                "pattern_types": request.payload.get("pattern_types", [])
            }
        elif request.source == "file":
            # For now, just extract text content
            requirements = {
                "description": request.payload.get("content", ""),
                "filename": request.payload.get("filename")
            }
        elif request.source == "jira":
            requirements = {
                "description": request.payload.get("summary", "") + " " + request.payload.get("description", ""),
                "jira_key": request.payload.get("key"),
                "priority": request.payload.get("priority")
            }
        
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
            updated_at=datetime.now()
        )
        
        # Store session
        store = get_session_store()
        await store.update_session(session_id, session_state)
        
        # Store provider configuration in session for later use
        if request.provider_config:
            session_state.provider_config = request.provider_config.dict()
        
        # Immediately advance to VALIDATING phase (simulate processing)
        session_state.phase = Phase.VALIDATING
        session_state.progress = 30
        session_state.updated_at = datetime.now()
        await store.update_session(session_id, session_state)
        
        # Check if we need Q&A or can proceed to matching
        if not requirements.get("description") or len(requirements.get("description", "").strip()) < 10:
            # Need more information - go to Q&A phase
            session_state.phase = Phase.QNA
            session_state.progress = 40
            session_state.missing_fields = ["workflow_variability", "data_sensitivity", "human_oversight"]
        else:
            # Sufficient information - proceed to matching
            session_state.phase = Phase.MATCHING
            session_state.progress = 60
        
        session_state.updated_at = datetime.now()
        await store.update_session(session_id, session_state)
        
        app_logger.info(f"Created new session: {session_id} in phase: {session_state.phase.value}")
        return IngestResponse(session_id=session_id)
        
    except Exception as e:
        app_logger.error(f"Error in ingest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str):
    """Get session status and progress."""
    try:
        store = get_session_store()
        session = await store.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Auto-advance phases if needed
        if session.phase == Phase.MATCHING and not session.matches:
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
        
        return StatusResponse(
            phase=session.phase.value,
            progress=session.progress,
            missing_fields=session.missing_fields
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting status for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qa/{session_id}", response_model=QAResponse)
async def process_qa(session_id: str, request: QARequest):
    """Process Q&A answers."""
    try:
        question_loop = get_question_loop()
        result = await question_loop.process_answers(session_id, request.answers)
        
        return QAResponse(
            complete=result.complete,
            next_questions=[q.to_dict() for q in result.next_questions]
        )
        
    except Exception as e:
        app_logger.error(f"Error in Q&A for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match", response_model=MatchResponse)
async def match_patterns(request: MatchRequest):
    """Match patterns against requirements."""
    try:
        store = get_session_store()
        session = await store.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        matcher = get_pattern_matcher()
        constraints = {"banned_tools": []}  # TODO: Get from config
        
        matches = await matcher.match_patterns(
            session.requirements, 
            constraints, 
            top_k=request.top_k
        )
        
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
        
        return MatchResponse(
            candidates=[m.to_dict() for m in matches]
        )
        
    except Exception as e:
        app_logger.error(f"Error in pattern matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend", response_model=RecommendResponse)
async def generate_recommendations(request: RecommendRequest):
    """Generate automation recommendations."""
    try:
        store = get_session_store()
        session = await store.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # First get pattern matches if not already done
        if not session.matches:
            matcher = get_pattern_matcher()
            constraints = {"banned_tools": []}
            matches = await matcher.match_patterns(
                session.requirements, 
                constraints, 
                top_k=request.top_k
            )
        else:
            # Convert stored matches back to MatchResult objects (simplified)
            from app.pattern.matcher import MatchResult
            matches = [
                MatchResult(
                    pattern_id=m.pattern_id,
                    pattern_name=f"Pattern {m.pattern_id}",
                    feasibility="Automatable",
                    tech_stack=["Python", "FastAPI"],
                    confidence=m.confidence,
                    tag_score=0.8,
                    vector_score=0.7,
                    blended_score=m.score,
                    rationale=m.rationale
                ) for m in session.matches
            ]
        
        # Generate recommendations
        rec_service = get_recommendation_service()
        recommendations = rec_service.generate_recommendations(matches, session.requirements)
        
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
        
        return RecommendResponse(
            feasibility=overall_feasibility,
            recommendations=[rec.dict() for rec in recommendations],
            tech_stack=unique_tech_stack,
            reasoning=reasoning
        )
        
    except Exception as e:
        app_logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export", response_model=ExportResponse)
async def export_results(request: ExportRequest):
    """Export session results with format validation."""
    try:
        store = get_session_store()
        session = await store.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        export_service = get_export_service()
        
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


@app.post("/providers/test", response_model=ProviderTestResponse)
async def test_provider(request: ProviderTestRequest):
    """Test LLM provider connection."""
    try:
        app_logger.info(f"Testing provider: {request.provider} with model: {request.model}")
        
        if request.provider == "openai":
            if not request.api_key:
                return ProviderTestResponse(ok=False, message="API key required for OpenAI")
            
            # Validate model name
            valid_models = ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
            if request.model not in valid_models:
                return ProviderTestResponse(
                    ok=False, 
                    message=f"Invalid model '{request.model}'. Valid models: {', '.join(valid_models)}"
                )
            
            provider = OpenAIProvider(api_key=request.api_key, model=request.model)
            success, error_msg = await provider.test_connection_detailed()
            
            return ProviderTestResponse(
                ok=success,
                message="Connection successful" if success else f"Connection failed: {error_msg}"
            )
        else:
            return ProviderTestResponse(ok=False, message=f"Provider {request.provider} not implemented")
            
    except Exception as e:
        app_logger.error(f"Error testing provider {request.provider}: {e}")
        return ProviderTestResponse(ok=False, message=f"Unexpected error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.3.2"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)