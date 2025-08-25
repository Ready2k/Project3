"""Q&A tab component for interactive question and answer functionality."""

import asyncio
from typing import Dict, List, Optional, Any

import streamlit as st
import httpx

from app.ui.tabs.base import BaseTab

# Import logger for error handling
from app.utils.logger import app_logger

# API configuration
API_BASE_URL = "http://localhost:8000"


class QATab(BaseTab):
    """Q&A tab for interactive question and answer functionality."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return "❓ Q&A"
    
    def can_render(self) -> bool:
        return st.session_state.get('session_id') is not None
    
    def render(self) -> None:
        """Render the Q&A tab content."""
        if not st.session_state.session_id:
            st.info("👈 Please start an analysis in the Analysis tab first.")
            return
        
        st.header("❓ Interactive Q&A")
        st.markdown("Answer these questions to improve the analysis accuracy.")
        
        # Check if we have questions
        if not st.session_state.qa_questions:
            self._load_questions()
        
        if st.session_state.qa_questions:
            self._render_questions()
        else:
            self._render_no_questions()
    
    def _load_questions(self):
        """Load Q&A questions for the current session."""
        try:
            response = asyncio.run(self._make_api_request("GET", f"/qa/{st.session_state.session_id}"))
            st.session_state.qa_questions = response.get('questions', [])
            
            if st.session_state.qa_questions:
                st.success(f"✅ Loaded {len(st.session_state.qa_questions)} questions")
            
        except Exception as e:
            st.error(f"Failed to load questions: {str(e)}")
            app_logger.error(f"Q&A questions load failed: {str(e)}")
    
    def _render_questions(self):
        """Render the Q&A questions form."""
        questions = st.session_state.qa_questions
        
        st.info(f"📝 Please answer the following {len(questions)} questions to improve analysis accuracy:")
        
        with st.form("qa_form"):
            answers = {}
            
            for i, question in enumerate(questions):
                st.subheader(f"Question {i + 1}")
                
                # Use text_area instead of text_input to avoid password manager interference
                answer = st.text_area(
                    question.get('question', f'Question {i + 1}'),
                    key=f"qa_answer_{i}_{hash(question.get('question', ''))}",
                    height=100,
                    placeholder="Enter your answer here...",
                    help=question.get('help_text', 'Provide a detailed answer to help improve the analysis.')
                )
                
                answers[question.get('field_id', f'question_{i}')] = answer
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                submitted = st.form_submit_button("✅ Submit Answers", type="primary")
            
            with col2:
                skip_qa = st.form_submit_button("⏭️ Skip Q&A")
            
            with col3:
                refresh_questions = st.form_submit_button("🔄 Refresh Questions")
            
            if submitted:
                self._submit_answers(answers)
            elif skip_qa:
                self._skip_qa()
            elif refresh_questions:
                self._refresh_questions()
    
    def _render_no_questions(self):
        """Render when no questions are available."""
        st.info("🤔 No questions available for this session.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Generate Questions", key="generate_questions_btn"):
                self._generate_questions()
        
        with col2:
            if st.button("⏭️ Continue Without Q&A", key="skip_qa_btn"):
                self._skip_qa()
    
    def _submit_answers(self, answers: Dict[str, str]):
        """Submit Q&A answers."""
        try:
            # Filter out empty answers
            filtered_answers = {k: v for k, v in answers.items() if v.strip()}
            
            if not filtered_answers:
                st.warning("Please provide at least one answer before submitting.")
                return
            
            st.session_state.processing = True
            
            # Submit answers to API
            response = asyncio.run(self._make_api_request(
                "POST", 
                f"/qa/{st.session_state.session_id}/answers",
                {'answers': filtered_answers}
            ))
            
            # Update session state
            st.session_state.current_phase = response.get('phase', 'Q&A Completed')
            st.session_state.progress = response.get('progress', st.session_state.progress + 20)
            
            st.success(f"✅ Answers submitted successfully! Answered {len(filtered_answers)} questions.")
            
            # Clear questions to prevent re-submission
            st.session_state.qa_questions = []
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to submit answers: {str(e)}")
            app_logger.error(f"Q&A answers submission failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    def _skip_qa(self):
        """Skip the Q&A process."""
        try:
            st.session_state.processing = True
            
            # Notify API that Q&A is skipped
            response = asyncio.run(self._make_api_request(
                "POST", 
                f"/qa/{st.session_state.session_id}/skip"
            ))
            
            # Update session state
            st.session_state.current_phase = response.get('phase', 'Q&A Skipped')
            st.session_state.progress = response.get('progress', st.session_state.progress + 10)
            
            st.info("⏭️ Q&A skipped. Proceeding with available information.")
            
            # Clear questions
            st.session_state.qa_questions = []
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to skip Q&A: {str(e)}")
            app_logger.error(f"Q&A skip failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    def _generate_questions(self):
        """Generate new questions for the session."""
        try:
            st.session_state.processing = True
            
            # Request new questions from API
            response = asyncio.run(self._make_api_request(
                "POST", 
                f"/qa/{st.session_state.session_id}/generate"
            ))
            
            st.session_state.qa_questions = response.get('questions', [])
            
            if st.session_state.qa_questions:
                st.success(f"✅ Generated {len(st.session_state.qa_questions)} new questions")
            else:
                st.info("No additional questions needed for this analysis.")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to generate questions: {str(e)}")
            app_logger.error(f"Q&A question generation failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    def _refresh_questions(self):
        """Refresh the current questions."""
        st.session_state.qa_questions = []
        self._load_questions()
        st.rerun()
    
    async def _make_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None, timeout: float = 30.0) -> Dict:
        """Make async API request to FastAPI backend."""
        url = f"{API_BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 404:
                raise ValueError("Session not found")
            elif response.status_code != 200:
                raise ValueError(f"API error: {response.status_code} - {response.text}")
            
            return response.json()