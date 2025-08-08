# Requirements Document

## Introduction

AgenticOrNot v1.3.2 is an interactive GUI + API system that judges if user stories/requirements are automatable with agentic AI. The system asks clarifying questions, matches requirements to reusable solution patterns, and exports results with feasibility assessments. It features pluggable LLM providers, vector matching capabilities, and constraint-aware recommendations while maintaining 100% test coverage and following TDD principles.

## Requirements

### Requirement 1

**User Story:** As a business analyst, I want to input requirements through multiple channels (text, file upload, Jira integration), so that I can assess automation feasibility regardless of how my requirements are stored.

#### Acceptance Criteria

1. WHEN a user submits text input THEN the system SHALL create a session_id and begin processing
2. WHEN a user uploads a file (txt/docx/json/csv) THEN the system SHALL parse the content and extract requirements
3. WHEN a user provides Jira credentials and ticket URL THEN the system SHALL fetch ticket data and map it to requirements format
4. WHEN any input is received THEN the system SHALL validate the input format and return appropriate error messages for invalid inputs

### Requirement 2

**User Story:** As a system user, I want real-time progress tracking through distinct processing phases, so that I understand what the system is doing and can monitor completion status.

#### Acceptance Criteria

1. WHEN processing begins THEN the system SHALL progress through phases: PARSING → VALIDATING → QNA → MATCHING → RECOMMENDING → DONE
2. WHEN in any phase THEN the system SHALL provide progress percentage (0-100) via GET /status/{session_id}
3. WHEN missing information is detected THEN the system SHALL identify missing_fields and transition to QNA phase
4. WHEN all required information is collected THEN the system SHALL automatically proceed to the next phase

### Requirement 3

**User Story:** As a user, I want an interactive Q&A system that asks clarifying questions when information is missing, so that the system can make accurate automation assessments.

#### Acceptance Criteria

1. WHEN the system detects missing fields THEN it SHALL generate targeted questions from qa/templates.json
2. WHEN a user provides answers via POST /qa/{session_id} THEN the system SHALL update the session state and determine if more questions are needed
3. WHEN the confidence threshold is met OR max_questions (default 5) is reached THEN the system SHALL proceed to matching phase
4. WHEN questions cover workflow variability, data sensitivity, human-in-the-loop, SLAs, integration endpoints, and volume/spike behavior THEN the system SHALL have comprehensive coverage

### Requirement 4

**User Story:** As a user, I want the system to match my requirements against a library of reusable solution patterns using both tag filtering and vector similarity, so that I get relevant automation recommendations.

#### Acceptance Criteria

1. WHEN requirements are processed THEN the system SHALL perform fast tag filtering based on domain and pattern metadata
2. WHEN tag filtering is complete THEN the system SHALL perform vector embedding similarity search using FAISS index
3. WHEN both scores are available THEN the system SHALL blend scores using configurable weights: w1*tag_score + w2*vector_score + w3*pattern_confidence
4. WHEN constraints are defined THEN the system SHALL filter out banned tools/patterns before ranking results

### Requirement 5

**User Story:** As a user, I want feasibility recommendations with confidence scores and technical stack suggestions, so that I can make informed decisions about automation implementation.

#### Acceptance Criteria

1. WHEN matching is complete THEN the system SHALL return feasibility assessment: "Yes|Partial|No"
2. WHEN recommendations are generated THEN each SHALL include pattern_id, confidence score (0-1), and rationale
3. WHEN tech stack is determined THEN the system SHALL provide specific technology recommendations
4. WHEN reasoning is provided THEN it SHALL explain the decision-making process in human-readable format

### Requirement 6

**User Story:** As a user, I want to export results in multiple formats (JSON, Markdown), so that I can integrate findings into my existing documentation and workflow tools.

#### Acceptance Criteria

1. WHEN export is requested THEN the system SHALL support both JSON and Markdown formats via POST /export
2. WHEN JSON export is generated THEN it SHALL validate against the defined pattern schema
3. WHEN Markdown export is generated THEN it SHALL be human-readable and properly formatted
4. WHEN export is complete THEN the system SHALL provide a download_url for file access

### Requirement 7

**User Story:** As a system administrator, I want pluggable LLM provider support with live switching capabilities, so that I can use different AI models based on cost, performance, or availability requirements.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL support OpenAI, Anthropic/Bedrock, Claude Direct, and Internal HTTP providers
2. WHEN a provider is selected THEN the system SHALL use the appropriate API client and authentication method
3. WHEN provider testing is requested THEN POST /providers/test SHALL validate connectivity and return success/failure status
4. WHEN provider switching occurs THEN the system SHALL maintain session state and continue processing with the new provider

### Requirement 8

**User Story:** As a security-conscious user, I want PII redaction and secure credential handling, so that sensitive information is protected throughout the system.

#### Acceptance Criteria

1. WHEN logging occurs THEN the system SHALL redact secrets and PII from all log entries
2. WHEN API keys are used THEN they SHALL never be persisted to disk or database
3. WHEN prompts are generated THEN PII SHALL be scrubbed before sending to LLM providers
4. WHEN audit trails are created THEN sensitive information SHALL be redacted while maintaining operational visibility

### Requirement 9

**User Story:** As a developer, I want comprehensive test coverage with deterministic fakes, so that the system is reliable and maintainable.

#### Acceptance Criteria

1. WHEN tests are run THEN the system SHALL achieve 100% statement AND branch coverage
2. WHEN LLM providers are tested THEN FakeLLM and FakeEmbedder SHALL provide deterministic, seeded responses
3. WHEN integration tests run THEN they SHALL use mocked external dependencies (httpx, databases)
4. WHEN e2e tests execute THEN they SHALL validate the complete Streamlit ↔ FastAPI flow

### Requirement 10

**User Story:** As a system operator, I want observability through metrics collection and audit trails, so that I can monitor system performance and usage patterns.

#### Acceptance Criteria

1. WHEN LLM calls are made THEN the system SHALL log provider, model, latency_ms, tokens, and created_at to SQLite
2. WHEN pattern matching occurs THEN the system SHALL record session_id, pattern_id, score, and accepted status
3. WHEN the Streamlit UI is accessed THEN it SHALL provide a charting tab for model comparison and performance metrics
4. WHEN audit data is stored THEN PII SHALL be redacted while maintaining operational insights