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

### Changed
- Q&A input fields changed from `text_input` to `text_area` to prevent password manager interference
- Tech stack display now shows categorized technologies with explanations instead of basic lists
- Pattern creation logic now checks for conceptual similarity before creating new patterns
- Enhanced pattern matching with weighted scoring system (business process 40%, domain 20%, pattern types 20%, feasibility 10%, compliance 10%)

### Fixed
- Password manager (1Password) interference with Q&A input fields
- Q&A answer counting issues that showed incorrect progress
- Pattern duplication problem (e.g., PAT-015 and PAT-016 for same use case)
- Poor tech stack categorization and lack of context in recommendations
- Text formatting issues with run-on paragraphs in technical analysis

### Technical Details
- Added `_is_conceptually_similar()` method with 70% similarity threshold
- Added `_enhance_existing_pattern()` method for intelligent pattern merging
- Added `categorize_tech_stack_with_descriptions()` method in TechStackGenerator
- Added `_render_formatted_text()` helper for better text display
- Enhanced RecommendationService with async pattern creation decision logic

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