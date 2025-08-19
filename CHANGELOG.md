# Changelog

All notable changes to the Automated AI Assessment (AAA) system will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pattern duplication prevention system with conceptual similarity detection
- Smart pattern enhancement instead of creating duplicates
- Enhanced tech stack categorization with 9 specific categories and descriptions
- Individual technology descriptions explaining purpose and use cases
- Debug mode for Q&A troubleshooting
- Session tracking for pattern enhancements with audit trail
- Improved text formatting with automatic paragraph breaks and section headers
- **Tech Stack Wiring Diagram**: New diagram type showing technical component connections
- **Comprehensive Technology Constraints**: Banned technologies, compliance requirements, budget constraints
- **Robust Mermaid Error Handling**: Improved diagram generation with fallbacks and user guidance
- **AWS Bedrock Credentials Configuration**: Full support for AWS credentials in Streamlit UI and API
  - Individual field input and combined format options
  - Environment variable support (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
  - Secure credential handling with password-masked inputs
  - Backward compatibility with existing AWS credential methods

### Changed
- Q&A input fields changed from `text_input` to `text_area` to prevent password manager interference
- Tech stack display now shows categorized technologies with explanations instead of basic lists
- Pattern creation logic now checks for conceptual similarity before creating new patterns
- Enhanced pattern matching with weighted scoring system (business process 40%, domain 20%, pattern types 20%, feasibility 10%, compliance 10%)
- **Diagram system expanded** from 3 to 4 diagram types with enhanced error handling
- **Input methods enhanced** with comprehensive constraint capture across text, file, and Jira inputs

### Fixed
- Password manager (1Password) interference with Q&A input fields
- Q&A answer counting issues that showed incorrect progress
- Pattern duplication problem (e.g., PAT-015 and PAT-016 for same use case)
- Poor tech stack categorization and lack of context in recommendations
- Text formatting issues with run-on paragraphs in technical analysis
- **Mermaid diagram syntax errors** from malformed LLM output
- **Missing enterprise constraints** functionality for technology restrictions

### Technical Details
- Added `_is_conceptually_similar()` method with 70% similarity threshold
- Added `_enhance_existing_pattern()` method for intelligent pattern merging
- Added `categorize_tech_stack_with_descriptions()` method in TechStackGenerator
- Added `_render_formatted_text()` helper for better text display
- Enhanced RecommendationService with async pattern creation decision logic
- **Added `build_tech_stack_wiring_diagram()`** for technical architecture visualization
- **Added `_clean_mermaid_code()`** for robust diagram generation error handling
- **Enhanced constraint handling** throughout the recommendation pipeline

## [1.0.0] - 2024-12-XX

### Added
- Initial release of Automated AI Assessment system
- Multi-provider LLM support (OpenAI, Anthropic, Bedrock, Internal, Fake)
- Intelligent pattern matching with tag filtering and vector similarity
- AI-generated Q&A system for requirement clarification
- LLM-driven tech stack generation and architecture explanations
- Interactive Mermaid diagram generation with enhanced viewing
- Comprehensive export system (JSON, Markdown, HTML)
- Real-time progress tracking and session management
- Complete audit trail for LLM interactions
- 100% test coverage with deterministic fakes
- Docker containerization with production-ready setup
- Pattern library management with CRUD operations
- Jira integration for ticket-based requirements
- Observability dashboard with performance metrics