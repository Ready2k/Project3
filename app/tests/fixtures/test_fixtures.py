"""Comprehensive test fixtures for patterns, requirements, and responses."""

import pytest
import json
from typing import Dict, List, Any

from app.pattern.matcher import MatchResult
from app.state.store import SessionState, QAExchange, PatternMatch, Recommendation
from app.qa.question_loop import Question, QAResult


class TestDataFixtures:
    """Comprehensive test data fixtures."""
    
    @pytest.fixture
    def sample_patterns(self) -> List[Dict[str, Any]]:
        """Sample pattern data for testing."""
        return [
            {
                "pattern_id": "PAT-001",
                "name": "Data Processing Automation",
                "description": "Automate data processing workflows with Python and Pandas",
                "feasibility": "Automatable",
                "confidence_score": 0.9,
                "domain": "data_processing",
                "pattern_type": "workflow",
                "tech_stack": ["Python", "Pandas", "NumPy"],
                "tags": ["data", "processing", "automation", "etl"],
                "complexity": "medium",
                "estimated_effort": "2-4 weeks",
                "prerequisites": ["Python knowledge", "Data understanding"],
                "limitations": ["Large datasets may require optimization"],
                "examples": [
                    "CSV file processing",
                    "Data validation and cleaning",
                    "Report generation"
                ]
            },
            {
                "pattern_id": "PAT-002",
                "name": "API Integration Automation",
                "description": "Automate API integrations and data synchronization",
                "feasibility": "Partially Automatable",
                "confidence_score": 0.75,
                "domain": "api_integration",
                "pattern_type": "integration",
                "tech_stack": ["Python", "Requests", "FastAPI"],
                "tags": ["api", "integration", "sync", "rest"],
                "complexity": "high",
                "estimated_effort": "4-8 weeks",
                "prerequisites": ["API documentation", "Authentication setup"],
                "limitations": ["Rate limiting", "API changes"],
                "examples": [
                    "CRM synchronization",
                    "Payment processing",
                    "Third-party data feeds"
                ]
            },
            {
                "pattern_id": "PAT-003",
                "name": "Report Generation",
                "description": "Automated report generation from various data sources",
                "feasibility": "Automatable",
                "confidence_score": 0.85,
                "domain": "reporting",
                "pattern_type": "workflow",
                "tech_stack": ["Python", "Matplotlib", "Jinja2"],
                "tags": ["reporting", "visualization", "automation"],
                "complexity": "low",
                "estimated_effort": "1-2 weeks",
                "prerequisites": ["Data access", "Report templates"],
                "limitations": ["Complex visualizations may need manual design"],
                "examples": [
                    "Daily sales reports",
                    "Performance dashboards",
                    "Compliance reports"
                ]
            },
            {
                "pattern_id": "PAT-004",
                "name": "Database Migration",
                "description": "Automated database schema and data migration",
                "feasibility": "Partially Automatable",
                "confidence_score": 0.6,
                "domain": "database",
                "pattern_type": "migration",
                "tech_stack": ["Python", "SQLAlchemy", "Alembic"],
                "tags": ["database", "migration", "schema", "data"],
                "complexity": "high",
                "estimated_effort": "6-12 weeks",
                "prerequisites": ["Database expertise", "Backup procedures"],
                "limitations": ["Complex transformations need manual review"],
                "examples": [
                    "Legacy system migration",
                    "Cloud database migration",
                    "Schema versioning"
                ]
            },
            {
                "pattern_id": "PAT-005",
                "name": "Email Automation",
                "description": "Automated email processing and response",
                "feasibility": "Not Automatable",
                "confidence_score": 0.3,
                "domain": "communication",
                "pattern_type": "workflow",
                "tech_stack": [],
                "tags": ["email", "communication", "manual"],
                "complexity": "high",
                "estimated_effort": "Not recommended",
                "prerequisites": ["Human judgment required"],
                "limitations": ["Requires human understanding and empathy"],
                "examples": [
                    "Customer support emails",
                    "Complex negotiations",
                    "Sensitive communications"
                ]
            }
        ]
    
    @pytest.fixture
    def sample_requirements(self) -> List[Dict[str, Any]]:
        """Sample requirements for testing."""
        return [
            {
                "description": "Automate daily processing of customer data from CSV files",
                "domain": "data_processing",
                "frequency": "daily",
                "data_sensitivity": "medium",
                "volume": {"daily": 10000, "peak": 50000},
                "integrations": ["database", "email"],
                "human_review": "optional",
                "sla": {"response_time_ms": 30000},
                "compliance": ["GDPR"],
                "workflow_steps": ["download", "validate", "process", "store", "notify"],
                "criticality": "high",
                "existing_tools": ["Excel", "manual scripts"],
                "budget": "medium",
                "timeline": "3 months"
            },
            {
                "description": "Integrate with external payment API for order processing",
                "domain": "api_integration",
                "frequency": "real-time",
                "data_sensitivity": "high",
                "volume": {"daily": 5000, "peak": 20000},
                "integrations": ["payment_gateway", "database", "notification_service"],
                "human_review": "required",
                "sla": {"response_time_ms": 2000},
                "compliance": ["PCI-DSS", "GDPR"],
                "workflow_steps": ["validate", "authorize", "process", "confirm", "log"],
                "criticality": "critical",
                "existing_tools": ["manual processing"],
                "budget": "high",
                "timeline": "6 months"
            },
            {
                "description": "Generate weekly sales reports automatically",
                "domain": "reporting",
                "frequency": "weekly",
                "data_sensitivity": "low",
                "volume": {"weekly": 1, "monthly": 4},
                "integrations": ["sales_database", "email"],
                "human_review": "none",
                "sla": {"response_time_ms": 300000},
                "compliance": [],
                "workflow_steps": ["extract", "analyze", "format", "distribute"],
                "criticality": "medium",
                "existing_tools": ["manual Excel reports"],
                "budget": "low",
                "timeline": "1 month"
            },
            {
                "description": "Migrate legacy customer database to cloud",
                "domain": "database",
                "frequency": "one-time",
                "data_sensitivity": "high",
                "volume": {"total_records": 1000000},
                "integrations": ["legacy_db", "cloud_db", "backup_system"],
                "human_review": "required",
                "sla": {"downtime_hours": 4},
                "compliance": ["GDPR", "HIPAA"],
                "workflow_steps": ["backup", "transform", "migrate", "validate", "cutover"],
                "criticality": "critical",
                "existing_tools": ["legacy system"],
                "budget": "high",
                "timeline": "12 months"
            },
            {
                "description": "Handle customer support emails automatically",
                "domain": "communication",
                "frequency": "continuous",
                "data_sensitivity": "medium",
                "volume": {"daily": 500, "peak": 2000},
                "integrations": ["email_server", "crm", "knowledge_base"],
                "human_review": "required",
                "sla": {"response_time_ms": 3600000},
                "compliance": ["GDPR"],
                "workflow_steps": ["receive", "classify", "route", "respond", "escalate"],
                "criticality": "high",
                "existing_tools": ["manual email handling"],
                "budget": "medium",
                "timeline": "6 months"
            }
        ]
    
    @pytest.fixture
    def sample_match_results(self) -> List[MatchResult]:
        """Sample pattern match results."""
        return [
            MatchResult(
                pattern_id="PAT-001",
                pattern_name="Data Processing Automation",
                feasibility="Automatable",
                tech_stack=["Python", "Pandas", "NumPy"],
                confidence=0.92,
                tag_score=0.9,
                vector_score=0.94,
                blended_score=0.92,
                rationale="High match for data processing automation with CSV files"
            ),
            MatchResult(
                pattern_id="PAT-003",
                pattern_name="Report Generation",
                feasibility="Automatable",
                tech_stack=["Python", "Matplotlib", "Jinja2"],
                confidence=0.78,
                tag_score=0.7,
                vector_score=0.86,
                blended_score=0.78,
                rationale="Good match for automated reporting requirements"
            ),
            MatchResult(
                pattern_id="PAT-002",
                pattern_name="API Integration Automation",
                feasibility="Partially Automatable",
                tech_stack=["Python", "Requests", "FastAPI"],
                confidence=0.65,
                tag_score=0.6,
                vector_score=0.7,
                blended_score=0.65,
                rationale="Partial match - some integration aspects apply"
            )
        ]
    
    @pytest.fixture
    def sample_questions(self) -> List[Question]:
        """Sample Q&A questions."""
        return [
            Question(
                text="What is the typical volume of data processed daily?",
                field="data_volume",
                template_category="volume_assessment",
                question_type="text"
            ),
            Question(
                text="How sensitive is the data being processed?",
                field="data_sensitivity",
                template_category="security_assessment",
                question_type="select",
                options=["low", "medium", "high", "critical"]
            ),
            Question(
                text="What is the required processing frequency?",
                field="frequency",
                template_category="workflow_variability",
                question_type="select",
                options=["real-time", "hourly", "daily", "weekly", "monthly", "on-demand"]
            ),
            Question(
                text="Are there any compliance requirements?",
                field="compliance",
                template_category="compliance_assessment",
                question_type="multiselect",
                options=["GDPR", "HIPAA", "PCI-DSS", "SOX", "None"]
            ),
            Question(
                text="What systems need to be integrated?",
                field="integrations",
                template_category="integration_assessment",
                question_type="text"
            )
        ]
    
    @pytest.fixture
    def sample_qa_result(self, sample_questions) -> QAResult:
        """Sample Q&A result."""
        return QAResult(
            complete=False,
            confidence=0.7,
            next_questions=sample_questions[:3]  # First 3 questions
        )
    
    @pytest.fixture
    def sample_session_state(self, sample_requirements) -> SessionState:
        """Sample session state."""
        session = SessionState(
            session_id="test-session-123",
            requirements=sample_requirements[0]
        )
        
        # Add some Q&A exchanges
        session.qa_exchanges = [
            QAExchange(
                question="What is the data volume?",
                answer="Approximately 10,000 records daily"
            ),
            QAExchange(
                question="How sensitive is the data?",
                answer="Medium sensitivity - customer data but not financial"
            )
        ]
        
        # Add pattern matches
        session.pattern_matches = [
            PatternMatch(
                pattern_id="PAT-001",
                score=0.92,
                accepted=True
            ),
            PatternMatch(
                pattern_id="PAT-003",
                score=0.78,
                accepted=True
            )
        ]
        
        # Add recommendations
        session.recommendations = [
            Recommendation(
                pattern_id="PAT-001",
                feasibility="Automatable",
                confidence=0.92,
                reasoning="Excellent match for data processing automation"
            )
        ]
        
        return session
    
    @pytest.fixture
    def sample_responses(self) -> Dict[str, str]:
        """Sample LLM responses for different scenarios."""
        return {
            "data_processing_questions": """Based on your data processing automation requirements, I need to understand a few key aspects:

1. **Data Volume**: What is the typical daily volume of data you process?
2. **Data Sources**: What are the primary data sources (CSV files, databases, APIs)?
3. **Processing Complexity**: What transformations or validations are required?
4. **Output Format**: What format should the processed data be in?
5. **Error Handling**: How should errors and exceptions be handled?

These details will help determine the best automation approach.""",
            
            "api_integration_questions": """For API integration automation, I need to clarify:

1. **API Type**: What type of API are you integrating with (REST, GraphQL, SOAP)?
2. **Authentication**: What authentication method is required?
3. **Rate Limits**: Are there any rate limiting considerations?
4. **Data Format**: What data formats are exchanged (JSON, XML, etc.)?
5. **Error Recovery**: How should API failures be handled?

This information will guide the integration strategy.""",
            
            "reporting_questions": """For automated reporting, please provide:

1. **Report Frequency**: How often should reports be generated?
2. **Data Sources**: What data sources feed into the reports?
3. **Report Format**: What format should the reports be in (PDF, Excel, HTML)?
4. **Distribution**: How should reports be distributed?
5. **Customization**: Are there different report variants needed?

These details will shape the reporting automation solution.""",
            
            "feasibility_analysis": """Based on the requirements analysis, here's the feasibility assessment:

**Automatable Aspects:**
- Data extraction and processing
- Standard transformations
- Report generation
- Basic error handling

**Partially Automatable:**
- Complex business logic validation
- Exception handling requiring judgment
- Integration with legacy systems

**Manual Oversight Required:**
- Quality assurance
- Exception resolution
- System monitoring

**Recommendation:** Proceed with automation for core processes while maintaining human oversight for exceptions.""",
            
            "technical_recommendations": """Technical Implementation Recommendations:

**Architecture:**
- Microservices-based approach for scalability
- Event-driven processing for real-time requirements
- Containerized deployment for portability

**Technology Stack:**
- Python for data processing and automation
- FastAPI for API development
- PostgreSQL for data storage
- Redis for caching and queuing
- Docker for containerization

**Implementation Phases:**
1. Core data processing automation
2. API integration layer
3. Reporting and monitoring
4. Error handling and recovery

**Estimated Timeline:** 3-4 months for full implementation"""
        }
    
    @pytest.fixture
    def pattern_files_directory(self, sample_patterns, tmp_path):
        """Create temporary directory with pattern files."""
        patterns_dir = tmp_path / "patterns"
        patterns_dir.mkdir()
        
        for pattern in sample_patterns:
            pattern_file = patterns_dir / f"{pattern['pattern_id']}.json"
            with open(pattern_file, 'w') as f:
                json.dump(pattern, f, indent=2)
        
        return patterns_dir
    
    @pytest.fixture
    def question_templates_directory(self, tmp_path):
        """Create temporary directory with question templates."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        templates = {
            "data_processing_questions": {
                "domain": "data_processing",
                "category": "volume_assessment",
                "questions": [
                    {
                        "text": "What is the typical daily volume of data?",
                        "field": "data_volume",
                        "type": "text",
                        "required": True
                    },
                    {
                        "text": "What is the data sensitivity level?",
                        "field": "data_sensitivity",
                        "type": "select",
                        "options": ["low", "medium", "high"],
                        "required": True
                    }
                ]
            },
            "api_integration_questions": {
                "domain": "api_integration",
                "category": "integration_assessment",
                "questions": [
                    {
                        "text": "What type of API are you integrating with?",
                        "field": "api_type",
                        "type": "select",
                        "options": ["REST", "GraphQL", "SOAP", "Other"],
                        "required": True
                    },
                    {
                        "text": "What authentication method is required?",
                        "field": "auth_method",
                        "type": "select",
                        "options": ["API Key", "OAuth", "Basic Auth", "JWT"],
                        "required": True
                    }
                ]
            },
            "reporting_questions": {
                "domain": "reporting",
                "category": "output_assessment",
                "questions": [
                    {
                        "text": "What format should the reports be in?",
                        "field": "report_format",
                        "type": "multiselect",
                        "options": ["PDF", "Excel", "HTML", "CSV"],
                        "required": True
                    },
                    {
                        "text": "How should reports be distributed?",
                        "field": "distribution_method",
                        "type": "select",
                        "options": ["Email", "File Share", "API", "Dashboard"],
                        "required": True
                    }
                ]
            }
        }
        
        templates_file = templates_dir / "templates.json"
        with open(templates_file, 'w') as f:
            json.dump(templates, f, indent=2)
        
        return templates_dir
    
    @pytest.fixture
    def export_directory(self, tmp_path):
        """Create temporary directory for exports."""
        export_dir = tmp_path / "exports"
        export_dir.mkdir()
        return export_dir
    
    @pytest.fixture
    def cache_directory(self, tmp_path):
        """Create temporary directory for caching."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        return cache_dir


class MockDataGenerators:
    """Generators for creating mock test data."""
    
    @staticmethod
    def generate_pattern(pattern_id: str, **overrides) -> Dict[str, Any]:
        """Generate a pattern with optional overrides."""
        base_pattern = {
            "pattern_id": pattern_id,
            "name": f"Test Pattern {pattern_id}",
            "description": f"Test pattern for {pattern_id}",
            "feasibility": "Automatable",
            "confidence_score": 0.8,
            "domain": "test_domain",
            "pattern_type": "workflow",
            "tech_stack": ["Python"],
            "tags": ["test", "automation"],
            "complexity": "medium",
            "estimated_effort": "2-4 weeks"
        }
        base_pattern.update(overrides)
        return base_pattern
    
    @staticmethod
    def generate_requirements(**overrides) -> Dict[str, Any]:
        """Generate requirements with optional overrides."""
        base_requirements = {
            "description": "Test automation requirements",
            "domain": "test_domain",
            "frequency": "daily",
            "data_sensitivity": "medium",
            "volume": {"daily": 1000},
            "integrations": ["test_system"],
            "human_review": "optional",
            "criticality": "medium"
        }
        base_requirements.update(overrides)
        return base_requirements
    
    @staticmethod
    def generate_match_result(pattern_id: str, **overrides) -> MatchResult:
        """Generate a match result with optional overrides."""
        defaults = {
            "pattern_id": pattern_id,
            "pattern_name": f"Test Pattern {pattern_id}",
            "feasibility": "Automatable",
            "tech_stack": ["Python"],
            "confidence": 0.8,
            "tag_score": 0.75,
            "vector_score": 0.85,
            "blended_score": 0.8,
            "rationale": f"Test match for {pattern_id}"
        }
        defaults.update(overrides)
        return MatchResult(**defaults)
    
    @staticmethod
    def generate_session_state(session_id: str, **overrides) -> SessionState:
        """Generate session state with optional overrides."""
        requirements = MockDataGenerators.generate_requirements()
        requirements.update(overrides.pop("requirements", {}))
        
        session = SessionState(session_id=session_id, requirements=requirements)
        
        # Apply any other overrides
        for key, value in overrides.items():
            setattr(session, key, value)
        
        return session


class TestScenarios:
    """Pre-defined test scenarios for common use cases."""
    
    @pytest.fixture
    def data_processing_scenario(self):
        """Complete data processing automation scenario."""
        return {
            "requirements": {
                "description": "Automate daily customer data processing from CSV files",
                "domain": "data_processing",
                "frequency": "daily",
                "data_sensitivity": "medium",
                "volume": {"daily": 10000},
                "integrations": ["database", "email"],
                "workflow_steps": ["download", "validate", "process", "store", "notify"]
            },
            "expected_patterns": ["PAT-001", "PAT-003"],
            "expected_feasibility": "Automatable",
            "expected_confidence_range": (0.8, 1.0),
            "expected_tech_stack": ["Python", "Pandas"],
            "expected_questions": [
                "What is the data volume?",
                "How sensitive is the data?",
                "What validation rules are required?"
            ]
        }
    
    @pytest.fixture
    def api_integration_scenario(self):
        """Complete API integration scenario."""
        return {
            "requirements": {
                "description": "Integrate with payment gateway API for order processing",
                "domain": "api_integration",
                "frequency": "real-time",
                "data_sensitivity": "high",
                "volume": {"daily": 5000},
                "integrations": ["payment_gateway", "database"],
                "compliance": ["PCI-DSS"]
            },
            "expected_patterns": ["PAT-002"],
            "expected_feasibility": "Partially Automatable",
            "expected_confidence_range": (0.6, 0.8),
            "expected_tech_stack": ["Python", "Requests", "FastAPI"],
            "expected_questions": [
                "What type of API?",
                "What authentication method?",
                "What are the rate limits?"
            ]
        }
    
    @pytest.fixture
    def complex_migration_scenario(self):
        """Complex database migration scenario."""
        return {
            "requirements": {
                "description": "Migrate legacy customer database to modern cloud platform",
                "domain": "database",
                "frequency": "one-time",
                "data_sensitivity": "high",
                "volume": {"total_records": 1000000},
                "integrations": ["legacy_db", "cloud_db", "backup_system"],
                "compliance": ["GDPR", "HIPAA"],
                "criticality": "critical"
            },
            "expected_patterns": ["PAT-004"],
            "expected_feasibility": "Partially Automatable",
            "expected_confidence_range": (0.5, 0.7),
            "expected_tech_stack": ["Python", "SQLAlchemy", "Alembic"],
            "expected_questions": [
                "What is the legacy database type?",
                "What transformations are needed?",
                "What is the acceptable downtime?"
            ]
        }
    
    @pytest.fixture
    def not_automatable_scenario(self):
        """Scenario that should not be automated."""
        return {
            "requirements": {
                "description": "Handle sensitive customer complaints and negotiations",
                "domain": "communication",
                "frequency": "continuous",
                "data_sensitivity": "high",
                "human_review": "required",
                "criticality": "critical"
            },
            "expected_patterns": ["PAT-005"],
            "expected_feasibility": "Not Automatable",
            "expected_confidence_range": (0.0, 0.4),
            "expected_tech_stack": [],
            "expected_questions": [
                "What type of communications?",
                "What human judgment is required?",
                "What are the risks of automation?"
            ]
        }