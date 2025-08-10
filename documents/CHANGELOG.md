# Changelog

All notable changes to Automated AI Assessment (AAA) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.2] - 2025-01-09

### Added
- **AI-Generated Architecture Diagrams**: Context, Container, and Sequence diagrams using Mermaid
  - LLM creates contextual diagrams based on specific requirements
  - Proper C4 architecture patterns with decision points and alternatives
  - On-demand generation with diagram code viewing
- **Enhanced Provider Selection**: FakeLLM now available as explicit choice instead of fallback
  - Clear provider selection in UI sidebar
  - No more silent fallbacks to FakeLLM
  - Better error messages when providers are misconfigured
- **AI-Powered Q&A System**: LLM generates contextual questions instead of hardcoded templates
  - Questions tailored to specific requirements
  - Focus on physical vs digital, data sources, and complexity
  - Intelligent completion detection

### Fixed
- **Session State Persistence**: Provider configuration now properly stored and retrieved
  - Fixed Q&A system using correct LLM provider instead of FakeLLM
  - Proper serialization of provider config in session state
- **Q&A Flow Improvements**: 
  - Added submit button to prevent constant API calls during typing
  - Fixed phase transitions from Q&A to matching
  - Smart polling that pauses during user input phases
  - Better progress tracking and status updates
- **Provider Audit Logging**: Observability dashboard now shows actual providers used
  - Fixed "fake/fake-llm" appearing when real providers were used
  - Proper provider tracking and performance metrics
- **Diagram Rendering**: Fixed Mermaid syntax errors
  - Automatic cleaning of markdown code blocks from LLM responses
  - Proper handling of diagram generation errors

### Improved
- **User Experience**: 
  - Real-time progress tracking with phase-aware updates
  - Better error handling and user feedback
  - Clearer provider configuration and testing
- **Documentation**: 
  - Updated README with new features and usage examples
  - Enhanced troubleshooting guide
  - Added diagram generation documentation

### Technical
- **Code Quality**: 
  - Better error handling and logging throughout
  - Improved session state management
  - Enhanced provider abstraction
- **Performance**: 
  - Reduced unnecessary API calls during Q&A
  - Smarter polling and status updates
  - Optimized diagram generation

## [1.3.1] - 2024-12-XX

### Added
- Initial release with core functionality
- Multi-provider LLM support (OpenAI, Bedrock, Claude, Internal)
- Pattern matching with FAISS vector search
- Template-based Q&A system
- Export functionality (JSON/Markdown)
- Streamlit web interface
- FastAPI backend
- Observability dashboard

### Features
- Session-based requirement analysis
- Feasibility assessment with confidence scores
- Tech stack recommendations
- Progress tracking
- Provider switching
- Audit logging