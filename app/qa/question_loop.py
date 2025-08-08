"""Q&A system for collecting missing requirements information."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.llm.base import LLMProvider
from app.state.store import SessionStore, QAExchange
from app.utils.logger import app_logger


@dataclass
class Question:
    """Individual question data."""
    text: str
    field: str
    template_category: str
    options: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "field": self.field,
            "template_category": self.template_category,
            "options": self.options
        }


@dataclass
class QAResult:
    """Result of Q&A processing."""
    complete: bool
    confidence: float
    next_questions: List[Question]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "complete": self.complete,
            "confidence": self.confidence,
            "next_questions": [q.to_dict() for q in self.next_questions]
        }


class TemplateLoader:
    """Loads and manages question templates."""
    
    def __init__(self, templates_path: Optional[str] = None):
        if templates_path is None:
            templates_path = Path(__file__).parent / "templates.json"
        self.templates_path = Path(templates_path)
        self._templates_cache: Optional[Dict[str, Any]] = None
    
    def load_templates(self) -> Dict[str, Any]:
        """Load question templates from JSON file."""
        if self._templates_cache is not None:
            return self._templates_cache
        
        try:
            with open(self.templates_path, 'r') as f:
                templates = json.load(f)
            
            self._templates_cache = templates
            app_logger.debug(f"Loaded {len(templates)} question templates")
            return templates
            
        except Exception as e:
            app_logger.error(f"Failed to load question templates: {e}")
            return {}
    
    def get_templates_for_fields(self, missing_fields: List[str]) -> List[Dict[str, Any]]:
        """Get templates that cover the missing fields."""
        templates = self.load_templates()
        matching_templates = []
        
        for template_name, template_data in templates.items():
            template_fields = template_data.get("fields", [])
            
            # Check if this template covers any missing fields
            if any(field in template_fields for field in missing_fields):
                matching_templates.append({
                    "name": template_name,
                    **template_data
                })
        
        # If no specific matches, return general templates
        if not matching_templates:
            for template_name, template_data in templates.items():
                if template_data.get("domain") == "general":
                    matching_templates.append({
                        "name": template_name,
                        **template_data
                    })
        
        return matching_templates
    
    def get_templates_for_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get templates for a specific domain."""
        templates = self.load_templates()
        domain_templates = []
        
        for template_name, template_data in templates.items():
            if template_data.get("domain") == domain:
                domain_templates.append({
                    "name": template_name,
                    **template_data
                })
        
        return domain_templates


class QuestionLoop:
    """Manages the Q&A loop for collecting missing information."""
    
    def __init__(self, 
                 llm_provider: LLMProvider,
                 template_loader: TemplateLoader,
                 session_store: SessionStore):
        """Initialize Q&A loop.
        
        Args:
            llm_provider: LLM provider for generating contextual questions
            template_loader: Loader for question templates
            session_store: Session state storage
        """
        self.llm_provider = llm_provider
        self.template_loader = template_loader
        self.session_store = session_store
    
    def _identify_missing_fields(self, requirements: Dict[str, Any]) -> List[str]:
        """Identify missing fields from requirements."""
        # Core fields that should be present for most automations
        core_fields = [
            "frequency", "data_sensitivity", "human_review", "processing_time",
            "criticality", "integrations", "typical_volume"
        ]
        
        missing_fields = []
        for field in core_fields:
            if field not in requirements or not requirements[field]:
                missing_fields.append(field)
        
        # Domain-specific fields
        domain = requirements.get("domain", "")
        if domain == "data_processing":
            domain_fields = ["target_websites", "content_change_frequency"]
            for field in domain_fields:
                if field not in requirements:
                    missing_fields.append(field)
        elif domain == "system_integration":
            domain_fields = ["api_rate_limits", "auth_method"]
            for field in domain_fields:
                if field not in requirements:
                    missing_fields.append(field)
        elif domain == "document_management":
            domain_fields = ["document_types", "extraction_fields", "accuracy_requirements"]
            for field in domain_fields:
                if field not in requirements:
                    missing_fields.append(field)
        
        return missing_fields
    
    def _calculate_confidence(self, requirements: Dict[str, Any]) -> float:
        """Calculate confidence based on requirement completeness."""
        total_possible_fields = 10  # Approximate number of important fields
        filled_fields = len([v for v in requirements.values() if v])
        
        # Base confidence on completeness
        completeness_ratio = min(filled_fields / total_possible_fields, 1.0)
        
        # Boost confidence if description is detailed
        description = requirements.get("description", "")
        if len(description) > 100:
            completeness_ratio += 0.1
        
        # Boost confidence if domain is specified
        if requirements.get("domain"):
            completeness_ratio += 0.1
        
        return min(completeness_ratio, 1.0)
    
    async def _generate_question_from_template(self, 
                                             template: Dict[str, Any], 
                                             requirements: Dict[str, Any]) -> List[Question]:
        """Generate questions from a template."""
        questions = []
        template_questions = template.get("questions", [])
        template_fields = template.get("fields", [])
        template_name = template.get("name", "unknown")
        
        # For now, use template questions directly
        # In a more advanced implementation, we could use LLM to contextualize
        for i, question_text in enumerate(template_questions):
            field = template_fields[i] if i < len(template_fields) else f"field_{i}"
            
            question = Question(
                text=question_text,
                field=field,
                template_category=template_name
            )
            questions.append(question)
        
        return questions
    
    async def generate_questions(self, 
                               session_id: str, 
                               max_questions: int = 5) -> List[Question]:
        """Generate questions for missing information.
        
        Args:
            session_id: Session identifier
            max_questions: Maximum number of questions to generate
            
        Returns:
            List of questions to ask the user
        """
        session = await self.session_store.get_session(session_id)
        if not session:
            app_logger.error(f"Session not found: {session_id}")
            return []
        
        # Check if we've already asked too many questions
        total_questions_asked = sum(len(qa.questions) for qa in session.qa_history)
        if total_questions_asked >= max_questions:
            app_logger.info(f"Max questions ({max_questions}) already reached for session {session_id}")
            return []
        
        # Identify missing fields
        missing_fields = self._identify_missing_fields(session.requirements)
        
        if not missing_fields:
            app_logger.info(f"No missing fields identified for session {session_id}")
            return []
        
        # Get relevant templates
        templates = self.template_loader.get_templates_for_fields(missing_fields)
        
        # Also get domain-specific templates if domain is known
        domain = session.requirements.get("domain")
        if domain:
            domain_templates = self.template_loader.get_templates_for_domain(domain)
            templates.extend(domain_templates)
        
        # Generate questions from templates
        all_questions = []
        for template in templates:
            template_questions = await self._generate_question_from_template(template, session.requirements)
            all_questions.extend(template_questions)
        
        # Remove duplicates and limit to max_questions
        seen_fields = set()
        unique_questions = []
        
        for question in all_questions:
            if question.field not in seen_fields and len(unique_questions) < max_questions:
                seen_fields.add(question.field)
                unique_questions.append(question)
        
        app_logger.info(f"Generated {len(unique_questions)} questions for session {session_id}")
        return unique_questions
    
    def _merge_answers(self, requirements: Dict[str, Any], answers: Dict[str, str]) -> Dict[str, Any]:
        """Merge user answers into requirements."""
        merged = requirements.copy()
        merged.update(answers)
        return merged
    
    async def process_answers(self, 
                            session_id: str, 
                            answers: Dict[str, str]) -> QAResult:
        """Process user answers and update session state.
        
        Args:
            session_id: Session identifier
            answers: User answers mapped by field name
            
        Returns:
            QAResult indicating if more questions are needed
        """
        session = await self.session_store.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        app_logger.info(f"Processing {len(answers)} answers for session {session_id}")
        
        # Merge answers into requirements
        updated_requirements = self._merge_answers(session.requirements, answers)
        
        # Check completeness and confidence
        missing_fields = self._identify_missing_fields(updated_requirements)
        confidence = self._calculate_confidence(updated_requirements)
        
        # Create Q&A exchange record
        qa_exchange = QAExchange(
            questions=[],  # We don't store the questions here, just the answers
            answers=answers,
            timestamp=session.updated_at
        )
        
        # Update session state
        session.requirements = updated_requirements
        session.missing_fields = missing_fields
        session.qa_history.append(qa_exchange)
        
        await self.session_store.update_session(session_id, session)
        
        # Determine if Q&A is complete
        complete = len(missing_fields) == 0 or confidence > 0.8
        
        # Generate next questions if not complete
        next_questions = []
        if not complete:
            next_questions = await self.generate_questions(session_id)
            if not next_questions:
                complete = True  # No more questions to ask
        
        result = QAResult(
            complete=complete,
            confidence=confidence,
            next_questions=next_questions
        )
        
        app_logger.info(f"Q&A result for session {session_id}: complete={complete}, confidence={confidence:.2f}")
        return result