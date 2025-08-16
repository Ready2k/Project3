"""
API endpoints for User Education and Guidance System.

Provides endpoints for accessing educational content, submitting appeals,
and managing user guidance for the advanced prompt attack defense system.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.security.advanced_prompt_defender import AdvancedPromptDefender
from app.security.defense_config import get_defense_config


# Pydantic models for API requests/responses
class AppealRequest(BaseModel):
    """Request model for submitting an appeal."""
    request_id: str = Field(..., description="ID of the blocked request")
    original_input: str = Field(..., description="Original input that was blocked")
    user_explanation: str = Field(..., description="User's explanation of their intent")
    business_justification: str = Field(..., description="Business justification for the request")
    contact_info: str = Field(..., description="Contact information for follow-up")


class AppealResponse(BaseModel):
    """Response model for appeal submission."""
    appeal_id: str = Field(..., description="Unique appeal ID")
    status: str = Field(..., description="Appeal status")
    message: str = Field(..., description="Confirmation message")


class AppealStatusResponse(BaseModel):
    """Response model for appeal status."""
    appeal_id: str = Field(..., description="Appeal ID")
    status: str = Field(..., description="Current status")
    submitted: str = Field(..., description="Submission timestamp")
    request_id: str = Field(..., description="Original request ID")


class EducationalContentResponse(BaseModel):
    """Response model for educational content."""
    content: Dict[str, str] = Field(..., description="Educational content by topic")


class AcceptableExamplesResponse(BaseModel):
    """Response model for acceptable examples."""
    examples: Dict[str, List[str]] = Field(..., description="Examples by category")


class SystemDocumentationResponse(BaseModel):
    """Response model for system documentation."""
    documentation: str = Field(..., description="Complete system documentation")


class GuidanceStatsResponse(BaseModel):
    """Response model for guidance statistics."""
    stats: Dict[str, Any] = Field(..., description="Guidance system statistics")


# Create router
router = APIRouter(prefix="/user-education", tags=["User Education"])

# Dependency to get the defender instance
def get_defender() -> AdvancedPromptDefender:
    """Get AdvancedPromptDefender instance."""
    config = get_defense_config()
    return AdvancedPromptDefender(config)


@router.get("/educational-content", response_model=EducationalContentResponse)
async def get_educational_content(
    topic: Optional[str] = None,
    defender: AdvancedPromptDefender = Depends(get_defender)
) -> EducationalContentResponse:
    """
    Get educational content about system usage.
    
    Args:
        topic: Specific topic to retrieve (optional, defaults to all)
        
    Returns:
        Educational content by topic
    """
    try:
        content = defender.get_educational_content(topic or "all")
        return EducationalContentResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve educational content: {str(e)}")


@router.get("/acceptable-examples", response_model=AcceptableExamplesResponse)
async def get_acceptable_examples(
    category: Optional[str] = None,
    defender: AdvancedPromptDefender = Depends(get_defender)
) -> AcceptableExamplesResponse:
    """
    Get examples of acceptable business automation requests.
    
    Args:
        category: Specific category to retrieve (optional, defaults to all)
        
    Returns:
        Examples by category
    """
    try:
        examples = defender.get_acceptable_examples(category or "all")
        return AcceptableExamplesResponse(examples=examples)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve examples: {str(e)}")


@router.get("/system-documentation", response_model=SystemDocumentationResponse)
async def get_system_documentation(
    defender: AdvancedPromptDefender = Depends(get_defender)
) -> SystemDocumentationResponse:
    """
    Get comprehensive system documentation for users.
    
    Returns:
        Complete system documentation in markdown format
    """
    try:
        documentation = defender.generate_system_documentation()
        return SystemDocumentationResponse(documentation=documentation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate documentation: {str(e)}")


@router.post("/appeals", response_model=AppealResponse)
async def submit_appeal(
    appeal_request: AppealRequest,
    defender: AdvancedPromptDefender = Depends(get_defender)
) -> AppealResponse:
    """
    Submit an appeal for a misclassified request.
    
    Args:
        appeal_request: Appeal details
        
    Returns:
        Appeal confirmation with ID
    """
    try:
        appeal_id = defender.submit_user_appeal(
            request_id=appeal_request.request_id,
            original_input=appeal_request.original_input,
            user_explanation=appeal_request.user_explanation,
            business_justification=appeal_request.business_justification,
            contact_info=appeal_request.contact_info
        )
        
        return AppealResponse(
            appeal_id=appeal_id,
            status="pending",
            message="Appeal submitted successfully. You will be contacted within 24-48 hours."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit appeal: {str(e)}")


@router.get("/appeals/{appeal_id}", response_model=AppealStatusResponse)
async def get_appeal_status(
    appeal_id: str,
    defender: AdvancedPromptDefender = Depends(get_defender)
) -> AppealStatusResponse:
    """
    Get the status of an appeal request.
    
    Args:
        appeal_id: Appeal ID to check
        
    Returns:
        Appeal status information
    """
    try:
        status = defender.get_appeal_status(appeal_id)
        if not status:
            raise HTTPException(status_code=404, detail="Appeal not found")
        
        return AppealStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve appeal status: {str(e)}")


@router.get("/appeals", response_model=List[Dict[str, Any]])
async def get_pending_appeals(
    defender: AdvancedPromptDefender = Depends(get_defender)
) -> List[Dict[str, Any]]:
    """
    Get all pending appeal requests (admin endpoint).
    
    Returns:
        List of pending appeals
    """
    try:
        pending_appeals = defender.get_pending_appeals()
        return pending_appeals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pending appeals: {str(e)}")


@router.put("/appeals/{appeal_id}")
async def process_appeal(
    appeal_id: str,
    decision: str,
    reviewer_notes: Optional[str] = None,
    defender: AdvancedPromptDefender = Depends(get_defender)
) -> Dict[str, str]:
    """
    Process an appeal request (admin endpoint).
    
    Args:
        appeal_id: Appeal ID to process
        decision: Decision (approved, rejected, under_review)
        reviewer_notes: Optional reviewer notes
        
    Returns:
        Processing confirmation
    """
    try:
        if decision not in ["approved", "rejected", "under_review"]:
            raise HTTPException(
                status_code=400, 
                detail="Decision must be one of: approved, rejected, under_review"
            )
        
        success = defender.process_appeal(appeal_id, decision, reviewer_notes or "")
        if not success:
            raise HTTPException(status_code=404, detail="Appeal not found")
        
        return {
            "message": f"Appeal {appeal_id} has been {decision}",
            "appeal_id": appeal_id,
            "decision": decision
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process appeal: {str(e)}")


@router.get("/stats", response_model=GuidanceStatsResponse)
async def get_guidance_statistics(
    defender: AdvancedPromptDefender = Depends(get_defender)
) -> GuidanceStatsResponse:
    """
    Get statistics about the user education and guidance system.
    
    Returns:
        Guidance system statistics
    """
    try:
        dashboard_data = defender.get_security_dashboard_data()
        stats = dashboard_data.get("user_education_stats", {})
        return GuidanceStatsResponse(stats=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for user education system.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "user-education",
        "message": "User Education and Guidance System is operational"
    }