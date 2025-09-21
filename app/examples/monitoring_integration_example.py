"""
Example demonstrating the TechStackMonitoringIntegrationService
integrated with tech stack generation workflow.
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime

from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService


class MockTechStackGenerator:
    """Mock tech stack generator for demonstration."""
    
    def __init__(self, monitoring_service: TechStackMonitoringIntegrationService):
        self.monitoring_service = monitoring_service
    
    async def generate_tech_stack(self, requirements: Dict[str, Any]) -> List[str]:
        """Generate tech stack with integrated monitoring."""
        
        # Start monitoring session
        session = self.monitoring_service.start_generation_monitoring(
            requirements=requirements,
            metadata={
                'generator_version': '2.0',
                'user_id': 'demo_user',
                'timestamp': datetime.now().isoformat()
            }
        )
        
        print(f"Started monitoring session: {session.session_id}")
        print(f"Correlation ID: {session.correlation_id}")
        
        try:
            # Step 1: Parse requirements
            await self._parse_requirements(session.session_id, requirements)
            
            # Step 2: Extract technologies
            extracted_techs = await self._extract_technologies(session.session_id, requirements)
            
            # Step 3: Call LLM for generation
            llm_response = await self._call_llm(session.session_id, extracted_techs)
            
            # Step 4: Validate results
            validated_stack = await self._validate_stack(session.session_id, llm_response)
            
            # Complete monitoring session
            completed_session = await self.monitoring_service.complete_generation_monitoring(
                session_id=session.session_id,
                final_tech_stack=validated_stack,
                generation_metrics={
                    'extraction_accuracy': 0.95,
                    'llm_response_quality': 0.88,
                    'validation_success': True,
                    'total_processing_time_ms': 2500
                },
                success=True
            )
            
            print(f"Completed monitoring session: {completed_session.session_id}")
            print(f"Session duration: {(completed_session.end_time - completed_session.start_time).total_seconds():.2f}s")
            
            return validated_stack
            
        except Exception as e:
            # Complete session with error
            await self.monitoring_service.complete_generation_monitoring(
                session_id=session.session_id,
                final_tech_stack=[],
                generation_metrics={'error': True},
                success=False,
                error_message=str(e)
            )
            raise
    
    async def _parse_requirements(self, session_id: str, requirements: Dict[str, Any]) -> None:
        """Mock requirement parsing with monitoring."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        await self.monitoring_service.track_parsing_step(
            session_id=session_id,
            step_name='extract_explicit_technologies',
            input_data={'requirements': requirements},
            output_data={
                'explicit_technologies': ['AWS Lambda', 'Python', 'Amazon DynamoDB'],
                'confidence_score': 0.92,
                'context_clues': ['serverless', 'aws', 'python']
            },
            duration_ms=100.0,
            success=True
        )
        
        print("✓ Requirements parsed and tracked")
    
    async def _extract_technologies(self, session_id: str, requirements: Dict[str, Any]) -> List[str]:
        """Mock technology extraction with monitoring."""
        await asyncio.sleep(0.15)  # Simulate processing time
        
        extracted_technologies = ['AWS Lambda', 'Python', 'Amazon DynamoDB', 'Amazon API Gateway']
        confidence_scores = {
            'AWS Lambda': 0.95,
            'Python': 0.92,
            'Amazon DynamoDB': 0.88,
            'Amazon API Gateway': 0.85
        }
        
        await self.monitoring_service.track_extraction_step(
            session_id=session_id,
            extraction_type='explicit_and_contextual',
            extracted_technologies=extracted_technologies,
            confidence_scores=confidence_scores,
            context_data={
                'domain': 'serverless',
                'cloud_provider': 'aws',
                'programming_language': 'python'
            },
            duration_ms=150.0,
            success=True
        )
        
        print("✓ Technologies extracted and tracked")
        return extracted_technologies
    
    async def _call_llm(self, session_id: str, extracted_techs: List[str]) -> List[str]:
        """Mock LLM call with monitoring."""
        await asyncio.sleep(0.8)  # Simulate LLM response time
        
        prompt_data = {
            'prompt_type': 'tech_stack_generation',
            'context_size': 1200,
            'explicit_technologies': extracted_techs,
            'domain_context': 'serverless web application'
        }
        
        response_data = {
            'generated_technologies': extracted_techs + ['AWS CloudFormation', 'Amazon CloudWatch'],
            'reasoning': 'Added infrastructure and monitoring components for serverless architecture',
            'confidence': 0.88
        }
        
        token_usage = {
            'prompt_tokens': 650,
            'completion_tokens': 180,
            'total_tokens': 830
        }
        
        await self.monitoring_service.track_llm_interaction(
            session_id=session_id,
            provider='OpenAI',
            model='gpt-4',
            prompt_data=prompt_data,
            response_data=response_data,
            token_usage=token_usage,
            duration_ms=800.0,
            success=True
        )
        
        print("✓ LLM interaction tracked")
        return response_data['generated_technologies']
    
    async def _validate_stack(self, session_id: str, tech_stack: List[str]) -> List[str]:
        """Mock validation with monitoring."""
        await asyncio.sleep(0.05)  # Simulate validation time
        
        validation_results = {
            'ecosystem_consistency': True,
            'compatibility_score': 0.94,
            'conflicts_detected': 0,
            'recommendations': ['Consider adding AWS X-Ray for distributed tracing']
        }
        
        await self.monitoring_service.track_validation_step(
            session_id=session_id,
            validation_type='ecosystem_compatibility',
            input_technologies=tech_stack,
            validation_results=validation_results,
            conflicts_detected=[],
            resolutions_applied=[],
            duration_ms=50.0,
            success=True
        )
        
        print("✓ Validation completed and tracked")
        return tech_stack


async def demonstrate_monitoring_integration():
    """Demonstrate the monitoring integration service."""
    print("=== Tech Stack Generation Monitoring Integration Demo ===\n")
    
    # Initialize monitoring service
    config = {
        'max_session_duration_hours': 24,
        'max_events_per_session': 1000,
        'real_time_streaming': True,
        'buffer_size': 50
    }
    
    monitoring_service = TechStackMonitoringIntegrationService(config)
    await monitoring_service.start_monitoring_integration()
    
    # Initialize mock generator with monitoring
    generator = MockTechStackGenerator(monitoring_service)
    
    # Sample requirements
    requirements = {
        'business_requirements': 'Build a serverless customer feedback API',
        'technical_requirements': 'Use AWS Lambda and Python, store data in DynamoDB',
        'constraints': {
            'cloud_provider': 'aws',
            'programming_language': 'python',
            'architecture_pattern': 'serverless'
        }
    }
    
    print("Requirements:")
    for key, value in requirements.items():
        print(f"  {key}: {value}")
    print()
    
    # Generate tech stack with monitoring
    try:
        tech_stack = await generator.generate_tech_stack(requirements)
        
        print(f"\nGenerated Tech Stack:")
        for i, tech in enumerate(tech_stack, 1):
            print(f"  {i}. {tech}")
        
        # Get monitoring metrics
        active_sessions = monitoring_service.get_active_sessions()
        service_metrics = monitoring_service.get_service_metrics()
        
        print(f"\nMonitoring Summary:")
        print(f"  Active sessions: {service_metrics['active_sessions']}")
        print(f"  Events buffered: {service_metrics['total_events_buffered']}")
        print(f"  Real-time streaming: {service_metrics['real_time_streaming_enabled']}")
        
        # Demonstrate session status retrieval
        if active_sessions:
            session_id = active_sessions[0]['session_id']
            session_status = monitoring_service.get_session_status(session_id)
            if session_status:
                print(f"  Last session events: {session_status['event_count']}")
                print(f"  Session duration: {session_status['duration_seconds']:.2f}s")
        
    except Exception as e:
        print(f"Error during generation: {e}")
    
    finally:
        # Cleanup
        await monitoring_service.stop_monitoring_integration()
        print("\n✓ Monitoring service stopped")


async def demonstrate_session_lifecycle():
    """Demonstrate complete session lifecycle monitoring."""
    print("\n=== Session Lifecycle Monitoring Demo ===\n")
    
    monitoring_service = TechStackMonitoringIntegrationService()
    await monitoring_service.start_monitoring_integration()
    
    # Start multiple sessions to demonstrate concurrent monitoring
    sessions = []
    for i in range(3):
        session = monitoring_service.start_generation_monitoring(
            requirements={'demo': f'requirements_{i}'},
            metadata={'demo_session': i}
        )
        sessions.append(session)
        print(f"Started session {i+1}: {session.session_id[:8]}...")
    
    # Add some events to each session
    for i, session in enumerate(sessions):
        await monitoring_service.track_parsing_step(
            session_id=session.session_id,
            step_name=f'demo_parsing_{i}',
            input_data={'demo': f'input_{i}'},
            output_data={'demo': f'output_{i}'},
            duration_ms=50.0 * (i + 1)
        )
    
    # Get session status
    print(f"\nActive Sessions: {len(monitoring_service.get_active_sessions())}")
    for session in sessions:
        status = monitoring_service.get_session_status(session.session_id)
        print(f"  Session {session.session_id[:8]}: {status['event_count']} events")
    
    # Complete sessions
    for i, session in enumerate(sessions):
        await monitoring_service.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=[f'tech_{i}'],
            generation_metrics={'demo': True},
            success=True
        )
    
    print(f"Completed all sessions. Active sessions: {len(monitoring_service.get_active_sessions())}")
    
    await monitoring_service.stop_monitoring_integration()


if __name__ == "__main__":
    async def main():
        await demonstrate_monitoring_integration()
        await demonstrate_session_lifecycle()
    
    asyncio.run(main())