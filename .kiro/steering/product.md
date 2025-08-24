# Product Overview

Automated AI Assessment (AAA) is an interactive GUI + API system that evaluates user stories/requirements for **autonomous agentic AI** implementation. The system uses advanced AI reasoning to assess autonomy potential, matches requirements to specialized agentic solution patterns, and provides comprehensive feasibility assessments with detailed implementation guidance. Features enterprise-grade security with advanced prompt defense capabilities and sophisticated multi-agent system design.

## Core Features

### Agentic AI Transformation
- **Autonomous Agent Assessment**: Advanced AI reasoning to evaluate autonomy potential with 90%+ accuracy scores
- **Agentic Pattern Library**: Specialized APAT-* patterns for autonomous agent solutions (95-98% autonomy levels)
- **Multi-Agent System Design**: Hierarchical, collaborative, and swarm intelligence architectures
- **Exception Handling Through Reasoning**: AI agents resolve problems autonomously rather than escalating
- **Comprehensive Autonomy Analysis**: Reasoning complexity, decision boundaries, and workflow automation assessment
- **Agentic Technology Catalog**: 12+ specialized frameworks (LangChain, AutoGen, CrewAI, Microsoft Semantic Kernel)

### Enhanced Analysis & Assessment
- **Multi-Provider LLM Support**: OpenAI, Anthropic/Bedrock, Claude Direct, Internal HTTP with security validation
- **Intelligent Pattern Matching**: Tag filtering + vector similarity with FAISS, prioritizing autonomous solutions
- **Interactive Q&A System**: LLM-generated clarifying questions with robust caching and security validation
- **Advanced Feasibility Assessment**: Detailed insights, challenges, recommended approach, and next steps with confidence scoring
- **AI-Generated Architecture Diagrams**: Context, Container, Sequence, and Tech Stack Wiring diagrams with enhanced viewing
- **LLM-Driven Tech Stack Generation**: Intelligent technology recommendations from 55+ catalog technologies

### Management & Analytics
- **Session Management**: Complete session continuity with resume functionality and cross-session compatibility
- **Technology Catalog Management**: Complete CRUD interface for managing technology database
- **Pattern Analytics**: Real-time analytics showing pattern match frequency, acceptance rates, and quality scores
- **Advanced Security System**: Multi-layered prompt defense with 8 specialized detectors
- **Professional Debug Controls**: Hidden debug information with optional sidebar toggles for development
- **Export Results**: JSON, Markdown, and interactive HTML formats
- **Constraint-Aware**: Filters banned tools and applies business constraints with security validation

## Security Features

- **Advanced Prompt Defense**: Multi-layered security system protecting against various attack vectors
- **Real-time Attack Detection**: 8 specialized detectors for comprehensive threat coverage
- **Multilingual Security**: Attack detection in 6 languages (EN, ES, FR, DE, ZH, JA)
- **Data Protection**: Prevents extraction of system prompts and sensitive environment variables
- **Business Logic Protection**: Safeguards configuration access and safety settings
- **User Education**: Contextual guidance for security violations with educational messaging
- **Performance Optimized**: Sub-100ms security validation with intelligent caching
- **Deployment Safety**: Gradual rollout with automatic rollback capabilities

## Architecture Components

- **FastAPI Backend**: REST API with async endpoints, robust caching, and security middleware
- **Streamlit Frontend**: Interactive web interface with enhanced diagram viewing and professional debug controls
- **Pattern Library**: JSON-based reusable solution patterns with CRUD management
- **Technology Catalog**: Centralized database of 55+ technologies with rich metadata
- **FAISS Index**: Vector similarity search for pattern matching
- **Q&A System**: LLM-powered question generation with duplicate prevention and security validation
- **Advanced Security System**: Multi-layered prompt defense with 8 specialized detectors
- **Security Monitoring**: Real-time attack detection and user education system
- **State Management**: Session persistence with diskcache/Redis and resume functionality
- **Export System**: JSON, Markdown, and interactive HTML export
- **Diagram System**: Mermaid-based architecture visualization with browser export
- **Audit System**: Comprehensive logging and observability with pattern match tracking and security events
- **Analytics Dashboard**: Pattern performance metrics with session filtering and time-based analysis
- **Deployment Management**: Gradual rollout system with automatic rollback capabilities

## Request Flow

1. **Ingest** → Create session, parse requirements (supports Jira integration and session resume)
2. **Q&A Loop** → LLM-generated clarifying questions with caching
3. **Pattern Matching** → Tag filtering + vector similarity
4. **Tech Stack Generation** → LLM-driven technology recommendations
5. **Architecture Analysis** → LLM-generated explanations and diagrams
6. **Recommendations** → Generate feasibility assessment
7. **Export** → Download results in JSON, Markdown, or interactive HTML