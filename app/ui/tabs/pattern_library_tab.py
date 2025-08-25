"""Pattern Library tab for the AAA application."""

import streamlit as st
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from datetime import datetime

from app.ui.tabs.base import BaseTab
from app.core.registry import ServiceRegistry
from app.ui.main_app import SessionManager


class PatternLibraryTab(BaseTab):
    """Tab for managing the pattern library."""
    
    def __init__(self, session_manager: SessionManager, service_registry: ServiceRegistry):
        super().__init__("pattern_library", "📚 Pattern Library", "Browse and manage solution patterns")
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    def initialize(self) -> None:
        """Initialize the tab."""
        pass
    
    def render(self) -> None:
        """Render the pattern library tab."""
        st.header("📚 Pattern Library")
        st.markdown("*Browse, search, and manage solution patterns*")
        
        # Create management tabs
        view_tab, edit_tab, create_tab = st.tabs([
            "👀 View Patterns", 
            "✏️ Edit Pattern", 
            "➕ Create Pattern"
        ])
        
        with view_tab:
            self._render_view_patterns()
        
        with edit_tab:
            self._render_edit_pattern()
        
        with create_tab:
            self._render_create_pattern()
    
    def _render_view_patterns(self) -> None:
        """Render the pattern viewing interface."""
        st.subheader("👀 Browse Patterns")
        
        try:
            # Load patterns
            patterns = self._load_patterns()
            
            if not patterns:
                st.info("📝 No patterns found. Create your first pattern in the 'Create Pattern' tab.")
                return
            
            # Search and filter
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_term = st.text_input(
                    "🔍 Search patterns:",
                    placeholder="Enter keywords...",
                    key="pattern_search"
                )
            
            with col2:
                # Get unique categories
                categories = list(set(p.get('category', 'Uncategorized') for p in patterns))
                category_filter = st.selectbox(
                    "📂 Category:",
                    ["All"] + sorted(categories),
                    key="pattern_category_filter"
                )
            
            with col3:
                # Get unique feasibility levels
                feasibility_levels = list(set(p.get('feasibility', 'Unknown') for p in patterns))
                feasibility_filter = st.selectbox(
                    "⚡ Feasibility:",
                    ["All"] + sorted(feasibility_levels),
                    key="pattern_feasibility_filter"
                )
            
            # Filter patterns
            filtered_patterns = self._filter_patterns(
                patterns, search_term, category_filter, feasibility_filter
            )
            
            st.write(f"Found {len(filtered_patterns)} patterns")
            
            # Display patterns
            for pattern in filtered_patterns:
                with st.expander(f"**{pattern.get('pattern_id', 'Unknown')}** - {pattern.get('name', 'Unnamed Pattern')}"):
                    self._render_pattern_details(pattern)
            
        except Exception as e:
            st.error(f"Error loading patterns: {str(e)}")
    
    def _render_edit_pattern(self) -> None:
        """Render the pattern editing interface."""
        st.subheader("✏️ Edit Pattern")
        
        try:
            patterns = self._load_patterns()
            
            if not patterns:
                st.info("📝 No patterns available to edit.")
                return
            
            # Pattern selection
            pattern_options = [f"{p.get('pattern_id', 'Unknown')} - {p.get('name', 'Unnamed')}" for p in patterns]
            selected_pattern_idx = st.selectbox(
                "Select pattern to edit:",
                range(len(pattern_options)),
                format_func=lambda x: pattern_options[x],
                key="edit_pattern_select"
            )
            
            if selected_pattern_idx is not None:
                pattern = patterns[selected_pattern_idx]
                
                # Edit form
                with st.form("edit_pattern_form"):
                    st.subheader(f"Editing: {pattern.get('pattern_id', 'Unknown')}")
                    
                    # Basic fields
                    name = st.text_input("Name:", value=pattern.get('name', ''))
                    description = st.text_area("Description:", value=pattern.get('description', ''))
                    category = st.text_input("Category:", value=pattern.get('category', ''))
                    feasibility = st.selectbox(
                        "Feasibility:",
                        ["Low", "Medium", "High", "Very High"],
                        index=["Low", "Medium", "High", "Very High"].index(pattern.get('feasibility', 'Medium'))
                    )
                    
                    # Tech stack
                    tech_stack = st.text_area(
                        "Tech Stack (one per line):",
                        value='\n'.join(pattern.get('tech_stack', []))
                    )
                    
                    # Tags
                    tags = st.text_input(
                        "Tags (comma-separated):",
                        value=', '.join(pattern.get('tags', []))
                    )
                    
                    # Submit button
                    if st.form_submit_button("💾 Save Changes"):
                        # Update pattern
                        updated_pattern = {
                            **pattern,
                            'name': name,
                            'description': description,
                            'category': category,
                            'feasibility': feasibility,
                            'tech_stack': [t.strip() for t in tech_stack.split('\n') if t.strip()],
                            'tags': [t.strip() for t in tags.split(',') if t.strip()]
                        }
                        
                        if self._save_pattern(updated_pattern):
                            st.success("✅ Pattern updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to save pattern")
            
        except Exception as e:
            st.error(f"Error editing pattern: {str(e)}")
    
    def _render_create_pattern(self) -> None:
        """Render the pattern creation interface."""
        st.subheader("➕ Create New Pattern")
        
        with st.form("create_pattern_form"):
            # Basic information
            st.subheader("Basic Information")
            
            pattern_id = st.text_input(
                "Pattern ID:",
                placeholder="PAT-XXX",
                help="Unique identifier for the pattern"
            )
            
            name = st.text_input(
                "Pattern Name:",
                placeholder="Enter a descriptive name"
            )
            
            description = st.text_area(
                "Description:",
                placeholder="Detailed description of the pattern",
                height=100
            )
            
            category = st.text_input(
                "Category:",
                placeholder="e.g., Automation, Integration, Analytics"
            )
            
            # Technical details
            st.subheader("Technical Details")
            
            feasibility = st.selectbox(
                "Feasibility Level:",
                ["Low", "Medium", "High", "Very High"]
            )
            
            tech_stack = st.text_area(
                "Technology Stack (one per line):",
                placeholder="Python\nFastAPI\nPostgreSQL\n...",
                height=100
            )
            
            tags = st.text_input(
                "Tags (comma-separated):",
                placeholder="automation, api, database"
            )
            
            # Implementation details
            st.subheader("Implementation Details")
            
            implementation_approach = st.text_area(
                "Implementation Approach:",
                placeholder="Describe the recommended implementation approach",
                height=100
            )
            
            challenges = st.text_area(
                "Potential Challenges:",
                placeholder="List potential challenges and considerations",
                height=80
            )
            
            next_steps = st.text_area(
                "Recommended Next Steps:",
                placeholder="Outline the recommended next steps",
                height=80
            )
            
            # Submit button
            if st.form_submit_button("🚀 Create Pattern"):
                if not pattern_id or not name:
                    st.error("❌ Pattern ID and Name are required")
                else:
                    # Create new pattern
                    new_pattern = {
                        'pattern_id': pattern_id,
                        'name': name,
                        'description': description,
                        'category': category,
                        'feasibility': feasibility,
                        'tech_stack': [t.strip() for t in tech_stack.split('\n') if t.strip()],
                        'tags': [t.strip() for t in tags.split(',') if t.strip()],
                        'implementation_approach': implementation_approach,
                        'challenges': challenges,
                        'next_steps': next_steps,
                        'created_at': str(datetime.now()),
                        'updated_at': str(datetime.now())
                    }
                    
                    if self._save_pattern(new_pattern):
                        st.success(f"✅ Pattern {pattern_id} created successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create pattern")
    
    def _render_pattern_details(self, pattern: Dict[str, Any]) -> None:
        """Render detailed pattern information."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**ID:** {pattern.get('pattern_id', 'Unknown')}")
            st.write(f"**Category:** {pattern.get('category', 'Uncategorized')}")
            st.write(f"**Feasibility:** {pattern.get('feasibility', 'Unknown')}")
        
        with col2:
            if pattern.get('tags'):
                st.write(f"**Tags:** {', '.join(pattern['tags'])}")
            if pattern.get('created_at'):
                st.write(f"**Created:** {pattern['created_at'][:10]}")
        
        if pattern.get('description'):
            st.write(f"**Description:** {pattern['description']}")
        
        if pattern.get('tech_stack'):
            st.write("**Tech Stack:**")
            for tech in pattern['tech_stack']:
                st.write(f"• {tech}")
        
        if pattern.get('implementation_approach'):
            with st.expander("Implementation Approach"):
                st.write(pattern['implementation_approach'])
        
        if pattern.get('challenges'):
            with st.expander("Challenges"):
                st.write(pattern['challenges'])
        
        if pattern.get('next_steps'):
            with st.expander("Next Steps"):
                st.write(pattern['next_steps'])
    
    def _load_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns from the data directory."""
        try:
            patterns = []
            patterns_dir = Path("data/patterns")
            
            if patterns_dir.exists():
                for pattern_file in patterns_dir.glob("*.json"):
                    try:
                        with open(pattern_file, 'r') as f:
                            pattern = json.load(f)
                            patterns.append(pattern)
                    except Exception as e:
                        st.warning(f"Failed to load pattern {pattern_file.name}: {str(e)}")
            
            return patterns
            
        except Exception as e:
            st.error(f"Error loading patterns: {str(e)}")
            return []
    
    def _filter_patterns(self, patterns: List[Dict[str, Any]], search_term: str, 
                        category_filter: str, feasibility_filter: str) -> List[Dict[str, Any]]:
        """Filter patterns based on search criteria."""
        filtered = patterns
        
        # Search term filter
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                p for p in filtered
                if (search_lower in p.get('name', '').lower() or
                    search_lower in p.get('description', '').lower() or
                    search_lower in p.get('pattern_id', '').lower() or
                    any(search_lower in tag.lower() for tag in p.get('tags', [])))
            ]
        
        # Category filter
        if category_filter != "All":
            filtered = [p for p in filtered if p.get('category') == category_filter]
        
        # Feasibility filter
        if feasibility_filter != "All":
            filtered = [p for p in filtered if p.get('feasibility') == feasibility_filter]
        
        return filtered
    
    def _save_pattern(self, pattern: Dict[str, Any]) -> bool:
        """Save a pattern to the data directory."""
        try:
            patterns_dir = Path("data/patterns")
            patterns_dir.mkdir(parents=True, exist_ok=True)
            
            pattern_id = pattern.get('pattern_id', 'unknown')
            pattern_file = patterns_dir / f"{pattern_id}.json"
            
            with open(pattern_file, 'w') as f:
                json.dump(pattern, f, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"Error saving pattern: {str(e)}")
            return False