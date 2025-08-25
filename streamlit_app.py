#!/usr/bin/env python3
"""
Main Streamlit application entry point for the AAA system.

This is the main entry point for the refactored Streamlit application
using the new modular architecture.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main application entry point."""
    try:
        # Import and run the main app
        from app.ui.main_app import AAAStreamlitApp
        
        # Create and run the application
        app = AAAStreamlitApp()
        app.run()
        
    except ImportError as e:
        # Fallback to legacy app if new architecture fails
        try:
            import streamlit as st
            st.title("🤖 Automated AI Assessment (AAA)")
            st.error(f"❌ New Architecture Import Error: {e}")
            st.warning("🔄 Attempting to load legacy interface...")
            
            # Try to load legacy app
            try:
                from legacy.streamlit_app_legacy import main as legacy_main
                st.success("✅ Loading legacy interface...")
                legacy_main()
            except ImportError:
                st.error("❌ Legacy interface also unavailable")
                st.error("💡 Please check system configuration and dependencies")
                
                # Show basic interface
                st.markdown("## Basic Interface")
                st.text_area("Enter your requirements:", placeholder="Describe what you want to automate...")
                if st.button("Analyze"):
                    st.info("⚠️ Analysis functionality requires full system setup")
                
        except Exception as fallback_error:
            print(f"Complete failure: {fallback_error}")
            
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Application Error: {e}")
        st.error("💡 An unexpected error occurred while starting the application.")
        
        # Show debug information
        with st.expander("🐛 Debug Information"):
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()