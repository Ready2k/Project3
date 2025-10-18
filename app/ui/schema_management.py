"""
Schema Management UI - Interface for configuring validation enums.

This module provides a Streamlit interface for users to view and modify
the configurable validation enums used in pattern schemas.
"""

import streamlit as st
import json

from app.pattern.dynamic_schema_loader import dynamic_schema_loader


def render_schema_management() -> None:
    """Render the schema management interface."""
    st.header("🔧 Schema Configuration")
    st.write(
        "Configure validation enums for pattern schemas. This allows you to customize what values are accepted for different pattern fields."
    )

    # Load current configuration
    try:
        config = dynamic_schema_loader.load_config()
        schema_enums = config.get("schema_enums", {})
        validation_settings = config.get("validation_settings", {})
    except Exception as e:
        st.error(f"Failed to load schema configuration: {e}")
        return

    # Validation Settings
    st.subheader("⚙️ Validation Settings")

    col1, col2 = st.columns(2)

    with col1:
        strict_mode = st.checkbox(
            "Strict Mode",
            value=validation_settings.get("strict_mode", False),
            help="When enabled, only predefined enum values are allowed",
        )

        allow_custom = st.checkbox(
            "Allow Custom Values",
            value=validation_settings.get("allow_custom_values", True),
            help="Allow patterns to use values not in the predefined lists",
        )

    with col2:
        warn_unknown = st.checkbox(
            "Warn on Unknown Values",
            value=validation_settings.get("warn_on_unknown_values", True),
            help="Log warnings when unknown enum values are encountered",
        )

        auto_add = st.checkbox(
            "Auto-add New Values",
            value=validation_settings.get("auto_add_new_values", True),
            help="Automatically add new values to extensible enums",
        )

    # Save settings button
    if st.button("💾 Save Validation Settings"):
        try:
            config["validation_settings"] = {
                "strict_mode": strict_mode,
                "allow_custom_values": allow_custom,
                "warn_on_unknown_values": warn_unknown,
                "auto_add_new_values": auto_add,
            }

            with open(dynamic_schema_loader.config_path, "w") as f:
                json.dump(config, f, indent=2)

            dynamic_schema_loader.clear_cache()
            st.success("✅ Validation settings saved successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Failed to save settings: {e}")

    st.divider()

    # Enum Management
    st.subheader("📋 Enum Configuration")

    if not schema_enums:
        st.info("No configurable enums found. Check your schema configuration file.")
        return

    # Enum selector
    enum_names = list(schema_enums.keys())
    selected_enum = st.selectbox(
        "Select Enum to Configure",
        enum_names,
        help="Choose which enum you want to view or modify",
    )

    if selected_enum:
        enum_config = schema_enums[selected_enum]

        # Enum info
        st.write(
            f"**Description:** {enum_config.get('description', 'No description available')}"
        )
        st.write(
            f"**User Extensible:** {'✅ Yes' if enum_config.get('user_extensible', False) else '❌ No'}"
        )

        # Current values
        current_values = enum_config.get("values", [])
        st.write(f"**Current Values ({len(current_values)}):**")

        # Display values in a nice format
        if current_values:
            # Create columns for better display
            cols = st.columns(3)
            for i, value in enumerate(current_values):
                with cols[i % 3]:
                    st.code(value)
        else:
            st.info("No values configured for this enum.")

        # Add new value (if extensible)
        if enum_config.get("user_extensible", False):
            st.subheader(f"➕ Add New Value to '{selected_enum}'")

            new_value = st.text_input(
                "New Value",
                placeholder="Enter new enum value...",
                help="Add a new allowed value for this enum",
            )

            col1, col2 = st.columns([1, 3])

            with col1:
                if st.button("Add Value", disabled=not new_value.strip()):
                    if new_value.strip():
                        success = dynamic_schema_loader.add_enum_value(
                            selected_enum, new_value.strip()
                        )
                        if success:
                            st.success(f"✅ Added '{new_value}' to {selected_enum}")
                            st.rerun()
                        else:
                            st.error(f"Failed to add value to {selected_enum}")

            # Remove value
            st.subheader(f"🗑️ Remove Value from '{selected_enum}'")

            if current_values:
                value_to_remove = st.selectbox(
                    "Select value to remove",
                    current_values,
                    help="Choose a value to remove from this enum",
                )

                if st.button("Remove Value", type="secondary"):
                    try:
                        current_values.remove(value_to_remove)
                        enum_config["values"] = current_values

                        with open(dynamic_schema_loader.config_path, "w") as f:
                            json.dump(config, f, indent=2)

                        dynamic_schema_loader.clear_cache()
                        st.success(
                            f"✅ Removed '{value_to_remove}' from {selected_enum}"
                        )
                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed to remove value: {e}")
        else:
            st.info(
                f"The '{selected_enum}' enum is not user extensible. Values are fixed by the system."
            )

    # Export/Import Configuration
    st.divider()
    st.subheader("📤 Export/Import Configuration")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📋 Export Configuration"):
            config_json = json.dumps(config, indent=2)
            st.download_button(
                label="💾 Download Configuration",
                data=config_json,
                file_name="schema_config.json",
                mime="application/json",
            )

    with col2:
        uploaded_file = st.file_uploader(
            "📁 Import Configuration",
            type=["json"],
            help="Upload a schema configuration file",
        )

        if uploaded_file is not None:
            try:
                imported_config = json.load(uploaded_file)

                # Validate basic structure
                if (
                    "schema_enums" in imported_config
                    and "validation_settings" in imported_config
                ):
                    if st.button("✅ Apply Imported Configuration"):
                        with open(dynamic_schema_loader.config_path, "w") as f:
                            json.dump(imported_config, f, indent=2)

                        dynamic_schema_loader.clear_cache()
                        st.success("✅ Configuration imported successfully!")
                        st.rerun()
                else:
                    st.error("Invalid configuration file format")

            except Exception as e:
                st.error(f"Failed to parse configuration file: {e}")


def render_enum_usage_stats() -> None:
    """Render statistics about enum usage in patterns."""
    st.subheader("📊 Enum Usage Statistics")

    try:
        # This would require analyzing existing patterns
        # For now, show a placeholder
        # Enum usage statistics placeholder
        st.info("📊 **Enum Usage Statistics**")
        st.write("Pattern analysis features:")

        with st.expander("📈 Usage Analytics (Coming Soon)"):
            st.write("Future features will include:")
            st.write("• Most commonly used enum values across patterns")
            st.write("• Unused enum values that could be removed")
            st.write("• Pattern distribution by enum categories")
            st.write("• Trend analysis of enum usage over time")

            # Placeholder for future implementation
            if st.button("🔄 Analyze Pattern Usage", disabled=True):
                st.info("This feature will be implemented in a future release.")
        # - Patterns that use non-standard values

    except Exception as e:
        st.error(f"Failed to generate usage statistics: {e}")
