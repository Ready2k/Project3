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
    question_type: str = "text"  # Default to text input
    options: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "question": self.text,  # UI expects "question" not "text"
            "id": self.field,       # UI expects "id" not "field"
            "type": self.question_type,
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
        # For LLM-generated Q&A, we consider the process complete if:
        # 1. We have a description
        # 2. We have at least 2 additional fields from Q&A
        # 3. Or we've already done one round of Q&A
        
        description = requirements.get("description", "")
        if not description or len(description.strip()) < 10:
            return ["description"]
        
        # Count non-description fields (these come from Q&A answers)
        qa_fields = {k: v for k, v in requirements.items() 
                    if k not in ["description", "domain", "pattern_types", "filename", "jira_key", "priority"]}
        
        # If we have at least 2 Q&A answers, consider it sufficient
        answered_fields = [k for k, v in qa_fields.items() if v and str(v).strip()]
        
        if len(answered_fields) >= 2:
            return []  # Sufficient information
        
        # If we have some answers but not enough, we might need more
        if len(answered_fields) >= 1:
            return []  # One good answer is often enough for basic analysis
        
        # If no Q&A answers yet, we need some
        return ["additional_context"]
    
    def _calculate_confidence(self, requirements: Dict[str, Any]) -> float:
        """Calculate confidence based on requirement completeness."""
        # Base confidence on having a good description
        description = requirements.get("description", "")
        if not description or len(description.strip()) < 10:
            return 0.1
        
        base_confidence = 0.6  # Good description gives us decent confidence
        
        # Count Q&A answers (excluding metadata fields)
        qa_fields = {k: v for k, v in requirements.items() 
                    if k not in ["description", "domain", "pattern_types", "filename", "jira_key", "priority"]}
        
        answered_fields = [k for k, v in qa_fields.items() if v and str(v).strip()]
        
        # Each Q&A answer increases confidence
        qa_boost = min(len(answered_fields) * 0.15, 0.3)  # Max 0.3 boost from Q&A
        
        final_confidence = min(base_confidence + qa_boost, 1.0)
        return final_confidence
    
    async def _generate_question_from_template(self, 
                                             template: Dict[str, Any], 
                                             requirements: Dict[str, Any]) -> List[Question]:
        """Generate questions from a template using LLM."""
        template_name = template.get("name", "unknown")
        template_domain = template.get("domain", "general")
        
        # Create a prompt for the LLM to generate contextual questions
        prompt = f"""You are an expert automation consultant analyzing whether a requirement can be automated with AI agents.

REQUIREMENT: {requirements.get('description', 'No description provided')}

ANALYSIS FOCUS: {template_name} ({template_domain} domain)

Your role is to ask 2-3 specific clarifying questions that will help determine if this requirement can be automated by AI agents. Focus on:

1. **Physical vs Digital**: Is this about physical objects or digital processes?
2. **Data Availability**: What data sources exist to make automated decisions?
3. **Decision Complexity**: How complex are the decisions involved?
4. **Integration Points**: What systems would need to connect?

Generate questions that are:
- Specific to this requirement
- Help distinguish between "Automatable", "Partially Automatable", or "Not Automatable"
- Focus on technical feasibility, not business value

Format your response as a JSON array of questions:
[
  {{"text": "Question 1?", "field": "field_name_1"}},
  {{"text": "Question 2?", "field": "field_name_2"}},
  {{"text": "Question 3?", "field": "field_name_3"}}
]

Only return the JSON array, no other text."""

        try:
            # Generate questions using LLM
            response = await self.llm_provider.generate(prompt)
            
            # Parse the JSON response
            import json
            questions_data = json.loads(response.strip())
            
            questions = []
            for q_data in questions_data:
                question = Question(
                    text=q_data["text"],
                    field=q_data["field"],
                    template_category=template_name,
                    question_type="text"
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            app_logger.error(f"Error generating LLM questions for {template_name}: {e}")
            # Fallback to a generic question
            return [Question(
                text=f"Please provide more details about the {template_name.replace('_', ' ')} aspects of this requirement.",
                field=f"{template_name}_details",
                template_category=template_name,
                question_type="text"
            )]
    
    async def generate_questions(self, 
                               session_id: str, 
                               max_questions: int = 5) -> List[Question]:
        """Generate questions for missing information using LLM.
        
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
        
        # Generate questions directly using LLM instead of templates
        prompt = f"""You are an expert automation consultant. Analyze this requirement and generate clarifying questions.

REQUIREMENT: {session.requirements.get('description', 'No description provided')}

Generate 3-4 specific questions to determine if this can be automated by AI agents.

Focus on:
- Physical vs digital processes
- Available data sources
- Decision complexity
- Current workflow

CRITICAL: Respond with ONLY a valid JSON array, no other text:

[
  {{"text": "Question 1?", "field": "field1"}},
  {{"text": "Question 2?", "field": "field2"}},
  {{"text": "Question 3?", "field": "field3"}}
]"""

        try:
            # Generate questions using LLM
            app_logger.info(f"Generating LLM questions for session {session_id}")
            response = await self.llm_provider.generate(prompt)
            
            app_logger.info(f"LLM response for questions: {response[:200]}...")  # Log first 200 chars
            
            if not response or not response.strip():
                app_logger.error("Empty response from LLM")
                raise ValueError("Empty LLM response")
            
            # Clean the response - sometimes LLM adds extra text
            response = response.strip()
            
            # Try to extract JSON if it's wrapped in other text
            if not response.startswith('['):
                # Look for JSON array in the response
                import re
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    response = json_match.group(0)
                else:
                    app_logger.error(f"No JSON array found in response: {response}")
                    raise ValueError("No JSON array in response")
            
            # Parse the JSON response
            questions_data = json.loads(response)
            
            if not isinstance(questions_data, list):
                app_logger.error(f"Expected list, got {type(questions_data)}: {questions_data}")
                raise ValueError("Response is not a list")
            
            questions = []
            for q_data in questions_data[:max_questions]:  # Limit to max_questions
                if not isinstance(q_data, dict) or 'text' not in q_data or 'field' not in q_data:
                    app_logger.warning(f"Skipping invalid question data: {q_data}")
                    continue
                    
                question = Question(
                    text=q_data["text"],
                    field=q_data["field"],
                    template_category="llm_generated",
                    question_type="text"
                )
                questions.append(question)
            
            app_logger.info(f"Generated {len(questions)} LLM questions for session {session_id}")
            return questions
            
        except Exception as e:
            app_logger.error(f"Error generating LLM questions for session {session_id}: {e}")
            # Fallback to essential questions
            return [
                Question(
                    text="Does this process involve physical objects or digital/virtual entities?",
                    field="physical_vs_digital",
                    template_category="fallback",
                    question_type="text"
                ),
                Question(
                    text="What data sources are currently available to assess the condition or trigger the action?",
                    field="data_sources",
                    template_category="fallback",
                    question_type="text"
                ),
                Question(
                    text="How is this process currently performed? (manual inspection, automated monitoring, scheduled intervals)",
                    field="current_process",
                    template_category="fallback",
                    question_type="text"
                )
            ]
    
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
        
        app_logger.info(f"Updated requirements: {list(updated_requirements.keys())}")
        app_logger.info(f"Missing fields: {missing_fields}")
        app_logger.info(f"Confidence: {confidence:.2f}")
        
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