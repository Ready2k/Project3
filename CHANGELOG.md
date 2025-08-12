# Changelog

All notable changes to the Automated AI Assessment (AAA) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **LLM-Driven Tech Stack Generation**: Replaced rule-based tech stack suggestions with intelligent LLM analysis
  - Contextual technology recommendations based on specific requirements
  - Pattern-aware suggestions using successful patterns as starting points
  - Constraint-aware filtering of banned tools and required integrations
  - Full audit trail of LLM prompts and responses
- **AI-Generated Architecture Explanations**: LLM-driven explanations of how technology components work together
  - Replaces hardcoded generic explanations with contextual analysis
  - Specific to user requirements and chosen technology stack
  - 2x more detailed than previous rule-based explanations
- **Enhanced LLM Message Observability**: Improved transparency and debugging capabilities

### Improved
- **Enhanced Diagram Viewing Experience**: Major improvements to Mermaid diagram rendering
  - Added "Open in Browser" button for full-size standalone viewing
  - Standalone HTML files with interactive controls (zoom, pan, print)
  - SVG download functionality for high-quality exports
  - Direct links to Mermaid Live Editor for code editing
  - Better fallback rendering with improved CSS styling
  - Added streamlit-mermaid package for native Streamlit integration
  - Downloadable HTML files with embedded Mermaid viewer

### Fixed
- **Question Generation Duplication**: Resolved duplicate LLM calls during Q&A phase
  - Implemented robust multi-layer caching system
  - Added rapid-fire request protection (30s at QuestionLoop, 10s at API level)
  - Improved cache key generation for stability and consistency
  - Added automatic cache cleanup to prevent memory leaks
  - Enhanced logging for better debugging and monitoring
  - Reduced unnecessary LLM API costs from eliminated duplicate calls
  - Purpose filtering for different types of LLM calls (tech_stack_generation, architecture_explanation)
  - Complete prompt and response logging with timing and metadata
  - Better categorization and display of LLM interactions

### Changed
- **Tech Stack Generation**: Moved from simple rule-based additions to intelligent LLM analysis
- **Architecture Explanations**: Now generated dynamically by LLM instead of using hardcoded templates
- **Pattern Creator**: Updated to use intelligent tech stack generation for new patterns
- **Recommendation Service**: Integrated with new TechStackGenerator for better technology suggestions

### Technical Details
- Added `TechStackGenerator` service (`app/services/tech_stack_generator.py`)
- Added `ArchitectureExplainer` service (`app/services/architecture_explainer.py`)
- Enhanced LLM audit logging with purpose tracking
- Updated Streamlit UI to use async LLM-driven architecture explanations
- Improved LLM message filtering and display in observability dashboard

### Benefits
- **More Realistic Tech Stacks**: No more generic suggestions like "OpenCV, WebSocket, pyzbar" for unrelated use cases
- **Justified Recommendations**: LLM provides reasoning for each technology choice
- **Full Transparency**: Complete visibility into AI decision-making process
- **Better User Experience**: Contextual, relevant technology suggestions that directly address requirements

## [Previous Versions]

Previous version history would be documented here as the project evolves.