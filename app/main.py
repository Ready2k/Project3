"""Streamlit UI for Automated AI Assessment (AAA)."""

# Load environment variables from .env file first
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not available
except Exception:
    pass  # Error loading .env file

import json
import time
from typing import Dict, Any

import requests
import streamlit as st

# Import logging
from app.utils.logger import app_logger

# Import agent display components
from app.ui.agent_formatter import (
    AgentDataFormatter,
    AgentSystemDisplay,
    AgentRoleDisplay,
    AgentCoordinationDisplay,
)
from app.ui.analysis_display import AgentRolesUIComponent, AgentDisplayErrorHandler
from app.services.tech_stack_enhancer import TechStackEnhancer
from app.exporters.agent_exporter import AgentSystemExporter

# Configure page
st.set_page_config(
    page_title="Automated AI Assessment (AAA)", page_icon="🤖", layout="wide"
)

# API base URL
API_BASE = "http://localhost:8000"


def call_api(
    endpoint: str, method: str = "GET", data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Call the FastAPI backend."""
    url = f"{API_BASE}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get("detail", str(e))
            st.error(f"API Error: {error_detail}")
        except Exception:
            st.error(f"API Error: {e}")
        return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return {}


def _check_if_agentic_solution(rec: Dict[str, Any]) -> bool:
    """Check if the recommendation is for an agentic solution."""

    reasoning = rec.get("reasoning", "").lower()
    agentic_keywords = [
        "agent",
        "autonomous",
        "agentic",
        "multi-agent",
        "reasoning",
        "decision-making",
    ]

    # Check reasoning for agentic indicators
    if any(keyword in reasoning for keyword in agentic_keywords):
        return True

    # Check recommendations for agentic patterns
    recommendations = rec.get("recommendations", [])
    for recommendation in recommendations:
        rec_reasoning = recommendation.get("reasoning", "").lower()
        if any(keyword in rec_reasoning for keyword in agentic_keywords):
            return True

    return False


def _export_agent_results(session_id: str, export_format: str, rec: Dict[str, Any]):
    """Export agent system results in specified format."""

    try:
        # Initialize components
        AgentDataFormatter()
        agent_exporter = AgentSystemExporter()
        tech_enhancer = TechStackEnhancer()

        # Create demonstration agent system (in production, this would come from API)
        tech_stack = rec.get("tech_stack", [])

        # Create mock agent system for export
        from app.ui.agent_formatter import AgentSystemDisplay, AgentRoleDisplay
        from app.services.multi_agent_designer import (
            MultiAgentSystemDesign,
            AgentRole,
            AgentArchitectureType,
        )

        # Create mock agent design for tech stack enhancement
        mock_agent_design = MultiAgentSystemDesign(
            architecture_type=AgentArchitectureType.SINGLE_AGENT,
            agent_roles=[
                AgentRole(
                    name="Processing Agent",
                    responsibility="Handle processing tasks",
                    autonomy_level=0.85,
                    capabilities=["processing", "decision-making"],
                    decision_authority={"scope": "processing"},
                    communication_requirements=["status_updates"],
                )
            ],
            coordination_patterns=[],
            deployment_requirements={"architecture": "single_agent"},
        )

        demo_agent_system = AgentSystemDisplay(
            has_agents=True,
            system_autonomy_score=0.85,
            agent_roles=[
                AgentRoleDisplay(
                    name="Autonomous Processing Agent",
                    responsibility="Handle end-to-end processing with autonomous decision-making",
                    autonomy_level=0.85,
                    autonomy_description="Highly Autonomous - Makes most decisions independently",
                    capabilities=[
                        "End-to-end processing",
                        "Autonomous decision-making",
                        "Exception handling",
                    ],
                    decision_authority={
                        "scope": "Processing decisions",
                        "limits": [],
                        "escalation_triggers": [],
                    },
                    decision_boundaries=["Authority Scope: Processing decisions"],
                    learning_capabilities=[
                        "Performance optimization",
                        "Pattern recognition",
                    ],
                    exception_handling="Autonomous resolution with multiple fallback strategies",
                    communication_requirements=[
                        "Status reporting",
                        "Alert notifications",
                    ],
                    performance_metrics=[
                        "Processing success rate (%)",
                        "Decision accuracy (%)",
                    ],
                    infrastructure_requirements={
                        "cpu": "4-8 cores",
                        "memory": "8-16 GB",
                    },
                    security_requirements=[
                        "Secure API authentication",
                        "Data encryption",
                    ],
                )
            ],
            coordination=None,
            deployment_requirements={"architecture": "single_agent"},
            tech_stack_validation=tech_enhancer.enhance_tech_stack_for_agents(
                tech_stack, mock_agent_design
            ),
            implementation_guidance=[
                {
                    "type": "framework",
                    "title": "Agent Framework Selection",
                    "content": "Use LangChain for flexible agent orchestration",
                }
            ],
        )

        # Export based on format
        if export_format == "json":
            export_data = agent_exporter.export_to_json(demo_agent_system, session_id)
            st.download_button(
                label="📄 Download Agent System JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"agent_system_{session_id}.json",
                mime="application/json",
            )

        elif export_format == "markdown":
            export_data = agent_exporter.export_to_markdown(
                demo_agent_system, session_id
            )
            st.download_button(
                label="📝 Download Agent System Markdown",
                data=export_data,
                file_name=f"agent_system_{session_id}.md",
                mime="text/markdown",
            )

        elif export_format == "html":
            export_data = agent_exporter.export_to_html(demo_agent_system, session_id)
            st.download_button(
                label="🌐 Download Agent System HTML",
                data=export_data,
                file_name=f"agent_system_{session_id}.html",
                mime="text/html",
            )

        elif export_format == "blueprint":
            blueprint_data = agent_exporter.create_deployment_blueprint(
                demo_agent_system, session_id
            )
            st.download_button(
                label="🏗️ Download Deployment Blueprint",
                data=json.dumps(blueprint_data, indent=2),
                file_name=f"agent_deployment_blueprint_{session_id}.json",
                mime="application/json",
            )

        st.success(
            f"✅ Agent system exported successfully in {export_format.upper()} format!"
        )

    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")


def _track_agent_display_analytics(agent_system: AgentSystemDisplay, session_id: str):
    """Track analytics for agent display usage."""

    try:
        # Track basic metrics
        analytics_data = {
            "session_id": session_id,
            "agent_count": len(agent_system.agent_roles),
            "system_autonomy_score": agent_system.system_autonomy_score,
            "architecture_type": (
                agent_system.coordination.architecture_type
                if agent_system.coordination
                else "single_agent"
            ),
            "has_coordination": agent_system.coordination is not None,
            "deployment_ready": agent_system.tech_stack_validation.get(
                "is_agent_ready", False
            ),
            "timestamp": time.time(),
        }

        # Calculate agent complexity metrics
        if agent_system.agent_roles:
            autonomy_levels = [
                agent.autonomy_level for agent in agent_system.agent_roles
            ]
            analytics_data.update(
                {
                    "avg_autonomy_level": sum(autonomy_levels) / len(autonomy_levels),
                    "max_autonomy_level": max(autonomy_levels),
                    "min_autonomy_level": min(autonomy_levels),
                    "high_autonomy_agents": sum(
                        1 for level in autonomy_levels if level > 0.8
                    ),
                }
            )

        # Store in session state for potential API call
        if "agent_analytics" not in st.session_state:
            st.session_state.agent_analytics = []
        st.session_state.agent_analytics.append(analytics_data)

        # In production, this would send to analytics API
        # call_api("/analytics/agent-display", "POST", analytics_data)

    except Exception as e:
        app_logger.error(f"Failed to track agent analytics: {e}")


def _render_agentic_solution_display(rec: Dict[str, Any], session_id: str):
    """Render agentic solution display if applicable."""

    app_logger.info(
        f"🔍 _render_agentic_solution_display called for session {session_id}"
    )

    try:
        # Check if this is an agentic solution
        is_agentic = False

        # Check feasibility and reasoning for agentic indicators
        rec.get("feasibility", "")
        reasoning = rec.get("reasoning", "").lower()

        # Look for agentic keywords in reasoning or recommendations
        agentic_keywords = [
            "agent",
            "autonomous",
            "agentic",
            "multi-agent",
            "reasoning",
            "decision-making",
        ]
        is_agentic = any(keyword in reasoning for keyword in agentic_keywords)

        # Also check if any recommendations mention agentic patterns or have agent_roles
        recommendations = rec.get("recommendations", [])

        for recommendation in recommendations:
            rec_reasoning = recommendation.get("reasoning", "").lower()
            has_agentic_keywords = any(
                keyword in rec_reasoning for keyword in agentic_keywords
            )
            has_agent_roles = bool(recommendation.get("agent_roles"))

            if has_agentic_keywords or has_agent_roles:
                is_agentic = True
                break

        app_logger.info(f"🔍 is_agentic determined as: {is_agentic}")

        if is_agentic:
            app_logger.info("🚀 Rendering agentic solution display")
            # Initialize components
            AgentDataFormatter()
            agent_ui = AgentRolesUIComponent()
            TechStackEnhancer()

            # Format agent system data
            tech_stack = rec.get("tech_stack", [])

            # Import classes are already available from the top-level imports

            # Extract agent roles from recommendations
            all_agent_roles = []
            system_autonomy_score = 0.0

            for recommendation in recommendations:
                agent_roles_data = recommendation.get("agent_roles", [])
                if agent_roles_data:
                    all_agent_roles.extend(agent_roles_data)
                    # Use the autonomy score from the first agent role as system score
                    if not system_autonomy_score and agent_roles_data:
                        system_autonomy_score = agent_roles_data[0].get(
                            "autonomy_level", 0.8
                        )

            # If no agent roles found, skip display
            if not all_agent_roles:
                app_logger.info("⚠️ No agent roles found, skipping agentic display")
                return

            app_logger.info(
                f"✅ Found {len(all_agent_roles)} agent roles, proceeding with display"
            )

            # Convert agent roles data to display format
            agent_role_displays = []
            for agent_role in all_agent_roles:
                # Get autonomy description
                autonomy_level = agent_role.get("autonomy_level", 0.8)
                if autonomy_level >= 0.9:
                    autonomy_desc = "Fully Autonomous - Operates independently with minimal oversight"
                elif autonomy_level >= 0.7:
                    autonomy_desc = (
                        "Highly Autonomous - Makes most decisions independently"
                    )
                elif autonomy_level >= 0.5:
                    autonomy_desc = "Semi-Autonomous - Requires some human guidance"
                else:
                    autonomy_desc = "Assisted - Requires significant human oversight"

                # Format decision authority
                decision_auth = agent_role.get("decision_authority", {})
                if isinstance(decision_auth, dict):
                    scope = decision_auth.get("scope", ["operational_decisions"])
                    limits = decision_auth.get(
                        "limitations", ["escalate_critical_errors"]
                    )
                    decision_boundaries = [
                        f"Authority Scope: {', '.join(scope) if isinstance(scope, list) else scope}",
                        f"Escalate when: {', '.join(limits) if isinstance(limits, list) else limits}",
                    ]
                else:
                    decision_boundaries = [f"Authority: {decision_auth}"]

                agent_role_display = AgentRoleDisplay(
                    name=agent_role.get("name", "Agent"),
                    responsibility=agent_role.get(
                        "responsibility", "Autonomous task execution"
                    ),
                    autonomy_level=autonomy_level,
                    autonomy_description=autonomy_desc,
                    capabilities=agent_role.get("capabilities", ["task_execution"]),
                    decision_authority=decision_auth,
                    decision_boundaries=decision_boundaries,
                    learning_capabilities=agent_role.get(
                        "learning_capabilities", ["pattern_recognition"]
                    ),
                    exception_handling=agent_role.get(
                        "exception_handling", "Autonomous resolution with escalation"
                    ),
                    communication_requirements=agent_role.get(
                        "communication_requirements", ["status_reporting"]
                    ),
                    performance_metrics=[
                        "Task completion rate (%)",
                        "Decision accuracy (%)",
                        "Response time (ms)",
                    ],
                    infrastructure_requirements={
                        "cpu": "2-4 cores",
                        "memory": "4-8 GB",
                        "storage": "20-50 GB",
                    },
                    security_requirements=[
                        "Authentication",
                        "Audit logging",
                        "Data encryption",
                    ],
                )
                agent_role_displays.append(agent_role_display)

            # Create agent system display
            if len(all_agent_roles) > 1:
                # Multi-agent system
                agent_system = AgentSystemDisplay(
                    has_agents=True,
                    system_autonomy_score=system_autonomy_score,
                    agent_roles=agent_role_displays,
                    coordination=AgentCoordinationDisplay(
                        architecture_type="multi_agent",
                        architecture_description="Multiple specialized agents working together",
                        communication_protocols=[
                            {
                                "type": "REST API",
                                "participants": "All agents",
                                "format": "JSON",
                                "reliability": "High",
                                "latency": "Low",
                            }
                        ],
                        coordination_mechanisms=[
                            {
                                "type": "Collaborative",
                                "participants": "All agents",
                                "criteria": "Task requirements and agent capabilities",
                                "conflict_resolution": "Consensus-based decision making",
                                "metrics": "Task completion rate, coordination efficiency",
                            }
                        ],
                        interaction_patterns=[
                            {
                                "type": "Collaborative",
                                "description": "Agents collaborate and coordinate tasks",
                                "participants": "All agents",
                            }
                        ],
                        conflict_resolution="Collaborative consensus with escalation",
                        workflow_distribution={
                            "distribution_strategy": "Capability-based allocation",
                            "load_balancing": "Dynamic load distribution",
                            "fault_tolerance": "Redundancy and failover",
                            "scaling_approach": "Horizontal scaling",
                        },
                    ),
                    deployment_requirements={
                        "architecture": "multi_agent",
                        "agent_count": len(all_agent_roles),
                        "estimated_timeline": "3-6 weeks",
                        "infrastructure_needs": {
                            "compute": "High - Multiple agents require significant resources",
                            "memory": "High - Agent state and coordination",
                            "storage": "Medium - Agent data and logs",
                            "network": "High - Inter-agent communication",
                        },
                        "complexity_factors": [
                            "Multiple agents require coordination",
                            "High autonomy requires extensive testing",
                        ],
                    },
                    tech_stack_validation={
                        "status": "compatible",
                        "recommendations": tech_stack[:5],
                    },
                    implementation_guidance=[
                        {
                            "type": "framework",
                            "title": "Multi-Agent Framework",
                            "content": "Consider using CrewAI or LangChain for multi-agent coordination",
                        },
                        {
                            "type": "infrastructure",
                            "title": "Infrastructure Setup",
                            "content": "Set up container orchestration and monitoring for multiple agents",
                        },
                    ],
                )
            else:
                # Single agent system
                agent_system = AgentSystemDisplay(
                    has_agents=True,
                    system_autonomy_score=system_autonomy_score,
                    agent_roles=agent_role_displays,
                    coordination=None,
                    deployment_requirements={
                        "architecture": "single_agent",
                        "agent_count": 1,
                        "estimated_timeline": "1-3 weeks",
                        "infrastructure_needs": {
                            "compute": "Medium - Single agent processing",
                            "memory": "Medium - Agent state storage",
                            "storage": "Low - Agent logs and data",
                            "network": "Standard - API communication",
                        },
                        "complexity_factors": [
                            "Single agent simplifies deployment",
                            "High autonomy requires thorough testing",
                        ],
                    },
                    tech_stack_validation={
                        "status": "compatible",
                        "recommendations": tech_stack[:3],
                    },
                    implementation_guidance=[
                        {
                            "type": "framework",
                            "title": "Single Agent Framework",
                            "content": "Consider using LangChain or OpenAI Assistants API for single-agent implementation",
                        },
                        {
                            "type": "infrastructure",
                            "title": "Infrastructure Setup",
                            "content": "Set up monitoring and logging for the autonomous agent",
                        },
                    ],
                )

            # Render the agent system with accessibility features
            agent_ui.render_agent_system(agent_system)
            agent_ui.render_accessible_agent_summary(agent_system)

            # Track agent display analytics
            _track_agent_display_analytics(agent_system, session_id)

    except Exception as e:
        # Handle errors gracefully
        error_handler = AgentDisplayErrorHandler()
        error_handler.handle_ui_rendering_error(e, "Agentic Solution Display")


def get_provider_config(
    provider: str, model: str, api_key: str = None
) -> Dict[str, Any]:
    """Get provider configuration for API calls."""
    config = {
        "provider": provider,
        "model": model,
        "api_key": api_key or "",
        "endpoint_url": "",
        "region": "",
        "aws_access_key_id": None,
        "aws_secret_access_key": None,
        "aws_session_token": None,
    }
    return config


def main():
    """Main Streamlit application."""
    st.title("🤖 Automated AI Assessment (AAA)")
    st.markdown("**Assess automation feasibility of your requirements**")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # Debug mode
        debug_mode = st.checkbox(
            "🐛 Debug Mode", help="Show detailed error messages and logs"
        )

        # Provider selection
        provider = st.selectbox(
            "LLM Provider", ["fake", "openai", "claude", "bedrock"], index=0
        )

        if provider == "openai":
            model = st.selectbox(
                "Model", ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"], index=0
            )
        else:
            model = st.text_input("Model", value="fake-model")

        if provider != "fake":
            api_key = st.text_input("API Key", type="password")
        else:
            api_key = None

            if st.button("Test Connection"):
                if api_key:
                    if debug_mode:
                        st.info(f"🔍 Testing {provider} with model {model}")

                    result = call_api(
                        "/providers/test",
                        "POST",
                        {"provider": provider, "model": model, "api_key": api_key},
                    )

                    if debug_mode:
                        st.json(result)

                    if result.get("ok"):
                        st.success("✅ Connection successful")
                    else:
                        error_msg = result.get("message", "Connection failed")
                        st.error(f"❌ {error_msg}")

                        # Show helpful hints
                        if (
                            "authentication" in error_msg.lower()
                            or "api key" in error_msg.lower()
                        ):
                            st.info(
                                "💡 **Tip**: Check that your API key is correct and has the right permissions"
                            )
                        elif (
                            "model" in error_msg.lower()
                            and "not found" in error_msg.lower()
                        ):
                            st.info(
                                "💡 **Tip**: Try using 'gpt-4o' or 'gpt-3.5-turbo' instead"
                            )
                        elif "rate limit" in error_msg.lower():
                            st.info(
                                "💡 **Tip**: You've hit the rate limit. Wait a moment and try again"
                            )
                else:
                    st.warning("Please enter an API key")

    # Main interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📝 Input", "❓ Q&A", "📊 Results", "🤖 Agent Solution", "ℹ️ About"]
    )

    with tab1:
        st.header("Requirement Input")

        # Input method selection
        input_method = st.radio(
            "Input Method", ["Text", "File Upload", "Jira"], horizontal=True
        )

        if input_method == "Text":
            description = st.text_area(
                "Describe your automation requirement:",
                placeholder="e.g., I need to automatically extract data from websites and store it in a database...",
                height=150,
            )

            col1, col2 = st.columns(2)
            with col1:
                domain = st.selectbox(
                    "Domain (optional)",
                    [
                        "",
                        "data_processing",
                        "system_integration",
                        "document_management",
                        "machine_learning",
                    ],
                    index=0,
                )

            with col2:
                pattern_types = st.multiselect(
                    "Pattern Types (optional)",
                    [
                        "web_automation",
                        "api_integration",
                        "document_processing",
                        "ml_pipeline",
                        "workflow_automation",
                    ],
                )

            if st.button("🚀 Start Analysis", type="primary"):
                if description:
                    payload = {
                        "text": description,
                        "domain": domain if domain else None,
                        "pattern_types": pattern_types,
                    }

                    # Get provider configuration
                    provider_config = get_provider_config(
                        provider, model, api_key if provider != "fake" else None
                    )

                    result = call_api(
                        "/ingest",
                        "POST",
                        {
                            "source": "text",
                            "payload": payload,
                            "provider_config": provider_config,
                        },
                    )

                    if result.get("session_id"):
                        st.session_state.session_id = result["session_id"]
                        st.success(
                            f"✅ Analysis started! Session ID: {result['session_id']}"
                        )
                        st.rerun()
                    else:
                        st.error("Failed to start analysis")
                else:
                    st.warning("Please enter a description")

        elif input_method == "File Upload":
            uploaded_file = st.file_uploader(
                "Upload requirement document", type=["txt", "md", "json"]
            )

            if uploaded_file and st.button("🚀 Start Analysis", type="primary"):
                content = uploaded_file.read().decode("utf-8")

                # Get provider configuration
                provider_config = get_provider_config(
                    provider, model, api_key if provider != "fake" else None
                )

                result = call_api(
                    "/ingest",
                    "POST",
                    {
                        "source": "file",
                        "payload": {"content": content, "filename": uploaded_file.name},
                        "provider_config": provider_config,
                    },
                )

                if result.get("session_id"):
                    st.session_state.session_id = result["session_id"]
                    st.success(
                        f"✅ Analysis started! Session ID: {result['session_id']}"
                    )
                    st.rerun()

        elif input_method == "Jira":
            st.subheader("🎫 Jira Integration")

            with st.form("jira_form"):
                st.write("**Jira Configuration**")

                col1, col2 = st.columns(2)
                with col1:
                    jira_base_url = st.text_input(
                        "Jira Base URL",
                        placeholder="https://your-domain.atlassian.net",
                        help="Your Jira instance URL",
                    )
                    jira_email = st.text_input(
                        "Email",
                        placeholder="your-email@company.com",
                        help="Your Jira account email",
                    )

                with col2:
                    jira_api_token = st.text_input(
                        "API Token",
                        type="password",
                        help="Generate from Jira Account Settings > Security > API tokens",
                    )
                    jira_ticket_key = st.text_input(
                        "Ticket Key",
                        placeholder="PROJ-123",
                        help="Jira ticket key (e.g., PROJ-123)",
                    )

                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    test_connection = st.form_submit_button(
                        "🔗 Test Connection", type="secondary"
                    )

                with col2:
                    fetch_ticket = st.form_submit_button(
                        "📥 Fetch Ticket", type="secondary"
                    )

                with col3:
                    submit_jira = st.form_submit_button(
                        "🚀 Start Analysis", type="primary"
                    )

            # Handle test connection
            if test_connection:
                if not all([jira_base_url, jira_email, jira_api_token]):
                    st.error("❌ Please fill in all Jira configuration fields")
                else:
                    with st.spinner("Testing Jira connection..."):
                        test_result = call_api(
                            "/jira/test",
                            {
                                "base_url": jira_base_url,
                                "email": jira_email,
                                "api_token": jira_api_token,
                            },
                        )

                        if test_result and test_result.get("ok"):
                            st.success("✅ Jira connection successful!")
                        else:
                            error_msg = (
                                test_result.get("message", "Unknown error")
                                if test_result
                                else "Connection failed"
                            )
                            st.error(f"❌ Connection failed: {error_msg}")

            # Handle fetch ticket
            if fetch_ticket:
                if not all(
                    [jira_base_url, jira_email, jira_api_token, jira_ticket_key]
                ):
                    st.error("❌ Please fill in all fields including ticket key")
                else:
                    with st.spinner(f"Fetching ticket {jira_ticket_key}..."):
                        fetch_result = call_api(
                            "/jira/fetch",
                            {
                                "ticket_key": jira_ticket_key,
                                "base_url": jira_base_url,
                                "email": jira_email,
                                "api_token": jira_api_token,
                            },
                        )

                        if fetch_result:
                            ticket_data = fetch_result.get("ticket_data", {})
                            requirements = fetch_result.get("requirements", {})

                            st.success(
                                f"✅ Successfully fetched ticket: {ticket_data.get('key', 'Unknown')}"
                            )

                            # Display ticket preview
                            with st.expander("📋 Ticket Preview", expanded=True):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.write(
                                        f"**Key:** {ticket_data.get('key', 'N/A')}"
                                    )
                                    st.write(
                                        f"**Summary:** {ticket_data.get('summary', 'N/A')}"
                                    )
                                    st.write(
                                        f"**Status:** {ticket_data.get('status', 'N/A')}"
                                    )
                                    st.write(
                                        f"**Priority:** {ticket_data.get('priority', 'N/A')}"
                                    )

                                with col2:
                                    st.write(
                                        f"**Type:** {ticket_data.get('issue_type', 'N/A')}"
                                    )
                                    st.write(
                                        f"**Assignee:** {ticket_data.get('assignee', 'N/A')}"
                                    )
                                    st.write(
                                        f"**Reporter:** {ticket_data.get('reporter', 'N/A')}"
                                    )

                                    if ticket_data.get("labels"):
                                        st.write(
                                            f"**Labels:** {', '.join(ticket_data['labels'])}"
                                        )

                                if ticket_data.get("description"):
                                    st.write("**Description:**")
                                    st.write(
                                        ticket_data["description"][:500] + "..."
                                        if len(ticket_data.get("description", "")) > 500
                                        else ticket_data.get("description", "")
                                    )

                                # Show inferred requirements
                                st.write("**Inferred Requirements:**")
                                if requirements.get("domain"):
                                    st.write(f"- **Domain:** {requirements['domain']}")
                                if requirements.get("pattern_types"):
                                    st.write(
                                        f"- **Pattern Types:** {', '.join(requirements['pattern_types'])}"
                                    )
                        else:
                            st.error(
                                "❌ Failed to fetch ticket. Please check your credentials and ticket key."
                            )

            # Handle submit analysis
            if submit_jira:
                if not all(
                    [jira_base_url, jira_email, jira_api_token, jira_ticket_key]
                ):
                    st.error("❌ Please fill in all fields")
                else:
                    with st.spinner("Starting Jira analysis..."):
                        # Use the ingest endpoint with Jira source
                        payload = {
                            "ticket_key": jira_ticket_key,
                            "base_url": jira_base_url,
                            "email": jira_email,
                            "api_token": jira_api_token,
                        }

                        # Get provider configuration
                        provider_config = get_provider_config(
                            provider, model, api_key if provider != "fake" else None
                        )

                        result = call_api(
                            "/ingest",
                            "POST",
                            {
                                "source": "jira",
                                "payload": payload,
                                "provider_config": provider_config,
                            },
                        )

                        if result and "session_id" in result:
                            st.session_state.session_id = result["session_id"]
                            st.success(
                                f"✅ Jira analysis started! Session ID: {result['session_id']}"
                            )
                            st.rerun()
                        else:
                            st.error(
                                "❌ Failed to start analysis. Please check your configuration."
                            )

    with tab2:
        st.header("Questions & Answers")

        if "session_id" not in st.session_state:
            st.info("👈 Please start an analysis in the Input tab first")
        else:
            session_id = st.session_state.session_id

            # Get session status
            status = call_api(f"/status/{session_id}")

            if status:
                st.write(f"**Phase:** {status.get('phase', 'Unknown')}")
                st.progress(status.get("progress", 0) / 100)

                if status.get("phase") == "QNA" or status.get("missing_fields"):
                    st.subheader("Please answer the following questions:")

                    # Generate questions (simplified - in real implementation, this would be more dynamic)
                    questions = [
                        {
                            "text": "How often should this automation run?",
                            "field": "frequency",
                        },
                        {
                            "text": "What is the criticality of this process?",
                            "field": "criticality",
                        },
                        {
                            "text": "Does this process handle sensitive data?",
                            "field": "data_sensitivity",
                        },
                    ]

                    answers = {}
                    for q in questions:
                        if q["field"] == "frequency":
                            answers[q["field"]] = st.selectbox(
                                q["text"],
                                [
                                    "",
                                    "hourly",
                                    "daily",
                                    "weekly",
                                    "monthly",
                                    "on-demand",
                                ],
                                key=f"q_{q['field']}",
                            )
                        elif q["field"] == "criticality":
                            answers[q["field"]] = st.selectbox(
                                q["text"],
                                ["", "low", "medium", "high", "critical"],
                                key=f"q_{q['field']}",
                            )
                        elif q["field"] == "data_sensitivity":
                            answers[q["field"]] = st.selectbox(
                                q["text"],
                                ["", "low", "medium", "high"],
                                key=f"q_{q['field']}",
                            )

                    if st.button("Submit Answers"):
                        # Filter out empty answers
                        filtered_answers = {k: v for k, v in answers.items() if v}

                        if filtered_answers:
                            result = call_api(
                                f"/qa/{session_id}",
                                "POST",
                                {"answers": filtered_answers},
                            )

                            if result.get("complete"):
                                st.success(
                                    "✅ Q&A complete! Moving to pattern matching..."
                                )
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.info(
                                    "Thank you! Please refresh to see if more questions are needed."
                                )
                        else:
                            st.warning("Please answer at least one question")
                else:
                    st.success("✅ Q&A phase complete!")

    with tab3:
        st.header("Analysis Results")

        if "session_id" not in st.session_state:
            st.info("👈 Please start an analysis in the Input tab first")
        else:
            session_id = st.session_state.session_id
            app_logger.info(f"DEBUG: Using session_id from session_state: {session_id}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔍 Find Pattern Matches"):
                    with st.spinner("Finding pattern matches..."):
                        result = call_api(
                            "/match", "POST", {"session_id": session_id, "top_k": 5}
                        )

                        if result.get("candidates"):
                            st.session_state.matches = result["candidates"]
                            st.success(
                                f"Found {len(result['candidates'])} pattern matches!"
                            )
                        else:
                            st.warning("No pattern matches found")

            with col2:
                if st.button("💡 Generate Recommendations"):
                    with st.spinner("Generating recommendations..."):
                        result = call_api(
                            "/recommend", "POST", {"session_id": session_id, "top_k": 3}
                        )

                        if result:
                            st.session_state.recommendations = result
                            st.success("Recommendations generated!")
                        else:
                            st.warning("Failed to generate recommendations")

            # Display results
            if "recommendations" in st.session_state:
                rec = st.session_state.recommendations

                st.subheader("🎯 Feasibility Assessment")

                # Feasibility badge
                feasibility = rec.get("feasibility", "Unknown")
                if feasibility == "Automatable":
                    st.success(f"✅ **{feasibility}**")
                elif feasibility == "Partially Automatable":
                    st.warning(f"⚠️ **{feasibility}**")
                else:
                    st.error(f"❌ **{feasibility}**")

                # Technology stack
                if rec.get("tech_stack"):
                    st.subheader("🛠️ Recommended Technology Stack")
                    cols = st.columns(min(len(rec["tech_stack"]), 4))
                    for i, tech in enumerate(rec["tech_stack"]):
                        with cols[i % 4]:
                            st.code(tech)

                # Reasoning
                if rec.get("reasoning"):
                    st.subheader("🧠 Reasoning")
                    st.write(rec["reasoning"])

                # Detailed recommendations
                if rec.get("recommendations"):
                    st.subheader("📋 Detailed Recommendations")
                    for i, recommendation in enumerate(rec["recommendations"], 1):
                        with st.expander(
                            f"Recommendation {i}: {recommendation.get('pattern_id', 'Unknown')}"
                        ):
                            st.write(
                                f"**Feasibility:** {recommendation.get('feasibility', 'Unknown')}"
                            )
                            st.write(
                                f"**Confidence:** {recommendation.get('confidence', 0):.0%}"
                            )
                            st.write(
                                f"**Reasoning:** {recommendation.get('reasoning', 'No reasoning provided')}"
                            )

                # Export options
                st.subheader("📤 Export Results")

                # Check if this is an agentic solution for enhanced exports
                is_agentic = _check_if_agentic_solution(rec)

                if is_agentic:
                    st.write("**Enhanced Agent Exports Available:**")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.button("📄 Export JSON"):
                            _export_agent_results(session_id, "json", rec)

                    with col2:
                        if st.button("📝 Export Markdown"):
                            _export_agent_results(session_id, "markdown", rec)

                    with col3:
                        if st.button("🌐 Export HTML"):
                            _export_agent_results(session_id, "html", rec)

                    with col4:
                        if st.button("🏗️ Export Blueprint"):
                            _export_agent_results(session_id, "blueprint", rec)
                else:
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("📄 Export JSON"):
                            result = call_api(
                                "/export",
                                "POST",
                                {"session_id": session_id, "format": "json"},
                            )
                            if result.get("download_url"):
                                st.success(f"✅ Exported to: {result['download_url']}")

                    with col2:
                        if st.button("📝 Export Markdown"):
                            result = call_api(
                                "/export",
                                "POST",
                                {"session_id": session_id, "format": "md"},
                            )
                            if result.get("download_url"):
                                st.success(f"✅ Exported to: {result['download_url']}")

            elif "matches" in st.session_state:
                st.subheader("🔍 Pattern Matches")

                for i, match in enumerate(st.session_state.matches, 1):
                    with st.expander(
                        f"Match {i}: {match.get('pattern_id', 'Unknown')} ({match.get('blended_score', 0):.0%})"
                    ):
                        st.write(f"**Pattern:** {match.get('pattern_name', 'Unknown')}")
                        st.write(f"**Score:** {match.get('blended_score', 0):.0%}")
                        st.write(
                            f"**Rationale:** {match.get('rationale', 'No rationale provided')}"
                        )

    with tab4:
        st.header("🤖 Agentic AI Solution Design")

        if "session_id" not in st.session_state:
            st.info("👈 Please start an analysis in the Input tab first")
        elif "recommendations" not in st.session_state:
            st.info("👈 Please generate recommendations in the Results tab first")
        else:
            session_id = st.session_state.session_id
            rec = st.session_state.recommendations

            # Always try to render the agentic solution display
            st.write("**Analyzing your requirements for agentic AI potential...**")

            try:
                _render_agentic_solution_display(rec, session_id)
            except Exception as e:
                st.error(f"Error displaying agentic solution: {e}")
                st.write("**Debug Info:**")
                st.write(f"- Session ID: {session_id}")
                st.write(f"- Recommendations available: {'Yes' if rec else 'No'}")
                if rec:
                    st.write(
                        f"- Number of recommendations: {len(rec.get('recommendations', []))}"
                    )
                    st.write(
                        f"- Has reasoning: {'Yes' if rec.get('reasoning') else 'No'}"
                    )

                    # Check for agentic indicators
                    reasoning = rec.get("reasoning", "").lower()
                    agentic_keywords = [
                        "agent",
                        "autonomous",
                        "agentic",
                        "multi-agent",
                        "reasoning",
                        "decision-making",
                    ]
                    has_agentic_keywords = any(
                        keyword in reasoning for keyword in agentic_keywords
                    )
                    st.write(
                        f"- Has agentic keywords in reasoning: {has_agentic_keywords}"
                    )

                    # Check recommendations for agent_roles
                    recommendations = rec.get("recommendations", [])
                    agent_roles_count = 0
                    for recommendation in recommendations:
                        agent_roles_count += len(recommendation.get("agent_roles", []))
                    st.write(f"- Total agent roles found: {agent_roles_count}")

    with tab5:
        st.header("ℹ️ About Automated AI Assessment (AAA)")

        st.markdown(
            """
        **Automated AI Assessment (AAA)** is an enterprise-grade system that evaluates whether user stories and requirements 
        can be automated using agentic AI. The system combines intelligent pattern matching, LLM-powered analysis, 
        and comprehensive security to provide accurate feasibility assessments.
        """
        )

        # Version and Release Info
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 System Information")
            st.write("**Version:** 2.3.0")
            st.write("**Release:** Technology Catalog")
            st.write("**Build Date:** August 2025")
            st.write("**License:** MIT")

        with col2:
            st.subheader("🔗 Quick Links")
            st.markdown("- [📚 Documentation](http://localhost:8000/docs)")
            st.markdown("- [🏥 Health Check](http://localhost:8000/health)")
            st.markdown("- [📊 API Status](http://localhost:8000/status)")
            st.markdown("- [🔍 Pattern Library](./data/patterns)")

        # Core Features
        st.subheader("🚀 Core Features")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
            **🤖 AI-Powered Analysis**
            - Multi-provider LLM support (OpenAI, Claude, Bedrock)
            - Intelligent pattern matching with FAISS
            - AI-generated clarifying questions
            - LLM-driven tech stack recommendations
            
            **📊 Assessment & Analytics**
            - Feasibility scoring (Automatable/Partial/Not)
            - Pattern analytics dashboard
            - Real-time progress tracking
            - Comprehensive audit trails
            
            **🏗️ Architecture Generation**
            - Context and container diagrams
            - Sequence flow diagrams
            - Tech stack wiring diagrams
            - Interactive diagram viewing
            """
            )

        with col2:
            st.markdown(
                """
            **🛡️ Enterprise Security**
            - Advanced prompt defense system
            - 8 specialized attack detectors
            - Multilingual security (6 languages)
            - Data egress protection
            
            **📚 Technology Management**
            - 55+ technology catalog
            - 17 technology categories
            - Complete CRUD interface
            - Automatic LLM updates
            
            **🎯 Enterprise Features**
            - Technology constraints support
            - Compliance requirements (GDPR, HIPAA, SOX)
            - Export to JSON/Markdown/HTML
            - Jira integration
            """
            )

        # Security Features
        st.subheader("🛡️ Advanced Security System")

        st.markdown(
            """
        The system includes a comprehensive multi-layered security framework designed to protect against 
        various attack vectors while maintaining high performance.
        """
        )

        security_col1, security_col2 = st.columns(2)

        with security_col1:
            st.markdown(
                """
            **🔍 Attack Detection**
            - **Overt Injection**: Direct prompt manipulation
            - **Covert Injection**: Hidden attacks (base64, markdown, zero-width)
            - **Context Attacks**: Buried instructions, lorem ipsum
            - **Data Egress**: System prompt extraction prevention
            """
            )

        with security_col2:
            st.markdown(
                """
            **🔒 Protection Systems**
            - **Business Logic**: Configuration access protection
            - **Protocol Tampering**: JSON validation and format protection
            - **Scope Validation**: Business domain enforcement
            - **Multilingual**: Attack detection in 6 languages
            """
            )

        st.info(
            "🚀 **Performance**: Sub-100ms security validation with intelligent caching and parallel detection"
        )

        # Technology Stack
        st.subheader("🛠️ Technology Stack")

        tech_col1, tech_col2, tech_col3 = st.columns(3)

        with tech_col1:
            st.markdown(
                """
            **🐍 Backend**
            - Python 3.10+
            - FastAPI (async)
            - Pydantic validation
            - SQLAlchemy ORM
            - FAISS vector search
            """
            )

        with tech_col2:
            st.markdown(
                """
            **🎨 Frontend**
            - Streamlit UI
            - Streamlit-Mermaid
            - Interactive diagrams
            - Professional debug controls
            - Real-time updates
            """
            )

        with tech_col3:
            st.markdown(
                """
            **🔧 Infrastructure**
            - Docker containerization
            - Redis/Diskcache
            - Structured logging
            - Health monitoring
            - Gradual deployment
            """
            )

        # Recent Updates
        st.subheader("📈 Recent Updates")

        with st.expander(
            "🛡️ v2.3.0 - Advanced Prompt Defense System (August 2025)", expanded=True
        ):
            st.markdown(
                """
            - **Multi-layered Security**: 8 specialized detectors for comprehensive threat coverage
            - **Multilingual Support**: Attack detection in English, Spanish, French, German, Chinese, Japanese
            - **Performance Optimized**: Sub-100ms validation with intelligent caching
            - **User Education**: Contextual guidance for security violations
            - **Deployment Safety**: Gradual rollout with automatic rollback capabilities
            - **Configuration Integration**: Full Pydantic model integration with YAML configuration
            """
            )

        with st.expander("🧹 v2.2.0 - Code Quality & Analytics (August 2025)"):
            st.markdown(
                """
            - **Pattern Analytics**: Restored complete analytics functionality with real-time dashboards
            - **Code Quality**: Removed all TODO/FIXME comments, structured logging throughout
            - **Error Resolution**: Fixed type safety issues and dict/string handling
            - **Professional UI**: Hidden debug info by default with optional toggles
            - **Enhanced Navigation**: Improved cross-tab navigation with clear user guidance
            """
            )

        with st.expander("📚 v2.1.0 - Technology Catalog (August 2025)"):
            st.markdown(
                """
            - **Technology Catalog**: Centralized database of 55+ technologies across 17 categories
            - **CRUD Management**: Complete management interface in Streamlit
            - **Performance**: 90% faster startup time vs pattern file scanning
            - **LLM Integration**: Automatic technology suggestions with smart categorization
            - **Backup Safety**: Automatic backups before any catalog modifications
            """
            )

        # Support Information
        st.subheader("🆘 Support & Troubleshooting")

        st.markdown(
            """
        **Common Issues:**
        - **LLM Connection Errors**: Check API keys and model names (use 'gpt-4o', not 'gpt-5')
        - **Import Errors**: Ensure PYTHONPATH includes project root
        - **Port Conflicts**: Modify ports in docker-compose.yml or Makefile
        - **Missing Dependencies**: Run `make install` or `pip install -r requirements.txt`
        
        **Debug Mode**: Enable the debug checkbox in the sidebar for detailed error messages and logs.
        
        **Health Checks**: Visit [/health](http://localhost:8000/health) for system status monitoring.
        """
        )

        # Footer
        st.markdown("---")
        st.markdown(
            """
        <div style='text-align: center; color: #666;'>
            <p><strong>Automated AI Assessment (AAA)</strong> - Enterprise-grade automation feasibility assessment</p>
            <p>Built with ❤️ using Python, FastAPI, and Streamlit</p>
        </div>
        """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
