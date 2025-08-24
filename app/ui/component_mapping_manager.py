"""
Component Mapping Management Interface for Streamlit.

Provides UI for managing dynamic component mapping rules.
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger

from app.diagrams.dynamic_component_mapper import (
    DynamicComponentMapper, ComponentMapping, ComponentType, DeploymentModel
)


class ComponentMappingManager:
    """Manages component mapping rules through Streamlit UI."""
    
    def __init__(self):
        self.mapper = DynamicComponentMapper()
    
    def render_management_interface(self):
        """Render the complete component mapping management interface."""
        st.header("🔧 Component Mapping Management")
        
        st.markdown("""
        Manage how technologies are mapped to infrastructure diagram components.
        This system automatically determines the appropriate visual representation
        for each technology in your infrastructure diagrams.
        """)
        
        # Tabs for different management functions
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 View Rules", 
            "➕ Add Rule", 
            "🧪 Test Mapping", 
            "📊 Statistics"
        ])
        
        with tab1:
            self._render_rules_viewer()
        
        with tab2:
            self._render_rule_creator()
        
        with tab3:
            self._render_mapping_tester()
        
        with tab4:
            self._render_statistics()
    
    def _render_rules_viewer(self):
        """Render the rules viewing interface."""
        st.subheader("📋 Current Mapping Rules")
        
        if not self.mapper.mapping_rules:
            st.warning("No mapping rules found. Create some rules to get started.")
            return
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            component_filter = st.selectbox(
                "Filter by Component Type",
                ["All"] + [ct.value for ct in ComponentType],
                key="rules_component_filter"
            )
        
        with col2:
            deployment_filter = st.selectbox(
                "Filter by Deployment Model", 
                ["All"] + [dm.value for dm in DeploymentModel],
                key="rules_deployment_filter"
            )
        
        # Display rules
        filtered_rules = self._filter_rules(component_filter, deployment_filter)
        
        for i, rule in enumerate(filtered_rules):
            with st.expander(f"Rule {i+1}: {rule.technology_pattern}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Pattern:**", rule.technology_pattern)
                    st.write("**Component Type:**", rule.component_type.value)
                    st.write("**Deployment Model:**", rule.deployment_model.value)
                
                with col2:
                    st.write("**Specific Component:**", rule.specific_component or "Auto")
                    st.write("**Tags:**", ", ".join(rule.tags) if rule.tags else "None")
                
                # Test this rule
                if st.button(f"Test Rule {i+1}", key=f"test_rule_{i}"):
                    self._test_single_rule(rule)
    
    def _render_rule_creator(self):
        """Render the rule creation interface."""
        st.subheader("➕ Add New Mapping Rule")
        
        with st.form("add_mapping_rule"):
            col1, col2 = st.columns(2)
            
            with col1:
                pattern = st.text_input(
                    "Technology Pattern (Regex)",
                    placeholder="e.g., (langchain|crewai)",
                    help="Regular expression to match technology names"
                )
                
                component_type = st.selectbox(
                    "Component Type",
                    [ct.value for ct in ComponentType]
                )
                
                deployment_model = st.selectbox(
                    "Deployment Model", 
                    [dm.value for dm in DeploymentModel]
                )
            
            with col2:
                specific_component = st.text_input(
                    "Specific Component (Optional)",
                    placeholder="e.g., Server, Lambda",
                    help="Specific diagram component class name"
                )
                
                tags_input = st.text_input(
                    "Tags (comma-separated)",
                    placeholder="e.g., ai, orchestration, framework"
                )
                
                description = st.text_area(
                    "Description",
                    placeholder="Brief description of what this rule matches"
                )
            
            # Test pattern
            test_tech = st.text_input(
                "Test Technology Name",
                placeholder="Enter a technology name to test the pattern"
            )
            
            submitted = st.form_submit_button("Add Rule")
            
            if submitted:
                if pattern and component_type and deployment_model:
                    # Parse tags
                    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
                    
                    # Create new rule
                    new_rule = ComponentMapping(
                        technology_pattern=pattern,
                        component_type=ComponentType(component_type),
                        deployment_model=DeploymentModel(deployment_model),
                        specific_component=specific_component or None,
                        tags=tags
                    )
                    
                    try:
                        self.mapper.add_mapping_rule(new_rule)
                        st.success("✅ Mapping rule added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to add rule: {e}")
                else:
                    st.error("❌ Please fill in all required fields")
            
            # Test pattern if provided
            if test_tech and pattern:
                import re
                try:
                    if re.search(pattern, test_tech, re.IGNORECASE):
                        st.success(f"✅ Pattern matches '{test_tech}'")
                    else:
                        st.warning(f"⚠️ Pattern does not match '{test_tech}'")
                except re.error as e:
                    st.error(f"❌ Invalid regex pattern: {e}")
    
    def _render_mapping_tester(self):
        """Render the mapping testing interface."""
        st.subheader("🧪 Test Technology Mapping")
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_technologies = st.text_area(
                "Technologies to Test (one per line)",
                placeholder="langchain_orchestrator\ncrewai_coordinator\nopenai_api\nvector_db",
                height=200
            )
            
            provider_hint = st.selectbox(
                "Provider Hint (Optional)",
                ["Auto"] + [dm.value for dm in DeploymentModel]
            )
        
        with col2:
            if st.button("🧪 Test Mappings", type="primary"):
                if test_technologies:
                    technologies = [tech.strip() for tech in test_technologies.split('\n') if tech.strip()]
                    
                    st.subheader("Mapping Results:")
                    
                    results = []
                    for tech in technologies:
                        hint = None if provider_hint == "Auto" else provider_hint
                        provider, component = self.mapper.map_technology_to_component(tech, hint)
                        results.append({
                            "Technology": tech,
                            "Provider": provider,
                            "Component": component,
                            "Full Path": f"{provider}.{component}"
                        })
                    
                    # Display as table
                    st.table(results)
                    
                    # Show any warnings
                    for tech in technologies:
                        hint = None if provider_hint == "Auto" else provider_hint
                        provider, component = self.mapper.map_technology_to_component(tech, hint)
                        if provider == "onprem" and component == "server":
                            st.warning(f"⚠️ '{tech}' fell back to generic server - consider adding a specific rule")
    
    def _render_statistics(self):
        """Render mapping statistics and insights."""
        st.subheader("📊 Mapping Statistics")
        
        # Rule statistics
        total_rules = len(self.mapper.mapping_rules)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Rules", total_rules)
        
        with col2:
            component_types = set(rule.component_type for rule in self.mapper.mapping_rules)
            st.metric("Component Types", len(component_types))
        
        with col3:
            deployment_models = set(rule.deployment_model for rule in self.mapper.mapping_rules)
            st.metric("Deployment Models", len(deployment_models))
        
        # Component type distribution
        if self.mapper.mapping_rules:
            st.subheader("Component Type Distribution")
            
            component_counts = {}
            for rule in self.mapper.mapping_rules:
                ct = rule.component_type.value
                component_counts[ct] = component_counts.get(ct, 0) + 1
            
            st.bar_chart(component_counts)
        
        # Cache statistics
        st.subheader("Cache Statistics")
        cache_size = len(self.mapper._mapping_cache)
        st.metric("Cached Mappings", cache_size)
        
        if cache_size > 0:
            if st.button("Clear Cache"):
                self.mapper._mapping_cache.clear()
                st.success("✅ Cache cleared")
                st.rerun()
    
    def _filter_rules(self, component_filter: str, deployment_filter: str) -> List[ComponentMapping]:
        """Filter rules based on selected criteria."""
        filtered = self.mapper.mapping_rules
        
        if component_filter != "All":
            filtered = [r for r in filtered if r.component_type.value == component_filter]
        
        if deployment_filter != "All":
            filtered = [r for r in filtered if r.deployment_model.value == deployment_filter]
        
        return filtered
    
    def _test_single_rule(self, rule: ComponentMapping):
        """Test a single mapping rule."""
        st.write(f"**Testing rule:** {rule.technology_pattern}")
        
        # Test with some common technology names
        test_cases = [
            "langchain_orchestrator",
            "crewai_coordinator", 
            "openai_api",
            "vector_db",
            "neo4j",
            "drools_engine",
            "workflow_manager"
        ]
        
        import re
        matches = []
        for tech in test_cases:
            if re.search(rule.technology_pattern, tech, re.IGNORECASE):
                matches.append(tech)
        
        if matches:
            st.success(f"✅ Rule matches: {', '.join(matches)}")
        else:
            st.info("ℹ️ Rule doesn't match any test cases")


def render_component_mapping_tab():
    """Render the component mapping management tab."""
    manager = ComponentMappingManager()
    manager.render_management_interface()


if __name__ == "__main__":
    # For testing
    render_component_mapping_tab()