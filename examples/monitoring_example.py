"""
Comprehensive example demonstrating the tech stack monitoring system.

This example shows how to use the monitoring, quality assurance, and
dashboard components for tech stack generation quality tracking.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Import monitoring components
from app.monitoring.tech_stack_monitor import TechStackMonitor
from app.monitoring.quality_assurance import QualityAssuranceSystem
from app.monitoring.integration_service import MonitoringIntegrationService


async def demonstrate_monitoring_system():
    """Demonstrate the complete monitoring system functionality."""
    print("🔍 Tech Stack Generation Monitoring System Demo")
    print("=" * 60)
    
    # Initialize monitoring system
    print("\n1. Initializing monitoring system...")
    integration_service = MonitoringIntegrationService()
    
    try:
        # Start monitoring
        await integration_service.start_monitoring_integration()
        print("✅ Monitoring system started successfully")
        
        # Demonstrate tech stack generation monitoring
        await demonstrate_tech_stack_monitoring(integration_service)
        
        # Demonstrate catalog health monitoring
        await demonstrate_catalog_monitoring(integration_service)
        
        # Demonstrate user feedback tracking
        await demonstrate_user_feedback(integration_service)
        
        # Demonstrate quality assurance
        await demonstrate_quality_assurance(integration_service)
        
        # Demonstrate dashboard data
        demonstrate_dashboard_data(integration_service)
        
        # Demonstrate alerts and recommendations
        demonstrate_alerts_and_recommendations(integration_service)
        
        # Demonstrate data export
        demonstrate_data_export(integration_service)
        
    except Exception as e:
        print(f"❌ Error in monitoring demo: {e}")
    
    finally:
        # Stop monitoring
        await integration_service.stop_monitoring_integration()
        print("\n✅ Monitoring system stopped")


async def demonstrate_tech_stack_monitoring(integration_service):
    """Demonstrate monitoring tech stack generation processes."""
    print("\n2. Demonstrating tech stack generation monitoring...")
    
    # Simulate multiple tech stack generation sessions
    test_sessions = [
        {
            "session_id": "aws_web_app_001",
            "requirements": {
                "description": "Build a scalable web application using AWS services with real-time features",
                "explicit_technologies": ["AWS Lambda", "Amazon S3", "Amazon DynamoDB"]
            },
            "extracted_technologies": ["AWS Lambda", "Amazon S3", "Amazon DynamoDB", "FastAPI", "React"],
            "expected_technologies": ["AWS Lambda", "Amazon S3", "Amazon DynamoDB", "FastAPI", "React", "Amazon CloudFront"],
            "explicit_technologies": ["AWS Lambda", "Amazon S3", "Amazon DynamoDB"],
            "generated_stack": ["AWS Lambda", "Amazon S3", "Amazon DynamoDB", "FastAPI", "React"],
            "processing_time": 12.5,
            "llm_calls": 2,
            "catalog_additions": 0
        },
        {
            "session_id": "microservices_002",
            "requirements": {
                "description": "Design microservices architecture with container orchestration",
                "explicit_technologies": ["Docker", "Kubernetes"]
            },
            "extracted_technologies": ["Docker", "Kubernetes", "FastAPI", "PostgreSQL"],
            "expected_technologies": ["Docker", "Kubernetes", "FastAPI", "PostgreSQL", "Redis", "Nginx"],
            "explicit_technologies": ["Docker", "Kubernetes"],
            "generated_stack": ["Docker", "Kubernetes", "FastAPI", "PostgreSQL", "Redis"],
            "processing_time": 18.3,
            "llm_calls": 3,
            "catalog_additions": 1
        },
        {
            "session_id": "ml_pipeline_003",
            "requirements": {
                "description": "Create machine learning pipeline with data processing capabilities",
                "explicit_technologies": ["Python", "TensorFlow", "Apache Spark"]
            },
            "extracted_technologies": ["Python", "TensorFlow", "Apache Spark", "Jupyter", "MLflow"],
            "expected_technologies": ["Python", "TensorFlow", "Apache Spark", "Jupyter", "MLflow", "Apache Kafka"],
            "explicit_technologies": ["Python", "TensorFlow", "Apache Spark"],
            "generated_stack": ["Python", "TensorFlow", "Apache Spark", "Jupyter", "MLflow"],
            "processing_time": 25.7,
            "llm_calls": 4,
            "catalog_additions": 2
        }
    ]
    
    for session in test_sessions:
        print(f"   📊 Monitoring session: {session['session_id']}")
        
        await integration_service.monitor_tech_stack_generation(
            session_id=session["session_id"],
            requirements=session["requirements"],
            extracted_technologies=session["extracted_technologies"],
            expected_technologies=session["expected_technologies"],
            explicit_technologies=session["explicit_technologies"],
            generated_stack=session["generated_stack"],
            processing_time=session["processing_time"],
            llm_calls=session["llm_calls"],
            catalog_additions=session["catalog_additions"]
        )
        
        # Calculate and display metrics
        extracted_count = len(session["extracted_technologies"])
        expected_count = len(session["expected_technologies"])
        explicit_included = len([tech for tech in session["explicit_technologies"] 
                               if tech in session["generated_stack"]])
        explicit_total = len(session["explicit_technologies"])
        
        accuracy = extracted_count / expected_count if expected_count > 0 else 0
        inclusion_rate = explicit_included / explicit_total if explicit_total > 0 else 0
        
        print(f"      - Extraction accuracy: {accuracy:.1%}")
        print(f"      - Explicit inclusion rate: {inclusion_rate:.1%}")
        print(f"      - Processing time: {session['processing_time']:.1f}s")
    
    print("✅ Tech stack generation monitoring completed")


async def demonstrate_catalog_monitoring(integration_service):
    """Demonstrate catalog health monitoring."""
    print("\n3. Demonstrating catalog health monitoring...")
    
    # Simulate catalog health updates over time
    catalog_scenarios = [
        {
            "scenario": "Healthy catalog state",
            "total_technologies": 150,
            "missing_technologies": 3,
            "inconsistent_entries": 1,
            "pending_review": 5
        },
        {
            "scenario": "Catalog needs attention",
            "total_technologies": 150,
            "missing_technologies": 12,
            "inconsistent_entries": 8,
            "pending_review": 25
        },
        {
            "scenario": "Critical catalog issues",
            "total_technologies": 150,
            "missing_technologies": 25,
            "inconsistent_entries": 15,
            "pending_review": 60
        }
    ]
    
    for scenario in catalog_scenarios:
        print(f"   📚 Scenario: {scenario['scenario']}")
        
        await integration_service.update_catalog_health_metrics(
            total_technologies=scenario["total_technologies"],
            missing_technologies=scenario["missing_technologies"],
            inconsistent_entries=scenario["inconsistent_entries"],
            pending_review=scenario["pending_review"]
        )
        
        # Calculate health metrics
        consistency_rate = 1 - (scenario["inconsistent_entries"] / scenario["total_technologies"])
        missing_rate = scenario["missing_technologies"] / scenario["total_technologies"]
        
        print(f"      - Consistency rate: {consistency_rate:.1%}")
        print(f"      - Missing rate: {missing_rate:.1%}")
        print(f"      - Pending review: {scenario['pending_review']} entries")
        
        # Small delay to simulate time progression
        await asyncio.sleep(0.1)
    
    print("✅ Catalog health monitoring completed")


async def demonstrate_user_feedback(integration_service):
    """Demonstrate user satisfaction tracking."""
    print("\n4. Demonstrating user satisfaction tracking...")
    
    # Simulate user feedback for different sessions
    feedback_data = [
        {
            "session_id": "aws_web_app_001",
            "relevance_score": 4.5,
            "accuracy_score": 4.0,
            "completeness_score": 4.2,
            "feedback_text": "Great AWS recommendations, very relevant to my requirements"
        },
        {
            "session_id": "microservices_002",
            "relevance_score": 3.8,
            "accuracy_score": 4.2,
            "completeness_score": 3.5,
            "feedback_text": "Good microservices stack but missing some monitoring tools"
        },
        {
            "session_id": "ml_pipeline_003",
            "relevance_score": 4.8,
            "accuracy_score": 4.5,
            "completeness_score": 4.0,
            "feedback_text": "Excellent ML pipeline recommendations, covered all major components"
        }
    ]
    
    for feedback in feedback_data:
        print(f"   👤 Recording feedback for: {feedback['session_id']}")
        
        await integration_service.record_user_feedback(
            session_id=feedback["session_id"],
            relevance_score=feedback["relevance_score"],
            accuracy_score=feedback["accuracy_score"],
            completeness_score=feedback["completeness_score"],
            feedback_text=feedback["feedback_text"]
        )
        
        overall_score = (feedback["relevance_score"] + feedback["accuracy_score"] + 
                        feedback["completeness_score"]) / 3
        
        print(f"      - Overall satisfaction: {overall_score:.1f}/5")
        print(f"      - Feedback: {feedback['feedback_text'][:50]}...")
    
    print("✅ User satisfaction tracking completed")


async def demonstrate_quality_assurance(integration_service):
    """Demonstrate quality assurance system."""
    print("\n5. Demonstrating quality assurance system...")
    
    # Generate a comprehensive quality report
    print("   🔍 Generating quality assurance report...")
    
    try:
        report = await integration_service.generate_quality_report()
        
        if report:
            print(f"   📋 Quality Report Generated: {report.get('report_id', 'N/A')}")
            print(f"      - Overall Score: {report.get('overall_score', 0):.1%}")
            
            summary = report.get('summary', {})
            print(f"      - Checks Passed: {summary.get('passed', 0)}")
            print(f"      - Checks Failed: {summary.get('failed', 0)}")
            print(f"      - Warnings: {summary.get('warnings', 0)}")
            print(f"      - Health Status: {summary.get('health_status', 'Unknown').title()}")
            
            # Show some recommendations
            recommendations = report.get('recommendations', [])
            if recommendations:
                print("      - Top Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"        {i}. {rec}")
        else:
            print("   ⚠️ No quality report available")
    
    except Exception as e:
        print(f"   ❌ Error generating quality report: {e}")
    
    # Run specific quality checks
    print("\n   🔍 Running specific quality checks...")
    
    check_types = ["accuracy", "performance", "consistency"]
    
    for check_type in check_types:
        try:
            result = await integration_service.run_quality_check(check_type)
            
            if 'error' not in result:
                print(f"      - {check_type.title()} Check: {result.get('status', 'unknown').title()}")
                print(f"        Score: {result.get('score', 0):.1%}")
                print(f"        Message: {result.get('message', 'No message')}")
            else:
                print(f"      - {check_type.title()} Check: Error - {result['error']}")
        
        except Exception as e:
            print(f"      - {check_type.title()} Check: Exception - {e}")
    
    print("✅ Quality assurance demonstration completed")


def demonstrate_dashboard_data(integration_service):
    """Demonstrate dashboard data retrieval."""
    print("\n6. Demonstrating dashboard data...")
    
    try:
        dashboard_data = integration_service.get_quality_dashboard_data()
        
        print("   📊 Dashboard Data Summary:")
        
        # Summary metrics
        summary = dashboard_data.get('summary', {})
        print(f"      - Total Sessions: {summary.get('total_sessions', 0)}")
        print(f"      - Total Alerts: {summary.get('total_alerts', 0)}")
        print(f"      - Critical Alerts: {summary.get('critical_alerts', 0)}")
        
        # Accuracy metrics
        accuracy = dashboard_data.get('accuracy', {})
        if accuracy:
            print(f"      - Average Accuracy: {accuracy.get('average', 0):.1%}")
            print(f"      - Accuracy Trend: {accuracy.get('trend', 'Unknown').title()}")
        
        # Performance metrics
        performance = dashboard_data.get('performance', {})
        if performance:
            print(f"      - Average Response Time: {performance.get('average_time', 0):.1f}s")
            print(f"      - Max Response Time: {performance.get('max_time', 0):.1f}s")
            print(f"      - Performance Trend: {performance.get('trend', 'Unknown').title()}")
        
        # Satisfaction metrics
        satisfaction = dashboard_data.get('satisfaction', {})
        if satisfaction:
            print(f"      - Average Satisfaction: {satisfaction.get('average', 0):.1f}/5")
            print(f"      - Satisfaction Trend: {satisfaction.get('trend', 'Unknown').title()}")
    
    except Exception as e:
        print(f"   ❌ Error retrieving dashboard data: {e}")
    
    print("✅ Dashboard data demonstration completed")


def demonstrate_alerts_and_recommendations(integration_service):
    """Demonstrate alerts and recommendations."""
    print("\n7. Demonstrating alerts and recommendations...")
    
    # Get recent alerts
    try:
        alerts = integration_service.get_recent_alerts(hours=24)
        
        print(f"   🚨 Recent Alerts ({len(alerts)} found):")
        
        if alerts:
            # Group alerts by level
            alert_levels = {}
            for alert in alerts:
                level = alert.get('level', 'unknown')
                if level not in alert_levels:
                    alert_levels[level] = []
                alert_levels[level].append(alert)
            
            for level, level_alerts in alert_levels.items():
                print(f"      - {level.upper()}: {len(level_alerts)} alerts")
                
                # Show first few alerts of each level
                for alert in level_alerts[:2]:
                    print(f"        • {alert.get('category', 'Unknown')}: {alert.get('message', 'No message')}")
        else:
            print("      - No recent alerts")
    
    except Exception as e:
        print(f"   ❌ Error retrieving alerts: {e}")
    
    # Get performance recommendations
    try:
        recommendations = integration_service.get_performance_recommendations()
        
        print(f"\n   💡 Performance Recommendations ({len(recommendations)} found):")
        
        if recommendations:
            # Group by priority
            priority_groups = {}
            for rec in recommendations:
                priority = rec.get('priority', 'medium')
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(rec)
            
            for priority in ['high', 'medium', 'low']:
                if priority in priority_groups:
                    print(f"      - {priority.upper()} Priority ({len(priority_groups[priority])} recommendations):")
                    
                    for rec in priority_groups[priority][:2]:
                        print(f"        • {rec.get('description', 'No description')}")
                        print(f"          Impact: {rec.get('impact', 'Not specified')}")
        else:
            print("      - No performance recommendations")
    
    except Exception as e:
        print(f"   ❌ Error retrieving recommendations: {e}")
    
    print("✅ Alerts and recommendations demonstration completed")


def demonstrate_data_export(integration_service):
    """Demonstrate data export functionality."""
    print("\n8. Demonstrating data export...")
    
    # Create exports directory
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    
    # Export monitoring data
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_file = exports_dir / f"monitoring_demo_export_{timestamp}.json"
        
        success = integration_service.export_monitoring_data(str(export_file), hours=24)
        
        if success:
            print(f"   📁 Monitoring data exported to: {export_file}")
            
            # Show export file info
            if export_file.exists():
                file_size = export_file.stat().st_size
                print(f"      - File size: {file_size:,} bytes")
                
                # Show sample of exported data
                with open(export_file) as f:
                    data = json.load(f)
                
                print(f"      - Metrics exported: {len(data.get('metrics', []))}")
                print(f"      - Alerts exported: {len(data.get('alerts', []))}")
                print(f"      - Time window: {data.get('time_window_hours', 0)} hours")
        else:
            print("   ❌ Failed to export monitoring data")
    
    except Exception as e:
        print(f"   ❌ Error during data export: {e}")
    
    print("✅ Data export demonstration completed")


def print_monitoring_summary():
    """Print a summary of monitoring system capabilities."""
    print("\n" + "=" * 60)
    print("📊 MONITORING SYSTEM CAPABILITIES SUMMARY")
    print("=" * 60)
    
    capabilities = [
        "🎯 Real-time accuracy tracking for technology extraction",
        "⚡ Performance monitoring with response time analysis",
        "📚 Catalog health monitoring and consistency checking",
        "👤 User satisfaction tracking and feedback analysis",
        "🔍 Automated quality assurance with comprehensive checks",
        "🚨 Intelligent alerting for system issues and degradation",
        "💡 Performance optimization recommendations",
        "📊 Interactive dashboard with real-time metrics",
        "📁 Data export capabilities for analysis and reporting",
        "🔄 Automated monitoring workflows and periodic checks"
    ]
    
    for capability in capabilities:
        print(f"  {capability}")
    
    print("\n🎉 The monitoring system provides comprehensive visibility")
    print("   into tech stack generation quality and performance!")


async def main():
    """Main function to run the monitoring system demonstration."""
    try:
        await demonstrate_monitoring_system()
        print_monitoring_summary()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())