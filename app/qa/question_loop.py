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
        
        # If we have LLM analysis, use its confidence level
        llm_confidence = requirements.get("llm_analysis_confidence_level")
        if llm_confidence and isinstance(llm_confidence, (int, float)):
            # Blend LLM confidence with our calculated confidence
            final_confidence = (base_confidence + qa_boost) * 0.4 + llm_confidence * 0.6
        else:
            final_confidence = base_confidence + qa_boost
        
        return min(final_confidence, 1.0)
    
    async def _generate_question_from_template(self, 
                                             template: Dict[str, Any], 
                                             requirements: Dict[str, Any]) -> List[Question]:
        """Generate questions from a template using LLM."""
        template_name = template.get("name", "unknown")
        template_domain = template.get("domain", "general")
        
        # Create a prompt for the LLM to generate contextual questions
        prompt = f"""You are an expert consultant in software-based AI agents and Agentic AI solutions.
You analyze software requirements to determine whether they can be implemented by agentic systems
that reason, plan, and act within digital environments (not physical/industrial automation).

SCOPE GATE (read carefully):
- If the requirement primarily involves physical-world manipulation (e.g., washing a car, cleaning a room, warehouse picking, walking a dog, feeding pets, watering plants) 
  and does NOT present a fully digital control surface (APIs, RPA on software UIs, webhooks, queues) that the agent can operate end-to-end,
  then respond with EXACTLY an empty JSON array: []
- Only if there is a clear, software-only execution path should you proceed to generate questions.

PHYSICAL EXAMPLES THAT MUST RETURN []: "Feed my pet", "Water plants", "Clean house", "Walk dog"
DIGITAL EXAMPLES THAT CAN PROCEED: "Send feeding reminders", "Track feeding schedule", "Order pet food online"

REQUIREMENT: {requirements.get('description', 'No description provided')}

IMPORTANT CONSTRAINTS TO CONSIDER:
- Banned Technologies: {requirements.get('constraints', {}).get('banned_tools', [])}
- Required Integrations: {requirements.get('constraints', {}).get('required_integrations', [])}
- Compliance Requirements: {requirements.get('constraints', {}).get('compliance_requirements', [])}
- Data Sensitivity: {requirements.get('constraints', {}).get('data_sensitivity', 'Not specified')}

Format your response as a JSON array of questions:

If you proceed (i.e., scope is digital or digitally controllable), generate EXACTLY 2 to 4 clarifying questions to assess agentic feasibility.

Coverage targets:
1) Physical vs Digital: confirm digital-only scope and any physical steps
2) Data Availability: sources, access methods, latency/freshness, permissions
3) Decision Complexity: rules vs ambiguity, human-in-the-loop, SLAs
4) Integration Points: systems/APIs, events, webhooks, auth, error handling

Rules:
- Questions must be specific to this requirement
- Questions should help decide: "Automatable by agents", "Partially automatable", or "Not automatable"
- Focus on technical feasibility and operational constraints, not business value
- Respond with ONLY a valid JSON array
- If physical-only with no digital control surface, respond with [] (nothing else)
- If proceeding, each array item must be an object with:
    - "text": the exact question
    - "field": a short identifier (e.g., "process_scope", "data_sources", "decision_complexity", "integrations")

Example (format only):
[
  {{"text": "Question 1?", "field": "field_name_1"}},
  {{"text": "Question 2?", "field": "field_name_2"}},
  {{"text": "Question 3?", "field": "field_name_3"}}
]

Only return the JSON array, no other text.


"""
        try:
            # Generate questions using LLM
            response = await self.llm_provider.generate(prompt, purpose="question_generation")
            
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
    
    def _cleanup_old_cache_entries(self):
        """Clean up old cache entries to prevent memory leaks."""
        if not hasattr(QuestionLoop, '_global_question_cache'):
            return
        
        from datetime import datetime, timedelta
        current_time = datetime.now()
        expired_keys = []
        
        for key, (_, cache_time) in QuestionLoop._global_question_cache.items():
            # Remove entries older than 1 hour
            if current_time - cache_time > timedelta(hours=1):
                expired_keys.append(key)
        
        for key in expired_keys:
            del QuestionLoop._global_question_cache[key]
        
        if expired_keys:
            app_logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
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
        
        # Pre-processing scope gate check for physical tasks
        description = session.requirements.get('description', '').lower()
        physical_indicators = [
            'feed', 'feeding', 'water', 'watering', 'clean', 'cleaning', 
            'walk', 'walking', 'pick up', 'pickup', 'move', 'moving',
            'pet', 'animal', 'plant', 'garden', 'physical', 'manually',
            'snail', 'dog', 'cat', 'bird', 'fish'
        ]
        
        digital_indicators = [
            'remind', 'notification', 'alert', 'schedule', 'track', 'monitor',
            'order', 'purchase', 'api', 'webhook', 'database', 'software',
            'app', 'system', 'digital', 'online', 'email', 'sms', 'automate'
        ]
        
        physical_score = sum(1 for indicator in physical_indicators if indicator in description)
        digital_score = sum(1 for indicator in digital_indicators if indicator in description)
        
        # If clearly physical with minimal digital indicators, reject immediately
        # Note: "automate" is often used in physical task descriptions, so we allow for 1 digital indicator
        if physical_score >= 2 and digital_score <= 1:
            app_logger.info(f"🚫 SCOPE GATE: Rejecting physical task - '{description[:100]}...' (physical:{physical_score}, digital:{digital_score})")
            return []
        
        # Check if we've already asked too many questions
        total_questions_asked = sum(len(qa.questions) for qa in session.qa_history)
        if total_questions_asked >= max_questions:
            app_logger.info(f"Max questions ({max_questions}) already reached for session {session_id}")
            return []
        
        # Check if we have recently generated questions for this session
        # Use a more robust caching mechanism
        from datetime import datetime, timedelta
        
        # Create a stable cache key based on session and requirements
        requirements_hash = hash(str(sorted(session.requirements.items())))
        cache_key = f"{session_id}_{requirements_hash}"
        
        # Initialize global cache if it doesn't exist
        if not hasattr(QuestionLoop, '_global_question_cache'):
            QuestionLoop._global_question_cache = {}
        
        # Check if we have valid cached questions
        if cache_key in QuestionLoop._global_question_cache:
            cached_questions, cache_time = QuestionLoop._global_question_cache[cache_key]
            # Use cached questions if they're less than 10 minutes old
            if datetime.now() - cache_time < timedelta(minutes=10):
                app_logger.info(f"Using cached questions for session {session_id} (cached {len(cached_questions)} questions)")
                return cached_questions
            else:
                # Remove expired cache entry
                del QuestionLoop._global_question_cache[cache_key]
                app_logger.info(f"Expired cache entry removed for session {session_id}")
        
        # Check if we've already generated questions recently for this exact session
        # This prevents rapid-fire duplicate calls
        recent_cache_key = f"{session_id}_recent"
        if recent_cache_key in QuestionLoop._global_question_cache:
            _, recent_time = QuestionLoop._global_question_cache[recent_cache_key]
            # If we generated questions less than 30 seconds ago, return empty list
            if datetime.now() - recent_time < timedelta(seconds=30):
                app_logger.info(f"Preventing duplicate question generation for session {session_id} (too recent)")
                return []
        
        # Generate questions directly using LLM instead of templates
        prompt = f"""You are an expert consultant in software-based AI agents and Agentic AI solutions.
You analyze software requirements to determine whether they can be implemented by agentic systems
that reason, plan, and act within digital environments (not physical/industrial automation).

SCOPE GATE (read carefully):
- If the requirement primarily involves physical-world manipulation (e.g., washing a car, cleaning a room, warehouse picking, walking a dog) 
  and does NOT present a fully digital control surface (APIs, RPA on software UIs, webhooks, queues) that the agent can operate end-to-end,
  then respond with EXACTLY an empty JSON array: []
- Only if there is a clear, software-only execution path should you proceed to generate questions.

REQUIREMENT: {session.requirements.get('description', 'No description provided')}

IMPORTANT CONSTRAINTS TO CONSIDER:
- Banned Technologies: {session.requirements.get('constraints', {}).get('banned_tools', [])}
- Required Integrations: {session.requirements.get('constraints', {}).get('required_integrations', [])}
- Compliance Requirements: {session.requirements.get('constraints', {}).get('compliance_requirements', [])}
- Data Sensitivity: {session.requirements.get('constraints', {}).get('data_sensitivity', 'Not specified')}
- Budget Constraints: {session.requirements.get('constraints', {}).get('budget_constraints', 'Not specified')}
- Deployment Preference: {session.requirements.get('constraints', {}).get('deployment_preference', 'Not specified')}

If you proceed (i.e., scope is digital or digitally controllable), generate EXACTLY 2 to 4 clarifying questions to assess agentic feasibility.

Coverage targets:
1) Physical vs Digital: confirm digital-only scope and any physical steps
2) Data Availability: sources, access methods, latency/freshness, permissions
3) Decision Complexity: rules vs ambiguity, human-in-the-loop, SLAs
4) Integration Points: systems/APIs, events, webhooks, auth, error handling

Rules:
- Questions must be specific to this requirement
- Questions should help decide: "Automatable by agents", "Partially automatable", or "Not automatable"
- Focus on technical feasibility and operational constraints, not business value
- Respond with ONLY a valid JSON array
- If physical-only with no digital control surface, respond with [] (nothing else)
- If proceeding, each array item must be an object with:
    - "text": the exact question
    - "field": a short identifier (e.g., "process_scope", "data_sources", "decision_complexity", "integrations")

Example (format only):
[
  {{"text": "Question 1?", "field": "field1"}},
  {{"text": "Question 2?", "field": "field2"}},
  {{"text": "Question 3?", "field": "field3"}}
]
"""

        try:
            # Generate questions using LLM
            app_logger.info(f"Generating LLM questions for session {session_id}")
            app_logger.info(f"Requirements description: {session.requirements.get('description', 'No description')[:100]}...")
            app_logger.info(f"Question generation prompt hash: {hash(prompt)}")  # Debug: track unique prompts
            
            # Mark that we're about to generate questions
            recent_cache_key = f"{session_id}_recent"
            QuestionLoop._global_question_cache[recent_cache_key] = ([], datetime.now())
            
            response = await self.llm_provider.generate(prompt, purpose="question_generation")
            
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
            
            # Cache the generated questions in global cache
            from datetime import datetime
            current_time = datetime.now()
            
            # Clean up old cache entries (keep cache size manageable)
            self._cleanup_old_cache_entries()
            
            # Cache the questions with the stable key
            QuestionLoop._global_question_cache[cache_key] = (questions, current_time)
            
            # Also set the recent generation marker to prevent immediate duplicates
            recent_cache_key = f"{session_id}_recent"
            QuestionLoop._global_question_cache[recent_cache_key] = ([], current_time)
            
            app_logger.info(f"Cached {len(questions)} questions for session {session_id}")
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
    
    async def _analyze_answers_with_llm(self, 
                                      session_id: str, 
                                      requirements: Dict[str, Any], 
                                      answers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze user answers using LLM to extract insights and assess automation feasibility.
        
        Args:
            session_id: Session identifier
            requirements: Current requirements
            answers: User answers to analyze
            
        Returns:
            Dictionary with LLM analysis insights
        """
        if not self.llm_provider:
            app_logger.warning(f"No LLM provider available for answer analysis in session {session_id}")
            return {}
        
        # Format the answers for LLM analysis
        answers_text = "\n".join([f"Q: {field}\nA: {answer}" for field, answer in answers.items()])
        
        prompt = f"""You are an expert consultant in software-based AI agents and Agentic AI solutions.
You analyze software requirements to determine whether they can be implemented by agentic systems
that reason, plan, and act within digital environments (not physical/industrial automation).

SCOPE GATE (read carefully):
- If the requirement primarily involves physical-world manipulation (e.g., washing a car, cleaning a room, warehouse picking) 
  and does NOT present a fully digital control surface (APIs, RPA on software UIs, webhooks, queues) that the agent can operate end-to-end,
  then respond with EXACTLY an empty JSON array: []
- Only if there is a clear, software-only execution path should you proceed to generate questions.

ORIGINAL REQUIREMENT: {requirements.get('description', 'No description provided')}

IMPORTANT CONSTRAINTS:
- Banned Technologies: {requirements.get('constraints', {}).get('banned_tools', [])}
- Required Integrations: {requirements.get('constraints', {}).get('required_integrations', [])}
- Compliance Requirements: {requirements.get('constraints', {}).get('compliance_requirements', [])}
- Data Sensitivity: {requirements.get('constraints', {}).get('data_sensitivity', 'Not specified')}

USER ANSWERS:
{answers_text}

Based on these answers, analyze the automation feasibility and provide insights in JSON format:

{{
  "automation_feasibility": "Automatable|Partially Automatable|Not Automatable",
  "feasibility_reasoning": "Detailed explanation of why this assessment was made",
  "key_insights": ["insight1", "insight2", "insight3"],
  "automation_challenges": ["challenge1", "challenge2"],
  "recommended_approach": "Specific recommendation based on the answers",
  "confidence_level": 0.85,
  "next_steps": ["step1", "step2"]
}}

Focus on:
- Physical vs digital nature of the process
- Available data sources and integration points
- Complexity of decision-making required
- Current workflow and automation readiness
- Risk factors and compliance considerations

Respond with ONLY valid JSON, no other text."""

        try:
            app_logger.info(f"Analyzing answers with LLM for session {session_id}")
            response = await self.llm_provider.generate(prompt, purpose="answer_analysis")
            
            app_logger.info(f"LLM answer analysis response: {response[:200]}...")
            
            # Parse JSON response
            import json
            import re
            
            # Clean the response - sometimes LLM adds extra text
            response = response.strip()
            
            # Try to extract JSON if it's wrapped in other text
            if not response.startswith('{'):
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response = json_match.group()
            
            analysis = json.loads(response)
            
            # Add prefix to avoid conflicts with user answers
            prefixed_analysis = {}
            for key, value in analysis.items():
                prefixed_analysis[f"llm_analysis_{key}"] = value
            
            app_logger.info(f"Successfully analyzed answers for session {session_id}")
            return prefixed_analysis
            
        except Exception as e:
            app_logger.error(f"Error analyzing answers with LLM for session {session_id}: {e}")
            return {}
    
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
        app_logger.info(f"Answers received: {answers}")
        
        # Send answers to LLM for analysis and evaluation
        llm_analysis = await self._analyze_answers_with_llm(session_id, session.requirements, answers)
        
        # Merge answers into requirements
        updated_requirements = self._merge_answers(session.requirements, answers)
        
        # Merge LLM analysis insights into requirements
        if llm_analysis:
            updated_requirements.update(llm_analysis)
        
        # Check completeness and confidence
        missing_fields = self._identify_missing_fields(updated_requirements)
        confidence = self._calculate_confidence(updated_requirements)
        
        app_logger.info(f"Updated requirements: {list(updated_requirements.keys())}")
        app_logger.info(f"Missing fields: {missing_fields}")
        app_logger.info(f"Confidence: {confidence:.2f}")
        
        # Log LLM analysis if available
        if llm_analysis:
            feasibility = llm_analysis.get("llm_analysis_automation_feasibility", "Unknown")
            llm_confidence = llm_analysis.get("llm_analysis_confidence_level", "Unknown")
            app_logger.info(f"LLM Analysis: Feasibility={feasibility}, Confidence={llm_confidence}")
        
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
        # Consider LLM analysis in completeness determination
        llm_has_clear_assessment = updated_requirements.get("llm_analysis_automation_feasibility") is not None
        
        complete = (len(missing_fields) == 0 or 
                   confidence > 0.8 or 
                   (llm_has_clear_assessment and confidence > 0.6))
        
        # Generate next questions if not complete
        next_questions = []
        if not complete:
            app_logger.info(f"Q&A not complete for session {session_id}, generating more questions")
            next_questions = await self.generate_questions(session_id)
            if not next_questions:
                app_logger.info(f"No more questions generated for session {session_id}, marking complete")
                complete = True  # No more questions to ask
        
        result = QAResult(
            complete=complete,
            confidence=confidence,
            next_questions=next_questions
        )
        
        app_logger.info(f"Q&A result for session {session_id}: complete={complete}, confidence={confidence:.2f}")
        return result