"""Tests to ensure banned tools never appear in system outputs."""

import pytest
from unittest.mock import Mock, patch
from app.security.validation import SecurityValidator
from app.api import validate_output_security


class TestBannedToolsValidation:
    """Test validation that banned tools never appear in outputs."""
    
    def setup_method(self):
        self.validator = SecurityValidator()
    
    def test_banned_tools_list_completeness(self):
        """Test that banned tools list includes expected security tools."""
        expected_banned_tools = [
            "metasploit", "burp suite", "sqlmap", "nmap", "masscan", "wireshark",
            "john the ripper", "hashcat", "aircrack", "hydra", "nikto",
            "owasp zap", "beef framework", "maltego", "shodan", "censys"
        ]
        
        for tool in expected_banned_tools:
            assert tool in self.validator.banned_tools
    
    def test_validate_no_banned_tools_clean_text(self):
        """Test validation passes for clean text without banned tools."""
        clean_texts = [
            "We recommend using Python and FastAPI for this automation project.",
            "The system should integrate with existing APIs using REST protocols.",
            "Consider implementing authentication using OAuth2 and JWT tokens.",
            "Use Docker for containerization and Kubernetes for orchestration.",
            "Monitor the system with Prometheus and Grafana dashboards."
        ]
        
        for text in clean_texts:
            assert self.validator.validate_no_banned_tools(text) is True
    
    def test_validate_no_banned_tools_with_banned_exact_match(self):
        """Test validation fails when banned tools appear exactly."""
        banned_texts = [
            "Use metasploit to test the security of the system.",
            "Run nmap to scan for open ports.",
            "Configure burp suite for web application testing.",
            "Use sqlmap to test for SQL injection vulnerabilities.",
            "Set up wireshark to monitor network traffic."
        ]
        
        for text in banned_texts:
            assert self.validator.validate_no_banned_tools(text) is False
    
    def test_validate_no_banned_tools_case_insensitive(self):
        """Test validation is case insensitive."""
        banned_texts = [
            "Use METASPLOIT for penetration testing.",
            "Run NMAP to discover services.",
            "Configure Burp Suite for testing.",
            "Use SqlMap for database testing.",
            "Set up WireShark for packet analysis."
        ]
        
        for text in banned_texts:
            assert self.validator.validate_no_banned_tools(text) is False
    
    def test_validate_no_banned_tools_partial_words(self):
        """Test that partial word matches don't trigger false positives."""
        # These should NOT be flagged as they're not exact tool names
        safe_texts = [
            "The network mapping functionality is important.",  # "map" in "mapping"
            "We need to hash the passwords securely.",  # "hash" in "hash"
            "The application should be air-gapped for security.",  # "air" in "air-gapped"
            "Use a beef server for the backend.",  # "beef" as food, not the tool (now "beef framework" is banned)
            "The system should be robust and secure."  # "robust" contains "bust"
        ]
        
        for text in safe_texts:
            assert self.validator.validate_no_banned_tools(text) is True
    
    def test_validate_no_banned_tools_multiple_banned(self):
        """Test validation fails when multiple banned tools appear."""
        text = "Use nmap for discovery and metasploit for exploitation testing."
        assert self.validator.validate_no_banned_tools(text) is False
    
    def test_validate_no_banned_tools_in_context(self):
        """Test validation fails even when banned tools appear in legitimate context."""
        # Even if mentioned in a security context, these should still be flagged
        banned_contexts = [
            "Avoid using tools like metasploit in production environments.",
            "Security scanners such as nmap should not be used on production systems.",
            "Unlike burp suite, our tool focuses on automation rather than security testing.",
            "This is different from sqlmap which is used for database testing."
        ]
        
        for text in banned_contexts:
            assert self.validator.validate_no_banned_tools(text) is False
    
    def test_validate_output_security_function(self):
        """Test the global validate_output_security function."""
        # Test with clean data
        clean_data = {
            "recommendations": [
                {
                    "pattern_id": "PAT-001",
                    "feasibility": "Automatable",
                    "tech_stack": ["Python", "FastAPI", "Docker"],
                    "reasoning": "This can be automated using standard web technologies."
                }
            ]
        }
        
        assert validate_output_security(clean_data) is True
        
        # Test with banned tool in data
        banned_data = {
            "recommendations": [
                {
                    "pattern_id": "PAT-002", 
                    "feasibility": "Partially Automatable",
                    "tech_stack": ["Python", "nmap", "Docker"],  # Contains banned tool
                    "reasoning": "Use nmap for network discovery."
                }
            ]
        }
        
        assert validate_output_security(banned_data) is False
    
    def test_validate_output_security_different_data_types(self):
        """Test output validation with different data types."""
        # Test with string
        clean_string = "Use Python and FastAPI for automation."
        assert validate_output_security(clean_string) is True
        
        banned_string = "Use metasploit for security testing."
        assert validate_output_security(banned_string) is False
        
        # Test with list
        clean_list = ["Python", "FastAPI", "Docker", "Kubernetes"]
        assert validate_output_security(clean_list) is True
        
        banned_list = ["Python", "nmap", "Docker"]
        assert validate_output_security(banned_list) is False
        
        # Test with complex nested structure
        complex_clean = {
            "feasibility": "Automatable",
            "recommendations": [
                {"tech": ["Python", "FastAPI"]},
                {"tech": ["Docker", "Redis"]}
            ],
            "reasoning": "Standard automation technologies"
        }
        assert validate_output_security(complex_clean) is True
        
        complex_banned = {
            "feasibility": "Partially Automatable", 
            "recommendations": [
                {"tech": ["Python", "FastAPI"]},
                {"tech": ["sqlmap", "Redis"]}  # Contains banned tool
            ],
            "reasoning": "Use sqlmap for testing"
        }
        assert validate_output_security(complex_banned) is False


@pytest.mark.asyncio
async def test_banned_tools_in_api_responses():
    """Test that API responses are validated for banned tools."""
    from app.api import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Mock the recommendation service to return banned tools
    with patch('app.api.get_recommendation_service') as mock_rec_service:
        mock_service = Mock()
        mock_recommendation = Mock()
        mock_recommendation.dict.return_value = {
            "pattern_id": "PAT-001",
            "feasibility": "Automatable",
            "tech_stack": ["Python", "nmap"],  # Contains banned tool
            "reasoning": "Use nmap for network discovery"
        }
        mock_recommendation.feasibility = "Automatable"
        mock_recommendation.tech_stack = ["Python", "nmap"]
        mock_recommendation.reasoning = "Use nmap for network discovery"
        
        mock_service.generate_recommendations.return_value = [mock_recommendation]
        mock_rec_service.return_value = mock_service
        
        # Create a session first
        ingest_response = client.post("/ingest", json={
            "source": "text",
            "payload": {"text": "Automate network monitoring system"}
        })
        session_id = ingest_response.json()["session_id"]
        
        # Try to get recommendations (should fail security validation)
        response = client.post("/recommend", json={
            "session_id": session_id,
            "top_k": 3
        })
        
        # Should return 500 due to security validation failure
        assert response.status_code == 500
        assert "security validation" in response.json()["message"].lower()


def test_banned_tools_comprehensive_list():
    """Test that the banned tools list covers major security/penetration testing tools."""
    validator = SecurityValidator()
    
    # Categories of tools that should be banned
    penetration_testing_tools = ["metasploit", "beef framework"]
    network_scanners = ["nmap", "masscan"]
    web_scanners = ["nikto", "owasp zap", "burp suite"]
    password_crackers = ["john the ripper", "hashcat", "hydra"]
    traffic_analyzers = ["wireshark"]
    vulnerability_scanners = ["sqlmap"]
    osint_tools = ["maltego", "shodan", "censys"]
    wireless_tools = ["aircrack"]
    
    all_expected_tools = (
        penetration_testing_tools + network_scanners + web_scanners + 
        password_crackers + traffic_analyzers + vulnerability_scanners + 
        osint_tools + wireless_tools
    )
    
    for tool in all_expected_tools:
        assert tool in validator.banned_tools, f"Expected banned tool '{tool}' not found in banned_tools list"
    
    # Test that each category is represented
    assert len(validator.banned_tools) >= len(all_expected_tools)


def test_legitimate_tools_not_banned():
    """Test that legitimate development and automation tools are not banned."""
    validator = SecurityValidator()
    
    legitimate_tools = [
        "python", "javascript", "java", "docker", "kubernetes", "jenkins",
        "ansible", "terraform", "prometheus", "grafana", "elasticsearch",
        "redis", "postgresql", "mysql", "mongodb", "fastapi", "django",
        "react", "vue", "angular", "nginx", "apache", "git", "github",
        "gitlab", "aws", "azure", "gcp", "oauth2", "jwt", "ssl", "tls"
    ]
    
    for tool in legitimate_tools:
        test_text = f"We recommend using {tool} for this automation project."
        assert validator.validate_no_banned_tools(test_text) is True, f"Legitimate tool '{tool}' was incorrectly flagged as banned"


@pytest.mark.parametrize("banned_tool", [
    "metasploit", "burp suite", "sqlmap", "nmap", "masscan", "wireshark",
    "john the ripper", "hashcat", "aircrack", "hydra", "nikto",
    "owasp zap", "beef framework", "maltego", "shodan", "censys"
])
def test_each_banned_tool_individually(banned_tool):
    """Test each banned tool individually to ensure detection works."""
    validator = SecurityValidator()
    
    test_sentences = [
        f"Use {banned_tool} for testing.",
        f"Configure {banned_tool} with these settings.",
        f"The {banned_tool} tool is recommended.",
        f"Install {banned_tool} on the system.",
        f"Run {banned_tool} to analyze the network."
    ]
    
    for sentence in test_sentences:
        assert validator.validate_no_banned_tools(sentence) is False, f"Failed to detect banned tool '{banned_tool}' in sentence: '{sentence}'"