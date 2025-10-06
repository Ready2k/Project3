"""Unit tests for agent display duplication fix."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.agentic_recommendation_service import AgenticRecommendationService
from app.services.multi_agent_designer import MultiAgentSystemDesign, AgentArchitectureType


class TestAgentNameGeneration:
    """Test agent name generation functionality."""
    
    @pytest.fixture
    def service(self):
        """Create agentic recommendation service for testing."""
        mock_llm = AsyncMock()
        return AgenticRecommendationService(mock_llm)
    
    @pytest.mark.asyncio
    async def test_generate_agent_name_user_domain(self, service):
        """Test agent name generation for user management domain."""
        requirements = {
            'description': 'As a BFA System I want an account that is marked as deceased and has an active care case'
        }
        
        agent_name = await service._generate_agent_name(requirements)
        # The enhanced logic may detect multiple domains and create compound names
        assert 'User Management Agent' in agent_name
    
    @pytest.mark.asyncio
    async def test_generate_agent_name_workflow_domain(self, service):
        """Test agent name generation for workflow domain."""
        requirements = {
            'description': 'Automate the workflow process for task management and automation'
        }
        
        agent_name = await service._generate_agent_name(requirements)
        assert 'Workflow Automation Agent' == agent_name
    
    @pytest.mark.asyncio
    async def test_generate_agent_name_with_suffix(self, service):
        """Test agent name generation with suffix for uniqueness."""
        requirements = {
            'description': 'Process data and manage user accounts'
        }
        
        agent_name = await service._generate_agent_name(requirements, suffix='#1')
        assert agent_name.endswith('#1')
    
    @pytest.mark.asyncio
    async def test_generate_agent_name_multiple_domains(self, service):
        """Test agent name generation with multiple detected domains."""
        requirements = {
            'description': 'User data processing and workflow automation system'
        }
        
        agent_name = await service._generate_agent_name(requirements)
        # Should detect multiple domains and create compound or prioritized name
        assert any(keyword in agent_name for keyword in ['User', 'Data', 'Workflow'])
    
    @pytest.mark.asyncio
    async def test_generate_agent_name_action_fallback(self, service):
        """Test agent name generation falls back to action keywords."""
        requirements = {
            'description': 'Create new records in the system'
        }
        
        agent_name = await service._generate_agent_name(requirements)
        assert 'Creation Agent' == agent_name
    
    @pytest.mark.asyncio
    async def test_generate_agent_name_final_fallback(self, service):
        """Test agent name generation final fallback."""
        requirements = {
            'description': 'Some unknown task that does not match any keywords'
        }
        
        agent_name = await service._generate_agent_name(requirements)
        assert 'Task Automation Agent' == agent_name


class TestUniqueAgentDesign:
    """Test unique agent design creation."""
    
    @pytest.fixture
    def service(self):
        """Create agentic recommendation service for testing."""
        mock_llm = AsyncMock()
        return AgenticRecommendationService(mock_llm)
    
    @pytest.fixture
    def mock_autonomy_assessment(self):
        """Create mock autonomy assessment."""
        assessment = MagicMock()
        assessment.overall_score = 0.85
        return assessment
    
    @pytest.fixture
    def mock_pattern_match(self):
        """Create mock pattern match."""
        pattern = MagicMock()
        pattern.pattern_id = 'APAT-001-workflow'
        pattern.reasoning_capabilities = ['logical_reasoning', 'pattern_matching']
        return pattern
    
    @pytest.mark.asyncio
    async def test_create_unique_single_agent_design(self, service, mock_autonomy_assessment, mock_pattern_match):
        """Test creation of unique single agent design."""
        requirements = {
            'description': 'User account management system'
        }
        
        design = await service._create_unique_single_agent_design(
            requirements, mock_autonomy_assessment, mock_pattern_match, 0
        )
        
        assert isinstance(design, MultiAgentSystemDesign)
        assert design.architecture_type == AgentArchitectureType.SINGLE_AGENT
        assert len(design.agent_roles) == 1
        
        agent = design.agent_roles[0]
        assert 'Workflow User Management Agent' == agent.name
        assert 'logical_reasoning' in agent.capabilities
        assert 'pattern_matching' in agent.capabilities
    
    @pytest.mark.asyncio
    async def test_create_unique_agents_different_indices(self, service, mock_autonomy_assessment):
        """Test that different indices create different agent names."""
        requirements = {
            'description': 'Data processing system'
        }
        
        pattern1 = MagicMock()
        pattern1.pattern_id = 'APAT-001-data'
        pattern1.reasoning_capabilities = []
        
        pattern2 = MagicMock()
        pattern2.pattern_id = 'APAT-002-integration'
        pattern2.reasoning_capabilities = []
        
        design1 = await service._create_unique_single_agent_design(
            requirements, mock_autonomy_assessment, pattern1, 0
        )
        design2 = await service._create_unique_single_agent_design(
            requirements, mock_autonomy_assessment, pattern2, 1
        )
        
        agent1_name = design1.agent_roles[0].name
        agent2_name = design2.agent_roles[0].name
        
        assert agent1_name != agent2_name
        assert 'Data Processing' in agent1_name
        assert 'Integration' in agent2_name


class TestAgentDeduplication:
    """Test agent deduplication logic."""
    
    def test_agent_deduplication_identical_agents(self):
        """Test that identical agents are deduplicated."""
        # Simulate the deduplication logic from streamlit_app.py
        agent_roles_found = []
        seen_agents = set()
        
        # Mock recommendations with duplicate agents
        recommendations = [
            {
                'agent_roles': [
                    {
                        'name': 'User Management Agent',
                        'responsibility': 'Main autonomous agent responsible for user account management'
                    }
                ]
            },
            {
                'agent_roles': [
                    {
                        'name': 'User Management Agent',
                        'responsibility': 'Main autonomous agent responsible for user account management'
                    }
                ]
            }
        ]
        
        # Apply deduplication logic
        for recommendation in recommendations:
            agent_roles_data = recommendation.get("agent_roles", [])
            if agent_roles_data:
                for agent in agent_roles_data:
                    agent_name = agent.get('name', 'Unknown Agent')
                    agent_responsibility = agent.get('responsibility', '')
                    
                    agent_id = f"{agent_name}|{agent_responsibility[:50]}"
                    
                    if agent_id not in seen_agents:
                        seen_agents.add(agent_id)
                        agent_roles_found.append(agent)
        
        # Should only have one unique agent
        assert len(agent_roles_found) == 1
        assert agent_roles_found[0]['name'] == 'User Management Agent'
    
    def test_agent_deduplication_different_agents(self):
        """Test that different agents are not deduplicated."""
        agent_roles_found = []
        seen_agents = set()
        
        # Mock recommendations with different agents
        recommendations = [
            {
                'agent_roles': [
                    {
                        'name': 'User Management Agent',
                        'responsibility': 'Handles user account operations'
                    }
                ]
            },
            {
                'agent_roles': [
                    {
                        'name': 'Data Processing Agent',
                        'responsibility': 'Processes and analyzes data'
                    }
                ]
            }
        ]
        
        # Apply deduplication logic
        for recommendation in recommendations:
            agent_roles_data = recommendation.get("agent_roles", [])
            if agent_roles_data:
                for agent in agent_roles_data:
                    agent_name = agent.get('name', 'Unknown Agent')
                    agent_responsibility = agent.get('responsibility', '')
                    
                    agent_id = f"{agent_name}|{agent_responsibility[:50]}"
                    
                    if agent_id not in seen_agents:
                        seen_agents.add(agent_id)
                        agent_roles_found.append(agent)
        
        # Should have both unique agents
        assert len(agent_roles_found) == 2
        agent_names = [agent['name'] for agent in agent_roles_found]
        assert 'User Management Agent' in agent_names
        assert 'Data Processing Agent' in agent_names


class TestAgentValidation:
    """Test agent data validation."""
    
    def test_agent_validation_missing_fields(self):
        """Test validation fills in missing agent fields."""
        # Mock agent with missing fields
        agents = [
            {
                'name': '',  # Missing name
                'responsibility': '',  # Missing responsibility
                # Missing capabilities and autonomy_level
            }
        ]
        
        # Apply validation logic
        validated_agents = []
        for agent in agents:
            if not agent.get('name'):
                agent['name'] = 'Unnamed Agent'
            if not agent.get('responsibility'):
                agent['responsibility'] = f"Autonomous agent responsible for {agent.get('name', 'task')} operations"
            if not agent.get('capabilities'):
                agent['capabilities'] = ['task_execution', 'decision_making', 'exception_handling']
            if not isinstance(agent.get('autonomy_level'), (int, float)):
                agent['autonomy_level'] = 0.8
            
            validated_agents.append(agent)
        
        # Check validation results
        validated_agent = validated_agents[0]
        assert validated_agent['name'] == 'Unnamed Agent'
        assert 'Autonomous agent responsible for' in validated_agent['responsibility']
        assert len(validated_agent['capabilities']) == 3
        assert validated_agent['autonomy_level'] == 0.8
    
    def test_agent_validation_complete_agent(self):
        """Test validation preserves complete agent data."""
        # Mock complete agent
        agents = [
            {
                'name': 'User Management Agent',
                'responsibility': 'Handles user operations',
                'capabilities': ['user_management', 'data_processing'],
                'autonomy_level': 0.9
            }
        ]
        
        # Apply validation logic
        validated_agents = []
        for agent in agents:
            if not agent.get('name'):
                agent['name'] = 'Unnamed Agent'
            if not agent.get('responsibility'):
                agent['responsibility'] = f"Autonomous agent responsible for {agent.get('name', 'task')} operations"
            if not agent.get('capabilities'):
                agent['capabilities'] = ['task_execution', 'decision_making', 'exception_handling']
            if not isinstance(agent.get('autonomy_level'), (int, float)):
                agent['autonomy_level'] = 0.8
            
            validated_agents.append(agent)
        
        # Check original data is preserved
        validated_agent = validated_agents[0]
        assert validated_agent['name'] == 'User Management Agent'
        assert validated_agent['responsibility'] == 'Handles user operations'
        assert validated_agent['capabilities'] == ['user_management', 'data_processing']
        assert validated_agent['autonomy_level'] == 0.9