"""API client for Streamlit UI to communicate with FastAPI backend."""

import asyncio
from typing import Dict, Any, Optional, List, Coroutine
import httpx
import streamlit as st

from app.utils.imports import require_service
from app.utils.error_boundaries import error_boundary, AsyncOperationManager


class AAA_APIClient:
    """Client for communicating with the AAA FastAPI backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip('/')
        self._async_manager: Optional[AsyncOperationManager] = None
    
    @property
    def async_manager(self) -> AsyncOperationManager:
        """Lazy initialization of async manager to avoid event loop issues."""
        if self._async_manager is None:
            self._async_manager = AsyncOperationManager(max_concurrent=5, timeout_seconds=30.0)
        return self._async_manager
    
    @error_boundary("api_request", timeout_seconds=30.0, max_retries=2)
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=data)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json().get("detail", str(e))
                # Get logger service for error logging
                app_logger = require_service('logger', context="api_request")
                app_logger.error(f"API HTTP Error {e.response.status_code}: {error_detail}")
                return {"error": f"API Error: {error_detail}"}
            except Exception as e:
                # Get logger service for error logging
                try:
                    app_logger = require_service('logger', context="api_request")
                    app_logger.error(f"Unexpected API error: {e}")
                except Exception:
                    pass
                app_logger.error(f"API HTTP Error {e.response.status_code}: {str(e)}")
                return {"error": f"API Error: {str(e)}"}
        except httpx.RequestError as e:
            # Get logger service for error logging
            app_logger = require_service('logger', context="api_request")
            app_logger.error(f"API Connection Error: {e}")
            return {"error": f"Connection Error: {e}"}
        except Exception as e:
            # Get logger service for error logging
            app_logger = require_service('logger', context="api_request")
            app_logger.error(f"Unexpected API Error: {e}")
            return {"error": f"Unexpected Error: {e}"}
    
    async def ingest_requirements(self, source: str, payload: Dict[str, Any], provider_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest requirements and create a new session."""
        data = {
            "source": source,
            "payload": payload,
            "provider_config": provider_config
        }
        return await self.make_request("POST", "/ingest", data)
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a session."""
        return await self.make_request("GET", f"/status/{session_id}")
    
    async def submit_qa_answers(self, session_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        """Submit Q&A answers for a session."""
        data = {"answers": answers}
        return await self.make_request("POST", f"/qa/{session_id}", data)
    
    async def get_pattern_matches(self, session_id: str, top_k: int = 5) -> Dict[str, Any]:
        """Get pattern matches for a session."""
        data = {"session_id": session_id, "top_k": top_k}
        return await self.make_request("POST", "/match", data)
    
    async def get_recommendations(self, session_id: str, top_k: int = 3) -> Dict[str, Any]:
        """Get recommendations for a session."""
        data = {"session_id": session_id, "top_k": top_k}
        return await self.make_request("POST", "/recommend", data)
    
    async def export_results(self, session_id: str, format: str) -> Dict[str, Any]:
        """Export session results in specified format."""
        data = {"session_id": session_id, "format": format}
        return await self.make_request("POST", "/export", data)
    
    async def test_provider_connection(self, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test LLM provider connection."""
        return await self.make_request("POST", "/providers/test", provider_config)
    
    async def discover_models(self, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """Discover available models for a provider."""
        return await self.make_request("POST", "/providers/models", provider_config)
    
    async def test_jira_connection(self, jira_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Jira connection."""
        return await self.make_request("POST", "/jira/test", jira_config)
    
    async def fetch_jira_ticket(self, jira_config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch a Jira ticket."""
        return await self.make_request("POST", "/jira/fetch", jira_config)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get API health status."""
        return await self.make_request("GET", "/health")
    
    async def batch_requests(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple API requests concurrently."""
        async def make_single_request(request_config):
            method = request_config.get("method", "GET")
            endpoint = request_config.get("endpoint")
            data = request_config.get("data")
            return await self.make_request(method, endpoint, data)
        
        operations = [make_single_request(req) for req in requests]
        return await self.async_manager.execute_batch(operations, "batch_api_requests")


class StreamlitAPIIntegration:
    """Integration layer between Streamlit UI and API client."""
    
    def __init__(self, api_client: AAA_APIClient) -> None:
        self.api_client = api_client
    
    def run_async_operation(self, coro: Coroutine[Any, Any, Any], fallback_value: Any = None, operation_name: str = "api_operation") -> Any:
        """Run async operation in Streamlit context."""
        try:
            # Check if we're in an async context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a task for the coroutine
                asyncio.create_task(coro)
                # For Streamlit, we need to handle this differently
                # This is a simplified approach - in production you might want to use st.session_state
                return None  # Placeholder - would need proper async handling
            else:
                # Run the coroutine
                return loop.run_until_complete(coro)
        except Exception as e:
            # Get logger service for error logging
            app_logger = require_service('logger', context="run_async_operation")
            app_logger.error(f"Async operation '{operation_name}' failed: {e}")
            if fallback_value is not None:
                return fallback_value
            raise
    
    def submit_requirements_with_ui_feedback(self, source: str, payload: Dict[str, Any], provider_config: Optional[Dict[str, Any]] = None) -> None:
        """Submit requirements with UI feedback."""
        with st.spinner("🚀 Starting analysis..."):
            try:
                result = self.run_async_operation(
                    self.api_client.ingest_requirements(source, payload, provider_config),
                    operation_name="submit_requirements"
                )
                
                if result and result.get("session_id"):
                    st.session_state.session_id = result["session_id"]
                    st.success(f"✅ Analysis started! Session ID: {result['session_id']}")
                    st.rerun()
                else:
                    error_msg = result.get("error", "Unknown error") if result else "Failed to start analysis"
                    st.error(f"❌ {error_msg}")
                    
            except Exception as e:
                st.error(f"❌ Failed to submit requirements: {str(e)}")
    
    def load_session_status_with_ui_feedback(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session status with UI feedback."""
        try:
            result = self.run_async_operation(
                self.api_client.get_session_status(session_id),
                operation_name="load_session_status"
            )
            
            if result and not result.get("error"):
                # Update session state
                st.session_state.phase = result.get("phase", "unknown")
                st.session_state.progress = result.get("progress", 0)
                st.session_state.missing_fields = result.get("missing_fields", [])
                
                if result.get("requirements"):
                    st.session_state.requirements = result["requirements"]
                
                return result
            else:
                error_msg = result.get("error", "Unknown error") if result else "Failed to load session"
                st.error(f"❌ {error_msg}")
                return None
                
        except Exception as e:
            st.error(f"❌ Failed to load session: {str(e)}")
            return None
    
    def submit_qa_answers_with_ui_feedback(self, session_id: str, answers: Dict[str, str]) -> None:
        """Submit Q&A answers with UI feedback."""
        with st.spinner("💭 Processing answers..."):
            try:
                result = self.run_async_operation(
                    self.api_client.submit_qa_answers(session_id, answers),
                    operation_name="submit_qa_answers"
                )
                
                if result and not result.get("error"):
                    if result.get("complete"):
                        st.success("✅ Q&A complete! Moving to recommendations...")
                        st.session_state.qa_complete = True
                    else:
                        st.session_state.next_questions = result.get("next_questions", [])
                    st.rerun()
                else:
                    error_msg = result.get("error", "Unknown error") if result else "Failed to submit answers"
                    st.error(f"❌ {error_msg}")
                    
            except Exception as e:
                st.error(f"❌ Failed to submit answers: {str(e)}")
    
    def load_recommendations_with_ui_feedback(self, session_id: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
        """Load recommendations with UI feedback."""
        with st.spinner("🧠 Generating recommendations..."):
            try:
                result = self.run_async_operation(
                    self.api_client.get_recommendations(session_id, top_k),
                    operation_name="load_recommendations"
                )
                
                if result and not result.get("error"):
                    st.session_state.recommendations = result.get("recommendations", [])
                    st.session_state.feasibility = result.get("feasibility", "")
                    st.session_state.tech_stack = result.get("tech_stack", [])
                    st.session_state.reasoning = result.get("reasoning", "")
                    return result
                else:
                    error_msg = result.get("error", "Unknown error") if result else "Failed to load recommendations"
                    st.error(f"❌ {error_msg}")
                    return None
                    
            except Exception as e:
                st.error(f"❌ Failed to load recommendations: {str(e)}")
                return None
    
    def export_results_with_ui_feedback(self, session_id: str, format: str) -> Optional[Dict[str, Any]]:
        """Export results with UI feedback."""
        with st.spinner(f"📤 Exporting as {format.upper()}..."):
            try:
                result = self.run_async_operation(
                    self.api_client.export_results(session_id, format),
                    operation_name="export_results"
                )
                
                if result and not result.get("error"):
                    download_url = result.get("download_url")
                    if download_url:
                        st.success("✅ Export complete!")
                        st.markdown(f"[📥 Download {format.upper()} file]({download_url})")
                    return result
                else:
                    error_msg = result.get("error", "Unknown error") if result else "Failed to export"
                    st.error(f"❌ {error_msg}")
                    return None
                    
            except Exception as e:
                st.error(f"❌ Failed to export: {str(e)}")
                return None
    
    def test_provider_connection_with_ui_feedback(self, provider_config: Dict[str, Any]) -> bool:
        """Test provider connection with UI feedback."""
        with st.spinner("🔗 Testing connection..."):
            try:
                result = self.run_async_operation(
                    self.api_client.test_provider_connection(provider_config),
                    operation_name="test_provider_connection"
                )
                
                if result and result.get("ok"):
                    st.success("✅ Connection successful!")
                    return True
                else:
                    error_msg = result.get("message", "Connection failed") if result else "Connection failed"
                    st.error(f"❌ {error_msg}")
                    
                    # Show helpful hints
                    if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                        st.info("💡 **Tip**: Check that your API key is correct and has the right permissions")
                    elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                        st.info("💡 **Tip**: Try using 'gpt-4o' or 'gpt-3.5-turbo' instead")
                    elif "rate limit" in error_msg.lower():
                        st.info("💡 **Tip**: You've hit the rate limit. Wait a moment and try again")
                    
                    return False
                    
            except Exception as e:
                st.error(f"❌ Connection test failed: {str(e)}")
                return False


# Global instances for convenience
api_client = AAA_APIClient()
streamlit_integration = StreamlitAPIIntegration(api_client)