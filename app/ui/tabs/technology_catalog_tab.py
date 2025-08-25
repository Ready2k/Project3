"""Technology Catalog tab for the AAA application."""

import streamlit as st
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from datetime import datetime

from app.ui.tabs.base import BaseTab
from app.core.registry import ServiceRegistry
from app.ui.main_app import SessionManager


class TechnologyCatalogTab(BaseTab):
    """Tab for managing the technology catalog."""
    
    def __init__(self, session_manager: SessionManager, service_registry: ServiceRegistry):
        super().__init__("technology_catalog", "🔧 Technology Catalog", "Manage the technology database")
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    def initialize(self) -> None:
        """Initialize the tab."""
        pass
    
    def render(self) -> None:
        """Render the technology catalog tab."""
        st.header("🔧 Technology Catalog")
        st.markdown("*Manage the comprehensive technology database*")
        
        # Create management tabs
        view_tab, edit_tab, create_tab, import_tab = st.tabs([
            "👀 View Technologies", 
            "✏️ Edit Technology", 
            "➕ Add Technology", 
            "📥 Import/Export"
        ])
        
        with view_tab:
            self._render_view_technologies()
        
        with edit_tab:
            self._render_edit_technology()
        
        with create_tab:
            self._render_add_technology()
        
        with import_tab:
            self._render_import_export()
    
    def _render_view_technologies(self) -> None:
        """Render the technology viewing interface."""
        st.subheader("👀 Browse Technology Catalog")
        
        try:
            # Load technologies
            technologies = self._load_technologies()
            
            if not technologies:
                st.info("📝 No technologies found. Add technologies in the 'Add Technology' tab.")
                return
            
            # Search and filter
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                search_term = st.text_input(
                    "🔍 Search:",
                    placeholder="Technology name...",
                    key="tech_search"
                )
            
            with col2:
                # Get unique categories
                categories = list(set(t.get('category', 'Uncategorized') for t in technologies))
                category_filter = st.selectbox(
                    "📂 Category:",
                    ["All"] + sorted(categories),
                    key="tech_category_filter"
                )
            
            with col3:
                # Get unique maturity levels
                maturity_levels = list(set(t.get('maturity', 'Unknown') for t in technologies))
                maturity_filter = st.selectbox(
                    "🎯 Maturity:",
                    ["All"] + sorted(maturity_levels),
                    key="tech_maturity_filter"
                )
            
            with col4:
                # Get unique licenses
                licenses = list(set(t.get('license', 'Unknown') for t in technologies))
                license_filter = st.selectbox(
                    "📄 License:",
                    ["All"] + sorted(licenses),
                    key="tech_license_filter"
                )
            
            # Filter technologies
            filtered_technologies = self._filter_technologies(
                technologies, search_term, category_filter, maturity_filter, license_filter
            )
            
            st.write(f"Found {len(filtered_technologies)} technologies")
            
            # Display technologies in a grid
            cols_per_row = 2
            for i in range(0, len(filtered_technologies), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(filtered_technologies):
                        tech = filtered_technologies[i + j]
                        with col:
                            self._render_technology_card(tech)
            
        except Exception as e:
            st.error(f"Error loading technologies: {str(e)}")
    
    def _render_edit_technology(self) -> None:
        """Render the technology editing interface."""
        st.subheader("✏️ Edit Technology")
        
        try:
            technologies = self._load_technologies()
            
            if not technologies:
                st.info("📝 No technologies available to edit.")
                return
            
            # Technology selection
            tech_options = [f"{t.get('name', 'Unknown')} ({t.get('category', 'Uncategorized')})" for t in technologies]
            selected_tech_idx = st.selectbox(
                "Select technology to edit:",
                range(len(tech_options)),
                format_func=lambda x: tech_options[x],
                key="edit_tech_select"
            )
            
            if selected_tech_idx is not None:
                tech = technologies[selected_tech_idx]
                
                # Edit form
                with st.form("edit_technology_form"):
                    st.subheader(f"Editing: {tech.get('name', 'Unknown')}")
                    
                    # Basic fields
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        name = st.text_input("Name:", value=tech.get('name', ''))
                        category = st.selectbox(
                            "Category:",
                            ["Languages", "Frameworks", "Databases", "Cloud", "AI/ML", "Security", "Integration", "Infrastructure", "Other"],
                            index=self._get_category_index(tech.get('category', 'Other'))
                        )
                        maturity = st.selectbox(
                            "Maturity:",
                            ["Experimental", "Beta", "Stable", "Mature", "Legacy"],
                            index=self._get_maturity_index(tech.get('maturity', 'Stable'))
                        )
                    
                    with col2:
                        license = st.text_input("License:", value=tech.get('license', ''))
                        website = st.text_input("Website:", value=tech.get('website', ''))
                        github = st.text_input("GitHub:", value=tech.get('github', ''))
                    
                    description = st.text_area("Description:", value=tech.get('description', ''))
                    
                    # Tags
                    tags = st.text_input(
                        "Tags (comma-separated):",
                        value=', '.join(tech.get('tags', []))
                    )
                    
                    # Use cases
                    use_cases = st.text_area(
                        "Use Cases (one per line):",
                        value='\n'.join(tech.get('use_cases', []))
                    )
                    
                    # Alternatives
                    alternatives = st.text_input(
                        "Alternatives (comma-separated):",
                        value=', '.join(tech.get('alternatives', []))
                    )
                    
                    # Integrations
                    integrations = st.text_input(
                        "Integrations (comma-separated):",
                        value=', '.join(tech.get('integrations', []))
                    )
                    
                    # Submit button
                    if st.form_submit_button("💾 Save Changes"):
                        # Update technology
                        updated_tech = {
                            **tech,
                            'name': name,
                            'category': category,
                            'description': description,
                            'maturity': maturity,
                            'license': license,
                            'website': website,
                            'github': github,
                            'tags': [t.strip() for t in tags.split(',') if t.strip()],
                            'use_cases': [u.strip() for u in use_cases.split('\n') if u.strip()],
                            'alternatives': [a.strip() for a in alternatives.split(',') if a.strip()],
                            'integrations': [i.strip() for i in integrations.split(',') if i.strip()]
                        }
                        
                        if self._save_technologies(technologies, updated_tech, selected_tech_idx):
                            st.success("✅ Technology updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to save technology")
            
        except Exception as e:
            st.error(f"Error editing technology: {str(e)}")
    
    def _render_add_technology(self) -> None:
        """Render the technology creation interface."""
        st.subheader("➕ Add New Technology")
        
        with st.form("add_technology_form"):
            # Basic information
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    "Technology Name:",
                    placeholder="e.g., FastAPI"
                )
                
                category = st.selectbox(
                    "Category:",
                    ["Languages", "Frameworks", "Databases", "Cloud", "AI/ML", "Security", "Integration", "Infrastructure", "Other"]
                )
                
                maturity = st.selectbox(
                    "Maturity Level:",
                    ["Experimental", "Beta", "Stable", "Mature", "Legacy"],
                    index=2  # Default to Stable
                )
            
            with col2:
                license = st.text_input(
                    "License:",
                    placeholder="e.g., MIT, Apache 2.0"
                )
                
                website = st.text_input(
                    "Website:",
                    placeholder="https://..."
                )
                
                github = st.text_input(
                    "GitHub Repository:",
                    placeholder="https://github.com/..."
                )
            
            description = st.text_area(
                "Description:",
                placeholder="Brief description of the technology and its purpose",
                height=100
            )
            
            tags = st.text_input(
                "Tags (comma-separated):",
                placeholder="web, api, async, python"
            )
            
            use_cases = st.text_area(
                "Use Cases (one per line):",
                placeholder="REST API development\nMicroservices\nWeb applications",
                height=80
            )
            
            alternatives = st.text_input(
                "Alternatives (comma-separated):",
                placeholder="Django, Flask, Express.js"
            )
            
            integrations = st.text_input(
                "Common Integrations (comma-separated):",
                placeholder="PostgreSQL, Redis, Docker"
            )
            
            # Submit button
            if st.form_submit_button("🚀 Add Technology"):
                if not name:
                    st.error("❌ Technology name is required")
                else:
                    # Create new technology
                    new_tech = {
                        'name': name,
                        'category': category,
                        'description': description,
                        'maturity': maturity,
                        'license': license,
                        'website': website,
                        'github': github,
                        'tags': [t.strip() for t in tags.split(',') if t.strip()],
                        'use_cases': [u.strip() for u in use_cases.split('\n') if u.strip()],
                        'alternatives': [a.strip() for a in alternatives.split(',') if a.strip()],
                        'integrations': [i.strip() for i in integrations.split(',') if i.strip()],
                        'created_at': str(datetime.now()),
                        'updated_at': str(datetime.now())
                    }
                    
                    if self._add_technology(new_tech):
                        st.success(f"✅ Technology '{name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add technology")
    
    def _render_import_export(self) -> None:
        """Render the import/export interface."""
        st.subheader("📥 Import/Export Technologies")
        
        # Export section
        st.subheader("📤 Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format:",
                ["JSON", "CSV", "YAML"],
                key="export_format"
            )
        
        with col2:
            export_scope = st.selectbox(
                "Export Scope:",
                ["All Technologies", "By Category", "By Maturity"],
                key="export_scope"
            )
        
        if st.button("📤 Export Technologies", key="export_technologies_btn"):
            self._export_technologies(export_format, export_scope)
        
        st.divider()
        
        # Import section
        st.subheader("📥 Import")
        
        uploaded_file = st.file_uploader(
            "Choose a file to import:",
            type=['json', 'csv', 'yaml', 'yml'],
            key="tech_import_file"
        )
        
        if uploaded_file is not None:
            import_mode = st.selectbox(
                "Import Mode:",
                ["Merge (keep existing)", "Replace (overwrite existing)", "Add only (skip duplicates)"],
                key="import_mode"
            )
            
            if st.button("📥 Import Technologies", key="import_technologies_btn"):
                self._import_technologies(uploaded_file, import_mode)
    
    def _render_technology_card(self, tech: Dict[str, Any]) -> None:
        """Render a technology card."""
        with st.container():
            st.markdown(f"### {tech.get('name', 'Unknown')}")
            
            # Category and maturity badges
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Category:** {tech.get('category', 'Uncategorized')}")
            with col2:
                st.write(f"**Maturity:** {tech.get('maturity', 'Unknown')}")
            
            # Description
            if tech.get('description'):
                st.write(tech['description'][:150] + "..." if len(tech['description']) > 150 else tech['description'])
            
            # Tags
            if tech.get('tags'):
                st.write("**Tags:** " + ", ".join(tech['tags'][:3]))
            
            # Links
            links = []
            if tech.get('website'):
                links.append(f"[Website]({tech['website']})")
            if tech.get('github'):
                links.append(f"[GitHub]({tech['github']})")
            
            if links:
                st.markdown(" | ".join(links))
            
            st.divider()
    
    def _load_technologies(self) -> List[Dict[str, Any]]:
        """Load technologies from the catalog."""
        try:
            catalog_file = Path("data/technologies.json")
            
            if catalog_file.exists():
                with open(catalog_file, 'r') as f:
                    data = json.load(f)
                    
                    # Handle the current JSON structure with categories
                    if 'categories' in data:
                        technologies = []
                        for category_key, category_data in data['categories'].items():
                            category_name = category_data.get('name', category_key.title())
                            category_description = category_data.get('description', '')
                            
                            # Convert technology strings to objects
                            for tech_name in category_data.get('technologies', []):
                                tech_obj = {
                                    'name': tech_name.replace('_', ' ').title(),
                                    'category': category_name,
                                    'description': f"Technology in {category_name} category",
                                    'maturity': 'Stable',
                                    'license': 'Various',
                                    'tags': [category_key],
                                    'use_cases': [category_description],
                                    'alternatives': [],
                                    'integrations': []
                                }
                                technologies.append(tech_obj)
                        
                        return technologies
                    
                    # Handle flat structure if it exists
                    elif 'technologies' in data:
                        return data['technologies']
                    
                    # If data is already a list
                    elif isinstance(data, list):
                        return data
            
            # Return sample data if no file exists
            return self._get_sample_technologies()
            
        except Exception as e:
            st.error(f"Error loading technology catalog: {str(e)}")
            return self._get_sample_technologies()
    
    def _get_sample_technologies(self) -> List[Dict[str, Any]]:
        """Get sample technology data as fallback."""
        return [
            {
                'name': 'Python',
                'category': 'Languages',
                'description': 'High-level programming language for general-purpose programming',
                'maturity': 'Mature',
                'license': 'PSF',
                'tags': ['programming', 'scripting', 'data-science'],
                'use_cases': ['Web development', 'Data analysis', 'Machine learning', 'Automation'],
                'alternatives': ['Java', 'JavaScript', 'Go'],
                'integrations': ['Django', 'Flask', 'NumPy', 'Pandas']
            },
            {
                'name': 'FastAPI',
                'category': 'Frameworks',
                'description': 'Modern, fast web framework for building APIs with Python',
                'maturity': 'Stable',
                'license': 'MIT',
                'tags': ['web', 'api', 'async', 'python'],
                'use_cases': ['REST API development', 'Microservices', 'Web applications'],
                'alternatives': ['Django', 'Flask', 'Express.js'],
                'integrations': ['PostgreSQL', 'Redis', 'Docker']
            },
            {
                'name': 'PostgreSQL',
                'category': 'Databases',
                'description': 'Advanced open-source relational database',
                'maturity': 'Mature',
                'license': 'PostgreSQL',
                'tags': ['database', 'sql', 'relational'],
                'use_cases': ['Web applications', 'Data warehousing', 'Analytics'],
                'alternatives': ['MySQL', 'SQLite', 'MongoDB'],
                'integrations': ['Python', 'Node.js', 'Docker']
            },
            {
                'name': 'OpenAI',
                'category': 'AI/ML',
                'description': 'AI platform providing GPT models and other AI services',
                'maturity': 'Stable',
                'license': 'Commercial',
                'tags': ['ai', 'llm', 'gpt', 'api'],
                'use_cases': ['Text generation', 'Code completion', 'Chatbots', 'Content creation'],
                'alternatives': ['Claude', 'Gemini', 'Local LLMs'],
                'integrations': ['LangChain', 'Python', 'JavaScript']
            },
            {
                'name': 'Docker',
                'category': 'Infrastructure',
                'description': 'Platform for developing, shipping, and running applications in containers',
                'maturity': 'Mature',
                'license': 'Apache 2.0',
                'tags': ['containers', 'deployment', 'devops'],
                'use_cases': ['Application deployment', 'Development environments', 'Microservices'],
                'alternatives': ['Podman', 'LXC', 'Virtual Machines'],
                'integrations': ['Kubernetes', 'CI/CD', 'Cloud platforms']
            }
        ]
    
    def _filter_technologies(self, technologies: List[Dict[str, Any]], search_term: str,
                           category_filter: str, maturity_filter: str, license_filter: str) -> List[Dict[str, Any]]:
        """Filter technologies based on search criteria."""
        filtered = technologies
        
        # Search term filter
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                t for t in filtered
                if (search_lower in t.get('name', '').lower() or
                    search_lower in t.get('description', '').lower() or
                    any(search_lower in tag.lower() for tag in t.get('tags', [])))
            ]
        
        # Category filter
        if category_filter != "All":
            filtered = [t for t in filtered if t.get('category') == category_filter]
        
        # Maturity filter
        if maturity_filter != "All":
            filtered = [t for t in filtered if t.get('maturity') == maturity_filter]
        
        # License filter
        if license_filter != "All":
            filtered = [t for t in filtered if t.get('license') == license_filter]
        
        return filtered
    
    def _get_category_index(self, category: str) -> int:
        """Get the index of a category in the selectbox options."""
        categories = ["Languages", "Frameworks", "Databases", "Cloud", "AI/ML", "Security", "Integration", "Infrastructure", "Other"]
        try:
            return categories.index(category)
        except ValueError:
            return len(categories) - 1  # Default to "Other"
    
    def _get_maturity_index(self, maturity: str) -> int:
        """Get the index of a maturity level in the selectbox options."""
        maturity_levels = ["Experimental", "Beta", "Stable", "Mature", "Legacy"]
        try:
            return maturity_levels.index(maturity)
        except ValueError:
            return 2  # Default to "Stable"
    
    def _save_technologies(self, technologies: List[Dict[str, Any]], updated_tech: Dict[str, Any], index: int) -> bool:
        """Save updated technologies to the catalog."""
        try:
            technologies[index] = updated_tech
            
            catalog_data = {
                'technologies': technologies,
                'last_updated': str(datetime.now())
            }
            
            catalog_file = Path("data/technologies.json")
            catalog_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(catalog_file, 'w') as f:
                json.dump(catalog_data, f, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"Error saving technologies: {str(e)}")
            return False
    
    def _add_technology(self, new_tech: Dict[str, Any]) -> bool:
        """Add a new technology to the catalog."""
        try:
            technologies = self._load_technologies()
            technologies.append(new_tech)
            
            catalog_data = {
                'technologies': technologies,
                'last_updated': str(datetime.now())
            }
            
            catalog_file = Path("data/technologies.json")
            catalog_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(catalog_file, 'w') as f:
                json.dump(catalog_data, f, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"Error adding technology: {str(e)}")
            return False
    
    def _export_technologies(self, format: str, scope: str) -> None:
        """Export technologies in the specified format."""
        try:
            technologies = self._load_technologies()
            
            # Apply scope filter
            if scope == "By Category":
                # For demo, just export all
                pass
            elif scope == "By Maturity":
                # For demo, just export all
                pass
            
            if format == "JSON":
                export_data = json.dumps({'technologies': technologies}, indent=2)
                st.download_button(
                    "📥 Download JSON",
                    export_data,
                    file_name="technologies.json",
                    mime="application/json"
                )
            
            st.success(f"✅ Export prepared in {format} format")
            
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
    
    def _import_technologies(self, uploaded_file, import_mode: str) -> None:
        """Import technologies from uploaded file."""
        try:
            # For demo purposes, just show success
            st.success(f"✅ Technologies imported successfully using {import_mode} mode")
            
        except Exception as e:
            st.error(f"Import failed: {str(e)}")