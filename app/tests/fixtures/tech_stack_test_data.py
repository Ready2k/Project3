"""
Test data sets for various technology contexts and domains.

This module provides comprehensive test data for validating tech stack generation
across different domains, cloud providers, and technology ecosystems.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pytest


@dataclass
class TechStackTestCase:
    """Test case for tech stack generation."""
    name: str
    requirements: Dict[str, Any]
    expected_technologies: List[str]
    expected_ecosystem: Optional[str]
    expected_confidence_min: float
    expected_inclusion_rate_min: float
    description: str


class TechStackTestDataSets:
    """Comprehensive test data sets for tech stack generation validation."""
    
    @pytest.fixture
    def aws_ecosystem_test_cases(self) -> List[TechStackTestCase]:
        """Test cases for AWS ecosystem validation."""
        return [
            TechStackTestCase(
                name="AWS Serverless Web Application",
                requirements={
                    "description": """
                    Build a serverless web application using AWS Lambda for backend logic,
                    AWS API Gateway for REST APIs, Amazon DynamoDB for data storage,
                    Amazon S3 for static file hosting, and Amazon CloudFront for CDN.
                    Use AWS Cognito for user authentication and Amazon SES for email notifications.
                    """,
                    "domain": "web_application",
                    "architecture": "serverless",
                    "explicit_technologies": [
                        "AWS Lambda", "AWS API Gateway", "Amazon DynamoDB", 
                        "Amazon S3", "Amazon CloudFront", "AWS Cognito", "Amazon SES"
                    ],
                    "cloud_provider": "AWS",
                    "scalability": "high",
                    "cost_optimization": "serverless"
                },
                expected_technologies=[
                    "AWS Lambda", "AWS API Gateway", "Amazon DynamoDB", 
                    "Amazon S3", "Amazon CloudFront", "AWS Cognito", "Amazon SES"
                ],
                expected_ecosystem="AWS",
                expected_confidence_min=0.9,
                expected_inclusion_rate_min=0.85,
                description="Complete AWS serverless stack with all major services"
            ),
            
            TechStackTestCase(
                name="AWS Data Processing Pipeline",
                requirements={
                    "description": """
                    Create a data processing pipeline using AWS Glue for ETL operations,
                    Amazon S3 for data lake storage, Amazon Redshift for data warehousing,
                    AWS Step Functions for workflow orchestration, and Amazon QuickSight for analytics.
                    Use AWS Lambda for data transformations and Amazon Kinesis for streaming data.
                    """,
                    "domain": "data_processing",
                    "architecture": "data_pipeline",
                    "explicit_technologies": [
                        "AWS Glue", "Amazon S3", "Amazon Redshift", "AWS Step Functions",
                        "Amazon QuickSight", "AWS Lambda", "Amazon Kinesis"
                    ],
                    "cloud_provider": "AWS",
                    "data_volume": "large",
                    "processing_type": "batch_and_streaming"
                },
                expected_technologies=[
                    "AWS Glue", "Amazon S3", "Amazon Redshift", "AWS Step Functions",
                    "Amazon QuickSight", "AWS Lambda", "Amazon Kinesis"
                ],
                expected_ecosystem="AWS",
                expected_confidence_min=0.88,
                expected_inclusion_rate_min=0.8,
                description="AWS data processing and analytics pipeline"
            ),
            
            TechStackTestCase(
                name="AWS Microservices Architecture",
                requirements={
                    "description": """
                    Build microservices architecture using Amazon EKS for container orchestration,
                    AWS Application Load Balancer for traffic distribution, Amazon RDS for databases,
                    Amazon ElastiCache for caching, Amazon SQS for message queuing,
                    and AWS X-Ray for distributed tracing. Use AWS Secrets Manager for secrets.
                    """,
                    "domain": "microservices",
                    "architecture": "containerized",
                    "explicit_technologies": [
                        "Amazon EKS", "AWS Application Load Balancer", "Amazon RDS",
                        "Amazon ElastiCache", "Amazon SQS", "AWS X-Ray", "AWS Secrets Manager"
                    ],
                    "cloud_provider": "AWS",
                    "scalability": "horizontal",
                    "monitoring": "comprehensive"
                },
                expected_technologies=[
                    "Amazon EKS", "AWS Application Load Balancer", "Amazon RDS",
                    "Amazon ElastiCache", "Amazon SQS", "AWS X-Ray", "AWS Secrets Manager"
                ],
                expected_ecosystem="AWS",
                expected_confidence_min=0.87,
                expected_inclusion_rate_min=0.8,
                description="AWS microservices with container orchestration"
            )
        ]
    
    @pytest.fixture
    def azure_ecosystem_test_cases(self) -> List[TechStackTestCase]:
        """Test cases for Azure ecosystem validation."""
        return [
            TechStackTestCase(
                name="Azure Serverless Application",
                requirements={
                    "description": """
                    Develop serverless application using Azure Functions for compute,
                    Azure API Management for API gateway, Azure Cosmos DB for database,
                    Azure Storage for file storage, and Azure CDN for content delivery.
                    Integrate with Azure Active Directory for authentication.
                    """,
                    "domain": "web_application",
                    "architecture": "serverless",
                    "explicit_technologies": [
                        "Azure Functions", "Azure API Management", "Azure Cosmos DB",
                        "Azure Storage", "Azure CDN", "Azure Active Directory"
                    ],
                    "cloud_provider": "Azure",
                    "authentication": "enterprise",
                    "global_distribution": True
                },
                expected_technologies=[
                    "Azure Functions", "Azure API Management", "Azure Cosmos DB",
                    "Azure Storage", "Azure CDN", "Azure Active Directory"
                ],
                expected_ecosystem="Azure",
                expected_confidence_min=0.9,
                expected_inclusion_rate_min=0.85,
                description="Complete Azure serverless stack"
            ),
            
            TechStackTestCase(
                name="Azure Data Analytics Platform",
                requirements={
                    "description": """
                    Build analytics platform using Azure Data Factory for ETL,
                    Azure Data Lake Storage for data lake, Azure Synapse Analytics for warehousing,
                    Azure Stream Analytics for real-time processing, and Power BI for visualization.
                    Use Azure Event Hubs for event streaming and Azure Machine Learning for ML.
                    """,
                    "domain": "data_analytics",
                    "architecture": "data_platform",
                    "explicit_technologies": [
                        "Azure Data Factory", "Azure Data Lake Storage", "Azure Synapse Analytics",
                        "Azure Stream Analytics", "Power BI", "Azure Event Hubs", "Azure Machine Learning"
                    ],
                    "cloud_provider": "Azure",
                    "analytics_type": "real_time_and_batch",
                    "ml_integration": True
                },
                expected_technologies=[
                    "Azure Data Factory", "Azure Data Lake Storage", "Azure Synapse Analytics",
                    "Azure Stream Analytics", "Power BI", "Azure Event Hubs", "Azure Machine Learning"
                ],
                expected_ecosystem="Azure",
                expected_confidence_min=0.88,
                expected_inclusion_rate_min=0.8,
                description="Azure data analytics and ML platform"
            ),
            
            TechStackTestCase(
                name="Azure Container Platform",
                requirements={
                    "description": """
                    Create container platform using Azure Kubernetes Service for orchestration,
                    Azure Container Registry for image storage, Azure SQL Database for data,
                    Azure Redis Cache for caching, and Azure Service Bus for messaging.
                    Use Azure Monitor for observability and Azure Key Vault for secrets.
                    """,
                    "domain": "container_platform",
                    "architecture": "containerized",
                    "explicit_technologies": [
                        "Azure Kubernetes Service", "Azure Container Registry", "Azure SQL Database",
                        "Azure Redis Cache", "Azure Service Bus", "Azure Monitor", "Azure Key Vault"
                    ],
                    "cloud_provider": "Azure",
                    "container_orchestration": "kubernetes",
                    "security": "enterprise_grade"
                },
                expected_technologies=[
                    "Azure Kubernetes Service", "Azure Container Registry", "Azure SQL Database",
                    "Azure Redis Cache", "Azure Service Bus", "Azure Monitor", "Azure Key Vault"
                ],
                expected_ecosystem="Azure",
                expected_confidence_min=0.87,
                expected_inclusion_rate_min=0.8,
                description="Azure container orchestration platform"
            )
        ]
    
    @pytest.fixture
    def gcp_ecosystem_test_cases(self) -> List[TechStackTestCase]:
        """Test cases for Google Cloud Platform ecosystem validation."""
        return [
            TechStackTestCase(
                name="GCP Serverless Application",
                requirements={
                    "description": """
                    Build serverless application using Google Cloud Functions for compute,
                    Google Cloud API Gateway for API management, Google Firestore for database,
                    Google Cloud Storage for file storage, and Google Cloud CDN for delivery.
                    Use Google Identity and Access Management for security.
                    """,
                    "domain": "web_application",
                    "architecture": "serverless",
                    "explicit_technologies": [
                        "Google Cloud Functions", "Google Cloud API Gateway", "Google Firestore",
                        "Google Cloud Storage", "Google Cloud CDN", "Google IAM"
                    ],
                    "cloud_provider": "GCP",
                    "database_type": "nosql",
                    "security_model": "iam"
                },
                expected_technologies=[
                    "Google Cloud Functions", "Google Cloud API Gateway", "Google Firestore",
                    "Google Cloud Storage", "Google Cloud CDN", "Google IAM"
                ],
                expected_ecosystem="GCP",
                expected_confidence_min=0.9,
                expected_inclusion_rate_min=0.85,
                description="Complete GCP serverless stack"
            ),
            
            TechStackTestCase(
                name="GCP Data Processing Platform",
                requirements={
                    "description": """
                    Create data platform using Google Cloud Dataflow for stream/batch processing,
                    Google BigQuery for data warehousing, Google Cloud Pub/Sub for messaging,
                    Google Cloud Dataproc for Spark/Hadoop, and Google Data Studio for visualization.
                    Use Google Cloud AI Platform for machine learning workflows.
                    """,
                    "domain": "data_processing",
                    "architecture": "data_platform",
                    "explicit_technologies": [
                        "Google Cloud Dataflow", "Google BigQuery", "Google Cloud Pub/Sub",
                        "Google Cloud Dataproc", "Google Data Studio", "Google Cloud AI Platform"
                    ],
                    "cloud_provider": "GCP",
                    "processing_framework": "apache_beam",
                    "ml_integration": True
                },
                expected_technologies=[
                    "Google Cloud Dataflow", "Google BigQuery", "Google Cloud Pub/Sub",
                    "Google Cloud Dataproc", "Google Data Studio", "Google Cloud AI Platform"
                ],
                expected_ecosystem="GCP",
                expected_confidence_min=0.88,
                expected_inclusion_rate_min=0.8,
                description="GCP data processing and ML platform"
            ),
            
            TechStackTestCase(
                name="GCP Kubernetes Platform",
                requirements={
                    "description": """
                    Build platform using Google Kubernetes Engine for container orchestration,
                    Google Container Registry for images, Google Cloud SQL for databases,
                    Google Cloud Memorystore for caching, and Google Cloud Load Balancing.
                    Use Google Cloud Operations for monitoring and Google Secret Manager.
                    """,
                    "domain": "container_platform",
                    "architecture": "kubernetes",
                    "explicit_technologies": [
                        "Google Kubernetes Engine", "Google Container Registry", "Google Cloud SQL",
                        "Google Cloud Memorystore", "Google Cloud Load Balancing",
                        "Google Cloud Operations", "Google Secret Manager"
                    ],
                    "cloud_provider": "GCP",
                    "orchestration": "gke",
                    "observability": "google_cloud_operations"
                },
                expected_technologies=[
                    "Google Kubernetes Engine", "Google Container Registry", "Google Cloud SQL",
                    "Google Cloud Memorystore", "Google Cloud Load Balancing",
                    "Google Cloud Operations", "Google Secret Manager"
                ],
                expected_ecosystem="GCP",
                expected_confidence_min=0.87,
                expected_inclusion_rate_min=0.8,
                description="GCP Kubernetes container platform"
            )
        ]
    
    @pytest.fixture
    def open_source_stack_test_cases(self) -> List[TechStackTestCase]:
        """Test cases for open source technology stacks."""
        return [
            TechStackTestCase(
                name="Python Web Application Stack",
                requirements={
                    "description": """
                    Build web application using FastAPI for backend API, PostgreSQL for database,
                    Redis for caching and sessions, React for frontend, and Docker for containerization.
                    Use Nginx as reverse proxy and Celery for background tasks.
                    """,
                    "domain": "web_application",
                    "architecture": "traditional",
                    "explicit_technologies": [
                        "FastAPI", "PostgreSQL", "Redis", "React", "Docker", "Nginx", "Celery"
                    ],
                    "ecosystem": "open_source",
                    "language": "python",
                    "deployment": "containerized"
                },
                expected_technologies=[
                    "FastAPI", "PostgreSQL", "Redis", "React", "Docker", "Nginx", "Celery"
                ],
                expected_ecosystem="open_source",
                expected_confidence_min=0.9,
                expected_inclusion_rate_min=0.9,
                description="Complete Python web application stack"
            ),
            
            TechStackTestCase(
                name="Node.js Microservices Stack",
                requirements={
                    "description": """
                    Create microservices using Node.js with Express framework, MongoDB for database,
                    RabbitMQ for message queuing, Elasticsearch for search, and Kubernetes for orchestration.
                    Use Prometheus for monitoring and Grafana for visualization.
                    """,
                    "domain": "microservices",
                    "architecture": "microservices",
                    "explicit_technologies": [
                        "Node.js", "Express", "MongoDB", "RabbitMQ", "Elasticsearch",
                        "Kubernetes", "Prometheus", "Grafana"
                    ],
                    "ecosystem": "open_source",
                    "language": "javascript",
                    "monitoring": "prometheus_grafana"
                },
                expected_technologies=[
                    "Node.js", "Express", "MongoDB", "RabbitMQ", "Elasticsearch",
                    "Kubernetes", "Prometheus", "Grafana"
                ],
                expected_ecosystem="open_source",
                expected_confidence_min=0.88,
                expected_inclusion_rate_min=0.85,
                description="Node.js microservices with monitoring"
            ),
            
            TechStackTestCase(
                name="Java Enterprise Stack",
                requirements={
                    "description": """
                    Build enterprise application using Spring Boot for backend, MySQL for database,
                    Apache Kafka for event streaming, Apache Tomcat for application server,
                    and Angular for frontend. Use Jenkins for CI/CD and SonarQube for code quality.
                    """,
                    "domain": "enterprise_application",
                    "architecture": "monolithic",
                    "explicit_technologies": [
                        "Spring Boot", "MySQL", "Apache Kafka", "Apache Tomcat",
                        "Angular", "Jenkins", "SonarQube"
                    ],
                    "ecosystem": "open_source",
                    "language": "java",
                    "ci_cd": "jenkins"
                },
                expected_technologies=[
                    "Spring Boot", "MySQL", "Apache Kafka", "Apache Tomcat",
                    "Angular", "Jenkins", "SonarQube"
                ],
                expected_ecosystem="open_source",
                expected_confidence_min=0.87,
                expected_inclusion_rate_min=0.85,
                description="Java enterprise application stack"
            ),
            
            TechStackTestCase(
                name="Data Science Platform Stack",
                requirements={
                    "description": """
                    Create data science platform using Python with Jupyter notebooks, pandas for data manipulation,
                    scikit-learn for machine learning, Apache Spark for big data processing,
                    and MLflow for ML lifecycle management. Use Apache Airflow for workflow orchestration.
                    """,
                    "domain": "data_science",
                    "architecture": "data_platform",
                    "explicit_technologies": [
                        "Python", "Jupyter", "pandas", "scikit-learn", "Apache Spark",
                        "MLflow", "Apache Airflow"
                    ],
                    "ecosystem": "open_source",
                    "use_case": "machine_learning",
                    "workflow_orchestration": "airflow"
                },
                expected_technologies=[
                    "Python", "Jupyter", "pandas", "scikit-learn", "Apache Spark",
                    "MLflow", "Apache Airflow"
                ],
                expected_ecosystem="open_source",
                expected_confidence_min=0.9,
                expected_inclusion_rate_min=0.9,
                description="Open source data science and ML platform"
            )
        ]
    
    @pytest.fixture
    def mixed_ecosystem_test_cases(self) -> List[TechStackTestCase]:
        """Test cases for mixed ecosystem scenarios."""
        return [
            TechStackTestCase(
                name="Hybrid Cloud Application",
                requirements={
                    "description": """
                    Build hybrid application using AWS Lambda for serverless functions,
                    PostgreSQL (on-premise) for primary database, Redis (cloud) for caching,
                    and React for frontend. Use Docker for containerization and GitHub Actions for CI/CD.
                    """,
                    "domain": "hybrid_application",
                    "architecture": "hybrid",
                    "explicit_technologies": [
                        "AWS Lambda", "PostgreSQL", "Redis", "React", "Docker", "GitHub Actions"
                    ],
                    "deployment": "hybrid_cloud",
                    "database_location": "on_premise",
                    "compute_location": "cloud"
                },
                expected_technologies=[
                    "AWS Lambda", "PostgreSQL", "Redis", "React", "Docker", "GitHub Actions"
                ],
                expected_ecosystem="mixed",
                expected_confidence_min=0.75,
                expected_inclusion_rate_min=0.8,
                description="Hybrid cloud with mixed technologies"
            ),
            
            TechStackTestCase(
                name="Multi-Cloud Data Pipeline",
                requirements={
                    "description": """
                    Create data pipeline using AWS S3 for data lake, Google BigQuery for analytics,
                    Apache Kafka for streaming, and Azure Machine Learning for ML models.
                    Use Terraform for infrastructure as code and Kubernetes for orchestration.
                    """,
                    "domain": "data_pipeline",
                    "architecture": "multi_cloud",
                    "explicit_technologies": [
                        "AWS S3", "Google BigQuery", "Apache Kafka", "Azure Machine Learning",
                        "Terraform", "Kubernetes"
                    ],
                    "deployment": "multi_cloud",
                    "iac_tool": "terraform",
                    "orchestration": "kubernetes"
                },
                expected_technologies=[
                    "AWS S3", "Google BigQuery", "Apache Kafka", "Azure Machine Learning",
                    "Terraform", "Kubernetes"
                ],
                expected_ecosystem="mixed",
                expected_confidence_min=0.7,
                expected_inclusion_rate_min=0.75,
                description="Multi-cloud data pipeline with IaC"
            ),
            
            TechStackTestCase(
                name="Enterprise Integration Platform",
                requirements={
                    "description": """
                    Build integration platform using Azure Service Bus for messaging,
                    Oracle Database for enterprise data, Salesforce API for CRM integration,
                    and custom Java applications. Use MuleSoft for API management and monitoring.
                    """,
                    "domain": "enterprise_integration",
                    "architecture": "integration_platform",
                    "explicit_technologies": [
                        "Azure Service Bus", "Oracle Database", "Salesforce API",
                        "Java", "MuleSoft"
                    ],
                    "integration_type": "enterprise",
                    "api_management": "mulesoft",
                    "database": "oracle"
                },
                expected_technologies=[
                    "Azure Service Bus", "Oracle Database", "Salesforce API",
                    "Java", "MuleSoft"
                ],
                expected_ecosystem="mixed",
                expected_confidence_min=0.72,
                expected_inclusion_rate_min=0.75,
                description="Enterprise integration with mixed vendors"
            )
        ]
    
    @pytest.fixture
    def domain_specific_test_cases(self) -> List[TechStackTestCase]:
        """Test cases for domain-specific technology requirements."""
        return [
            TechStackTestCase(
                name="Financial Services Trading Platform",
                requirements={
                    "description": """
                    Build high-frequency trading platform using C++ for low-latency components,
                    Apache Kafka for market data streaming, Redis for real-time caching,
                    PostgreSQL with TimescaleDB for time-series data, and Python for analytics.
                    Ensure sub-millisecond latency and regulatory compliance.
                    """,
                    "domain": "financial_services",
                    "use_case": "high_frequency_trading",
                    "explicit_technologies": [
                        "C++", "Apache Kafka", "Redis", "PostgreSQL", "TimescaleDB", "Python"
                    ],
                    "latency_requirement": "sub_millisecond",
                    "compliance": ["MiFID II", "GDPR"],
                    "performance": "ultra_low_latency"
                },
                expected_technologies=[
                    "C++", "Apache Kafka", "Redis", "PostgreSQL", "TimescaleDB", "Python"
                ],
                expected_ecosystem="specialized",
                expected_confidence_min=0.85,
                expected_inclusion_rate_min=0.9,
                description="Ultra-low latency financial trading platform"
            ),
            
            TechStackTestCase(
                name="Healthcare Data Platform",
                requirements={
                    "description": """
                    Create healthcare data platform using FHIR for health data standards,
                    MongoDB for document storage, Apache Spark for data processing,
                    TensorFlow for medical AI models, and React for clinical dashboards.
                    Ensure HIPAA compliance and data encryption at rest and in transit.
                    """,
                    "domain": "healthcare",
                    "use_case": "clinical_data_platform",
                    "explicit_technologies": [
                        "FHIR", "MongoDB", "Apache Spark", "TensorFlow", "React"
                    ],
                    "compliance": ["HIPAA", "GDPR"],
                    "data_standards": "fhir",
                    "ai_use_case": "medical_diagnosis"
                },
                expected_technologies=[
                    "FHIR", "MongoDB", "Apache Spark", "TensorFlow", "React"
                ],
                expected_ecosystem="specialized",
                expected_confidence_min=0.83,
                expected_inclusion_rate_min=0.85,
                description="HIPAA-compliant healthcare data platform"
            ),
            
            TechStackTestCase(
                name="IoT Edge Computing Platform",
                requirements={
                    "description": """
                    Build IoT platform using MQTT for device communication, InfluxDB for time-series data,
                    Apache Kafka for event streaming, Docker for edge deployment,
                    and Grafana for monitoring. Use TensorFlow Lite for edge AI inference.
                    """,
                    "domain": "iot",
                    "use_case": "edge_computing",
                    "explicit_technologies": [
                        "MQTT", "InfluxDB", "Apache Kafka", "Docker", "Grafana", "TensorFlow Lite"
                    ],
                    "deployment": "edge_devices",
                    "protocol": "mqtt",
                    "ai_inference": "edge"
                },
                expected_technologies=[
                    "MQTT", "InfluxDB", "Apache Kafka", "Docker", "Grafana", "TensorFlow Lite"
                ],
                expected_ecosystem="iot_specialized",
                expected_confidence_min=0.82,
                expected_inclusion_rate_min=0.85,
                description="IoT edge computing with AI inference"
            ),
            
            TechStackTestCase(
                name="Gaming Backend Platform",
                requirements={
                    "description": """
                    Create gaming backend using Unity for game engine integration,
                    Redis for player sessions and leaderboards, MongoDB for game data,
                    WebSocket for real-time multiplayer, and Node.js for game services.
                    Use AWS GameLift for dedicated game servers and matchmaking.
                    """,
                    "domain": "gaming",
                    "use_case": "multiplayer_backend",
                    "explicit_technologies": [
                        "Unity", "Redis", "MongoDB", "WebSocket", "Node.js", "AWS GameLift"
                    ],
                    "game_type": "multiplayer",
                    "real_time": True,
                    "matchmaking": "aws_gamelift"
                },
                expected_technologies=[
                    "Unity", "Redis", "MongoDB", "WebSocket", "Node.js", "AWS GameLift"
                ],
                expected_ecosystem="gaming_specialized",
                expected_confidence_min=0.8,
                expected_inclusion_rate_min=0.85,
                description="Real-time multiplayer gaming backend"
            )
        ]
    
    @pytest.fixture
    def performance_test_cases(self) -> List[TechStackTestCase]:
        """Test cases for performance and scalability requirements."""
        return [
            TechStackTestCase(
                name="High-Throughput API Platform",
                requirements={
                    "description": """
                    Build high-throughput API platform handling 100K+ requests per second
                    using Go for high-performance backend, Redis Cluster for distributed caching,
                    Apache Cassandra for write-heavy workloads, and NGINX for load balancing.
                    Use Prometheus and Grafana for performance monitoring.
                    """,
                    "domain": "high_performance_api",
                    "architecture": "high_throughput",
                    "explicit_technologies": [
                        "Go", "Redis Cluster", "Apache Cassandra", "NGINX", "Prometheus", "Grafana"
                    ],
                    "throughput_requirement": "100k_rps",
                    "scalability": "horizontal",
                    "monitoring": "prometheus_grafana"
                },
                expected_technologies=[
                    "Go", "Redis Cluster", "Apache Cassandra", "NGINX", "Prometheus", "Grafana"
                ],
                expected_ecosystem="high_performance",
                expected_confidence_min=0.85,
                expected_inclusion_rate_min=0.9,
                description="Ultra-high throughput API platform"
            ),
            
            TechStackTestCase(
                name="Big Data Processing Platform",
                requirements={
                    "description": """
                    Create big data platform processing petabytes of data using Apache Spark
                    for distributed processing, Apache Hadoop for storage, Apache Kafka for streaming,
                    Elasticsearch for search and analytics, and Apache Airflow for workflow management.
                    Use Apache Zeppelin for data exploration and visualization.
                    """,
                    "domain": "big_data",
                    "architecture": "distributed_processing",
                    "explicit_technologies": [
                        "Apache Spark", "Apache Hadoop", "Apache Kafka", "Elasticsearch",
                        "Apache Airflow", "Apache Zeppelin"
                    ],
                    "data_scale": "petabyte",
                    "processing_type": "batch_and_streaming",
                    "workflow_orchestration": "airflow"
                },
                expected_technologies=[
                    "Apache Spark", "Apache Hadoop", "Apache Kafka", "Elasticsearch",
                    "Apache Airflow", "Apache Zeppelin"
                ],
                expected_ecosystem="big_data",
                expected_confidence_min=0.88,
                expected_inclusion_rate_min=0.9,
                description="Petabyte-scale big data processing platform"
            )
        ]
    
    @pytest.fixture
    def all_test_cases(self, aws_ecosystem_test_cases, azure_ecosystem_test_cases, 
                      gcp_ecosystem_test_cases, open_source_stack_test_cases,
                      mixed_ecosystem_test_cases, domain_specific_test_cases,
                      performance_test_cases) -> List[TechStackTestCase]:
        """All test cases combined for comprehensive testing."""
        return (
            aws_ecosystem_test_cases + azure_ecosystem_test_cases + 
            gcp_ecosystem_test_cases + open_source_stack_test_cases +
            mixed_ecosystem_test_cases + domain_specific_test_cases +
            performance_test_cases
        )


class TechStackValidationMetrics:
    """Metrics collection and validation for tech stack generation."""
    
    @staticmethod
    def calculate_inclusion_rate(expected: List[str], actual: List[str]) -> float:
        """Calculate the rate of expected technologies included in actual stack."""
        if not expected:
            return 1.0
        
        included = sum(1 for tech in expected if tech in actual)
        return included / len(expected)
    
    @staticmethod
    def calculate_precision(expected: List[str], actual: List[str]) -> float:
        """Calculate precision: relevant technologies / total generated technologies."""
        if not actual:
            return 0.0
        
        relevant = sum(1 for tech in actual if tech in expected)
        return relevant / len(actual)
    
    @staticmethod
    def calculate_recall(expected: List[str], actual: List[str]) -> float:
        """Calculate recall: relevant technologies / total expected technologies."""
        if not expected:
            return 1.0
        
        relevant = sum(1 for tech in expected if tech in actual)
        return relevant / len(expected)
    
    @staticmethod
    def calculate_f1_score(precision: float, recall: float) -> float:
        """Calculate F1 score from precision and recall."""
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def validate_ecosystem_consistency(tech_stack: List[str], expected_ecosystem: str) -> bool:
        """Validate that the tech stack is consistent with the expected ecosystem."""
        if expected_ecosystem == "mixed":
            return True  # Mixed ecosystems are always valid
        
        ecosystem_indicators = {
            "AWS": ["AWS", "Amazon"],
            "Azure": ["Azure", "Microsoft"],
            "GCP": ["Google", "GCP"],
            "open_source": []  # Open source doesn't have specific prefixes
        }
        
        if expected_ecosystem not in ecosystem_indicators:
            return True  # Unknown ecosystems are considered valid
        
        indicators = ecosystem_indicators[expected_ecosystem]
        if not indicators:  # Open source case
            # Check that there are no cloud-specific technologies
            cloud_techs = [tech for tech in tech_stack 
                          if any(indicator in tech for indicator in ["AWS", "Amazon", "Azure", "Microsoft", "Google", "GCP"])]
            return len(cloud_techs) == 0
        
        # For cloud ecosystems, check consistency
        ecosystem_techs = [tech for tech in tech_stack 
                          if any(indicator in tech for indicator in indicators)]
        other_cloud_techs = [tech for tech in tech_stack 
                           if any(indicator in tech for other_indicators in ecosystem_indicators.values() 
                                 if other_indicators != indicators
                                 for indicator in other_indicators)]
        
        # Allow some mixed technologies, but majority should be from the expected ecosystem
        if ecosystem_techs and other_cloud_techs:
            return len(ecosystem_techs) >= len(other_cloud_techs)
        
        return len(ecosystem_techs) > 0 or len(other_cloud_techs) == 0


if __name__ == "__main__":
    # Example usage for testing
    test_data = TechStackTestDataSets()
    metrics = TechStackValidationMetrics()
    
    # Example validation
    expected = ["AWS Lambda", "Amazon S3", "DynamoDB"]
    actual = ["AWS Lambda", "Amazon S3", "DynamoDB", "Python", "Docker"]
    
    inclusion_rate = metrics.calculate_inclusion_rate(expected, actual)
    precision = metrics.calculate_precision(expected, actual)
    recall = metrics.calculate_recall(expected, actual)
    f1_score = metrics.calculate_f1_score(precision, recall)
    
    print(f"Inclusion Rate: {inclusion_rate:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1 Score: {f1_score:.2%}")