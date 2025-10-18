"""Unit tests for Jira service components."""

import pytest
from app.config import JiraConfig
from app.services.jira import JiraService, JiraTicket, JiraConnectionError


class TestJiraConfig:
    """Test Jira configuration."""

    def test_default_config(self):
        """Test default Jira configuration values."""
        config = JiraConfig()
        assert config.base_url is None
        assert config.email is None
        assert config.api_token is None
        assert config.timeout == 30

    def test_custom_config(self):
        """Test custom Jira configuration values."""
        config = JiraConfig(
            base_url="https://custom.atlassian.net",
            email="custom@example.com",
            api_token="custom_token",
            timeout=60,
        )
        assert config.base_url == "https://custom.atlassian.net"
        assert config.email == "custom@example.com"
        assert config.api_token == "custom_token"
        assert config.timeout == 60


class TestJiraTicket:
    """Test Jira ticket model."""

    def test_minimal_ticket(self):
        """Test creating ticket with minimal required fields."""
        ticket = JiraTicket(
            key="TEST-1", summary="Test ticket", status="Open", issue_type="Task"
        )
        assert ticket.key == "TEST-1"
        assert ticket.summary == "Test ticket"
        assert ticket.status == "Open"
        assert ticket.issue_type == "Task"
        assert ticket.description is None
        assert ticket.priority is None
        assert ticket.assignee is None
        assert ticket.reporter is None
        assert ticket.labels == []
        assert ticket.components == []

    def test_full_ticket(self):
        """Test creating ticket with all fields."""
        ticket = JiraTicket(
            key="PROJ-123",
            summary="Implement feature",
            description="Detailed description",
            priority="High",
            status="In Progress",
            issue_type="Story",
            assignee="John Doe",
            reporter="Jane Smith",
            labels=["backend", "api"],
            components=["Authentication", "API"],
            created="2024-01-15T10:30:00.000+0000",
            updated="2024-01-16T14:20:00.000+0000",
        )
        assert ticket.key == "PROJ-123"
        assert ticket.summary == "Implement feature"
        assert ticket.description == "Detailed description"
        assert ticket.priority == "High"
        assert ticket.status == "In Progress"
        assert ticket.issue_type == "Story"
        assert ticket.assignee == "John Doe"
        assert ticket.reporter == "Jane Smith"
        assert ticket.labels == ["backend", "api"]
        assert ticket.components == ["Authentication", "API"]
        assert ticket.created == "2024-01-15T10:30:00.000+0000"
        assert ticket.updated == "2024-01-16T14:20:00.000+0000"


class TestJiraServiceValidation:
    """Test Jira service validation methods."""

    def test_validate_config_missing_base_url(self):
        """Test validation with missing base URL."""
        config = JiraConfig(email="test@example.com", api_token="token")
        service = JiraService(config)

        with pytest.raises(JiraConnectionError, match="base URL is required"):
            service._validate_config()

    def test_validate_config_missing_email(self):
        """Test validation with missing email."""
        config = JiraConfig(base_url="https://test.atlassian.net", api_token="token")
        service = JiraService(config)

        with pytest.raises(
            JiraConnectionError, match="Email is required for API token authentication"
        ):
            service._validate_config()

    def test_validate_config_missing_api_token(self):
        """Test validation with missing API token."""
        config = JiraConfig(
            base_url="https://test.atlassian.net", email="test@example.com"
        )
        service = JiraService(config)

        with pytest.raises(JiraConnectionError, match="API token is required"):
            service._validate_config()

    def test_validate_config_success(self):
        """Test successful validation."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token",
        )
        service = JiraService(config)

        # Should not raise any exception
        service._validate_config()


class TestJiraServiceTextExtraction:
    """Test Jira service text extraction methods."""

    @pytest.fixture
    def jira_service(self):
        """Create Jira service for testing."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token",
        )
        return JiraService(config)

    def test_extract_text_from_simple_adf(self, jira_service):
        """Test extracting text from simple ADF content."""
        adf_content = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Simple paragraph text."}],
                }
            ],
        }

        text = jira_service._extract_text_from_adf(adf_content)
        assert "Simple paragraph text." in text

    def test_extract_text_from_complex_adf(self, jira_service):
        """Test extracting text from complex ADF content."""
        adf_content = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "First paragraph with "},
                        {"type": "text", "text": "multiple text nodes."},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Second paragraph."}],
                },
            ],
        }

        text = jira_service._extract_text_from_adf(adf_content)
        assert "First paragraph with" in text
        assert "multiple text nodes." in text
        assert "Second paragraph." in text

    def test_extract_text_from_empty_adf(self, jira_service):
        """Test extracting text from empty ADF content."""
        adf_content = {"type": "doc", "version": 1, "content": []}

        text = jira_service._extract_text_from_adf(adf_content)
        assert text == ""

    def test_extract_text_from_malformed_adf(self, jira_service):
        """Test extracting text from malformed ADF content."""
        adf_content = {"invalid": "structure"}

        # Should not raise exception, should return string representation
        text = jira_service._extract_text_from_adf(adf_content)
        assert isinstance(text, str)


class TestJiraServiceRequirementsMapping:
    """Test Jira service requirements mapping."""

    @pytest.fixture
    def jira_service(self):
        """Create Jira service for testing."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token",
        )
        return JiraService(config)

    def test_map_basic_ticket(self, jira_service):
        """Test mapping basic ticket to requirements."""
        ticket = JiraTicket(
            key="TEST-1", summary="Basic ticket", status="Open", issue_type="Task"
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert requirements["source"] == "jira"
        assert requirements["jira_key"] == "TEST-1"
        assert requirements["description"] == "Basic ticket"
        assert requirements["status"] == "Open"
        assert requirements["issue_type"] == "Task"
        assert requirements["priority"] is None
        assert requirements["assignee"] is None
        assert requirements["reporter"] is None
        assert requirements["labels"] == []
        assert requirements["components"] == []

    def test_map_ticket_with_description(self, jira_service):
        """Test mapping ticket with description."""
        ticket = JiraTicket(
            key="TEST-2",
            summary="Ticket with description",
            description="Detailed description here",
            status="Open",
            issue_type="Task",
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert (
            "Ticket with description - Detailed description here"
            in requirements["description"]
        )

    def test_map_ticket_domain_inference(self, jira_service):
        """Test domain inference from components and labels."""
        ticket = JiraTicket(
            key="TEST-3",
            summary="Backend API task",
            status="Open",
            issue_type="Task",
            components=["Backend", "API"],
            labels=["backend"],
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert requirements["domain"] == "backend"

    def test_map_ticket_pattern_type_inference(self, jira_service):
        """Test pattern type inference from issue type and description."""
        ticket = JiraTicket(
            key="TEST-4",
            summary="New feature development",
            description="Implement new API endpoint for user management",
            status="Open",
            issue_type="Story",
            components=["API"],
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert "feature_development" in requirements["pattern_types"]
        assert "api_development" in requirements["pattern_types"]

    def test_map_bug_ticket(self, jira_service):
        """Test mapping bug ticket."""
        ticket = JiraTicket(
            key="BUG-1",
            summary="Fix login issue",
            description="Users cannot login with special characters",
            status="Open",
            issue_type="Bug",
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert "bug_fix" in requirements["pattern_types"]

    def test_map_task_with_deployment_keywords(self, jira_service):
        """Test mapping task with deployment keywords."""
        ticket = JiraTicket(
            key="TASK-1",
            summary="Deploy application to production",
            description="Deploy the latest version to production environment",
            status="Open",
            issue_type="Task",
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert "deployment" in requirements["pattern_types"]

    def test_map_task_with_testing_keywords(self, jira_service):
        """Test mapping task with testing keywords."""
        ticket = JiraTicket(
            key="TASK-2",
            summary="QA testing for new feature",
            description="Perform quality assurance testing",
            status="Open",
            issue_type="Task",
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert "testing" in requirements["pattern_types"]

    def test_map_automation_ticket(self, jira_service):
        """Test mapping automation-related ticket."""
        ticket = JiraTicket(
            key="AUTO-1",
            summary="Automate deployment process",
            description="Create automation script for deployment",
            status="Open",
            issue_type="Task",
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert "automation" in requirements["pattern_types"]

    def test_map_database_ticket(self, jira_service):
        """Test mapping database-related ticket."""
        ticket = JiraTicket(
            key="DB-1",
            summary="Database migration",
            description="Migrate user table schema",
            status="Open",
            issue_type="Task",
        )

        requirements = jira_service.map_ticket_to_requirements(ticket)

        assert "data_processing" in requirements["pattern_types"]
