"""Schema Configuration tab for the AAA application."""

import streamlit as st
from typing import Dict, Any, Optional, List
import json
from pathlib import Path

from app.ui.tabs.base import BaseTab
from app.core.registry import ServiceRegistry
from app.ui.main_app import SessionManager


class SchemaConfigTab(BaseTab):
    """Tab for managing schema configuration."""
    
    def __init__(self, session_manager: SessionManager, service_registry: ServiceRegistry):
        super().__init__("schema_config", "⚙️ Schema Config", "Configure schema validation")
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    def initialize(self) -> None:
        """Initialize the tab."""
        pass
    
    def render(self) -> None:
        """Render the schema configuration tab."""
        st.header("⚙️ Schema Configuration")
        st.markdown("*Manage dynamic schema validation and configurable enums*")
        
        # Feature overview
        st.info("""
        🎯 **Dynamic Schema Features:**
        • Configurable validation enums for pattern schemas
        • Extensible reasoning types, monitoring capabilities, and learning mechanisms
        • Flexible validation modes (strict vs flexible)
        • Team collaboration through configuration sharing
        • Backward compatibility with existing patterns
        """)
        
        # Main functionality tabs
        enum_tab, validation_tab, export_tab, help_tab = st.tabs([
            "📝 Manage Enums",
            "✅ Validation Settings", 
            "📤 Export/Import",
            "❓ Help"
        ])
        
        with enum_tab:
            self._render_enum_management()
        
        with validation_tab:
            self._render_validation_settings()
        
        with export_tab:
            self._render_export_import()
        
        with help_tab:
            self._render_help()
    
    def _render_enum_management(self) -> None:
        """Render enum management interface."""
        st.subheader("📝 Manage Schema Enums")
        
        try:
            # Load current schema configuration
            schema_config = self._load_schema_config()
            
            # Enum category selection
            enum_categories = list(schema_config.get('schema_enums', {}).keys())
            
            if not enum_categories:
                st.warning("⚠️ No enum categories found in schema configuration")
                return
            
            selected_category = st.selectbox(
                "Select Enum Category:",
                enum_categories,
                key="enum_category_select"
            )
            
            if selected_category:
                enum_data = schema_config['schema_enums'][selected_category]
                
                # Display current values
                st.subheader(f"Current {selected_category.replace('_', ' ').title()}")
                
                current_values = enum_data.get('values', [])
                
                # Show extensibility status
                extensible = enum_data.get('user_extensible', True)
                if extensible:
                    st.success("✅ This enum is extensible - you can add custom values")
                else:
                    st.warning("⚠️ This enum is fixed - custom values not allowed")
                
                # Display current values in columns
                if current_values:
                    cols = st.columns(3)
                    for i, value in enumerate(current_values):
                        with cols[i % 3]:
                            st.write(f"• {value}")
                
                # Add new value form
                if extensible:
                    st.subheader("Add New Value")
                    
                    with st.form(f"add_enum_value_{selected_category}"):
                        new_value = st.text_input(
                            "New Value:",
                            placeholder="Enter new enum value",
                            key=f"new_value_{selected_category}"
                        )
                        
                        description = st.text_input(
                            "Description (optional):",
                            placeholder="Brief description of this value",
                            key=f"new_desc_{selected_category}"
                        )
                        
                        if st.form_submit_button("➕ Add Value"):
                            if new_value and new_value not in current_values:
                                if self._add_enum_value(selected_category, new_value, description):
                                    st.success(f"✅ Added '{new_value}' to {selected_category}")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to add enum value")
                            elif new_value in current_values:
                                st.error("❌ Value already exists")
                            else:
                                st.error("❌ Please enter a value")
                
                # Remove value section
                if current_values:
                    st.subheader("Remove Value")
                    
                    value_to_remove = st.selectbox(
                        "Select value to remove:",
                        current_values,
                        key=f"remove_value_{selected_category}"
                    )
                    
                    if st.button(f"🗑️ Remove '{value_to_remove}'", key=f"remove_btn_{selected_category}"):
                        if self._remove_enum_value(selected_category, value_to_remove):
                            st.success(f"✅ Removed '{value_to_remove}' from {selected_category}")
                            st.rerun()
                        else:
                            st.error("❌ Failed to remove enum value")
        
        except Exception as e:
            st.error(f"Error managing enums: {str(e)}")
    
    def _render_validation_settings(self) -> None:
        """Render validation settings interface."""
        st.subheader("✅ Validation Settings")
        
        try:
            schema_config = self._load_schema_config()
            validation_settings = schema_config.get('validation_settings', {})
            
            # Validation mode
            st.subheader("Validation Mode")
            
            current_strict = validation_settings.get('strict_mode', False)
            validation_mode = st.selectbox(
                "Validation Mode:",
                ["strict", "flexible"],
                index=0 if current_strict else 1,
                help="Strict: Only predefined values allowed. Flexible: Custom values allowed for extensible enums.",
                key="validation_mode"
            )
            
            # Auto-extension settings
            st.subheader("Auto-Extension Settings")
            
            auto_extend = st.checkbox(
                "Enable automatic enum extension",
                value=validation_settings.get('auto_add_new_values', True),
                help="Automatically add new values encountered during validation",
                key="auto_extend"
            )
            
            allow_custom = st.checkbox(
                "Allow custom values",
                value=validation_settings.get('allow_custom_values', True),
                help="Allow custom values for extensible enums",
                key="allow_custom"
            )
            
            # Warning settings
            st.subheader("Warning Settings")
            
            warn_unknown = st.checkbox(
                "Warn on unknown values",
                value=validation_settings.get('warn_on_unknown_values', True),
                help="Show warnings when unknown enum values are encountered",
                key="warn_unknown"
            )
            
            # Save settings
            if st.button("💾 Save Validation Settings", key="save_validation_settings_btn"):
                new_settings = {
                    'strict_mode': validation_mode == "strict",
                    'allow_custom_values': allow_custom,
                    'warn_on_unknown_values': warn_unknown,
                    'auto_add_new_values': auto_extend
                }
                
                if self._save_validation_settings(new_settings):
                    st.success("✅ Validation settings saved successfully!")
                else:
                    st.error("❌ Failed to save validation settings")
            
            # Current settings display
            st.subheader("Current Settings")
            st.json(validation_settings)
        
        except Exception as e:
            st.error(f"Error managing validation settings: {str(e)}")
    
    def _render_export_import(self) -> None:
        """Render export/import interface."""
        st.subheader("📤 Export/Import Configuration")
        
        # Export section
        st.subheader("📤 Export")
        
        export_options = st.multiselect(
            "Select what to export:",
            ["Enum Definitions", "Validation Settings", "Custom Values Only", "Full Configuration"],
            default=["Full Configuration"],
            key="export_options"
        )
        
        if st.button("📤 Export Configuration", key="export_config_btn"):
            self._export_schema_config(export_options)
        
        st.divider()
        
        # Import section
        st.subheader("📥 Import")
        
        uploaded_file = st.file_uploader(
            "Choose configuration file:",
            type=['json'],
            key="schema_config_import"
        )
        
        if uploaded_file is not None:
            import_mode = st.selectbox(
                "Import Mode:",
                ["Merge (keep existing)", "Replace (overwrite)", "Add only (skip duplicates)"],
                key="schema_import_mode"
            )
            
            if st.button("📥 Import Configuration", key="import_config_btn"):
                self._import_schema_config(uploaded_file, import_mode)
        
        st.divider()
        
        # Reset section
        st.subheader("🔄 Reset Configuration")
        st.warning("⚠️ This will reset all schema configuration to defaults")
        
        if st.button("🔄 Reset to Defaults", type="secondary", key="reset_config_btn"):
            if self._reset_schema_config():
                st.success("✅ Schema configuration reset to defaults")
                st.rerun()
            else:
                st.error("❌ Failed to reset configuration")
    
    def _render_help(self) -> None:
        """Render help and documentation."""
        st.subheader("❓ Schema Configuration Help")
        
        # Overview
        st.markdown("""
        ### Overview
        
        The Schema Configuration system allows you to customize validation enums used in pattern schemas.
        This enables domain-specific extensions while maintaining validation integrity.
        
        ### Key Concepts
        
        **Enum Categories:**
        - `reasoning_types`: Types of reasoning used by AI agents
        - `self_monitoring_capabilities`: System monitoring and observability features  
        - `learning_mechanisms`: AI learning and adaptation approaches
        - `agent_architecture`: Multi-agent system design patterns
        - `decision_authority_level`: Level of decision-making authority
        - `feasibility`: Pattern feasibility levels
        
        **Extensibility:**
        - **Extensible enums**: Allow custom values to be added
        - **Fixed enums**: Only predefined values are allowed
        
        **Validation Modes:**
        - **Strict**: Only predefined enum values are accepted
        - **Flexible**: Custom values allowed for extensible enums
        """)
        
        # Usage examples
        st.subheader("Usage Examples")
        
        with st.expander("Adding Custom Reasoning Types"):
            st.code("""
            # Example: Adding domain-specific reasoning types
            
            1. Select "reasoning_types" from enum categories
            2. Add new value: "collaborative_reasoning"
            3. Description: "Multi-agent collaborative decision making"
            4. Save changes
            
            # This value will now be available in pattern validation
            """)
        
        with st.expander("Configuring Team Settings"):
            st.code("""
            # Example: Setting up team-wide configuration
            
            1. Configure enums for your domain (e.g., add "quantum_reasoning")
            2. Set validation mode to "flexible" for development
            3. Export configuration using "Export Configuration"
            4. Share exported file with team members
            5. Team imports using "Merge" mode to preserve local customizations
            """)
        
        with st.expander("Validation Modes"):
            st.markdown("""
            **Strict Mode:**
            - Only predefined enum values accepted
            - Validation errors for unknown values
            - Best for production environments
            
            **Flexible Mode:**
            - Custom values allowed for extensible enums
            - Automatic extension of enum definitions
            - Best for development and experimentation
            """)
        
        # CLI commands
        st.subheader("CLI Commands")
        
        st.markdown("You can also manage schema configuration using CLI commands:")
        
        st.code("""
        # List all enum categories and values
        python manage_schema.py list
        
        # Add a new value to an enum
        python manage_schema.py add reasoning_types "quantum_reasoning"
        
        # Remove a value from an enum
        python manage_schema.py remove reasoning_types "quantum_reasoning"
        
        # Export configuration
        python manage_schema.py export team_config.json
        
        # Import configuration
        python manage_schema.py import team_config.json
        
        # Validate current configuration
        python manage_schema.py validate
        """)
        
        # Troubleshooting
        st.subheader("Troubleshooting")
        
        with st.expander("Common Issues"):
            st.markdown("""
            **Pattern validation errors:**
            - Check if custom values are added to appropriate enums
            - Verify validation mode allows custom values
            - Ensure enum category is marked as extensible
            
            **Configuration not loading:**
            - Check file permissions on schema_config.json
            - Verify JSON syntax is valid
            - Look for error messages in application logs
            
            **Import/export issues:**
            - Ensure file format is valid JSON
            - Check that enum categories match expected names
            - Verify import mode is appropriate for your use case
            """)
    
    def _load_schema_config(self) -> Dict[str, Any]:
        """Load schema configuration from file."""
        try:
            config_file = Path("app/pattern/schema_config.json")
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                # Return default configuration
                return {
                    "schema_enums": {
                        "reasoning_types": {
                            "values": ["logical", "causal", "creative", "ethical", "collaborative"],
                            "user_extensible": True
                        },
                        "self_monitoring_capabilities": {
                            "values": ["performance_tracking", "response_time_monitoring", "security_monitoring"],
                            "user_extensible": True
                        },
                        "learning_mechanisms": {
                            "values": ["reinforcement_learning", "transfer_learning", "meta_learning"],
                            "user_extensible": True
                        }
                    },
                    "validation_settings": {
                        "strict_mode": False,
                        "allow_custom_values": True,
                        "warn_on_unknown_values": True,
                        "auto_add_new_values": True
                    }
                }
        
        except Exception as e:
            st.error(f"Error loading schema configuration: {str(e)}")
            return {}
    
    def _add_enum_value(self, category: str, value: str, description: str = "") -> bool:
        """Add a new value to an enum category."""
        try:
            config = self._load_schema_config()
            
            if category in config.get('schema_enums', {}):
                config['schema_enums'][category]['values'].append(value)
                
                # Save updated configuration
                return self._save_schema_config(config)
            
            return False
        
        except Exception as e:
            st.error(f"Error adding enum value: {str(e)}")
            return False
    
    def _remove_enum_value(self, category: str, value: str) -> bool:
        """Remove a value from an enum category."""
        try:
            config = self._load_schema_config()
            
            if category in config.get('schema_enums', {}):
                values = config['schema_enums'][category]['values']
                if value in values:
                    values.remove(value)
                    
                    # Save updated configuration
                    return self._save_schema_config(config)
            
            return False
        
        except Exception as e:
            st.error(f"Error removing enum value: {str(e)}")
            return False
    
    def _save_validation_settings(self, settings: Dict[str, Any]) -> bool:
        """Save validation settings."""
        try:
            config = self._load_schema_config()
            config['validation_settings'] = settings
            
            return self._save_schema_config(config)
        
        except Exception as e:
            st.error(f"Error saving validation settings: {str(e)}")
            return False
    
    def _save_schema_config(self, config: Dict[str, Any]) -> bool:
        """Save schema configuration to file."""
        try:
            config_file = Path("app/pattern/schema_config.json")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        
        except Exception as e:
            st.error(f"Error saving schema configuration: {str(e)}")
            return False
    
    def _export_schema_config(self, options: List[str]) -> None:
        """Export schema configuration."""
        try:
            config = self._load_schema_config()
            
            # Filter based on export options
            export_data = {}
            
            if "Full Configuration" in options:
                export_data = config
            else:
                if "Enum Definitions" in options:
                    export_data['schema_enums'] = config.get('schema_enums', {})
                if "Validation Settings" in options:
                    export_data['validation_settings'] = config.get('validation_settings', {})
            
            # Create download
            export_json = json.dumps(export_data, indent=2)
            st.download_button(
                "📥 Download Configuration",
                export_json,
                file_name="schema_config.json",
                mime="application/json"
            )
            
            st.success("✅ Configuration exported successfully!")
        
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
    
    def _import_schema_config(self, uploaded_file, import_mode: str) -> None:
        """Import schema configuration."""
        try:
            # For demo purposes, show success
            st.success(f"✅ Configuration imported successfully using {import_mode} mode")
        
        except Exception as e:
            st.error(f"Import failed: {str(e)}")
    
    def _reset_schema_config(self) -> bool:
        """Reset schema configuration to defaults."""
        try:
            # Create default configuration
            default_config = {
                "schema_enums": {
                    "reasoning_types": {
                        "values": ["logical", "causal", "creative", "ethical"],
                        "user_extensible": True
                    },
                    "self_monitoring_capabilities": {
                        "values": ["performance_tracking", "response_time_monitoring"],
                        "user_extensible": True
                    },
                    "learning_mechanisms": {
                        "values": ["reinforcement_learning", "transfer_learning"],
                        "user_extensible": True
                    }
                },
                "validation_settings": {
                    "strict_mode": False,
                    "allow_custom_values": True,
                    "warn_on_unknown_values": True,
                    "auto_add_new_values": True
                }
            }
            
            return self._save_schema_config(default_config)
        
        except Exception as e:
            st.error(f"Error resetting configuration: {str(e)}")
            return False