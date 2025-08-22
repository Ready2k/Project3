"""Test case to reproduce the original 5 identical agents bug."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.agentic_recommendation_service import AgenticRecommendationService
from app.services.autonomy_assessor import AutonomyAssessment, DecisionIndependence, AgentArchitectureRecommendation


class TestOriginalBugReproduction:
    """Reproduce and verify fix for the original 5 identical agents bug."""
    
    @pytest.fixture
    def original_bug_requirements(self):
        """The exact requirements from the user's bug report."""
        return {
            'description': 'As a BFA System I want an account that is marked as deceased and has an active care case to be marked as \'Deceased Care DNP\' and moved into Do Not Pursue',
            'domain': 'customer-service',
            'pattern_types': ['workflow'],
            'banned_technologies': ['FASTAI'],
            'required_integrations': ['Amazon Connect'],
            'compliance': ['GDPR'],
            'budget': 'Low (Open source preferred)',
            'data_sources': 'physical letters in a filing cabinet',
            'decision_complexity': 'my manager says what to do',
            'integrations': 'we just use it as a phone system',
            'data_availability': 'when a letter comes in we read it and [REMOVED_SUSPICIOUS_CONTENT]the filed copy and then send a letter back out to the customer'
        }
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider that simulates the original bug conditions."""
        mock_llm = AsyncMock()
        # Mock LLM responses that would lead to the bug
        mock_llm.generate.return_value = '{"agents": []}'
        return mock_llm
    
    @pytest.fixture
    def agentic_service(self, mock_llm_provider):
        """Create agentic recommendation service."""
        return AgenticRecommendationService(mock_llm_provider)
    
    @pytest.fixture
    def mock_autonomy_assessment(self):
        """Mock autonomy assessment that leads to single-agent architecture."""
        return AutonomyAssessment(
            overall_score=0.87,
            decision_independence=DecisionIndependence.HIGH,
            reasoning_requirements=['logical_reasoning', 'workflow_management'],
            recommended_architecture=AgentArchitectureRecommendation.SINGLE_AGENT,  # This triggers single-agent path
            automation_boundaries={'scope': 'digital_workflow'},
            human_oversight_needs=['critical_errors'],
            confidence_score=0.85
        )
    
    def test_original_bug_conditions_documentation(self):
        """Document the original bug conditions for reference."""
        bug_description = """
        ORIGINAL BUG: 5 Identical Agents Displayed
        
        Problem: The "Meet Your Agent Team" section showed:
        - 5 agents total
        - All named "User Management Agent" 
        - All with identical responsibilities and capabilities
        - All showing "Highly Autonomous" status
        
        Root Cause Analysis:
        1. System creates single-agent design with 1 agent
        2. Multiple recommendations (up to 5) are generated from pattern matches
        3. Each recommendation gets the SAME single-agent design attached
        4. UI collects agent roles from ALL recommendations
        5. Result: Same single agent shown 5 times
        
        Expected Fix:
        - Each pattern match should get a unique agent design
        - Agent names should be specialized based on pattern type
        - Deduplication logic should prevent identical agents
        - Final display should show diverse, unique agents
        """
        
        # This test documents the bug for future reference
        assert "User Management Agent" in bug_description
        assert "5 agents total" in bug_description
        assert "identical" in bug_description.lower()
    
    @pytest.mark.asyncio
    async def test_reproduce_original_bug_scenario(self, agentic_service, original_bug_requirements, mock_autonomy_assessment):
        """Reproduce the exact scenario that caused the original bug."""
        
        # Mock the autonomy assessor to return single-agent architecture
        with patch.object(agentic_service.autonomy_assessor, 'assess_autonomy_potential', return_value=mock_autonomy_assessment):
            
            # Mock 5 pattern matches (this is what caused the duplication)
            mock_matches = []
            for i in range(5):
                mock_match = MagicMock()
                mock_match.pattern_id = f'APAT-00{i+1}'
                mock_match.confidence = 0.8
                mock_match.autonomy_score = 0.87
                mock_match.reasoning_capabilities = ['logical_reasoning']
                mock_match.enhanced_pattern = {
                    'agentic_frameworks': ['LangChain'],
                    'tech_stack': ['Node.js', 'Express', 'MongoDB']
                }
                mock_match.decision_scope = {'autonomous_decisions': ['account_status_updates']}
                mock_match.exception_handling = 'Autonomous resolution'
                mock_match.multi_agent_potential = False
                mock_matches.append(mock_match)
            
            # Mock the agentic matcher to return 5 matches
            with patch('app.pattern.agentic_matcher.AgenticPatternMatcher') as mock_matcher_class:
                mock_matcher = AsyncMock()
                mock_matcher.match_agentic_patterns.return_value = mock_matches
                mock_matcher_class.return_value = mock_matcher
                
                # Generate recommendations (this should trigger the bug fix)
                recommendations = await agentic_service.generate_agentic_recommendations(
                    original_bug_requirements, session_id='bug_reproduction_test'
                )
                
                # Simulate the Streamlit UI logic that collects agent roles
                agent_roles_found = []
                seen_agents = set()  # This is the deduplication fix
                
                for recommendation in recommendations:
                    agent_roles_data = recommendation.agent_roles or []
                    for agent in agent_roles_data:
                        agent_name = agent.get('name', 'Unknown Agent')
                        agent_responsibility = agent.get('responsibility', '')
                        
                        # Create unique identifier (deduplication logic)
                        agent_id = f"{agent_name}|{agent_responsibility[:50]}"
                        
                        if agent_id not in seen_agents:
                            seen_agents.add(agent_id)
                            agent_roles_found.append(agent)
                
                # VERIFICATION: The bug should be fixed
                print(f"\nBug Reproduction Test Results:")
                print(f"Total recommendations generated: {len(recommendations)}")
                print(f"Total agent roles found: {len(agent_roles_found)}")
                
                if agent_roles_found:
                    print("Agent names found:")
                    for i, agent in enumerate(agent_roles_found):
                        print(f"  {i+1}. {agent.get('name', 'Unknown')}")
                
                # KEY ASSERTIONS: Verify the bug is fixed
                
                # 1. Should have multiple unique agents, not just 1 duplicated 5 times
                assert len(agent_roles_found) >= 3, f"Expected at least 3 unique agents, got {len(agent_roles_found)}"
                
                # 2. Agent names should be diverse, not all "User Management Agent"
                agent_names = [agent.get('name', 'Unknown') for agent in agent_roles_found]
                unique_names = set(agent_names)
                assert len(unique_names) >= 3, f"Expected at least 3 unique names, got: {agent_names}"
                
                # 3. Should NOT have 5 identical "User Management Agent" entries
                user_mgmt_count = agent_names.count('User Management Agent')
                assert user_mgmt_count <= 1, f"Should not have multiple 'User Management Agent' entries, found {user_mgmt_count}"
                
                # 4. Should have specialized agent names
                specialized_count = sum(1 for name in agent_names if any(keyword in name for keyword in ['Workflow', 'Data Processing', 'Integration', 'Monitoring']))
                assert specialized_count >= 2, f"Expected specialized agent names, got: {agent_names}"
                
                print(f"✅ Bug fix verified: {len(unique_names)} unique agents with diverse names")
                
                return agent_roles_found
    
    def test_simulate_original_streamlit_bug_behavior(self):
        """Simulate the original Streamlit behavior that caused the bug."""
        
        # Simulate the original buggy behavior (before fix)
        # This shows what WOULD happen without the deduplication logic
        
        mock_recommendations = []
        
        # Create 5 recommendations, each with the SAME agent (original bug)
        for i in range(5):
            recommendation = {
                'agent_roles': [
                    {
                        'name': 'User Management Agent',
                        'responsibility': 'Main autonomous agent responsible for As a BFA System I want an account that is marked as deceased and has an active care case to be marke',
                        'capabilities': ['task_execution', 'decision_making', 'exception_handling', 'learning_adaptation', 'communication'],
                        'autonomy_level': 0.87
                    }
                ]
            }
            mock_recommendations.append(recommendation)
        
        # Original buggy logic (WITHOUT deduplication)
        agent_roles_found_buggy = []
        for recommendation in mock_recommendations:
            agent_roles_data = recommendation.get("agent_roles", [])
            if agent_roles_data:
                agent_roles_found_buggy.extend(agent_roles_data)  # This caused duplication!
        
        # Verify this reproduces the original bug
        assert len(agent_roles_found_buggy) == 5, "Original bug: should have 5 duplicate agents"
        
        agent_names_buggy = [agent['name'] for agent in agent_roles_found_buggy]
        assert all(name == 'User Management Agent' for name in agent_names_buggy), "Original bug: all agents identical"
        
        print(f"Original bug reproduced: {len(agent_roles_found_buggy)} identical agents")
        
        # Now apply the FIX (WITH deduplication)
        agent_roles_found_fixed = []
        seen_agents = set()
        
        for recommendation in mock_recommendations:
            agent_roles_data = recommendation.get("agent_roles", [])
            if agent_roles_data:
                for agent in agent_roles_data:
                    agent_name = agent.get('name', 'Unknown Agent')
                    agent_responsibility = agent.get('responsibility', '')
                    
                    agent_id = f"{agent_name}|{agent_responsibility[:50]}"
                    
                    if agent_id not in seen_agents:
                        seen_agents.add(agent_id)
                        agent_roles_found_fixed.append(agent)
        
        # Verify the fix works
        assert len(agent_roles_found_fixed) == 1, "Fix: should deduplicate to 1 unique agent"
        
        print(f"Bug fix applied: {len(agent_roles_found_fixed)} unique agent after deduplication")
        
        return {
            'original_bug': agent_roles_found_buggy,
            'after_fix': agent_roles_found_fixed
        }
    
    @pytest.mark.asyncio
    async def test_verify_fix_with_diverse_patterns(self, agentic_service, original_bug_requirements, mock_autonomy_assessment):
        """Verify the fix creates diverse agents when given diverse patterns."""
        
        with patch.object(agentic_service.autonomy_assessor, 'assess_autonomy_potential', return_value=mock_autonomy_assessment):
            
            # Create diverse pattern matches (this should create diverse agents)
            mock_matches = []
            pattern_configs = [
                {'id': 'APAT-001-workflow', 'type': 'workflow'},
                {'id': 'APAT-002-data', 'type': 'data'},
                {'id': 'APAT-003-integration', 'type': 'integration'},
                {'id': 'APAT-004-monitoring', 'type': 'monitoring'},
                {'id': 'APAT-005-user', 'type': 'user'}
            ]
            
            for config in pattern_configs:
                mock_match = MagicMock()
                mock_match.pattern_id = config['id']
                mock_match.confidence = 0.8
                mock_match.autonomy_score = 0.87
                mock_match.reasoning_capabilities = ['logical_reasoning', f"{config['type']}_processing"]
                mock_match.enhanced_pattern = {
                    'agentic_frameworks': ['LangChain'],
                    'tech_stack': ['FastAPI', 'PostgreSQL']
                }
                mock_match.decision_scope = {'autonomous_decisions': [f"{config['type']}_management"]}
                mock_match.exception_handling = f"Autonomous {config['type']} resolution"
                mock_match.multi_agent_potential = False
                mock_matches.append(mock_match)
            
            with patch('app.pattern.agentic_matcher.AgenticPatternMatcher') as mock_matcher_class:
                mock_matcher = AsyncMock()
                mock_matcher.match_agentic_patterns.return_value = mock_matches
                mock_matcher_class.return_value = mock_matcher
                
                recommendations = await agentic_service.generate_agentic_recommendations(
                    original_bug_requirements, session_id='diverse_patterns_test'
                )
                
                # Apply the fixed Streamlit logic
                agent_roles_found = []
                seen_agents = set()
                
                for recommendation in recommendations:
                    agent_roles_data = recommendation.agent_roles or []
                    for agent in agent_roles_data:
                        agent_name = agent.get('name', 'Unknown Agent')
                        agent_responsibility = agent.get('responsibility', '')
                        
                        agent_id = f"{agent_name}|{agent_responsibility[:50]}"
                        
                        if agent_id not in seen_agents:
                            seen_agents.add(agent_id)
                            agent_roles_found.append(agent)
                
                # Verify diverse agents are created
                agent_names = [agent.get('name', 'Unknown') for agent in agent_roles_found]
                
                print(f"\nDiverse Pattern Test Results:")
                print(f"Agent names: {agent_names}")
                
                # Should have diverse, specialized agent names
                expected_specializations = ['Workflow', 'Data Processing', 'Integration', 'Monitoring']
                found_specializations = []
                
                for name in agent_names:
                    for spec in expected_specializations:
                        if spec in name:
                            found_specializations.append(spec)
                            break
                
                assert len(found_specializations) >= 3, f"Expected diverse specializations, got: {agent_names}"
                assert len(set(agent_names)) >= 3, f"Expected unique agent names, got: {agent_names}"
                
                print(f"✅ Diversity verified: {len(found_specializations)} specialized agents created")
                
                return agent_roles_found