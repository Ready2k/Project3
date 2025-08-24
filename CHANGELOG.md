# Changelog

All notable changes to the Automated AI Assessment (AAA) system will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.6.0] - 2025-08-24 - Complete System Enhancement

### Added
- **Resume Previous Session Feature**: Complete session continuity functionality
  - New "Resume Previous Session" input method in Analysis tab
  - Session ID validation with UUID format checking and helpful error messages
  - Complete session state restoration (phase, progress, requirements, recommendations)
  - Session information display with copy-to-clipboard functionality
  - Cross-session compatibility with all input methods (Text, File Upload, Jira Integration)
  - Comprehensive help system with "Where do I find my Session ID?" guidance
- **Enhanced Mermaid Code Extraction**: Robust handling of mixed LLM responses
  - Smart code extraction from responses with explanatory text
  - Multiple format support (markdown blocks, explanations before/after, clean code)
  - Regex pattern matching for valid diagram types (flowchart, graph, sequenceDiagram, C4Context, etc.)
  - Syntax validation to ensure extracted code is valid Mermaid
  - Enhanced prompts with explicit instructions to discourage explanatory text
- **Jira Integration Agent Name Fix**: Dynamic, context-aware agent naming
  - Replaced hardcoded "Primary Autonomous Agent" with intelligent agent name generation
  - Context-aware names based on requirement content (User Management Agent, Communication Agent, etc.)
  - Simplified Jira integration to remove metadata pollution from requirements
  - Dynamic agent naming across all agent creation methods (single-agent, custom pattern, scope-limited)
- **Agentic Recommendation Service Bug Fix**: Critical attribute access fixes
  - Fixed `'AutonomyAssessment' object has no attribute 'workflow_automation'` error
  - Corrected attribute access in pattern saving methods (`workflow_automation` → `workflow_coverage`)
  - Fixed enum value access for proper serialization (`reasoning_complexity.value`)
  - Consistent implementation across both `_save_agentic_pattern()` and `_save_multi_agent_pattern()` methods

### Changed
- **Session Management**: Enhanced with resume functionality and improved user experience
- **Agent Naming**: All agents now get meaningful, context-specific names instead of generic labels
- **Jira Integration**: Streamlined to focus on essential fields (description combining summary + description)
- **Mermaid Processing**: Enhanced extraction and validation pipeline for better diagram rendering
- **Pattern Saving**: Fixed critical bugs preventing APAT pattern creation and saving

### Fixed
- **Session Resume Issues**: Users can now return to any previous analysis session using session ID
- **Mermaid Rendering Failures**: LLM responses with explanatory text no longer break diagram rendering
- **Generic Agent Names**: All agents in diagrams now show proper, contextual names
- **Pattern Saving Crashes**: Agentic recommendation service no longer crashes during pattern creation
- **Jira Metadata Pollution**: Jira ticket fields no longer pollute agent generation process
- **AttributeError Crashes**: Fixed attribute access issues in `AutonomyAssessment` class usage

### Technical Details
- **Resume Session Implementation**:
  - New `render_resume_session()` method with user-friendly form interface
  - Regex pattern matching for UUID format with case-insensitive support
  - Integration with existing `/status/{session_id}` endpoint for session retrieval
  - Enhanced error handling with comprehensive error messages and troubleshooting tips
- **Mermaid Code Extraction**:
  - New `_extract_mermaid_code()` function with intelligent extraction logic
  - Enhanced `_looks_like_mermaid_code()` function for syntax validation
  - Multiple fallback strategies for different response formats
  - Integration with existing `_clean_mermaid_code()` processing pipeline
- **Agent Name Generation**:
  - New `_generate_agent_name()` method with 14 domain categories
  - Intelligent keyword matching for user, data, email, report, workflow, integration, monitoring, security
  - Action-based fallbacks for comprehensive coverage
- **Jira Service Fixes**:
  - Streamlined `map_ticket_to_requirements()` to only use summary and description
  - Removed extra Jira fields (priority, status, assignee, reporter, labels, components) from requirements
- **Agentic Service Fixes**:
  - Corrected attribute names in pattern saving methods (lines ~936 and ~1029)
  - Fixed enum value access for proper JSON serialization
  - Enhanced error handling and validation in pattern creation

### Results
- ✅ Users can resume any previous session for improved workflow continuity
- ✅ Diagrams render correctly with mixed LLM responses containing explanatory text
- ✅ Agent names are context-specific and meaningful in all diagrams
- ✅ Agentic recommendation service works reliably without crashes
- ✅ APAT pattern creation and saving functions properly
- ✅ Enhanced collaboration through session ID sharing
- ✅ Improved system stability and user experience across all features

### Best Practices Applied
- Session continuity for long-running processes with robust validation
- Intelligent content extraction with multiple fallback strategies
- Dynamic, context-specific naming instead of hardcoded values
- Systematic bug fixing with comprehensive testing
- Enhanced user experience through improved error handling and guidance

## [2.5.0] - 2025-08-23 - Dynamic Schema System

### Added
- **Dynamic Schema System**: Configurable validation enums for extensible pattern validation
  - Configurable schema enums in `app/pattern/schema_config.json`
  - Dynamic schema generation with user-defined enum values
  - Flexible validation modes (strict vs flexible) with auto-extension capabilities
  - CLI management tool (`manage_schema.py`) for enum operations
  - Streamlit UI for visual enum management in "Schema Management" tab
  - Export/import capabilities for team collaboration
- **Extended Validation Enums**:
  - 12+ reasoning types (logical, causal, collaborative, creative, ethical, quantum_reasoning, etc.)
  - 9+ monitoring capabilities (performance_tracking, response_time_monitoring, security_monitoring, etc.)
  - 8+ learning mechanisms (reinforcement_learning, transfer_learning, meta_learning, etc.)
- **Management Interfaces**:
  - CLI tool with list, add, remove, validate, export/import commands
  - Web UI with filtering, search, and real-time validation
  - Configuration sharing between environments and teams

### Changed
- Pattern validation system now uses dynamic schema instead of hard-coded enums
- APAT pattern validation automatically detects and uses configurable schema
- Schema configuration supports per-enum extensibility flags
- Enhanced pattern loader with automatic schema detection

### Fixed
- **APAT-005 validation errors** completely resolved with configurable enums
- Hard-coded validation limitations preventing system extensibility
- Missing support for domain-specific reasoning types and monitoring capabilities
- Inability to extend learning mechanisms for new AI approaches
- Agent architecture restrictions to predefined patterns

### Technical Details
- **`app/pattern/schema_config.json`**: Centralized enum configuration with extensibility controls
- **`app/pattern/dynamic_schema_loader.py`**: Smart schema generation and validation system
- **`manage_schema.py`**: Comprehensive CLI tool for schema management
- **`app/ui/schema_management.py`**: Professional Streamlit interface for enum management
- **Enhanced Pattern Loader**: Automatic detection and use of dynamic schema for APAT patterns
- **Backward Compatibility**: Seamless integration with existing patterns and validation systems

### Migration Notes
- Existing patterns continue to work without changes
- New APAT patterns automatically benefit from extended validation options
- Teams can share schema configurations via export/import functionality
- System gracefully handles missing or invalid schema configurations

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
- **Mermaid diagram rendering issues** with version 10.2.4 compatibility
  - Unicode/emoji character conflicts causing syntax errors
  - Height parameter inconsistency in streamlit-mermaid library
  - Agent name sanitization for Mermaid node compatibility
  - Enhanced error handling with fallback to mermaid.live
- **Missing enterprise constraints** functionality for technology restrictions

### Technical Details
- Added `_is_conceptually_similar()` method with 70% similarity threshold
- Added `_enhance_existing_pattern()` method for intelligent pattern merging
- Added `categorize_tech_stack_with_descriptions()` method in TechStackGenerator
- Added `_render_formatted_text()` helper for better text display
- Enhanced RecommendationService with async pattern creation decision logic
- **Added `build_tech_stack_wiring_diagram()`** for technical architecture visualization
- **Enhanced Mermaid diagram generation**:
  - Improved `_sanitize()` function for Unicode character handling
  - Enhanced `_clean_mermaid_code()` with emoji-to-text replacement mapping
  - Added height parameter compatibility for streamlit-mermaid library versions
  - Robust error handling in `render_mermaid()` with user-friendly fallbacks
  - Updated agent architecture generation methods for safer syntax
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