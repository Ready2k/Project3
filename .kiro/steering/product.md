# Product Overview

Automated AI Assessment (AAA) is an interactive GUI + API system that judges if user stories/requirements are automatable with agentic AI. The system asks clarifying questions, matches requirements to reusable solution patterns, and exports results with feasibility assessments.

## Core Features

- **Multi-Provider LLM Support**: OpenAI, Anthropic/Bedrock, Claude Direct, Internal HTTP
- **Intelligent Pattern Matching**: Tag filtering + vector similarity with FAISS
- **Interactive Q&A System**: LLM-generated clarifying questions with robust caching
- **Feasibility Assessment**: Automatable, Partially Automatable, or Not Automatable
- **AI-Generated Architecture Diagrams**: Context, Container, Sequence, and Tech Stack Wiring diagrams with enhanced viewing
- **LLM-Driven Tech Stack Generation**: Intelligent technology recommendations from 55+ catalog technologies
- **Technology Catalog Management**: Complete CRUD interface for managing technology database
- **Export Results**: JSON, Markdown, and interactive HTML formats
- **Constraint-Aware**: Filters banned tools and applies business constraints

## Architecture Components

- **FastAPI Backend**: REST API with async endpoints and robust caching
- **Streamlit Frontend**: Interactive web interface with enhanced diagram viewing
- **Pattern Library**: JSON-based reusable solution patterns with CRUD management
- **Technology Catalog**: Centralized database of 55+ technologies with rich metadata
- **FAISS Index**: Vector similarity search for pattern matching
- **Q&A System**: LLM-powered question generation with duplicate prevention
- **State Management**: Session persistence with diskcache/Redis
- **Export System**: JSON, Markdown, and interactive HTML export
- **Diagram System**: Mermaid-based architecture visualization with browser export
- **Audit System**: Comprehensive logging and observability

## Request Flow

1. **Ingest** → Create session, parse requirements (supports Jira integration)
2. **Q&A Loop** → LLM-generated clarifying questions with caching
3. **Pattern Matching** → Tag filtering + vector similarity
4. **Tech Stack Generation** → LLM-driven technology recommendations
5. **Architecture Analysis** → LLM-generated explanations and diagrams
6. **Recommendations** → Generate feasibility assessment
7. **Export** → Download results in JSON, Markdown, or interactive HTML