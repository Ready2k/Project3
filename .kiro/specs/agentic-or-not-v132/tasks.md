# Implementation Plan

- [x] 1. Set up project structure and configuration system
  - Create directory structure matching SPEC.md layout
  - Implement Pydantic settings with config.yaml and .env support
  - Add PII redaction utilities and logging configuration
  - Write unit tests for config loading, merging, and redaction
  - _Requirements: 8.1, 8.3_

- [x] 2. Implement LLM provider abstraction and concrete providers
  - Create base LLM and embedding provider interfaces
  - Implement OpenAI provider with httpx client and authentication
  - Implement Bedrock provider with boto3 integration
  - Implement Claude Direct and Internal HTTP providers
  - Create deterministic FakeLLM and FakeEmbedder for testing
  - Write unit tests for all providers with mocked httpx responses
  - _Requirements: 7.1, 7.2, 9.2_

- [x] 3. Create session state management and storage
  - Implement SessionStore interface with diskcache backend
  - Create SessionState dataclass with all required fields
  - Add Redis backend implementation as alternative
  - Write unit tests for state persistence and retrieval
  - _Requirements: 2.1, 2.2, 3.2_

- [x] 4. Build pattern library system with validation
  - Create pattern JSON schema validation
  - Implement PatternLoader for reading pattern files
  - Create sample patterns (3) covering diverse domains
  - Add pattern validation and error handling
  - Write unit tests for pattern loading and schema validation
  - _Requirements: 4.1, 6.2_

- [x] 5. Implement vector embeddings and FAISS integration
  - Create FAISS index wrapper for vector operations
  - Implement sentence-transformers embedding generation
  - Add index building and search functionality
  - Write integration tests for embedding and search flow
  - _Requirements: 4.2, 4.3_

- [x] 6. Create pattern matching engine with scoring
  - Implement tag-based filtering logic
  - Add vector similarity search integration
  - Create score blending algorithm with configurable weights
  - Implement constraint filtering for banned tools/patterns
  - Write unit tests for matching logic and score calculation
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7. Build AI-powered Q&A system with dynamic question generation
  - ✅ Create LLM-generated contextual questions based on specific requirements
  - ✅ Implement QuestionLoop class with AI question generation
  - ✅ Add intelligent missing field detection and confidence calculation
  - ✅ Create QAExchange and QAResult data models with proper serialization
  - ✅ Fix session state persistence for provider configuration
  - ✅ Add proper phase transitions from Q&A to matching
  - ✅ Write unit tests for question generation and answer processing
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 8. Implement recommendation engine
  - Create recommendation generation logic
  - Add feasibility assessment (Yes/Partial/No) determination
  - Implement confidence scoring and rationale generation
  - Add tech stack suggestion based on patterns
  - Write unit tests for recommendation logic
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 9. Create export system with format validation
  - Implement JSON exporter with schema validation
  - Create Markdown exporter with proper formatting
  - Add file generation and download URL creation
  - Write unit tests for export format validation
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Build Jira integration service
  - Implement Jira API client with authentication
  - Add ticket fetching and requirement mapping
  - Create error handling for Jira connectivity issues
  - Write integration tests with mocked Jira responses
  - _Requirements: 1.3_

- [x] 11. Implement audit and observability system
  - Create SQLite database schema for runs and matches tables
  - Implement audit logging for LLM calls and pattern matches
  - Add PII redaction for audit data
  - Write unit tests for audit data collection
  - _Requirements: 10.1, 10.2, 10.4_

- [x] 12. Create FastAPI application with all endpoints
  - Implement POST /ingest endpoint with session creation
  - Add GET /status/{session_id} with progress tracking
  - Create POST /qa/{session_id} for Q&A interactions
  - Implement POST /match and POST /recommend endpoints
  - Add POST /export with format selection
  - Create POST /providers/test for connectivity testing
  - Write integration tests for all API endpoints
  - _Requirements: 1.1, 1.2, 2.3, 3.2, 5.1, 6.4, 7.3_

- [x] 13. Build Streamlit UI with enhanced provider switching and diagrams
  - ✅ Create main UI with input methods (text, file, Jira)
  - ✅ Implement smart progress tracking with phase-aware polling
  - ✅ Add comprehensive provider selection (OpenAI, Bedrock, Claude, Internal, FakeLLM)
  - ✅ Create results display with feasibility and recommendations
  - ✅ Add export buttons for JSON and Markdown
  - ✅ Implement AI-generated Mermaid diagrams (Context, Container, Sequence)
  - ✅ Fix Q&A interaction with submit button and proper validation
  - ✅ Add real-time status updates and error handling
  - ✅ Write e2e tests for UI to API integration
  - _Requirements: 1.1, 1.2, 1.3, 2.3, 6.4, 7.3_

- [x] 14. Add observability dashboard to Streamlit
  - ✅ Create metrics charting tab for model comparison
  - ✅ Implement performance visualization from audit data
  - ✅ Add usage pattern analysis with provider tracking
  - ✅ Fix provider audit logging to show real providers instead of FakeLLM
  - ✅ Write tests for dashboard functionality
  - _Requirements: 10.3_

- [x] 18. Implement AI-generated architecture diagrams
  - ✅ Create LLM-powered diagram generation for Context, Container, and Sequence diagrams
  - ✅ Implement Mermaid code generation with proper C4 architecture patterns
  - ✅ Add contextual diagram prompts based on specific requirements and recommendations
  - ✅ Fix Mermaid syntax cleaning to remove markdown code blocks
  - ✅ Integrate diagram generation into Streamlit UI with on-demand generation
  - ✅ Add diagram code viewing and validation
  - _Requirements: Enhanced visualization and architecture documentation_

- [ ] 15. Create comprehensive test suite with 100% coverage
  - Ensure all unit tests achieve 100% statement and branch coverage
  - Add property-based tests using Hypothesis for edge cases
  - Create integration tests for complete workflows
  - Implement e2e tests for provider switching and exports
  - Add test fixtures for patterns, requirements, and responses
  - _Requirements: 9.1, 9.3, 9.4_

- [ ] 16. Package application with Docker and deployment
  - Create Dockerfile with multi-stage build
  - Implement docker-compose.yml with optional Redis
  - Add Makefile with fmt, lint, test, and up targets
  - Create requirements.txt with all dependencies
  - Add .env.example with sample configuration
  - Write deployment documentation
  - _Requirements: All requirements integrated_

- [ ] 17. Implement security measures and final validation
  - Add input validation and sanitization
  - Implement rate limiting and request size limits
  - Add CORS configuration and security headers
  - Validate that banned tools never appear in outputs
  - Perform final security review and PII redaction testing
  - _Requirements: 8.1, 8.2, 8.3, 8.4_