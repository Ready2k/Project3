"""Technology extractor with NER and pattern matching capabilities."""

import re
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
import string

from .base import ExplicitTech, ExtractionMethod, TechnologyExtractor as BaseTechnologyExtractor
from app.utils.imports import require_service


@dataclass
class TechnologyAlias:
    """Technology alias mapping."""
    alias: str
    canonical_name: str
    confidence: float = 1.0
    context_required: bool = False
    category: Optional[str] = None
    ecosystem: Optional[str] = None


@dataclass
class NEREntity:
    """Named entity recognition result."""
    text: str
    label: str
    start: int
    end: int
    confidence: float = 0.0


@dataclass
class IntegrationPattern:
    """Integration pattern with associated technologies."""
    pattern: str
    technologies: List[str]
    confidence_multiplier: float = 1.0
    context_boost: Dict[str, float] = None


class TechnologyExtractor(BaseTechnologyExtractor):
    """Technology extractor with NER and pattern matching capabilities."""
    
    def __init__(self):
        """Initialize technology extractor."""
        try:
            self.logger = require_service('logger', context='TechnologyExtractor')
        except Exception:
            # Fallback to basic logging for testing
            import logging
            self.logger = logging.getLogger('TechnologyExtractor')
        
        # Initialize technology aliases and patterns
        self._init_technology_aliases()
        self._init_extraction_patterns()
    
    def _init_technology_aliases(self) -> None:
        """Initialize technology alias mappings."""
        self.technology_aliases = {
            # AWS Services
            'connect': TechnologyAlias('connect', 'Amazon Connect', 0.8, context_required=True, category='communication', ecosystem='aws'),
            'connect sdk': TechnologyAlias('connect sdk', 'Amazon Connect SDK', 0.9, category='sdk', ecosystem='aws'),
            'amazon connect': TechnologyAlias('amazon connect', 'Amazon Connect', 0.95, category='communication', ecosystem='aws'),
            'amazon connect sdk': TechnologyAlias('amazon connect sdk', 'Amazon Connect SDK', 0.95, category='sdk', ecosystem='aws'),
            's3': TechnologyAlias('s3', 'Amazon S3', 0.9, category='storage', ecosystem='aws'),
            'simple storage service': TechnologyAlias('simple storage service', 'Amazon S3', 0.9, category='storage', ecosystem='aws'),
            'lambda': TechnologyAlias('lambda', 'AWS Lambda', 0.8, context_required=True, category='compute', ecosystem='aws'),
            'aws lambda': TechnologyAlias('aws lambda', 'AWS Lambda', 0.95, category='compute', ecosystem='aws'),
            'comprehend': TechnologyAlias('comprehend', 'AWS Comprehend', 0.9, category='ai', ecosystem='aws'),
            'aws comprehend': TechnologyAlias('aws comprehend', 'AWS Comprehend', 0.95, category='ai', ecosystem='aws'),
            'bedrock': TechnologyAlias('bedrock', 'AWS Bedrock', 0.9, category='ai', ecosystem='aws'),
            'aws bedrock': TechnologyAlias('aws bedrock', 'AWS Bedrock', 0.95, category='ai', ecosystem='aws'),
            'dynamodb': TechnologyAlias('dynamodb', 'Amazon DynamoDB', 0.9, category='database', ecosystem='aws'),
            'dynamo db': TechnologyAlias('dynamo db', 'Amazon DynamoDB', 0.9, category='database', ecosystem='aws'),
            'rds': TechnologyAlias('rds', 'Amazon RDS', 0.9, category='database', ecosystem='aws'),
            'relational database service': TechnologyAlias('relational database service', 'Amazon RDS', 0.9, category='database', ecosystem='aws'),
            'ec2': TechnologyAlias('ec2', 'Amazon EC2', 0.9, category='compute', ecosystem='aws'),
            'elastic compute cloud': TechnologyAlias('elastic compute cloud', 'Amazon EC2', 0.9, category='compute', ecosystem='aws'),
            'ecs': TechnologyAlias('ecs', 'Amazon ECS', 0.9, category='container', ecosystem='aws'),
            'elastic container service': TechnologyAlias('elastic container service', 'Amazon ECS', 0.9, category='container', ecosystem='aws'),
            'eks': TechnologyAlias('eks', 'Amazon EKS', 0.9, category='container', ecosystem='aws'),
            'elastic kubernetes service': TechnologyAlias('elastic kubernetes service', 'Amazon EKS', 0.9, category='container', ecosystem='aws'),
            'cloudwatch': TechnologyAlias('cloudwatch', 'Amazon CloudWatch', 0.9, category='monitoring', ecosystem='aws'),
            'cloud watch': TechnologyAlias('cloud watch', 'Amazon CloudWatch', 0.9, category='monitoring', ecosystem='aws'),
            'sns': TechnologyAlias('sns', 'Amazon SNS', 0.9, category='messaging', ecosystem='aws'),
            'simple notification service': TechnologyAlias('simple notification service', 'Amazon SNS', 0.9, category='messaging', ecosystem='aws'),
            'sqs': TechnologyAlias('sqs', 'Amazon SQS', 0.9, category='messaging', ecosystem='aws'),
            'simple queue service': TechnologyAlias('simple queue service', 'Amazon SQS', 0.9, category='messaging', ecosystem='aws'),
            'api gateway': TechnologyAlias('api gateway', 'Amazon API Gateway', 0.9, category='api', ecosystem='aws'),
            'cloudfront': TechnologyAlias('cloudfront', 'Amazon CloudFront', 0.9, category='cdn', ecosystem='aws'),
            'cloud front': TechnologyAlias('cloud front', 'Amazon CloudFront', 0.9, category='cdn', ecosystem='aws'),
            'route 53': TechnologyAlias('route 53', 'Amazon Route 53', 0.9, category='dns', ecosystem='aws'),
            'route53': TechnologyAlias('route53', 'Amazon Route 53', 0.9, category='dns', ecosystem='aws'),
            
            # Azure Services
            'cognitive services': TechnologyAlias('cognitive services', 'Azure Cognitive Services', 0.9, category='ai', ecosystem='azure'),
            'azure cognitive services': TechnologyAlias('azure cognitive services', 'Azure Cognitive Services', 0.95, category='ai', ecosystem='azure'),
            'app service': TechnologyAlias('app service', 'Azure App Service', 0.9, category='compute', ecosystem='azure'),
            'azure app service': TechnologyAlias('azure app service', 'Azure App Service', 0.95, category='compute', ecosystem='azure'),
            'functions': TechnologyAlias('functions', 'Azure Functions', 0.8, context_required=True, category='compute', ecosystem='azure'),
            'azure functions': TechnologyAlias('azure functions', 'Azure Functions', 0.95, category='compute', ecosystem='azure'),
            'cosmos db': TechnologyAlias('cosmos db', 'Azure Cosmos DB', 0.9, category='database', ecosystem='azure'),
            'cosmosdb': TechnologyAlias('cosmosdb', 'Azure Cosmos DB', 0.9, category='database', ecosystem='azure'),
            'azure cosmos db': TechnologyAlias('azure cosmos db', 'Azure Cosmos DB', 0.95, category='database', ecosystem='azure'),
            'sql database': TechnologyAlias('sql database', 'Azure SQL Database', 0.8, context_required=True, category='database', ecosystem='azure'),
            'azure sql database': TechnologyAlias('azure sql database', 'Azure SQL Database', 0.95, category='database', ecosystem='azure'),
            'storage account': TechnologyAlias('storage account', 'Azure Storage Account', 0.9, category='storage', ecosystem='azure'),
            'azure storage': TechnologyAlias('azure storage', 'Azure Storage Account', 0.9, category='storage', ecosystem='azure'),
            'blob storage': TechnologyAlias('blob storage', 'Azure Blob Storage', 0.9, category='storage', ecosystem='azure'),
            'azure blob storage': TechnologyAlias('azure blob storage', 'Azure Blob Storage', 0.95, category='storage', ecosystem='azure'),
            'service bus': TechnologyAlias('service bus', 'Azure Service Bus', 0.9, category='messaging', ecosystem='azure'),
            'azure service bus': TechnologyAlias('azure service bus', 'Azure Service Bus', 0.95, category='messaging', ecosystem='azure'),
            'event hubs': TechnologyAlias('event hubs', 'Azure Event Hubs', 0.9, category='messaging', ecosystem='azure'),
            'azure event hubs': TechnologyAlias('azure event hubs', 'Azure Event Hubs', 0.95, category='messaging', ecosystem='azure'),
            
            # GCP Services
            'cloud functions': TechnologyAlias('cloud functions', 'Google Cloud Functions', 0.9, category='compute', ecosystem='gcp'),
            'google cloud functions': TechnologyAlias('google cloud functions', 'Google Cloud Functions', 0.95, category='compute', ecosystem='gcp'),
            'cloud run': TechnologyAlias('cloud run', 'Google Cloud Run', 0.9, category='compute', ecosystem='gcp'),
            'google cloud run': TechnologyAlias('google cloud run', 'Google Cloud Run', 0.95, category='compute', ecosystem='gcp'),
            'bigquery': TechnologyAlias('bigquery', 'Google BigQuery', 0.9, category='database', ecosystem='gcp'),
            'big query': TechnologyAlias('big query', 'Google BigQuery', 0.9, category='database', ecosystem='gcp'),
            'google bigquery': TechnologyAlias('google bigquery', 'Google BigQuery', 0.95, category='database', ecosystem='gcp'),
            'firestore': TechnologyAlias('firestore', 'Google Firestore', 0.9, category='database', ecosystem='gcp'),
            'google firestore': TechnologyAlias('google firestore', 'Google Firestore', 0.95, category='database', ecosystem='gcp'),
            'cloud storage': TechnologyAlias('cloud storage', 'Google Cloud Storage', 0.8, context_required=True, category='storage', ecosystem='gcp'),
            'google cloud storage': TechnologyAlias('google cloud storage', 'Google Cloud Storage', 0.95, category='storage', ecosystem='gcp'),
            'gcs': TechnologyAlias('gcs', 'Google Cloud Storage', 0.9, category='storage', ecosystem='gcp'),
            'compute engine': TechnologyAlias('compute engine', 'Google Compute Engine', 0.9, category='compute', ecosystem='gcp'),
            'google compute engine': TechnologyAlias('google compute engine', 'Google Compute Engine', 0.95, category='compute', ecosystem='gcp'),
            'gce': TechnologyAlias('gce', 'Google Compute Engine', 0.9, category='compute', ecosystem='gcp'),
            'gke': TechnologyAlias('gke', 'Google Kubernetes Engine', 0.9, category='container', ecosystem='gcp'),
            'google kubernetes engine': TechnologyAlias('google kubernetes engine', 'Google Kubernetes Engine', 0.95, category='container', ecosystem='gcp'),
            'pub/sub': TechnologyAlias('pub/sub', 'Google Cloud Pub/Sub', 0.9, category='messaging', ecosystem='gcp'),
            'pubsub': TechnologyAlias('pubsub', 'Google Cloud Pub/Sub', 0.9, category='messaging', ecosystem='gcp'),
            'google cloud pub/sub': TechnologyAlias('google cloud pub/sub', 'Google Cloud Pub/Sub', 0.95, category='messaging', ecosystem='gcp'),
            
            # Programming Languages & Frameworks
            'py': TechnologyAlias('py', 'Python', 0.7, category='language'),
            'python': TechnologyAlias('python', 'Python', 0.95, category='language'),
            'js': TechnologyAlias('js', 'JavaScript', 0.7, category='language'),
            'javascript': TechnologyAlias('javascript', 'JavaScript', 0.95, category='language'),
            'ts': TechnologyAlias('ts', 'TypeScript', 0.8, category='language'),
            'typescript': TechnologyAlias('typescript', 'TypeScript', 0.95, category='language'),
            'node': TechnologyAlias('node', 'Node.js', 0.8, category='runtime'),
            'nodejs': TechnologyAlias('nodejs', 'Node.js', 0.9, category='runtime'),
            'node.js': TechnologyAlias('node.js', 'Node.js', 0.95, category='runtime'),
            'react': TechnologyAlias('react', 'React', 0.9, category='frontend'),
            'reactjs': TechnologyAlias('reactjs', 'React', 0.9, category='frontend'),
            'react.js': TechnologyAlias('react.js', 'React', 0.9, category='frontend'),
            'vue': TechnologyAlias('vue', 'Vue.js', 0.8, category='frontend'),
            'vuejs': TechnologyAlias('vuejs', 'Vue.js', 0.9, category='frontend'),
            'vue.js': TechnologyAlias('vue.js', 'Vue.js', 0.95, category='frontend'),
            'angular': TechnologyAlias('angular', 'Angular', 0.9, category='frontend'),
            'angularjs': TechnologyAlias('angularjs', 'AngularJS', 0.9, category='frontend'),
            'django': TechnologyAlias('django', 'Django', 0.9, category='backend'),
            'flask': TechnologyAlias('flask', 'Flask', 0.9, category='backend'),
            'fastapi': TechnologyAlias('fastapi', 'FastAPI', 0.9, category='backend'),
            'fast api': TechnologyAlias('fast api', 'FastAPI', 0.9, category='backend'),
            'express': TechnologyAlias('express', 'Express.js', 0.8, category='backend'),
            'expressjs': TechnologyAlias('expressjs', 'Express.js', 0.9, category='backend'),
            'express.js': TechnologyAlias('express.js', 'Express.js', 0.95, category='backend'),
            'spring': TechnologyAlias('spring', 'Spring Framework', 0.8, category='backend'),
            'spring boot': TechnologyAlias('spring boot', 'Spring Boot', 0.9, category='backend'),
            'springboot': TechnologyAlias('springboot', 'Spring Boot', 0.9, category='backend'),
            'laravel': TechnologyAlias('laravel', 'Laravel', 0.9, category='backend'),
            'symfony': TechnologyAlias('symfony', 'Symfony', 0.9, category='backend'),
            'rails': TechnologyAlias('rails', 'Ruby on Rails', 0.9, category='backend'),
            'ruby on rails': TechnologyAlias('ruby on rails', 'Ruby on Rails', 0.95, category='backend'),
            'asp.net': TechnologyAlias('asp.net', 'ASP.NET', 0.9, category='backend'),
            'aspnet': TechnologyAlias('aspnet', 'ASP.NET', 0.9, category='backend'),
            'asp.net core': TechnologyAlias('asp.net core', 'ASP.NET Core', 0.95, category='backend'),
            
            # Databases
            'postgres': TechnologyAlias('postgres', 'PostgreSQL', 0.9, category='database'),
            'postgresql': TechnologyAlias('postgresql', 'PostgreSQL', 0.95, category='database'),
            'mysql': TechnologyAlias('mysql', 'MySQL', 0.9, category='database'),
            'mongo': TechnologyAlias('mongo', 'MongoDB', 0.8, category='database'),
            'mongodb': TechnologyAlias('mongodb', 'MongoDB', 0.95, category='database'),
            'redis': TechnologyAlias('redis', 'Redis', 0.9, category='cache'),
            'elasticsearch': TechnologyAlias('elasticsearch', 'Elasticsearch', 0.9, category='search'),
            'elastic': TechnologyAlias('elastic', 'Elasticsearch', 0.7, category='search'),
            'elastic search': TechnologyAlias('elastic search', 'Elasticsearch', 0.9, category='search'),
            'cassandra': TechnologyAlias('cassandra', 'Apache Cassandra', 0.9, category='database'),
            'apache cassandra': TechnologyAlias('apache cassandra', 'Apache Cassandra', 0.95, category='database'),
            'couchdb': TechnologyAlias('couchdb', 'Apache CouchDB', 0.9, category='database'),
            'couch db': TechnologyAlias('couch db', 'Apache CouchDB', 0.9, category='database'),
            'sqlite': TechnologyAlias('sqlite', 'SQLite', 0.9, category='database'),
            'mariadb': TechnologyAlias('mariadb', 'MariaDB', 0.9, category='database'),
            'oracle': TechnologyAlias('oracle', 'Oracle Database', 0.8, context_required=True, category='database'),
            'oracle db': TechnologyAlias('oracle db', 'Oracle Database', 0.9, category='database'),
            'oracle database': TechnologyAlias('oracle database', 'Oracle Database', 0.95, category='database'),
            'sql server': TechnologyAlias('sql server', 'Microsoft SQL Server', 0.9, category='database'),
            'mssql': TechnologyAlias('mssql', 'Microsoft SQL Server', 0.9, category='database'),
            'microsoft sql server': TechnologyAlias('microsoft sql server', 'Microsoft SQL Server', 0.95, category='database'),
            
            # Container & Orchestration
            'docker': TechnologyAlias('docker', 'Docker', 0.9, category='container'),
            'k8s': TechnologyAlias('k8s', 'Kubernetes', 0.9, category='orchestration'),
            'kubernetes': TechnologyAlias('kubernetes', 'Kubernetes', 0.95, category='orchestration'),
            'kube': TechnologyAlias('kube', 'Kubernetes', 0.8, category='orchestration'),
            'podman': TechnologyAlias('podman', 'Podman', 0.9, category='container'),
            'containerd': TechnologyAlias('containerd', 'containerd', 0.9, category='container'),
            'docker compose': TechnologyAlias('docker compose', 'Docker Compose', 0.9, category='orchestration'),
            'docker-compose': TechnologyAlias('docker-compose', 'Docker Compose', 0.9, category='orchestration'),
            'helm': TechnologyAlias('helm', 'Helm', 0.9, category='orchestration'),
            'istio': TechnologyAlias('istio', 'Istio', 0.9, category='service-mesh'),
            'linkerd': TechnologyAlias('linkerd', 'Linkerd', 0.9, category='service-mesh'),
            
            # Monitoring & Observability
            'prometheus': TechnologyAlias('prometheus', 'Prometheus', 0.9),
            'grafana': TechnologyAlias('grafana', 'Grafana', 0.9),
            'jaeger': TechnologyAlias('jaeger', 'Jaeger', 0.9),
            'zipkin': TechnologyAlias('zipkin', 'Zipkin', 0.9),
            
            # Message Queues
            'kafka': TechnologyAlias('kafka', 'Apache Kafka', 0.9),
            'rabbitmq': TechnologyAlias('rabbitmq', 'RabbitMQ', 0.9),
            'celery': TechnologyAlias('celery', 'Celery', 0.9),
            
            # AI/ML
            'openai': TechnologyAlias('openai', 'OpenAI API', 0.9),
            'anthropic': TechnologyAlias('anthropic', 'Anthropic Claude', 0.9),
            'huggingface': TechnologyAlias('huggingface', 'Hugging Face', 0.8),
            'transformers': TechnologyAlias('transformers', 'Hugging Face Transformers', 0.8),
            'langchain': TechnologyAlias('langchain', 'LangChain', 0.9),
            'langgraph': TechnologyAlias('langgraph', 'LangGraph', 0.9),
            'pandas': TechnologyAlias('pandas', 'Pandas', 0.9),
            'numpy': TechnologyAlias('numpy', 'NumPy', 0.9),
            'scikit-learn': TechnologyAlias('scikit-learn', 'Scikit-learn', 0.9),
            'sklearn': TechnologyAlias('sklearn', 'Scikit-learn', 0.8),
            'tensorflow': TechnologyAlias('tensorflow', 'TensorFlow', 0.9),
            'pytorch': TechnologyAlias('pytorch', 'PyTorch', 0.9),
            
            # Web Servers & Proxies
            'nginx': TechnologyAlias('nginx', 'Nginx', 0.9),
            'apache': TechnologyAlias('apache', 'Apache HTTP Server', 0.8, context_required=True),
            'gunicorn': TechnologyAlias('gunicorn', 'Gunicorn', 0.9),
            'uvicorn': TechnologyAlias('uvicorn', 'Uvicorn', 0.9),
            
            # Testing
            'pytest': TechnologyAlias('pytest', 'pytest', 0.9),
            'jest': TechnologyAlias('jest', 'Jest', 0.9),
            'junit': TechnologyAlias('junit', 'JUnit', 0.9),
            
            # Build Tools
            'webpack': TechnologyAlias('webpack', 'Webpack', 0.9),
            'vite': TechnologyAlias('vite', 'Vite', 0.9),
            'maven': TechnologyAlias('maven', 'Apache Maven', 0.9),
            'gradle': TechnologyAlias('gradle', 'Gradle', 0.9),
            'npm': TechnologyAlias('npm', 'npm', 0.9),
            'yarn': TechnologyAlias('yarn', 'Yarn', 0.9),
            
            # Version Control & CI/CD
            'git': TechnologyAlias('git', 'Git', 0.9),
            'github': TechnologyAlias('github', 'GitHub', 0.9),
            'gitlab': TechnologyAlias('gitlab', 'GitLab', 0.9),
            'jenkins': TechnologyAlias('jenkins', 'Jenkins', 0.9),
            'github actions': TechnologyAlias('github actions', 'GitHub Actions', 0.9),
            'circleci': TechnologyAlias('circleci', 'CircleCI', 0.9)
        }
    
    def _init_extraction_patterns(self) -> None:
        """Initialize regex patterns for technology extraction."""
        # Enhanced technology name patterns with better coverage
        self.tech_name_patterns = [
            # Exact technology names (comprehensive list)
            re.compile(r'\b(?:fastapi|django|flask|react|vue\.js|angular|docker|kubernetes|redis|postgresql|mysql|mongodb|python|javascript|typescript|java|golang|rust|php|ruby|scala|kotlin|swift|dart|elixir|erlang|haskell|clojure|f#|c\+\+|c#|\.net|node\.js|express\.js|spring|hibernate|laravel|symfony|rails|asp\.net)\b', re.IGNORECASE),
            
            # Cloud services with prefixes (enhanced patterns)
            re.compile(r'\b(?:amazon|aws)\s+([\w\s]+?)(?:\s+(?:service|api|sdk|platform|engine|database|storage|compute|function|lambda|gateway|queue|notification|monitoring|analytics|ml|ai))?(?:\s|$|[,.])', re.IGNORECASE),
            re.compile(r'\b(?:azure|microsoft\s+azure)\s+([\w\s]+?)(?:\s+(?:service|api|sdk|platform|engine|database|storage|compute|function|app|gateway|queue|notification|monitoring|analytics|ml|ai))?(?:\s|$|[,.])', re.IGNORECASE),
            re.compile(r'\b(?:google\s+cloud|gcp)\s+([\w\s]+?)(?:\s+(?:service|api|sdk|platform|engine|database|storage|compute|function|app|gateway|queue|notification|monitoring|analytics|ml|ai))?(?:\s|$|[,.])', re.IGNORECASE),
            
            # Technology with common suffixes (enhanced)
            re.compile(r'\b([\w\-\.]+)\s+(?:api|sdk|library|framework|service|database|db|engine|platform|tool|client|driver|connector|adapter|plugin|extension|middleware|runtime|compiler|interpreter|vm|container|image|registry)\b', re.IGNORECASE),
            
            # Programming languages and runtimes (comprehensive)
            re.compile(r'\b(?:python|javascript|typescript|java|golang|go\s+lang|rust|php|ruby|scala|kotlin|swift|dart|elixir|erlang|haskell|clojure|f#|c\+\+|c#|\.net|node\.js|deno|bun)\b', re.IGNORECASE),
            
            # Framework and library patterns
            re.compile(r'\b([\w\-\.]+)\s+(?:framework|library|package|module|component|widget|plugin|extension|addon|toolkit|suite|stack|platform)\b', re.IGNORECASE),
            
            # Database and storage patterns
            re.compile(r'\b([\w\-\.]+)\s+(?:database|db|storage|cache|index|search|analytics|warehouse|lake|mart|store|repository|vault)\b', re.IGNORECASE),
            
            # Integration and communication patterns
            re.compile(r'\b([\w\-\.]+)\s+(?:integration|connector|client|driver|adapter|bridge|gateway|proxy|broker|queue|stream|pipeline|channel|protocol|interface)\b', re.IGNORECASE),
            
            # Monitoring and observability patterns
            re.compile(r'\b([\w\-\.]+)\s+(?:monitoring|logging|tracing|metrics|analytics|dashboard|alerting|notification|observability|telemetry)\b', re.IGNORECASE),
            
            # DevOps and deployment patterns
            re.compile(r'\b([\w\-\.]+)\s+(?:deployment|orchestration|automation|pipeline|ci\/cd|build|test|release|provisioning|configuration|infrastructure)\b', re.IGNORECASE),
            
            # Implicit technology references (e.g., "Connect SDK" -> "Amazon Connect SDK")
            re.compile(r'\b(connect|comprehend|bedrock|lambda|s3|ec2|rds|dynamodb|sns|sqs|cloudwatch|api\s+gateway|route\s+53)\s+(?:sdk|api|service|client|integration)?\b', re.IGNORECASE),
            
            # Version-specific patterns
            re.compile(r'\b([\w\-\.]+)\s+(?:v\d+|version\s+\d+|\d+\.\d+|\d+\.\d+\.\d+)\b', re.IGNORECASE),
            
            # Abbreviated technology names
            re.compile(r'\b(?:js|ts|py|k8s|tf|aws|gcp|az|db|api|ui|ux|ml|ai|nlp|cv|dl|rl)\b', re.IGNORECASE)
        ]
        
        # Context patterns for disambiguation
        self.context_patterns = {
            'aws': re.compile(r'\b(?:aws|amazon\s+web\s+services)\b', re.IGNORECASE),
            'azure': re.compile(r'\b(?:azure|microsoft\s+cloud)\b', re.IGNORECASE),
            'gcp': re.compile(r'\b(?:gcp|google\s+cloud)\b', re.IGNORECASE),
            'database': re.compile(r'\b(?:database|db|storage|persistence)\b', re.IGNORECASE),
            'api': re.compile(r'\b(?:api|rest|endpoint|service)\b', re.IGNORECASE),
            'ml': re.compile(r'\b(?:machine\s+learning|ai|model|training)\b', re.IGNORECASE),
            'web': re.compile(r'\b(?:web|frontend|ui|interface)\b', re.IGNORECASE),
            'backend': re.compile(r'\b(?:backend|server|service)\b', re.IGNORECASE)
        }
        
        # Enhanced integration pattern indicators with associated technologies
        self.integration_patterns = {
            'rest_api': IntegrationPattern(
                pattern=r'\b(?:rest\s+api|restful|http\s+api|web\s+api|api\s+endpoint)\b',
                technologies=['FastAPI', 'Express.js', 'Spring Boot', 'Django REST Framework', 'Flask-RESTful', 'ASP.NET Web API'],
                confidence_multiplier=0.8,
                context_boost={'python': 1.2, 'javascript': 1.1, 'java': 1.1, 'c#': 1.1}
            ),
            'graphql': IntegrationPattern(
                pattern=r'\b(?:graphql|graph\s+ql)\b',
                technologies=['GraphQL', 'Apollo Server', 'GraphQL Yoga', 'Hasura', 'Prisma'],
                confidence_multiplier=0.9
            ),
            'websocket': IntegrationPattern(
                pattern=r'\b(?:websocket|web\s+socket|socket\.io|real\s*time|live\s+updates)\b',
                technologies=['Socket.IO', 'WebSocket API', 'SignalR', 'Phoenix Channels'],
                confidence_multiplier=0.8
            ),
            'grpc': IntegrationPattern(
                pattern=r'\b(?:grpc|g\s*rpc|protocol\s+buffers|protobuf)\b',
                technologies=['gRPC', 'Protocol Buffers', 'Envoy Proxy'],
                confidence_multiplier=0.9
            ),
            'message_queue': IntegrationPattern(
                pattern=r'\b(?:message\s+queue|messaging|queue|pub\s*sub|event\s+streaming)\b',
                technologies=['Apache Kafka', 'RabbitMQ', 'Amazon SQS', 'Azure Service Bus', 'Google Cloud Pub/Sub', 'Redis Streams'],
                confidence_multiplier=0.7,
                context_boost={'aws': 1.3, 'azure': 1.2, 'gcp': 1.2}
            ),
            'event_driven': IntegrationPattern(
                pattern=r'\b(?:event\s+driven|event\s+sourcing|cqrs|saga\s+pattern)\b',
                technologies=['Apache Kafka', 'Amazon EventBridge', 'Azure Event Grid', 'Google Cloud Eventarc'],
                confidence_multiplier=0.6,
                context_boost={'aws': 1.4, 'azure': 1.3, 'gcp': 1.3}
            ),
            'microservices': IntegrationPattern(
                pattern=r'\b(?:microservices|micro\s+services|service\s+mesh|distributed\s+system)\b',
                technologies=['Kubernetes', 'Docker', 'Istio', 'Consul', 'Envoy Proxy', 'Spring Cloud', 'Netflix OSS'],
                confidence_multiplier=0.6
            ),
            'database_orm': IntegrationPattern(
                pattern=r'\b(?:orm|object\s+relational\s+mapping|active\s+record|data\s+mapper)\b',
                technologies=['SQLAlchemy', 'Hibernate', 'Entity Framework', 'Sequelize', 'Prisma', 'TypeORM'],
                confidence_multiplier=0.7,
                context_boost={'python': 1.3, 'java': 1.2, 'javascript': 1.1, 'c#': 1.2}
            ),
            'caching': IntegrationPattern(
                pattern=r'\b(?:caching|cache|in\s*memory|session\s+storage)\b',
                technologies=['Redis', 'Memcached', 'Hazelcast', 'Amazon ElastiCache', 'Azure Cache for Redis'],
                confidence_multiplier=0.8,
                context_boost={'aws': 1.2, 'azure': 1.2}
            ),
            'search_engine': IntegrationPattern(
                pattern=r'\b(?:search\s+engine|full\s*text\s+search|elasticsearch|solr|indexing)\b',
                technologies=['Elasticsearch', 'Apache Solr', 'Amazon OpenSearch', 'Azure Cognitive Search', 'Algolia'],
                confidence_multiplier=0.8,
                context_boost={'aws': 1.2, 'azure': 1.2}
            ),
            'authentication': IntegrationPattern(
                pattern=r'\b(?:authentication|auth|oauth|jwt|saml|sso|identity)\b',
                technologies=['Auth0', 'Okta', 'AWS Cognito', 'Azure Active Directory', 'Firebase Auth', 'Keycloak'],
                confidence_multiplier=0.7,
                context_boost={'aws': 1.3, 'azure': 1.3, 'firebase': 1.2}
            ),
            'monitoring': IntegrationPattern(
                pattern=r'\b(?:monitoring|observability|logging|tracing|metrics|apm)\b',
                technologies=['Prometheus', 'Grafana', 'Jaeger', 'Zipkin', 'New Relic', 'Datadog', 'Elastic APM'],
                confidence_multiplier=0.7
            ),
            'ci_cd': IntegrationPattern(
                pattern=r'\b(?:ci\/cd|continuous\s+integration|continuous\s+deployment|pipeline|build\s+automation)\b',
                technologies=['GitHub Actions', 'Jenkins', 'GitLab CI', 'CircleCI', 'Azure DevOps', 'AWS CodePipeline'],
                confidence_multiplier=0.6,
                context_boost={'github': 1.3, 'gitlab': 1.2, 'aws': 1.2, 'azure': 1.2}
            ),
            'machine_learning': IntegrationPattern(
                pattern=r'\b(?:machine\s+learning|ml|artificial\s+intelligence|ai|deep\s+learning|neural\s+network|model\s+training)\b',
                technologies=['TensorFlow', 'PyTorch', 'Scikit-learn', 'Hugging Face', 'MLflow', 'Kubeflow', 'AWS SageMaker', 'Azure ML'],
                confidence_multiplier=0.7,
                context_boost={'python': 1.4, 'aws': 1.2, 'azure': 1.2}
            )
        }
        
        # NER-like entity patterns for technology recognition
        self.ner_patterns = {
            'TECH_NAME': [
                # Capitalized technology names
                re.compile(r'\b[A-Z][a-zA-Z]*(?:\.[A-Z][a-zA-Z]*)*\b'),
                # Technology names with numbers/versions
                re.compile(r'\b[A-Z][a-zA-Z]*\d+(?:\.\d+)*\b'),
                # Hyphenated technology names
                re.compile(r'\b[A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)+\b'),
                # Dot-separated names (like Vue.js, Node.js)
                re.compile(r'\b[A-Z][a-zA-Z]*(?:\.[a-z]+)+\b')
            ],
            'CLOUD_SERVICE': [
                # AWS service patterns
                re.compile(r'\b(?:Amazon|AWS)\s+[A-Z][a-zA-Z\s]+\b'),
                # Azure service patterns
                re.compile(r'\b(?:Azure|Microsoft)\s+[A-Z][a-zA-Z\s]+\b'),
                # GCP service patterns
                re.compile(r'\b(?:Google\s+Cloud|GCP)\s+[A-Z][a-zA-Z\s]+\b')
            ],
            'DATABASE': [
                re.compile(r'\b\w+(?:DB|SQL|Store|Base)\b', re.IGNORECASE)
            ],
            'FRAMEWORK': [
                re.compile(r'\b\w+(?:JS|Framework|Library)\b', re.IGNORECASE)
            ]
        }
    
    def extract_technologies(self, text: str) -> List[ExplicitTech]:
        """Extract technologies from text using various methods.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted technologies with metadata
        """
        if not text:
            return []
        
        technologies = []
        
        # Extract using alias matching
        alias_techs = self._extract_by_aliases(text)
        technologies.extend(alias_techs)
        
        # Extract using pattern matching
        pattern_techs = self._extract_by_patterns(text)
        technologies.extend(pattern_techs)
        
        # Extract using NER-like approach (simplified)
        ner_techs = self._extract_by_ner(text)
        technologies.extend(ner_techs)
        
        # Extract integration patterns
        integration_techs = self._extract_integration_technologies(text)
        technologies.extend(integration_techs)
        
        # Deduplicate and enhance with context
        deduplicated = self._deduplicate_and_enhance(technologies, text)
        
        self.logger.debug(f"Extracted {len(deduplicated)} technologies using multiple methods")
        return deduplicated
    
    def resolve_aliases(self, tech_name: str) -> Optional[str]:
        """Resolve technology aliases to canonical names with enhanced matching.
        
        Args:
            tech_name: Technology name to resolve
            
        Returns:
            Canonical name if found, None otherwise
        """
        if not tech_name:
            return None
            
        tech_lower = tech_name.lower().strip()
        
        # 1. Exact match
        if tech_lower in self.technology_aliases:
            return self.technology_aliases[tech_lower].canonical_name
        
        # 2. Handle common abbreviations and informal names
        resolved = self._resolve_abbreviations(tech_lower)
        if resolved:
            return resolved
        
        # 3. Try fuzzy matching for compound names
        resolved = self._fuzzy_match_aliases(tech_lower)
        if resolved:
            return resolved
        
        # 4. Try partial matching for compound names
        for alias, mapping in self.technology_aliases.items():
            if alias in tech_lower or tech_lower in alias:
                # Ensure it's a meaningful match (not just a substring)
                if len(alias) >= 3 and (len(alias) / len(tech_lower) >= 0.5 or len(tech_lower) / len(alias) >= 0.5):
                    return mapping.canonical_name
        
        return None
    
    def _resolve_abbreviations(self, tech_name: str) -> Optional[str]:
        """Resolve common abbreviations and informal names.
        
        Args:
            tech_name: Technology name to resolve
            
        Returns:
            Canonical name if found, None otherwise
        """
        # Common abbreviations and informal names
        abbreviation_map = {
            # Programming languages
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'py': 'Python',
            'rb': 'Ruby',
            'cs': 'C#',
            'cpp': 'C++',
            'c++': 'C++',
            'go': 'Go',
            
            # Cloud services
            'aws': 'Amazon Web Services',
            'gcp': 'Google Cloud Platform',
            'az': 'Microsoft Azure',
            
            # Databases
            'pg': 'PostgreSQL',
            'mysql': 'MySQL',
            'mongo': 'MongoDB',
            'es': 'Elasticsearch',
            
            # Container technologies
            'k8s': 'Kubernetes',
            'kube': 'Kubernetes',
            
            # Web technologies
            'html': 'HTML',
            'css': 'CSS',
            'xml': 'XML',
            'json': 'JSON',
            'yaml': 'YAML',
            'yml': 'YAML',
            
            # Protocols and standards
            'http': 'HTTP',
            'https': 'HTTPS',
            'tcp': 'TCP',
            'udp': 'UDP',
            'ssh': 'SSH',
            'ftp': 'FTP',
            'smtp': 'SMTP',
            
            # Development tools
            'git': 'Git',
            'npm': 'npm',
            'pip': 'pip',
            'cli': 'Command Line Interface',
            'api': 'Application Programming Interface',
            'sdk': 'Software Development Kit',
            'ide': 'Integrated Development Environment',
            
            # AI/ML
            'ml': 'Machine Learning',
            'ai': 'Artificial Intelligence',
            'dl': 'Deep Learning',
            'nlp': 'Natural Language Processing',
            'cv': 'Computer Vision',
            'nn': 'Neural Network',
            'cnn': 'Convolutional Neural Network',
            'rnn': 'Recurrent Neural Network',
            'lstm': 'Long Short-Term Memory',
            'gpt': 'Generative Pre-trained Transformer',
            
            # Architecture patterns
            'mvc': 'Model-View-Controller',
            'mvp': 'Model-View-Presenter',
            'mvvm': 'Model-View-ViewModel',
            'spa': 'Single Page Application',
            'pwa': 'Progressive Web Application',
            'soa': 'Service-Oriented Architecture',
            'rest': 'Representational State Transfer',
            'soap': 'Simple Object Access Protocol',
            'grpc': 'gRPC',
            
            # Database types
            'sql': 'Structured Query Language',
            'nosql': 'NoSQL',
            'rdbms': 'Relational Database Management System',
            'oltp': 'Online Transaction Processing',
            'olap': 'Online Analytical Processing',
            
            # Infrastructure
            'vm': 'Virtual Machine',
            'os': 'Operating System',
            'dns': 'Domain Name System',
            'cdn': 'Content Delivery Network',
            'lb': 'Load Balancer',
            'vpn': 'Virtual Private Network',
            'ssl': 'Secure Sockets Layer',
            'tls': 'Transport Layer Security'
        }
        
        if tech_name in abbreviation_map:
            canonical = abbreviation_map[tech_name]
            # Check if we have this in our aliases
            if canonical.lower() in self.technology_aliases:
                return self.technology_aliases[canonical.lower()].canonical_name
            return canonical
        
        return None
    
    def _fuzzy_match_aliases(self, tech_name: str) -> Optional[str]:
        """Perform fuzzy matching for technology aliases.
        
        Args:
            tech_name: Technology name to match
            
        Returns:
            Canonical name if found, None otherwise
        """
        # Simple fuzzy matching based on edit distance and common patterns
        best_match = None
        best_score = 0.0
        min_similarity = 0.7  # Minimum similarity threshold
        
        for alias, mapping in self.technology_aliases.items():
            # Calculate similarity score
            similarity = self._calculate_similarity(tech_name, alias)
            
            if similarity >= min_similarity and similarity > best_score:
                best_score = similarity
                best_match = mapping.canonical_name
        
        return best_match
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Simple similarity calculation based on common characters and length
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        if s1 == s2:
            return 1.0
        
        # Calculate character overlap
        s1_chars = set(s1)
        s2_chars = set(s2)
        
        intersection = len(s1_chars.intersection(s2_chars))
        union = len(s1_chars.union(s2_chars))
        
        if union == 0:
            return 0.0
        
        char_similarity = intersection / union
        
        # Calculate length similarity
        max_len = max(len(s1), len(s2))
        min_len = min(len(s1), len(s2))
        length_similarity = min_len / max_len if max_len > 0 else 0.0
        
        # Calculate substring similarity
        substring_similarity = 0.0
        if s1 in s2 or s2 in s1:
            substring_similarity = min_len / max_len
        
        # Weighted combination
        similarity = (char_similarity * 0.4 + length_similarity * 0.3 + substring_similarity * 0.3)
        
        return similarity
    
    def calculate_extraction_confidence(self, 
                                     tech: str, 
                                     method: ExtractionMethod, 
                                     context: str) -> float:
        """Calculate enhanced confidence score for extracted technology.
        
        Args:
            tech: Technology name
            method: Extraction method used
            context: Surrounding context
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence by extraction method
        base_confidence = {
            ExtractionMethod.EXPLICIT_MENTION: 1.0,
            ExtractionMethod.NER_EXTRACTION: 0.8,
            ExtractionMethod.PATTERN_MATCHING: 0.7,
            ExtractionMethod.CONTEXT_INFERENCE: 0.6,
            ExtractionMethod.ALIAS_RESOLUTION: 0.9,
            ExtractionMethod.INTEGRATION_PATTERN: 0.5
        }.get(method, 0.5)
        
        context_lower = context.lower()
        tech_lower = tech.lower()
        
        # 1. Boost confidence for known aliases
        if tech_lower in self.technology_aliases:
            alias_info = self.technology_aliases[tech_lower]
            base_confidence = max(base_confidence, alias_info.confidence)
            
            # Additional boost for ecosystem-specific context
            if alias_info.ecosystem and alias_info.ecosystem in context_lower:
                base_confidence = min(base_confidence * 1.2, 1.0)
        
        # 2. Context-based confidence adjustments
        context_boosts = self._calculate_context_confidence_boosts(tech, context_lower)
        for boost in context_boosts:
            base_confidence = min(base_confidence + boost, 1.0)
        
        # 3. Reduce confidence for ambiguous terms without proper context
        ambiguous_terms = {
            'lambda': ['aws', 'amazon', 'serverless'],
            'functions': ['azure', 'google', 'cloud', 'serverless'],
            'storage': ['cloud', 'aws', 'azure', 'google', 'object', 'blob'],
            'database': ['sql', 'nosql', 'relational', 'document'],
            'api': ['rest', 'graphql', 'web', 'service'],
            'service': ['web', 'micro', 'cloud', 'api'],
            'engine': ['search', 'database', 'compute', 'analytics'],
            'platform': ['cloud', 'development', 'deployment']
        }
        
        if tech_lower in ambiguous_terms:
            required_context = ambiguous_terms[tech_lower]
            if not any(ctx in context_lower for ctx in required_context):
                base_confidence *= 0.6  # Significant reduction for ambiguous terms without context
        
        # 4. Boost confidence for technology-specific context patterns
        tech_context_patterns = {
            'fastapi': ['async', 'python', 'rest', 'api', 'web'],
            'django': ['python', 'web', 'framework', 'orm'],
            'react': ['javascript', 'frontend', 'component', 'jsx'],
            'kubernetes': ['container', 'orchestration', 'k8s', 'cluster'],
            'docker': ['container', 'image', 'containerize', 'deployment'],
            'postgresql': ['database', 'sql', 'relational', 'postgres'],
            'redis': ['cache', 'memory', 'session', 'key-value'],
            'elasticsearch': ['search', 'index', 'analytics', 'elastic']
        }
        
        for tech_key, context_keywords in tech_context_patterns.items():
            if tech_key in tech_lower:
                matching_keywords = sum(1 for keyword in context_keywords if keyword in context_lower)
                if matching_keywords > 0:
                    boost = min(matching_keywords * 0.05, 0.15)  # Up to 15% boost
                    base_confidence = min(base_confidence + boost, 1.0)
        
        # 5. Version-specific confidence boost
        if re.search(r'\d+(?:\.\d+)*', tech):
            base_confidence = min(base_confidence + 0.05, 1.0)  # Slight boost for versioned technologies
        
        # 6. Ecosystem consistency boost
        ecosystem_boost = self._calculate_ecosystem_consistency_boost(tech, context_lower)
        base_confidence = min(base_confidence + ecosystem_boost, 1.0)
        
        # 7. Frequency-based confidence (technologies mentioned multiple times)
        frequency_boost = self._calculate_frequency_boost(tech, context_lower)
        base_confidence = min(base_confidence + frequency_boost, 1.0)
        
        return min(base_confidence, 1.0)
    
    def _calculate_context_confidence_boosts(self, tech: str, context: str) -> List[float]:
        """Calculate context-based confidence boosts.
        
        Args:
            tech: Technology name
            context: Context text (lowercase)
            
        Returns:
            List of confidence boost values
        """
        boosts = []
        
        # Technology category context boosts
        category_contexts = {
            'database': ['store', 'persist', 'query', 'data', 'record', 'table', 'schema'],
            'frontend': ['ui', 'interface', 'component', 'view', 'render', 'display'],
            'backend': ['server', 'api', 'service', 'endpoint', 'business', 'logic'],
            'cloud': ['deploy', 'scale', 'infrastructure', 'serverless', 'managed'],
            'container': ['deploy', 'orchestrate', 'scale', 'cluster', 'pod'],
            'messaging': ['queue', 'publish', 'subscribe', 'event', 'message', 'stream'],
            'monitoring': ['log', 'metric', 'trace', 'alert', 'dashboard', 'observe'],
            'ai': ['model', 'train', 'predict', 'inference', 'neural', 'learning']
        }
        
        tech_lower = tech.lower()
        
        # Check if technology belongs to a category and context matches
        for category, keywords in category_contexts.items():
            if any(cat_word in tech_lower for cat_word in [category, category[:-1]]):  # e.g., 'database' or 'databas'
                matching_keywords = sum(1 for keyword in keywords if keyword in context)
                if matching_keywords > 0:
                    boosts.append(min(matching_keywords * 0.03, 0.1))  # Up to 10% boost per category
        
        # Specific technology mention patterns
        if any(pattern in context for pattern in ['using', 'with', 'via', 'through', 'integrate']):
            boosts.append(0.05)
        
        if any(pattern in context for pattern in ['implement', 'build', 'develop', 'create']):
            boosts.append(0.03)
        
        return boosts
    
    def _calculate_ecosystem_consistency_boost(self, tech: str, context: str) -> float:
        """Calculate ecosystem consistency boost.
        
        Args:
            tech: Technology name
            context: Context text (lowercase)
            
        Returns:
            Confidence boost value
        """
        # Define ecosystem technologies
        ecosystems = {
            'aws': ['amazon', 'aws', 's3', 'lambda', 'ec2', 'rds', 'dynamodb', 'sns', 'sqs', 'comprehend', 'bedrock', 'connect'],
            'azure': ['azure', 'microsoft', 'cosmos', 'functions', 'service bus', 'blob storage'],
            'gcp': ['google', 'gcp', 'bigquery', 'firestore', 'cloud functions', 'pub/sub'],
            'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy', 'tensorflow', 'pytorch'],
            'javascript': ['react', 'vue', 'angular', 'express', 'node'],
            'java': ['spring', 'hibernate', 'maven', 'gradle']
        }
        
        tech_lower = tech.lower()
        
        for ecosystem, technologies in ecosystems.items():
            # Check if current technology belongs to this ecosystem
            if any(eco_tech in tech_lower for eco_tech in technologies):
                # Check if context mentions other technologies from the same ecosystem
                other_techs_in_context = sum(1 for eco_tech in technologies 
                                           if eco_tech != tech_lower and eco_tech in context)
                if other_techs_in_context > 0:
                    return min(other_techs_in_context * 0.05, 0.15)  # Up to 15% boost
        
        return 0.0
    
    def _calculate_frequency_boost(self, tech: str, context: str) -> float:
        """Calculate frequency-based confidence boost.
        
        Args:
            tech: Technology name
            context: Context text (lowercase)
            
        Returns:
            Confidence boost value
        """
        tech_lower = tech.lower()
        
        # Count exact mentions of the technology name
        mentions = len(re.findall(r'\b' + re.escape(tech_lower) + r'\b', context))
        
        # Check for alias mentions - but only if the tech name itself is an alias
        # Find the alias that maps to this tech
        for alias, mapping in self.technology_aliases.items():
            if mapping.canonical_name.lower() == tech_lower and alias != tech_lower:
                alias_mentions = len(re.findall(r'\b' + re.escape(alias) + r'\b', context))
                mentions += alias_mentions
        
        # Boost confidence based on frequency (diminishing returns)
        if mentions > 1:
            return min((mentions - 1) * 0.02, 0.08)  # Up to 8% boost for multiple mentions
        
        return 0.0
    
    def _extract_by_aliases(self, text: str) -> List[ExplicitTech]:
        """Extract technologies using alias matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted technologies
        """
        technologies = []
        text_lower = text.lower()
        
        for alias, mapping in self.technology_aliases.items():
            # Create regex pattern for the alias
            pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(text)
            
            for match in matches:
                # Check if context is required
                if mapping.context_required:
                    context_window = text[max(0, match.start()-100):match.end()+100]
                    if not self._has_relevant_context(alias, context_window):
                        continue
                
                confidence = self.calculate_extraction_confidence(
                    alias, ExtractionMethod.ALIAS_RESOLUTION, 
                    text[max(0, match.start()-50):match.end()+50]
                )
                
                tech = ExplicitTech(
                    name=mapping.canonical_name,
                    canonical_name=mapping.canonical_name,
                    confidence=confidence,
                    extraction_method=ExtractionMethod.ALIAS_RESOLUTION,
                    source_text=match.group(),
                    position=match.start(),
                    aliases=[alias],
                    context=text[max(0, match.start()-50):match.end()+50]
                )
                technologies.append(tech)
        
        return technologies
    
    def _extract_by_patterns(self, text: str) -> List[ExplicitTech]:
        """Extract technologies using pattern matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted technologies
        """
        technologies = []
        
        for pattern in self.tech_name_patterns:
            matches = pattern.finditer(text)
            
            for match in matches:
                # Extract the technology name
                tech_name = match.group(1) if match.groups() else match.group()
                tech_name = tech_name.strip()
                
                if len(tech_name) < 2:  # Skip very short matches
                    continue
                
                # Resolve to canonical name if possible
                canonical_name = self.resolve_aliases(tech_name)
                if not canonical_name:
                    canonical_name = tech_name
                
                confidence = self.calculate_extraction_confidence(
                    tech_name, ExtractionMethod.PATTERN_MATCHING,
                    text[max(0, match.start()-50):match.end()+50]
                )
                
                tech = ExplicitTech(
                    name=canonical_name,
                    canonical_name=canonical_name,
                    confidence=confidence,
                    extraction_method=ExtractionMethod.PATTERN_MATCHING,
                    source_text=match.group(),
                    position=match.start(),
                    context=text[max(0, match.start()-50):match.end()+50]
                )
                technologies.append(tech)
        
        return technologies
    
    def _extract_by_ner(self, text: str) -> List[ExplicitTech]:
        """Extract technologies using enhanced NER-like approach.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted technologies
        """
        technologies = []
        
        # Enhanced NER-like extraction with multiple entity types
        for entity_type, patterns in self.ner_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                
                for match in matches:
                    entity_text = match.group().strip()
                    
                    # Skip very short matches or common words
                    if len(entity_text) < 2 or self._is_common_word(entity_text):
                        continue
                    
                    # Check if it's a known technology
                    canonical_name = self.resolve_aliases(entity_text)
                    if canonical_name:
                        confidence = self.calculate_extraction_confidence(
                            entity_text, ExtractionMethod.NER_EXTRACTION,
                            text[max(0, match.start()-50):match.end()+50]
                        )
                        
                        tech = ExplicitTech(
                            name=canonical_name,
                            canonical_name=canonical_name,
                            confidence=confidence,
                            extraction_method=ExtractionMethod.NER_EXTRACTION,
                            source_text=entity_text,
                            position=match.start(),
                            context=text[max(0, match.start()-50):match.end()+50]
                        )
                        technologies.append(tech)
                    else:
                        # For unknown entities, check if they look like technology names
                        if self._looks_like_technology(entity_text, entity_type):
                            confidence = self._calculate_unknown_tech_confidence(entity_text, entity_type, text)
                            
                            tech = ExplicitTech(
                                name=entity_text,
                                canonical_name=entity_text,
                                confidence=confidence,
                                extraction_method=ExtractionMethod.NER_EXTRACTION,
                                source_text=entity_text,
                                position=match.start(),
                                context=text[max(0, match.start()-50):match.end()+50]
                            )
                            technologies.append(tech)
        
        return technologies
    
    def _is_common_word(self, word: str) -> bool:
        """Check if a word is a common non-technology word.
        
        Args:
            word: Word to check
            
        Returns:
            True if it's a common word
        """
        common_words = {
            'the', 'and', 'or', 'but', 'for', 'with', 'this', 'that', 'these', 'those',
            'a', 'an', 'in', 'on', 'at', 'by', 'from', 'to', 'of', 'as', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must',
            'shall', 'need', 'want', 'like', 'get', 'got', 'make', 'made', 'take',
            'taken', 'give', 'given', 'go', 'went', 'come', 'came', 'see', 'saw',
            'know', 'knew', 'think', 'thought', 'say', 'said', 'tell', 'told',
            'use', 'used', 'work', 'worked', 'call', 'called', 'find', 'found',
            'look', 'looked', 'ask', 'asked', 'try', 'tried', 'seem', 'seemed',
            'feel', 'felt', 'leave', 'left', 'put', 'keep', 'kept', 'let', 'begin',
            'began', 'help', 'helped', 'show', 'showed', 'hear', 'heard', 'play',
            'played', 'run', 'ran', 'move', 'moved', 'live', 'lived', 'believe',
            'believed', 'hold', 'held', 'bring', 'brought', 'happen', 'happened',
            'write', 'wrote', 'provide', 'provided', 'sit', 'sat', 'stand', 'stood',
            'lose', 'lost', 'pay', 'paid', 'meet', 'met', 'include', 'included',
            'continue', 'continued', 'set', 'expect', 'expected', 'build', 'built',
            'remain', 'remained', 'fall', 'fell', 'reach', 'reached', 'kill', 'killed',
            'raise', 'raised', 'pass', 'passed', 'sell', 'sold', 'require', 'required',
            'report', 'reported', 'decide', 'decided', 'pull', 'pulled'
        }
        return word.lower() in common_words
    
    def _looks_like_technology(self, text: str, entity_type: str) -> bool:
        """Check if text looks like a technology name.
        
        Args:
            text: Text to check
            entity_type: Type of entity detected
            
        Returns:
            True if it looks like a technology
        """
        # Skip very generic terms
        generic_terms = {'system', 'service', 'platform', 'application', 'software', 'tool', 'the', 'and', 'or'}
        if text.lower() in generic_terms:
            return False
        
        # Technology name indicators
        tech_indicators = [
            # Common technology suffixes
            r'(?:js|py|sql|db|api|sdk|cli|ui|ml|ai|os|vm)$',
            # Version patterns
            r'\d+(?:\.\d+)*$',
            # Framework/library patterns
            r'(?:framework|library|engine|platform|service|tool|kit)$',
            # Camel case patterns
            r'^[A-Z][a-z]+[A-Z]',
            # Dot notation
            r'\.',
            # Hyphenated names
            r'-'
        ]
        
        text_lower = text.lower()
        
        # Check for technology indicators
        for pattern in tech_indicators:
            if re.search(pattern, text_lower):
                return True
        
        # Entity type specific checks
        if entity_type == 'TECH_NAME':
            # Must be capitalized and not a common word
            return text[0].isupper() and not self._is_common_word(text) and text.lower() not in generic_terms
        elif entity_type == 'CLOUD_SERVICE':
            return True  # Cloud services are likely technologies
        elif entity_type in ['DATABASE', 'FRAMEWORK']:
            return True  # Database and framework patterns are likely technologies
        
        return False
    
    def _calculate_unknown_tech_confidence(self, text: str, entity_type: str, context: str) -> float:
        """Calculate confidence for unknown technology names.
        
        Args:
            text: Technology name
            entity_type: Type of entity
            context: Surrounding context
            
        Returns:
            Confidence score
        """
        base_confidence = {
            'TECH_NAME': 0.4,
            'CLOUD_SERVICE': 0.6,
            'DATABASE': 0.5,
            'FRAMEWORK': 0.5
        }.get(entity_type, 0.3)
        
        # Boost confidence based on context
        context_lower = context.lower()
        
        # Technology context indicators
        tech_context_patterns = [
            r'\b(?:using|with|via|through|integrate|implement|deploy|build|develop)\b',
            r'\b(?:api|sdk|library|framework|service|platform|tool|system)\b',
            r'\b(?:database|storage|cache|search|queue|stream)\b',
            r'\b(?:frontend|backend|server|client|web|mobile|desktop)\b'
        ]
        
        for pattern in tech_context_patterns:
            if re.search(pattern, context_lower):
                base_confidence = min(base_confidence + 0.1, 0.8)
        
        # Reduce confidence for very generic terms
        generic_terms = ['system', 'service', 'platform', 'tool', 'application', 'software']
        if text.lower() in generic_terms:
            base_confidence *= 0.5
        
        return base_confidence
    
    def _extract_integration_technologies(self, text: str) -> List[ExplicitTech]:
        """Extract technologies based on enhanced integration patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of inferred technologies
        """
        technologies = []
        text_lower = text.lower()
        
        for pattern_name, integration_pattern in self.integration_patterns.items():
            pattern = re.compile(integration_pattern.pattern, re.IGNORECASE)
            
            if pattern.search(text):
                # Get context for technology selection
                context_scores = self._calculate_context_scores(text_lower, integration_pattern.context_boost or {})
                
                for tech_name in integration_pattern.technologies:
                    # Calculate base confidence
                    base_confidence = self.calculate_extraction_confidence(
                        tech_name, ExtractionMethod.INTEGRATION_PATTERN, text
                    )
                    
                    # Apply pattern-specific confidence multiplier
                    confidence = base_confidence * integration_pattern.confidence_multiplier
                    
                    # Apply context boost
                    for context_key, boost in context_scores.items():
                        if boost > 1.0:
                            confidence = min(confidence * boost, 1.0)
                    
                    # Prioritize technologies based on detected programming language or ecosystem
                    confidence = self._apply_ecosystem_boost(tech_name, text_lower, confidence)
                    
                    tech = ExplicitTech(
                        name=tech_name,
                        canonical_name=tech_name,
                        confidence=confidence,
                        extraction_method=ExtractionMethod.INTEGRATION_PATTERN,
                        source_text=pattern_name,
                        context=f"Inferred from {pattern_name} pattern with context boost"
                    )
                    technologies.append(tech)
        
        return technologies
    
    def _calculate_context_scores(self, text: str, context_boost: Dict[str, float]) -> Dict[str, float]:
        """Calculate context scores for technology selection.
        
        Args:
            text: Text to analyze (lowercase)
            context_boost: Context boost configuration
            
        Returns:
            Dictionary of context scores
        """
        scores = {}
        
        for context_key, boost_value in context_boost.items():
            if context_key in text:
                scores[context_key] = boost_value
        
        return scores
    
    def _apply_ecosystem_boost(self, tech_name: str, text: str, base_confidence: float) -> float:
        """Apply ecosystem-specific confidence boost.
        
        Args:
            tech_name: Technology name
            text: Text context (lowercase)
            base_confidence: Base confidence score
            
        Returns:
            Adjusted confidence score
        """
        # Ecosystem mappings
        ecosystem_mappings = {
            'python': ['FastAPI', 'Django', 'Flask', 'SQLAlchemy', 'Celery', 'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch'],
            'javascript': ['Express.js', 'React', 'Vue.js', 'Angular', 'Node.js', 'Socket.IO', 'Sequelize', 'TypeORM'],
            'typescript': ['Express.js', 'React', 'Angular', 'Node.js', 'TypeORM', 'NestJS'],
            'java': ['Spring Boot', 'Spring Framework', 'Hibernate', 'Apache Kafka', 'Elasticsearch'],
            'c#': ['ASP.NET', 'ASP.NET Core', 'Entity Framework', 'SignalR'],
            'go': ['Gin', 'Echo', 'GORM', 'Kubernetes'],
            'rust': ['Actix', 'Rocket', 'Tokio'],
            'php': ['Laravel', 'Symfony', 'CodeIgniter'],
            'ruby': ['Ruby on Rails', 'Sinatra'],
            'aws': ['Amazon S3', 'AWS Lambda', 'Amazon RDS', 'Amazon SQS', 'Amazon SNS', 'AWS Bedrock', 'Amazon Connect'],
            'azure': ['Azure Functions', 'Azure Cosmos DB', 'Azure Service Bus', 'Azure Blob Storage'],
            'gcp': ['Google Cloud Functions', 'Google BigQuery', 'Google Cloud Pub/Sub', 'Google Cloud Storage']
        }
        
        confidence = base_confidence
        
        for ecosystem, technologies in ecosystem_mappings.items():
            if ecosystem in text and tech_name in technologies:
                confidence = min(confidence * 1.3, 1.0)  # 30% boost for ecosystem match
                break
        
        return confidence
    
    def _has_relevant_context(self, alias: str, context: str) -> bool:
        """Check if the context is relevant for the given alias.
        
        Args:
            alias: Technology alias
            context: Context window
            
        Returns:
            True if context is relevant
        """
        context_lower = context.lower()
        
        # Context requirements for ambiguous terms
        context_requirements = {
            'lambda': ['aws', 'amazon', 'serverless'],  # Removed 'function' to be more strict
            'functions': ['azure', 'google', 'cloud', 'serverless'],
            'storage': ['cloud', 'aws', 'azure', 'google', 'object'],
            'connect': ['aws', 'amazon', 'contact', 'center', 'call']
        }
        
        if alias in context_requirements:
            required_terms = context_requirements[alias]
            return any(term in context_lower for term in required_terms)
        
        return True
    
    def _deduplicate_and_enhance(self, technologies: List[ExplicitTech], text: str) -> List[ExplicitTech]:
        """Deduplicate technologies and enhance with additional context.
        
        Args:
            technologies: List of extracted technologies
            text: Original text for context enhancement
            
        Returns:
            Deduplicated and enhanced list of technologies
        """
        # Group by canonical name
        tech_groups = {}
        for tech in technologies:
            key = tech.canonical_name or tech.name
            if key not in tech_groups:
                tech_groups[key] = []
            tech_groups[key].append(tech)
        
        # Select best technology from each group
        deduplicated = []
        for tech_list in tech_groups.values():
            # Sort by confidence and select the best one
            best_tech = max(tech_list, key=lambda t: t.confidence)
            
            # Merge aliases from all instances
            all_aliases = set()
            for tech in tech_list:
                all_aliases.update(tech.aliases)
                if tech.source_text and tech.source_text != best_tech.name:
                    all_aliases.add(tech.source_text)
            
            best_tech.aliases = list(all_aliases)
            deduplicated.append(best_tech)
        
        return deduplicated