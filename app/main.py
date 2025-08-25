"""New modular Streamlit entry point for Automated AI Assessment (AAA)."""

from app.ui.main_app import create_app, AAAStreamlitApp


def main() -> None:
    """Main function to run the modular Streamlit app."""
    app: AAAStreamlitApp = create_app()
    app.run()


if __name__ == "__main__":
    main()