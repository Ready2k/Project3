"""Analysis display components for showing agent roles and coordination in the UI."""

import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
import json
import time
import urllib.parse

from app.ui.agent_formatter import AgentSystemDisplay, AgentRoleDisplay, AgentCoordinationDisplay
from app.utils.imports import require_service, optional_service

# Import streamlit_mermaid directly
try:
    import streamlit_mermaid as stmd
    MERMAID_AVAILABLE = True
except ImportError:
    MERMAID_AVAILABLE = False
    stmd = None


class AgentRolesUIComponent:
    """UI component for displaying agent roles and coordination."""
    
    def __init__(self) -> None:
        self.autonomy_colors = {
            (0.9, 1.0): "#00ff00",  # Green - Fully Autonomous
            (0.7, 0.9): "#90ee90",  # Light Green - Highly Autonomous
            (0.5, 0.7): "#ffff00",  # Yellow - Semi-Autonomous
            (0.3, 0.5): "#ffa500",  # Orange - Assisted
            (0.0, 0.3): "#ff0000"   # Red - Manual
        }
    
    def render_agent_system(self, agent_system: AgentSystemDisplay) -> None:
        """Render complete agent system display with accessibility features."""
        
        if not agent_system.has_agents:
            return
        
        # Get logger service
        app_logger = require_service('logger', context="render_agent_system")
        app_logger.info("Rendering agent system UI")
        
        # Add accessibility landmark
        st.markdown('<div role="main" aria-label="Agentic Solution Design">', unsafe_allow_html=True)
        
        st.header("🤖 Agentic Solution Design")
        
        # Add contextual help
        with st.expander("ℹ️ Understanding Agentic Solutions", expanded=False):
            st.markdown("""
            **What are Agentic Solutions?**
            
            Agentic solutions use AI agents that can reason, make decisions, and take actions autonomously. 
            Unlike traditional automation, these agents can handle exceptions, learn from experience, and 
            adapt to new situations without human intervention.
            
            **Key Concepts:**
            - **Autonomy Level (0.0-1.0)**: How independently the agent can operate
            - **Decision Boundaries**: What decisions the agent can make vs. when it escalates
            - **Coordination**: How multiple agents work together in complex systems
            - **Tech Stack Validation**: Ensuring your technology can support agent deployment
            
            **Autonomy Levels Explained:**
            - 🔴 **0.0-0.3 Manual**: Primarily human-driven with AI assistance
            - 🟠 **0.3-0.5 Assisted**: Significant human oversight required  
            - 🟡 **0.5-0.7 Semi-Autonomous**: Requires periodic human guidance
            - 🟢 **0.7-0.9 Highly Autonomous**: Makes most decisions independently
            - 🟢 **0.9-1.0 Fully Autonomous**: Operates independently with minimal oversight
            """)
        
        # Add skip navigation for screen readers
        st.markdown("""
        <div class="sr-only">
            <a href="#agent-overview" class="skip-link">Skip to Agent Overview</a>
            <a href="#tech-validation" class="skip-link">Skip to Tech Stack Validation</a>
        </div>
        """, unsafe_allow_html=True)
        
        # System overview
        self._render_system_overview(agent_system)
        
        # Agent roles with accessibility ID
        st.markdown('<div id="agent-overview">', unsafe_allow_html=True)
        self._render_agent_roles(agent_system.agent_roles)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Coordination (if multi-agent)
        if agent_system.coordination:
            self._render_coordination(agent_system.coordination)
        
        # Tech stack validation with accessibility ID
        st.markdown('<div id="tech-validation">', unsafe_allow_html=True)
        self._render_tech_stack_validation(agent_system.tech_stack_validation)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Deployment guidance
        self._render_deployment_guidance(
            agent_system.deployment_requirements,
            agent_system.implementation_guidance
        )
        
        # Close accessibility landmark
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add CSS for accessibility
        self._add_accessibility_css()
    
    def _render_system_overview(self, agent_system: AgentSystemDisplay) -> None:
        """Render system-level overview."""
        
        st.subheader("System Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "System Autonomy Score",
                f"{agent_system.system_autonomy_score:.1f}",
                help="Overall autonomy level of the agent system (0.0-1.0)"
            )
        
        with col2:
            st.metric(
                "Number of Agents",
                len(agent_system.agent_roles),
                help="Total number of specialized agents in the system"
            )
        
        with col3:
            architecture_type = "Single Agent"
            if agent_system.coordination:
                architecture_type = agent_system.coordination.architecture_type.replace("_", " ").title()
            
            st.metric(
                "Architecture",
                architecture_type,
                help="Agent system architecture pattern"
            )
        
        # System autonomy visualization
        self._render_autonomy_bar(agent_system.system_autonomy_score, "System Autonomy Level")
    
    def _render_agent_roles(self, agent_roles: List[AgentRoleDisplay]) -> None:
        """Render individual agent roles."""
        
        st.subheader("Agent Roles & Responsibilities")
        
        if not agent_roles:
            st.info("No agent roles defined for this system.")
            return
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Overview", "⚙️ Capabilities", "🔧 Operations"])
        
        with tab1:
            self._render_agent_overview(agent_roles)
        
        with tab2:
            self._render_agent_capabilities(agent_roles)
        
        with tab3:
            self._render_agent_operations(agent_roles)
    
    def _render_agent_overview(self, agent_roles: List[AgentRoleDisplay]) -> None:
        """Render agent overview information."""
        
        for i, agent in enumerate(agent_roles):
            with st.expander(
                f"🤖 {agent.name} (Autonomy: {agent.autonomy_level:.1f})", 
                expanded=(i == 0)  # Expand first agent by default
            ):
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**Primary Responsibility:**")
                    st.write(agent.responsibility)
                    
                    st.write("**Autonomy Level:**")
                    st.write(f"{agent.autonomy_description} ({agent.autonomy_level:.1f})")
                
                with col2:
                    # Autonomy level visualization
                    self._render_autonomy_bar(agent.autonomy_level, f"{agent.name} Autonomy")
                
                # Decision boundaries
                if agent.decision_boundaries:
                    st.write("**Decision Boundaries:**")
                    for boundary in agent.decision_boundaries:
                        st.write(f"• {boundary}")
                
                # Core capabilities preview
                if agent.capabilities:
                    st.write("**Core Capabilities:**")
                    # Show first 3 capabilities, with option to see more
                    preview_caps = agent.capabilities[:3]
                    for cap in preview_caps:
                        st.write(f"• {cap}")
                    
                    if len(agent.capabilities) > 3:
                        st.write(f"*... and {len(agent.capabilities) - 3} more capabilities*")
    
    def _render_agent_capabilities(self, agent_roles: List[AgentRoleDisplay]) -> None:
        """Render agent capabilities and learning mechanisms."""
        
        for agent in agent_roles:
            with st.expander(f"⚙️ {agent.name} - Capabilities"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Core Capabilities:**")
                    if agent.capabilities:
                        for capability in agent.capabilities:
                            st.write(f"• {capability}")
                    else:
                        st.write("*No specific capabilities defined*")
                    
                    st.write("**Learning Capabilities:**")
                    if agent.learning_capabilities:
                        for learning in agent.learning_capabilities:
                            st.write(f"• {learning}")
                    else:
                        st.write("*No learning capabilities defined*")
                
                with col2:
                    st.write("**Exception Handling:**")
                    st.write(agent.exception_handling or "*Standard exception handling*")
                    
                    st.write("**Performance Metrics:**")
                    if agent.performance_metrics:
                        # Show first few metrics, with option to see all
                        preview_metrics = agent.performance_metrics[:4]
                        for metric in preview_metrics:
                            st.write(f"• {metric}")
                        
                        if len(agent.performance_metrics) > 4:
                            with st.expander(f"View all {len(agent.performance_metrics)} metrics"):
                                for metric in agent.performance_metrics:
                                    st.write(f"• {metric}")
                    else:
                        st.write("*Standard performance metrics*")
                
                # Performance metrics visualization
                self._render_agent_performance_dashboard(agent)
                
                # Decision authority details
                if agent.decision_authority:
                    st.write("**Decision Authority:**")
                    with st.expander("View Decision Authority Details"):
                        st.json(agent.decision_authority)
    
    def _render_agent_operations(self, agent_roles: List[AgentRoleDisplay]) -> None:
        """Render operational requirements and infrastructure."""
        
        for agent in agent_roles:
            with st.expander(f"🔧 {agent.name} - Operations"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Infrastructure Requirements:**")
                    if agent.infrastructure_requirements:
                        for key, value in agent.infrastructure_requirements.items():
                            st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
                    else:
                        st.write("*Standard infrastructure requirements*")
                    
                    st.write("**Communication Requirements:**")
                    if agent.communication_requirements:
                        for comm in agent.communication_requirements:
                            st.write(f"• {comm}")
                    else:
                        st.write("*Standard communication protocols*")
                
                with col2:
                    st.write("**Security Requirements:**")
                    if agent.security_requirements:
                        for security in agent.security_requirements:
                            st.write(f"• {security}")
                    else:
                        st.write("*Standard security measures*")
                    
                    # Additional operational info
                    st.write("**Scaling Considerations:**")
                    if agent.autonomy_level > 0.8:
                        st.write("• High autonomy enables horizontal scaling")
                        st.write("• Minimal coordination overhead")
                    else:
                        st.write("• May require coordination for scaling")
                        st.write("• Monitor decision quality during scale-up")
                
                # Security and compliance details
                self._render_agent_security_details(agent)
    
    def _render_coordination(self, coordination: AgentCoordinationDisplay) -> None:
        """Render agent coordination and communication patterns."""
        
        st.subheader("🔄 Agent Coordination & Communication")
        
        # Architecture visualization
        self._render_architecture_diagram(coordination)
        
        # Architecture description
        st.write("**Architecture Type:**")
        st.write(f"{coordination.architecture_type.replace('_', ' ').title()}")
        st.write(coordination.architecture_description)
        
        # Create tabs for different coordination aspects
        coord_tab1, coord_tab2, coord_tab3 = st.tabs(["📡 Communication", "🔄 Coordination", "🌐 Interactions"])
        
        with coord_tab1:
            self._render_communication_protocols(coordination.communication_protocols)
        
        with coord_tab2:
            self._render_coordination_mechanisms(coordination.coordination_mechanisms)
        
        with coord_tab3:
            self._render_interaction_patterns(coordination.interaction_patterns, coordination.workflow_distribution)
    
    def _render_architecture_diagram(self, coordination: AgentCoordinationDisplay) -> None:
        """Render architecture diagram using Mermaid."""
        
        try:
            # Generate Mermaid diagram based on architecture type
            mermaid_code = self._generate_architecture_mermaid(coordination)
            
            if mermaid_code:
                st.write("**System Architecture Diagram:**")
                
                # Try to use streamlit-mermaid if available, otherwise show code
                try:
                    import streamlit_mermaid as stmd
                    # Try different height formats for compatibility
                    try:
                        stmd.st_mermaid(mermaid_code, height=400)
                    except TypeError:
                        # Fallback to string format if integer doesn't work
                        stmd.st_mermaid(mermaid_code, height="400px")
                    
                    # Add diagram controls
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔍 View Full Size"):
                            st.markdown(f"""
                            <div style="background: white; padding: 20px; border-radius: 8px; margin: 10px 0;">
                                <div class="mermaid" style="text-align: center;">
                                {mermaid_code}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        st.download_button(
                            "📄 Download Diagram Code",
                            mermaid_code,
                            file_name="agent_architecture.mmd",
                            mime="text/plain"
                        )
                    
                    with col3:
                        if st.button("🌐 Open in Mermaid Live"):
                            import urllib.parse
                            encoded_diagram = urllib.parse.quote(mermaid_code)
                            mermaid_url = f"https://mermaid.live/edit#{encoded_diagram}"
                            st.markdown(f"[Open in Mermaid Live Editor]({mermaid_url})")
                    
                except ImportError:
                    # Enhanced fallback with better visualization
                    with st.expander("View Architecture Diagram Code (Mermaid)", expanded=True):
                        st.code(mermaid_code, language="mermaid")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info("💡 Copy this code to [Mermaid Live Editor](https://mermaid.live) to view the diagram")
                        
                        with col2:
                            st.download_button(
                                "📄 Download Diagram",
                                mermaid_code,
                                file_name="agent_architecture.mmd",
                                mime="text/plain"
                            )
        
        except Exception as e:
            # Get logger service for error logging
            app_logger = require_service('logger', context="render_architecture_diagram")
            app_logger.error(f"Error rendering architecture diagram: {e}")
            st.info("Architecture diagram temporarily unavailable")
    
    def _render_communication_protocols(self, protocols: List[Dict[str, str]]) -> None:
        """Render communication protocols section."""
        
        if not protocols:
            st.info("No specific communication protocols defined")
            return
        
        st.write("**Communication Protocols:**")
        
        for i, protocol in enumerate(protocols):
            with st.expander(f"📡 {protocol['type'].replace('_', ' ').title()} Protocol", expanded=(i == 0)):
                
                # Protocol overview
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Participants:** {protocol['participants']}")
                    st.write(f"**Message Format:** {protocol['format']}")
                
                with col2:
                    st.write(f"**Reliability:** {protocol['reliability']}")
                    st.write(f"**Latency Requirements:** {protocol['latency']}")
                
                # Protocol characteristics visualization
                self._render_protocol_characteristics(protocol)
    
    def _render_coordination_mechanisms(self, mechanisms: List[Dict[str, str]]) -> None:
        """Render coordination mechanisms section."""
        
        if not mechanisms:
            st.info("No specific coordination mechanisms defined")
            return
        
        st.write("**Coordination Mechanisms:**")
        
        for i, mechanism in enumerate(mechanisms):
            with st.expander(f"🔄 {mechanism['type'].replace('_', ' ').title()} Coordination", expanded=(i == 0)):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Participants:** {mechanism['participants']}")
                    st.write(f"**Decision Criteria:** {mechanism['criteria']}")
                
                with col2:
                    st.write(f"**Conflict Resolution:** {mechanism['conflict_resolution']}")
                    st.write(f"**Performance Metrics:** {mechanism['metrics']}")
                
                # Mechanism flow diagram
                self._render_coordination_flow(mechanism)
    
    def _render_interaction_patterns(self, patterns: List[Dict[str, Any]], workflow_distribution: Dict[str, Any]) -> None:
        """Render interaction patterns and workflow distribution."""
        
        # Interaction patterns
        if patterns:
            st.write("**Interaction Patterns:**")
            
            for pattern in patterns:
                with st.container():
                    st.write(f"**{pattern['type']}**")
                    st.write(f"• {pattern['description']}")
                    if 'participants' in pattern:
                        st.write(f"• *Participants: {pattern['participants']}*")
                    st.divider()
        
        # Workflow distribution
        if workflow_distribution:
            st.write("**Workflow Distribution:**")
            
            # Create visual representation of workflow distribution
            self._render_workflow_distribution_chart(workflow_distribution)
            
            with st.expander("View Workflow Distribution Details"):
                for key, value in workflow_distribution.items():
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    def _generate_architecture_mermaid(self, coordination: AgentCoordinationDisplay) -> str:
        """Generate Mermaid diagram code for the architecture."""
        
        arch_type = coordination.architecture_type
        
        if arch_type == "hierarchical":
            return """
graph TD
    C[Coordinator Agent] --> S1[Specialist Agent 1]
    C --> S2[Specialist Agent 2]
    C --> S3[Specialist Agent 3]
    S1 --> E1[Executor 1]
    S2 --> E2[Executor 2]
    S3 --> E3[Executor 3]
    
    style C fill:#ff9999
    style S1 fill:#99ccff
    style S2 fill:#99ccff
    style S3 fill:#99ccff
    style E1 fill:#99ff99
    style E2 fill:#99ff99
    style E3 fill:#99ff99
"""
        
        elif arch_type == "peer_to_peer":
            return """
graph LR
    A1[Agent 1] <--> A2[Agent 2]
    A2 <--> A3[Agent 3]
    A3 <--> A4[Agent 4]
    A4 <--> A1
    A1 <--> A3
    A2 <--> A4
    
    style A1 fill:#99ccff
    style A2 fill:#99ccff
    style A3 fill:#99ccff
    style A4 fill:#99ccff
"""
        
        elif arch_type == "coordinator_based":
            return """
graph TD
    C[Coordinator] 
    C <--> W1[Worker Agent 1]
    C <--> W2[Worker Agent 2]
    C <--> W3[Worker Agent 3]
    C <--> W4[Worker Agent 4]
    
    style C fill:#ff9999
    style W1 fill:#99ff99
    style W2 fill:#99ff99
    style W3 fill:#99ff99
    style W4 fill:#99ff99
"""
        
        elif arch_type == "swarm_intelligence":
            return """
graph LR
    subgraph "Swarm Cluster"
        A1[Agent 1] -.-> A2[Agent 2]
        A2 -.-> A3[Agent 3]
        A3 -.-> A4[Agent 4]
        A4 -.-> A5[Agent 5]
        A5 -.-> A1
        A1 -.-> A3
        A2 -.-> A4
        A3 -.-> A5
    end
    
    style A1 fill:#ffcc99
    style A2 fill:#ffcc99
    style A3 fill:#ffcc99
    style A4 fill:#ffcc99
    style A5 fill:#ffcc99
"""
        
        else:
            return """
graph LR
    A[Agent System] --> B[Processing]
    B --> C[Output]
    
    style A fill:#99ccff
    style B fill:#99ff99
    style C fill:#ffcc99
"""
    
    def _render_protocol_characteristics(self, protocol: Dict[str, str]) -> None:
        """Render protocol characteristics as visual indicators."""
        
        st.write("**Protocol Characteristics:**")
        
        # Reliability indicator
        reliability = protocol.get('reliability', '').lower()
        if 'high' in reliability:
            st.success("🔒 High Reliability")
        elif 'medium' in reliability:
            st.warning("⚠️ Medium Reliability")
        else:
            st.info("ℹ️ Best Effort")
        
        # Latency indicator
        latency = protocol.get('latency', '').lower()
        if 'low' in latency or 'fast' in latency:
            st.success("⚡ Low Latency")
        elif 'medium' in latency:
            st.warning("🕐 Medium Latency")
        else:
            st.info("🐌 Higher Latency Acceptable")
    
    def _render_coordination_flow(self, mechanism: Dict[str, str]) -> None:
        """Render coordination mechanism flow."""
        
        mechanism_type = mechanism.get('type', '').lower()
        
        if mechanism_type == 'consensus_based':
            flow_diagram = """
graph LR
    A[Proposal] --> B[Agent Voting]
    B --> C{Consensus?}
    C -->|Yes| D[Execute]
    C -->|No| E[Negotiate]
    E --> B
"""
        elif mechanism_type == 'priority_based':
            flow_diagram = """
graph TD
    A[Task Request] --> B[Priority Check]
    B --> C[High Priority Agent]
    C --> D[Execute]
    B --> E[Lower Priority Agents]
    E --> F[Queue/Wait]
"""
        elif mechanism_type == 'market_based':
            flow_diagram = """
graph LR
    A[Task Auction] --> B[Agent Bidding]
    B --> C[Winner Selection]
    C --> D[Task Assignment]
    D --> E[Execution]
"""
        else:
            flow_diagram = """
graph LR
    A[Request] --> B[Coordination]
    B --> C[Decision]
    C --> D[Action]
"""
        
        # Use streamlit_mermaid for flow diagram
        if MERMAID_AVAILABLE and stmd:
            try:
                stmd.st_mermaid(flow_diagram, height=200)
            except Exception as e:
                app_logger.error(f"Error rendering coordination flow: {e}")
                with st.expander("View Coordination Flow (Mermaid)"):
                    st.code(flow_diagram, language="mermaid")
        else:
            with st.expander("View Coordination Flow (Mermaid)"):
                st.code(flow_diagram, language="mermaid")
    
    def _render_workflow_distribution_chart(self, workflow_distribution: Dict[str, Any]) -> None:
        """Render workflow distribution as a visual chart."""
        
        # Create a simple text-based visualization
        st.write("**Distribution Strategy:**")
        
        distribution_strategy = workflow_distribution.get('distribution_strategy', 'Unknown')
        st.info(f"📋 {distribution_strategy}")
        
        load_balancing = workflow_distribution.get('load_balancing', 'Unknown')
        st.info(f"⚖️ Load Balancing: {load_balancing}")
        
        fault_tolerance = workflow_distribution.get('fault_tolerance', 'Unknown')
        st.info(f"🛡️ Fault Tolerance: {fault_tolerance}")
        
        scaling_approach = workflow_distribution.get('scaling_approach', 'Unknown')
        st.info(f"📈 Scaling: {scaling_approach}")
    
    def _render_tech_stack_validation(self, validation: Dict[str, Any]) -> None:
        """Render tech stack validation for agent deployment."""
        
        st.subheader("🛠️ Tech Stack Validation for Agent Deployment")
        
        # Handle error case
        if "error" in validation:
            st.error(f"❌ {validation['error']}")
            if "fallback_recommendations" in validation:
                st.write("**Fallback Recommendations:**")
                for rec in validation["fallback_recommendations"]:
                    st.write(f"• {rec}")
            return
        
        # Deployment readiness overview
        self._render_deployment_readiness_overview(validation)
        
        # Create tabs for different validation aspects
        val_tab1, val_tab2, val_tab3 = st.tabs(["✅ Available", "❌ Missing", "🔧 Enhancements"])
        
        with val_tab1:
            self._render_available_components(validation)
        
        with val_tab2:
            self._render_missing_components(validation)
        
        with val_tab3:
            self._render_enhancement_suggestions(validation)
    
    def _render_deployment_readiness_overview(self, validation: Dict[str, Any]) -> None:
        """Render deployment readiness overview with visual indicators."""
        
        # Agent readiness status
        is_ready = validation.get("is_agent_ready", False)
        readiness_score = validation.get("readiness_score", 0.0)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if is_ready:
                st.success("✅ Tech stack is ready for agent deployment")
            else:
                st.warning("⚠️ Tech stack needs enhancements for agent deployment")
            
            # Readiness score visualization
            if readiness_score > 0:
                st.write("**Deployment Readiness Score:**")
                self._render_readiness_bar(readiness_score)
        
        with col2:
            # Quick stats
            missing_count = len(validation.get("missing_components", []))
            available_frameworks = len(validation.get("deployment_frameworks", []))
            
            st.metric("Missing Components", missing_count)
            st.metric("Agent Frameworks", available_frameworks)
        
        # Deployment timeline estimate
        if "estimated_setup_time" in validation:
            st.info(f"⏱️ Estimated Setup Time: {validation['estimated_setup_time']}")
    
    def _render_available_components(self, validation: Dict[str, Any]) -> None:
        """Render available tech stack components."""
        
        has_components = False
        
        # Agent frameworks
        if validation.get("deployment_frameworks"):
            has_components = True
            st.write("**🤖 Agent Frameworks:**")
            for framework in validation["deployment_frameworks"]:
                st.success(f"✅ {framework}")
                # Add framework-specific info
                self._render_framework_info(framework)
        
        # Orchestration tools
        if validation.get("orchestration_tools"):
            has_components = True
            st.write("**🔄 Orchestration Tools:**")
            for tool in validation["orchestration_tools"]:
                st.success(f"✅ {tool}")
        
        # Communication tools
        if validation.get("communication_tools"):
            has_components = True
            st.write("**📡 Communication Tools:**")
            for tool in validation["communication_tools"]:
                st.success(f"✅ {tool}")
        
        # Reasoning engines
        if validation.get("reasoning_engines"):
            has_components = True
            st.write("**🧠 Reasoning Engines:**")
            for engine in validation["reasoning_engines"]:
                st.success(f"✅ {engine}")
        
        # Monitoring tools
        if validation.get("monitoring_tools"):
            has_components = True
            st.write("**📊 Monitoring Tools:**")
            for tool in validation["monitoring_tools"]:
                st.success(f"✅ {tool}")
        
        if not has_components:
            st.info("No agent-specific components detected in current tech stack")
    
    def _render_missing_components(self, validation: Dict[str, Any]) -> None:
        """Render missing components and their impact."""
        
        missing_components = validation.get("missing_components", [])
        deployment_blockers = validation.get("deployment_blockers", [])
        
        if not missing_components and not deployment_blockers:
            st.success("🎉 No critical components missing!")
            return
        
        # Critical missing components
        if missing_components:
            st.write("**❌ Missing Critical Components:**")
            for component in missing_components:
                st.error(f"• {component}")
                # Add impact description
                self._render_component_impact(component)
        
        # Deployment blockers
        if deployment_blockers:
            st.write("**🚫 Deployment Blockers:**")
            for blocker in deployment_blockers:
                st.error(f"🚫 {blocker}")
        
        # Compatibility issues
        compatibility_issues = validation.get("compatibility_issues", [])
        if compatibility_issues:
            st.write("**⚠️ Compatibility Issues:**")
            for issue in compatibility_issues:
                st.warning(f"⚠️ {issue}")
    
    def _render_enhancement_suggestions(self, validation: Dict[str, Any]) -> None:
        """Render enhancement suggestions with detailed information."""
        
        # Agent enhancements
        agent_enhancements = validation.get("agent_enhancements", [])
        deployment_additions = validation.get("deployment_additions", [])
        monitoring_additions = validation.get("monitoring_additions", [])
        
        all_enhancements = agent_enhancements + deployment_additions + monitoring_additions
        
        if not all_enhancements:
            st.info("No specific enhancements recommended")
            return
        
        # Group by priority
        priority_groups = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for enhancement in all_enhancements:
            if isinstance(enhancement, dict):
                priority = enhancement.get("priority", "medium")
                priority_groups[priority].append(enhancement)
        
        # Render by priority
        for priority, enhancements in priority_groups.items():
            if not enhancements:
                continue
            
            priority_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(priority, "⚪")
            
            st.write(f"**{priority_emoji} {priority.title()} Priority:**")
            
            for enhancement in enhancements:
                with st.expander(f"{enhancement.get('technology', 'Unknown Technology')} - {enhancement.get('category', 'General')}"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Technology:** {enhancement.get('technology', 'Unknown')}")
                        st.write(f"**Category:** {enhancement.get('category', 'General')}")
                        st.write(f"**Priority:** {priority.title()}")
                    
                    with col2:
                        st.write(f"**Reason:** {enhancement.get('reason', 'No reason provided')}")
                        
                        alternatives = enhancement.get("alternatives", [])
                        if alternatives:
                            st.write(f"**Alternatives:** {', '.join(alternatives)}")
                    
                    # Integration notes
                    integration_notes = enhancement.get("integration_notes", "")
                    if integration_notes:
                        st.info(f"💡 {integration_notes}")
        
        # Integration requirements
        integration_requirements = validation.get("integration_requirements", [])
        if integration_requirements:
            st.write("**🔗 Integration Requirements:**")
            for req in integration_requirements:
                if isinstance(req, dict):
                    req_type = req.get("type", "Unknown")
                    reason = req.get("reason", "")
                    technologies = req.get("technologies", [])
                    
                    with st.expander(f"🔗 {req_type}"):
                        st.write(f"**Reason:** {reason}")
                        if technologies:
                            st.write(f"**Recommended Technologies:** {', '.join(technologies)}")
    
    def _render_framework_info(self, framework: str) -> None:
        """Render additional information about agent frameworks."""
        
        framework_info = {
            "LangChain": {
                "description": "Flexible agent orchestration with extensive tool integration",
                "strengths": ["Large ecosystem", "Active community", "Extensive documentation"],
                "use_cases": ["Single agents", "Multi-agent coordination", "Tool integration"]
            },
            "CrewAI": {
                "description": "Specialized for multi-agent collaboration and role-based systems",
                "strengths": ["Role-based agents", "Built-in coordination", "Easy setup"],
                "use_cases": ["Multi-agent teams", "Collaborative workflows", "Role specialization"]
            },
            "AutoGPT": {
                "description": "Autonomous agent framework with goal-oriented behavior",
                "strengths": ["High autonomy", "Goal decomposition", "Self-directed"],
                "use_cases": ["Autonomous tasks", "Goal-oriented workflows", "Independent operation"]
            },
            "AutoGen": {
                "description": "Microsoft's multi-agent conversation framework",
                "strengths": ["Conversation flows", "Agent interactions", "Microsoft ecosystem"],
                "use_cases": ["Conversational agents", "Multi-agent dialogues", "Enterprise integration"]
            }
        }
        
        info = framework_info.get(framework)
        if info:
            with st.expander(f"ℹ️ About {framework}"):
                st.write(f"**Description:** {info['description']}")
                st.write(f"**Key Strengths:** {', '.join(info['strengths'])}")
                st.write(f"**Best Use Cases:** {', '.join(info['use_cases'])}")
    
    def _render_component_impact(self, component: str) -> None:
        """Render the impact of missing components."""
        
        impact_descriptions = {
            "Agent Deployment Framework": "Cannot deploy or manage AI agents without a framework",
            "Agent Orchestration & Communication": "Multi-agent systems cannot coordinate effectively",
            "Reasoning & Memory Engine": "High-autonomy agents lack reasoning and memory capabilities",
            "Agent Monitoring & Observability": "Cannot track agent performance or debug issues"
        }
        
        impact = impact_descriptions.get(component)
        if impact:
            st.caption(f"💥 Impact: {impact}")
    
    def _render_deployment_guidance(self, 
                                  deployment_requirements: Dict[str, Any],
                                  implementation_guidance: List[Dict[str, str]]):
        """Render deployment guidance and implementation recommendations."""
        
        st.subheader("🚀 Deployment Guidance")
        
        # Deployment requirements
        if deployment_requirements:
            with st.expander("📋 Deployment Requirements", expanded=False):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if "architecture" in deployment_requirements:
                        st.write(f"**Architecture:** {deployment_requirements['architecture']}")
                    
                    if "agent_count" in deployment_requirements:
                        st.write(f"**Agent Count:** {deployment_requirements['agent_count']}")
                    
                    if "recommended_frameworks" in deployment_requirements:
                        st.write("**Recommended Frameworks:**")
                        for framework in deployment_requirements["recommended_frameworks"]:
                            st.write(f"• {framework}")
                
                with col2:
                    if "infrastructure_needs" in deployment_requirements:
                        st.write("**Infrastructure Needs:**")
                        for key, value in deployment_requirements["infrastructure_needs"].items():
                            st.write(f"• **{key.title()}:** {value}")
                
                # Deployment strategy
                if "deployment_strategy" in deployment_requirements:
                    st.write("**Deployment Strategy:**")
                    st.write(deployment_requirements["deployment_strategy"])
                
                # Scalability considerations
                if "scalability_considerations" in deployment_requirements:
                    st.write("**Scalability Considerations:**")
                    for consideration in deployment_requirements["scalability_considerations"]:
                        st.write(f"• {consideration}")
        
        # Implementation guidance
        if implementation_guidance:
            st.write("**Implementation Guidance:**")
            
            for guidance in implementation_guidance:
                guidance_type = guidance.get("type", "general")
                title = guidance.get("title", "Guidance")
                content = guidance.get("content", "")
                
                # Use different icons for different types
                type_icons = {
                    "framework": "🔧",
                    "architecture": "🏗️",
                    "communication": "📡",
                    "monitoring": "📊",
                    "security": "🔒",
                    "error": "❌",
                    "general": "💡"
                }
                
                icon = type_icons.get(guidance_type, "💡")
                
                with st.expander(f"{icon} {title}"):
                    st.write(content)
    
    def _render_autonomy_bar(self, autonomy_level: float, label: str) -> None:
        """Render autonomy level as a colored progress bar."""
        
        color = self._get_autonomy_color(autonomy_level)
        percentage = int(autonomy_level * 100)
        
        st.markdown(f"""
        <div style="margin: 10px 0;" role="progressbar" aria-valuenow="{percentage}" aria-valuemin="0" aria-valuemax="100" aria-label="{label}">
            <div style="font-size: 12px; margin-bottom: 5px;">{label}: {percentage}%</div>
            <div style="
                background: linear-gradient(90deg, {color} {percentage}%, #f0f0f0 {percentage}%);
                height: 20px;
                border-radius: 10px;
                border: 1px solid #ddd;
            " title="{label}: {percentage}%"></div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_readiness_bar(self, readiness_score: float) -> None:
        """Render deployment readiness as a colored progress bar."""
        
        percentage = int(readiness_score * 100)
        
        # Color based on readiness level
        if readiness_score >= 0.8:
            color = "#00ff00"  # Green
        elif readiness_score >= 0.6:
            color = "#90ee90"  # Light green
        elif readiness_score >= 0.4:
            color = "#ffff00"  # Yellow
        elif readiness_score >= 0.2:
            color = "#ffa500"  # Orange
        else:
            color = "#ff0000"  # Red
        
        st.markdown(f"""
        <div style="margin: 10px 0;" role="progressbar" aria-valuenow="{percentage}" aria-valuemin="0" aria-valuemax="100" aria-label="Deployment Readiness">
            <div style="font-size: 14px; margin-bottom: 5px;">Deployment Readiness: {percentage}%</div>
            <div style="
                background: linear-gradient(90deg, {color} {percentage}%, #f0f0f0 {percentage}%);
                height: 25px;
                border-radius: 12px;
                border: 1px solid #ddd;
            " title="Deployment Readiness: {percentage}%"></div>
        </div>
        """, unsafe_allow_html=True)
    
    def _get_autonomy_color(self, autonomy_level: float) -> str:
        """Get color for autonomy level visualization."""
        
        for (min_val, max_val), color in self.autonomy_colors.items():
            if min_val <= autonomy_level < max_val:
                return color
        
        # Handle edge case for 1.0
        if autonomy_level >= 0.9:
            return self.autonomy_colors[(0.9, 1.0)]
        
        return self.autonomy_colors[(0.0, 0.3)]
    
    def render_agent_summary_card(self, agent_system: AgentSystemDisplay):
        """Render a compact summary card for agent system (for use in other views)."""
        
        if not agent_system.has_agents:
            return
        
        with st.container():
            st.markdown("### 🤖 Agentic Solution Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Agents", len(agent_system.agent_roles))
            
            with col2:
                st.metric("Autonomy", f"{agent_system.system_autonomy_score:.1f}")
            
            with col3:
                architecture = "Single"
                if agent_system.coordination:
                    architecture = agent_system.coordination.architecture_type.replace("_", " ").title()
                st.metric("Architecture", architecture)
            
            # Quick agent list
            if agent_system.agent_roles:
                st.write("**Agent Roles:**")
                for agent in agent_system.agent_roles:
                    autonomy_emoji = "🟢" if agent.autonomy_level > 0.8 else "🟡" if agent.autonomy_level > 0.6 else "🔴"
                    st.write(f"{autonomy_emoji} {agent.name} ({agent.autonomy_level:.1f})")
    
    def _add_accessibility_css(self):
        """Add CSS for accessibility features."""
        
        st.markdown("""
        <style>
        /* Screen reader only content */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        /* Skip links for keyboard navigation */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            z-index: 1000;
        }
        
        .skip-link:focus {
            top: 6px;
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            .stExpander {
                border: 2px solid #000 !important;
            }
            
            .stMetric {
                border: 1px solid #000 !important;
            }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* Focus indicators */
        .stButton > button:focus,
        .stSelectbox > div > div:focus,
        .stExpander > div:focus {
            outline: 3px solid #4A90E2 !important;
            outline-offset: 2px !important;
        }
        
        /* Improved color contrast for text */
        .stMarkdown p {
            color: #1a1a1a;
        }
        
        /* Better spacing for touch targets */
        .stButton > button {
            min-height: 44px;
            min-width: 44px;
        }
        
        /* Responsive design for mobile */
        @media (max-width: 768px) {
            .stColumns > div {
                margin-bottom: 1rem;
            }
            
            .stMetric {
                font-size: 0.9rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _add_keyboard_navigation_support(self):
        """Add keyboard navigation support for interactive elements."""
        
        st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Add keyboard navigation for expandable sections
            const expanders = document.querySelectorAll('.streamlit-expanderHeader');
            expanders.forEach(expander => {
                expander.setAttribute('tabindex', '0');
                expander.setAttribute('role', 'button');
                expander.setAttribute('aria-expanded', 'false');
                
                expander.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.click();
                        const isExpanded = this.getAttribute('aria-expanded') === 'true';
                        this.setAttribute('aria-expanded', !isExpanded);
                    }
                });
            });
            
            // Add ARIA labels to metrics
            const metrics = document.querySelectorAll('.metric-container');
            metrics.forEach(metric => {
                const value = metric.querySelector('.metric-value');
                const label = metric.querySelector('.metric-label');
                if (value && label) {
                    metric.setAttribute('aria-label', `${label.textContent}: ${value.textContent}`);
                }
            });
        });
        </script>
        """, unsafe_allow_html=True)
    
    def render_accessible_agent_summary(self, agent_system: AgentSystemDisplay):
        """Render accessible summary for screen readers."""
        
        summary_text = f"""
        Agentic Solution Summary:
        - System has {len(agent_system.agent_roles)} agents
        - Overall autonomy score: {agent_system.system_autonomy_score:.1f} out of 1.0
        - Architecture: {agent_system.coordination.architecture_type if agent_system.coordination else 'Single Agent'}
        
        Agent Details:
        """
        
        for i, agent in enumerate(agent_system.agent_roles, 1):
            summary_text += f"""
        Agent {i}: {agent.name}
        - Role: {agent.responsibility}
        - Autonomy Level: {agent.autonomy_level:.1f} ({agent.autonomy_description})
        - Capabilities: {len(agent.capabilities)} capabilities including {', '.join(agent.capabilities[:3])}
        """
        
        # Add screen reader only summary
        st.markdown(f"""
        <div class="sr-only" aria-live="polite">
            {summary_text}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_agent_performance_dashboard(self, agent: AgentRoleDisplay) -> None:
        """Render performance metrics dashboard for an agent."""
        
        with st.expander("📊 Performance Metrics Dashboard"):
            
            # Performance overview
            st.write("**Performance Overview:**")
            
            # Create mock performance data for demonstration
            # In production, this would come from actual monitoring data
            performance_data = self._generate_mock_performance_data(agent)
            
            # Key performance indicators
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Task Success Rate",
                    f"{performance_data['task_success_rate']:.1f}%",
                    delta=f"{performance_data['task_success_delta']:+.1f}%"
                )
            
            with col2:
                st.metric(
                    "Avg Response Time",
                    f"{performance_data['avg_response_time']:.0f}ms",
                    delta=f"{performance_data['response_time_delta']:+.0f}ms"
                )
            
            with col3:
                st.metric(
                    "Decision Accuracy",
                    f"{performance_data['decision_accuracy']:.1f}%",
                    delta=f"{performance_data['decision_accuracy_delta']:+.1f}%"
                )
            
            with col4:
                st.metric(
                    "Uptime",
                    f"{performance_data['uptime']:.2f}%",
                    delta=f"{performance_data['uptime_delta']:+.2f}%"
                )
            
            # Performance trends
            st.write("**Performance Trends:**")
            
            # Autonomy-specific metrics
            if agent.autonomy_level > 0.7:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Autonomous Decision Metrics:**")
                    st.write(f"• Autonomous Success Rate: {performance_data['autonomous_success']:.1f}%")
                    st.write(f"• Exception Resolution: {performance_data['exception_resolution']:.1f}%")
                    st.write(f"• Learning Effectiveness: {performance_data['learning_effectiveness']:.1f}%")
                
                with col2:
                    st.write("**Quality Indicators:**")
                    st.write(f"• Decision Confidence: {performance_data['decision_confidence']:.1f}%")
                    st.write(f"• Error Recovery Rate: {performance_data['error_recovery']:.1f}%")
                    st.write(f"• Adaptation Speed: {performance_data['adaptation_speed']:.1f}/10")
            
            # Role-specific performance metrics
            self._render_role_specific_metrics(agent, performance_data)
            
            # Performance recommendations
            recommendations = self._generate_performance_recommendations(agent, performance_data)
            if recommendations:
                st.write("**Performance Recommendations:**")
                for rec in recommendations:
                    st.info(f"💡 {rec}")
    
    def _generate_mock_performance_data(self, agent: AgentRoleDisplay) -> Dict[str, float]:
        """Generate mock performance data for demonstration."""
        
        # Base performance influenced by autonomy level
        base_performance = 85 + (agent.autonomy_level * 10)
        
        return {
            "task_success_rate": min(99.5, base_performance + 5),
            "task_success_delta": 2.3,
            "avg_response_time": max(50, 200 - (agent.autonomy_level * 100)),
            "response_time_delta": -15,
            "decision_accuracy": min(98, base_performance + 3),
            "decision_accuracy_delta": 1.8,
            "uptime": min(99.99, 98.5 + agent.autonomy_level),
            "uptime_delta": 0.05,
            "autonomous_success": min(95, base_performance),
            "exception_resolution": min(90, base_performance - 5),
            "learning_effectiveness": min(85, base_performance - 10),
            "decision_confidence": min(92, base_performance - 3),
            "error_recovery": min(88, base_performance - 7),
            "adaptation_speed": min(9.5, 6 + (agent.autonomy_level * 3))
        }
    
    def _render_role_specific_metrics(self, agent: AgentRoleDisplay, performance_data: Dict[str, float]) -> None:
        """Render role-specific performance metrics."""
        
        if "coordinator" in agent.name.lower():
            st.write("**Coordination Metrics:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"• Coordination Efficiency: {performance_data.get('task_success_rate', 90):.1f}%")
                st.write(f"• Resource Utilization: {85 + agent.autonomy_level * 10:.1f}%")
            
            with col2:
                st.write(f"• Agent Sync Latency: {max(10, 50 - agent.autonomy_level * 30):.0f}ms")
                st.write(f"• Workflow Success Rate: {performance_data.get('decision_accuracy', 92):.1f}%")
        
        elif "specialist" in agent.name.lower():
            st.write("**Specialization Metrics:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"• Domain Expertise Score: {90 + agent.autonomy_level * 8:.1f}%")
                st.write(f"• Task Quality Rating: {88 + agent.autonomy_level * 10:.1f}%")
            
            with col2:
                st.write(f"• Knowledge Application: {85 + agent.autonomy_level * 12:.1f}%")
                st.write(f"• Specialization Depth: {8 + agent.autonomy_level * 2:.1f}/10")
        
        elif "monitor" in agent.name.lower():
            st.write("**Monitoring Metrics:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"• Alert Accuracy: {92 + agent.autonomy_level * 6:.1f}%")
                st.write(f"• Detection Latency: {max(5, 30 - agent.autonomy_level * 20):.0f}ms")
            
            with col2:
                st.write(f"• False Positive Rate: {max(0.5, 5 - agent.autonomy_level * 4):.1f}%")
                st.write(f"• Prediction Accuracy: {87 + agent.autonomy_level * 10:.1f}%")
    
    def _generate_performance_recommendations(self, agent: AgentRoleDisplay, performance_data: Dict[str, float]) -> List[str]:
        """Generate performance improvement recommendations."""
        
        recommendations = []
        
        # Response time recommendations
        if performance_data.get("avg_response_time", 0) > 500:
            recommendations.append("Consider optimizing agent reasoning algorithms to reduce response time")
        
        # Accuracy recommendations
        if performance_data.get("decision_accuracy", 0) < 90:
            recommendations.append("Enhance training data quality to improve decision accuracy")
        
        # Autonomy-specific recommendations
        if agent.autonomy_level > 0.8:
            if performance_data.get("autonomous_success", 0) < 85:
                recommendations.append("Review autonomous decision boundaries and exception handling logic")
            
            if performance_data.get("learning_effectiveness", 0) < 75:
                recommendations.append("Implement more sophisticated learning mechanisms and feedback loops")
        
        # Role-specific recommendations
        if "coordinator" in agent.name.lower():
            if performance_data.get("task_success_rate", 0) < 90:
                recommendations.append("Optimize coordination algorithms and resource allocation strategies")
        
        # Capability-specific recommendations
        if "api_integration" in agent.capabilities:
            recommendations.append("Monitor API rate limits and implement circuit breakers for reliability")
        
        if len(agent.capabilities) > 5:
            recommendations.append("Consider agent specialization to improve focus and performance")
        
        return recommendations
    
    def _render_agent_security_details(self, agent: AgentRoleDisplay) -> None:
        """Render detailed security and compliance information for an agent."""
        
        with st.expander("🔒 Security & Compliance Details"):
            
            # Security posture assessment
            security_score = self._calculate_security_score(agent)
            st.write("**Security Posture:**")
            self._render_security_score_bar(security_score)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Data Protection Measures:**")
                data_protection = self._get_data_protection_measures(agent)
                for measure in data_protection:
                    st.write(f"• {measure}")
                
                st.write("**Audit & Compliance:**")
                audit_measures = self._get_audit_measures(agent)
                for measure in audit_measures:
                    st.write(f"• {measure}")
            
            with col2:
                st.write("**Access Controls:**")
                access_controls = self._get_access_controls(agent)
                for control in access_controls:
                    st.write(f"• {control}")
                
                st.write("**Regulatory Compliance:**")
                compliance_items = self._get_compliance_items(agent)
                for item in compliance_items:
                    st.write(f"• {item}")
    
    def _calculate_security_score(self, agent: AgentRoleDisplay) -> float:
        """Calculate security score for an agent based on its characteristics."""
        
        score = 0.5  # Base score
        
        # Higher autonomy requires more security
        if agent.autonomy_level > 0.8:
            score += 0.2
        elif agent.autonomy_level > 0.6:
            score += 0.1
        
        # Security requirements boost score
        if len(agent.security_requirements) > 3:
            score += 0.2
        elif len(agent.security_requirements) > 1:
            score += 0.1
        
        # Capabilities that handle sensitive data
        sensitive_capabilities = ["data_processing", "database_access", "api_integration"]
        if any(cap in agent.capabilities for cap in sensitive_capabilities):
            score += 0.1
        
        return min(1.0, score)
    
    def _render_security_score_bar(self, security_score: float) -> None:
        """Render security score as a colored progress bar."""
        
        percentage = int(security_score * 100)
        
        # Color based on security level
        if security_score >= 0.8:
            color = "#00ff00"  # Green
            level = "High Security"
        elif security_score >= 0.6:
            color = "#90ee90"  # Light green
            level = "Good Security"
        elif security_score >= 0.4:
            color = "#ffff00"  # Yellow
            level = "Moderate Security"
        else:
            color = "#ffa500"  # Orange
            level = "Basic Security"
        
        st.markdown(f"""
        <div style="margin: 10px 0;" role="progressbar" aria-valuenow="{percentage}" aria-valuemin="0" aria-valuemax="100" aria-label="Security Level">
            <div style="font-size: 14px; margin-bottom: 5px;">{level}: {percentage}%</div>
            <div style="
                background: linear-gradient(90deg, {color} {percentage}%, #f0f0f0 {percentage}%);
                height: 20px;
                border-radius: 10px;
                border: 1px solid #ddd;
            " title="{level}: {percentage}%"></div>
        </div>
        """, unsafe_allow_html=True)
    
    def _get_data_protection_measures(self, agent: AgentRoleDisplay) -> List[str]:
        """Get data protection measures for an agent."""
        
        measures = [
            "Data encryption at rest and in transit",
            "PII detection and redaction",
            "Secure data storage with access logging"
        ]
        
        # Add agent-specific measures
        if agent.autonomy_level > 0.8:
            measures.append("Enhanced data validation for autonomous decisions")
        
        if "database_access" in agent.capabilities:
            measures.extend([
                "Database connection encryption",
                "Query parameter sanitization",
                "Data access audit trails"
            ])
        
        if "api_integration" in agent.capabilities:
            measures.extend([
                "API key rotation and secure storage",
                "Request/response data validation",
                "Rate limiting and throttling"
            ])
        
        return measures
    
    def _get_audit_measures(self, agent: AgentRoleDisplay) -> List[str]:
        """Get audit and compliance measures for an agent."""
        
        measures = [
            "Decision logging with timestamps",
            "Action audit trails",
            "Performance metrics tracking"
        ]
        
        # Add autonomy-specific audit measures
        if agent.autonomy_level > 0.7:
            measures.extend([
                "Autonomous decision rationale logging",
                "Exception handling audit trails",
                "Learning and adaptation tracking"
            ])
        
        # Add role-specific measures
        if "coordinator" in agent.name.lower():
            measures.extend([
                "System-wide coordination audit logs",
                "Resource allocation decision tracking",
                "Agent performance monitoring logs"
            ])
        
        return measures
    
    def _get_access_controls(self, agent: AgentRoleDisplay) -> List[str]:
        """Get access control measures for an agent."""
        
        controls = [
            "Role-based access control (RBAC)",
            "API authentication and authorization",
            "Session management and timeout"
        ]
        
        # Add agent-specific controls
        if agent.autonomy_level > 0.8:
            controls.extend([
                "Elevated privilege management",
                "Decision authority validation",
                "Autonomous action approval workflows"
            ])
        
        # Add capability-specific controls
        if "system_administration" in agent.capabilities:
            controls.append("Administrative privilege escalation controls")
        
        if "external_integration" in agent.capabilities:
            controls.append("External system access controls")
        
        return controls
    
    def _get_compliance_items(self, agent: AgentRoleDisplay) -> List[str]:
        """Get regulatory compliance items for an agent."""
        
        compliance = [
            "GDPR data processing compliance",
            "SOX audit trail requirements",
            "ISO 27001 security standards"
        ]
        
        # Add data-specific compliance
        data_capabilities = ["data_processing", "database_access", "file_processing"]
        if any(cap in agent.capabilities for cap in data_capabilities):
            compliance.extend([
                "CCPA privacy protection",
                "HIPAA data security (if applicable)",
                "PCI DSS compliance (if handling payments)"
            ])
        
        # Add autonomy-specific compliance
        if agent.autonomy_level > 0.8:
            compliance.extend([
                "AI governance framework compliance",
                "Algorithmic accountability standards",
                "Automated decision-making transparency"
            ])
        
        return compliance


class AgentDisplayErrorHandler:
    """Handle errors in agent display components."""
    
    @staticmethod
    def handle_agent_formatting_error(error: Exception, agent_data: Dict[str, Any]) -> AgentSystemDisplay:
        """Handle errors in agent data formatting."""
        
        # Get logger service for error logging
        app_logger = require_service('logger', context="_handle_agent_formatting_error")
        app_logger.error(f"Agent formatting error: {error}")
        
        # Return safe fallback display
        from app.ui.agent_formatter import AgentSystemDisplay
        
        return AgentSystemDisplay(
            has_agents=False,
            system_autonomy_score=0.0,
            agent_roles=[],
            coordination=None,
            deployment_requirements={},
            tech_stack_validation={"error": "Unable to format agent data"},
            implementation_guidance=[{
                "type": "error",
                "title": "Agent Information Unavailable",
                "content": "Agent role information temporarily unavailable"
            }]
        )
    
    @staticmethod
    def handle_tech_validation_error(error: Exception, tech_stack: List[str]) -> Dict[str, Any]:
        """Handle errors in tech stack validation."""
        
        # Get logger service for error logging
        app_logger = require_service('logger', context="_handle_tech_validation_error")
        app_logger.error(f"Tech validation error: {error}")
        
        return {
            "is_agent_ready": False,
            "error": "Unable to validate tech stack for agent deployment",
            "fallback_recommendations": [
                "Consider LangChain for agent framework",
                "Add Redis for agent state management",
                "Include monitoring tools for agent observability"
            ]
        }
    
    @staticmethod
    def handle_ui_rendering_error(error: Exception, component_name: str):
        """Handle errors in UI component rendering."""
        
        # Get logger service for error logging
        app_logger = require_service('logger', context="_handle_ui_rendering_error")
        app_logger.error(f"UI rendering error in {component_name}: {error}")
        
        st.error(f"❌ Error displaying {component_name}")
        st.write("Please try refreshing the page or contact support if the issue persists.")
        
        # Show error details in debug mode
        if st.session_state.get("debug_mode", False):
            with st.expander("Debug Information"):
                st.write(f"**Error:** {str(error)}")
                st.write(f"**Component:** {component_name}")
    


