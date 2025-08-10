# Product Overview

Automated AI Assessment (AAA) is an interactive GUI + API system that judges if user stories/requirements are automatable with agentic AI. The system asks clarifying questions, matches requirements to reusable solution patterns, and exports results with feasibility assessments.

## Core Features

- **Multi-Provider LLM Support**: OpenAI, Anthropic/Bedrock, Claude Direct, Internal HTTP
- **Intelligent Pattern Matching**: Tag filtering + vector similarity with FAISS
- **Interactive Q&A System**: Clarifying questions to gather missing requirements
- **Feasibility Assessment**: Automatable, Partially Automatable, or Not Automatable
- **Export Results**: JSON and Markdown formats
- **Constraint-Aware**: Filters banned tools and applies business constraints

## Architecture Components

- **FastAPI Backend**: REST API with async endpoints
- **Streamlit Frontend**: Interactive web interface
- **Pattern Library**: JSON-based reusable solution patterns
- **FAISS Index**: Vector similarity search for pattern matching
- **Q&A System**: Template-based question generation
- **State Management**: Session persistence with diskcache/Redis
- **Export System**: JSON and Markdown result export
- **Audit System**: Comprehensive logging and observability

## Request Flow

1. **Ingest** → Create session, parse requirements
2. **Q&A Loop** → Collect missing information
3. **Pattern Matching** → Tag filtering + vector similarity
4. **Recommendations** → Generate feasibility assessment
5. **Export** → Download results in preferred format