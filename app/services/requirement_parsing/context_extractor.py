"""Technology context extractor for building comprehensive technology context."""

from typing import Dict, List, Optional, Tuple

from .base import (
    ContextExtractor, ParsedRequirements, TechContext, ContextClues,
    DomainContext
)
from app.utils.imports import require_service

try:
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


class TechnologyContextExtractor(ContextExtractor):
    """Technology context extractor with priority-based organization."""
    
    def __init__(self):
        """Initialize technology context extractor."""
        try:
            self.logger = require_service('logger', context='TechnologyContextExtractor')
        except Exception:
            # Fallback to basic logging for testing
            import logging
            self.logger = logging.getLogger('TechnologyContextExtractor')
        
        # Initialize ecosystem mappings
        self._init_ecosystem_mappings()
        self._init_domain_preferences()
        self._init_technology_aliases()
        
        # Fuzzy matching threshold
        self.fuzzy_threshold = 80
    
    def _init_ecosystem_mappings(self) -> None:
        """Initialize technology ecosystem mappings."""
        self.ecosystem_mappings = {
            'aws': {
                'Amazon Connect', 'Amazon Connect SDK', 'AWS Lambda', 'Amazon S3',
                'AWS Comprehend', 'AWS Bedrock', 'Amazon DynamoDB', 'Amazon RDS',
                'Amazon EC2', 'Amazon ECS', 'Amazon EKS', 'Amazon CloudWatch',
                'Amazon SNS', 'Amazon SQS', 'AWS API Gateway', 'AWS Step Functions',
                'Amazon Kinesis', 'AWS Glue', 'Amazon Redshift', 'AWS CloudFormation'
            },
            'azure': {
                'Azure Cognitive Services', 'Azure App Service', 'Azure Functions',
                'Azure Cosmos DB', 'Azure SQL Database', 'Azure Storage Account',
                'Azure Service Bus', 'Azure Event Grid', 'Azure Monitor',
                'Azure Key Vault', 'Azure Active Directory', 'Azure DevOps'
            },
            'gcp': {
                'Google Cloud Functions', 'Google Cloud Run', 'Google BigQuery',
                'Google Firestore', 'Google Cloud Storage', 'Google Pub/Sub',
                'Google Cloud Monitoring', 'Google Cloud IAM', 'Google Kubernetes Engine'
            },
            'open_source': {
                'FastAPI', 'Django', 'Flask', 'React', 'Vue.js', 'Angular',
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
                'Docker', 'Kubernetes', 'Prometheus', 'Grafana', 'Apache Kafka',
                'RabbitMQ', 'Nginx', 'Apache HTTP Server', 'Jenkins'
            }
        }
    
    def _init_domain_preferences(self) -> None:
        """Initialize domain-specific technology preferences."""
        self.domain_preferences = {
            'data_processing': {
                'high_priority': ['Pandas', 'NumPy', 'Apache Spark', 'Apache Kafka'],
                'medium_priority': ['Elasticsearch', 'Redis', 'PostgreSQL'],
                'ecosystems': ['aws', 'gcp']  # Better big data support
            },
            'web_api': {
                'high_priority': ['FastAPI', 'Express.js', 'Spring Boot', 'Django REST Framework'],
                'medium_priority': ['Nginx', 'Redis', 'PostgreSQL'],
                'ecosystems': ['aws', 'azure', 'gcp']
            },
            'ml_ai': {
                'high_priority': ['OpenAI API', 'Hugging Face Transformers', 'LangChain', 'PyTorch', 'TensorFlow'],
                'medium_priority': ['Pandas', 'NumPy', 'Scikit-learn'],
                'ecosystems': ['aws', 'gcp']  # Better ML support
            },
            'automation': {
                'high_priority': ['Celery', 'Apache Kafka', 'RabbitMQ', 'Jenkins'],
                'medium_priority': ['Redis', 'PostgreSQL', 'Docker'],
                'ecosystems': ['aws', 'azure']
            },
            'monitoring': {
                'high_priority': ['Prometheus', 'Grafana', 'Jaeger', 'Elasticsearch'],
                'medium_priority': ['Redis', 'InfluxDB'],
                'ecosystems': ['aws', 'gcp']
            },
            'security': {
                'high_priority': ['HashiCorp Vault', 'OAuth 2.0', 'JWT'],
                'medium_priority': ['Redis', 'PostgreSQL'],
                'ecosystems': ['aws', 'azure']  # Better security services
            }
        }
    
    def build_context(self, parsed_req: ParsedRequirements) -> TechContext:
        """Build comprehensive technology context from parsed requirements.
        
        Args:
            parsed_req: Parsed requirements
            
        Returns:
            TechContext object with prioritized technologies
        """
        self.logger.info("Building technology context from parsed requirements")
        
        # Extract explicit technologies with confidence scores
        explicit_technologies = {}
        for tech in parsed_req.explicit_technologies:
            canonical_name = tech.canonical_name or tech.name
            
            # Try to resolve using fuzzy matching if not already canonical
            if not tech.canonical_name:
                fuzzy_result = self.resolve_alias_with_fuzzy_matching(tech.name, tech.context)
                if fuzzy_result:
                    canonical_name, fuzzy_confidence = fuzzy_result
                    # Adjust confidence based on fuzzy matching confidence
                    tech.confidence = min(tech.confidence * fuzzy_confidence, 1.0)
            
            explicit_technologies[canonical_name] = tech.confidence
        
        # Build contextual technologies from clues
        contextual_technologies = self._build_contextual_technologies(
            parsed_req.context_clues, parsed_req.domain_context
        )
        
        # Infer ecosystem preference
        ecosystem_preference = self.infer_ecosystem_preference(parsed_req.context_clues)
        
        # Build integration requirements
        integration_requirements = self._build_integration_requirements(
            parsed_req.context_clues, parsed_req.constraints
        )
        
        # Calculate priority weights
        priority_weights = self._calculate_priority_weights(
            explicit_technologies, contextual_technologies, parsed_req.domain_context
        )
        
        context = TechContext(
            explicit_technologies=explicit_technologies,
            contextual_technologies=contextual_technologies,
            domain_context=parsed_req.domain_context,
            ecosystem_preference=ecosystem_preference,
            integration_requirements=integration_requirements,
            banned_tools=parsed_req.constraints.banned_tools,
            priority_weights=priority_weights
        )
        
        self.logger.info(f"Built context with {len(explicit_technologies)} explicit technologies, "
                        f"{len(contextual_technologies)} contextual technologies, "
                        f"ecosystem preference: {ecosystem_preference}")
        
        return context
    
    def prioritize_technologies(self, context: TechContext) -> Dict[str, float]:
        """Prioritize technologies based on context and explicit mentions.
        
        Args:
            context: Technology context
            
        Returns:
            Dictionary mapping technology names to priority scores
        """
        priorities = {}
        
        # Explicit technologies get highest priority
        for tech, confidence in context.explicit_technologies.items():
            priorities[tech] = confidence * 1.0  # Priority weight 1.0
        
        # Contextual technologies get medium priority
        for tech, confidence in context.contextual_technologies.items():
            if tech not in priorities:  # Don't override explicit mentions
                base_priority = confidence * 0.8  # Priority weight 0.8
                
                # Apply ecosystem boost to contextual technologies if applicable
                if (context.ecosystem_preference and 
                    tech in self.ecosystem_mappings.get(context.ecosystem_preference, set())):
                    base_priority = min(base_priority * 1.3, 1.0)  # Increased to ensure > original
                
                priorities[tech] = base_priority
        
        # Apply ecosystem consistency boosts to explicit technologies
        if context.ecosystem_preference:
            ecosystem_techs = self.ecosystem_mappings.get(context.ecosystem_preference, set())
            for tech in context.explicit_technologies:
                if tech in ecosystem_techs and tech in priorities:
                    priorities[tech] = min(priorities[tech] * 1.3, 1.0)
        
        # Apply domain-specific boosts
        if context.domain_context.primary_domain:
            domain_prefs = self.domain_preferences.get(context.domain_context.primary_domain, {})
            
            # Boost high-priority technologies for this domain
            for tech in domain_prefs.get('high_priority', []):
                if tech in priorities:
                    priorities[tech] = min(priorities[tech] * 1.2, 1.0)
                else:
                    priorities[tech] = 0.6  # Add as medium priority
            
            # Boost medium-priority technologies for this domain
            for tech in domain_prefs.get('medium_priority', []):
                if tech in priorities:
                    priorities[tech] = min(priorities[tech] * 1.1, 1.0)
                elif tech not in priorities:
                    priorities[tech] = 0.4  # Add as low priority
        
        # Apply priority weights from context
        for tech, weight in context.priority_weights.items():
            if tech in priorities:
                priorities[tech] = min(priorities[tech] * weight, 1.0)
        
        # Remove banned technologies
        for banned_tech in context.banned_tools:
            # Remove exact matches and partial matches
            to_remove = []
            for tech in priorities:
                if (banned_tech.lower() in tech.lower() or 
                    tech.lower() in banned_tech.lower()):
                    to_remove.append(tech)
            
            for tech in to_remove:
                del priorities[tech]
                self.logger.debug(f"Removed banned technology: {tech}")
        
        self.logger.debug(f"Prioritized {len(priorities)} technologies")
        return priorities
    
    def infer_ecosystem_preference(self, context_clues: ContextClues) -> Optional[str]:
        """Infer ecosystem preference from context clues.
        
        Args:
            context_clues: Context clues from requirements
            
        Returns:
            Preferred ecosystem (aws, azure, gcp) or None
        """
        ecosystem_scores = {'aws': 0, 'azure': 0, 'gcp': 0}
        
        # Score based on cloud provider mentions
        for provider in context_clues.cloud_providers:
            if provider in ecosystem_scores:
                ecosystem_scores[provider] += 2.0
        
        # Score based on domain preferences
        for domain in context_clues.domains:
            domain_prefs = self.domain_preferences.get(domain, {})
            preferred_ecosystems = domain_prefs.get('ecosystems', [])
            for ecosystem in preferred_ecosystems:
                ecosystem_scores[ecosystem] += 0.5
        
        # Score based on deployment preferences
        for deployment in context_clues.deployment_preferences:
            if deployment == 'serverless':
                ecosystem_scores['aws'] += 2.0  # Increased to meet threshold
                ecosystem_scores['gcp'] += 1.5
                ecosystem_scores['azure'] += 1.2
            elif deployment == 'containerized':
                ecosystem_scores['gcp'] += 2.0  # Strong Kubernetes support
                ecosystem_scores['aws'] += 1.5
                ecosystem_scores['azure'] += 1.5
        
        # Find the highest scoring ecosystem
        max_score = max(ecosystem_scores.values())
        if max_score > 1.0:  # Require significant preference
            for ecosystem, score in ecosystem_scores.items():
                if score == max_score:
                    self.logger.debug(f"Inferred ecosystem preference: {ecosystem} (score: {score})")
                    return ecosystem
        
        return None
    
    def _build_contextual_technologies(self, 
                                     context_clues: ContextClues, 
                                     domain_context: DomainContext) -> Dict[str, float]:
        """Build contextual technologies from context clues.
        
        Args:
            context_clues: Context clues from requirements
            domain_context: Domain context information
            
        Returns:
            Dictionary mapping technology names to confidence scores
        """
        contextual_techs = {}
        
        # Map integration patterns to technologies
        integration_tech_map = {
            'database': [('PostgreSQL', 0.8), ('MySQL', 0.7), ('MongoDB', 0.6)],
            'messaging': [('Apache Kafka', 0.8), ('RabbitMQ', 0.7), ('Redis', 0.6)],
            'cache': [('Redis', 0.9), ('Memcached', 0.6)],
            'file_storage': [('Amazon S3', 0.8), ('MinIO', 0.6)],
            'notification': [('Amazon SNS', 0.7), ('Twilio', 0.6)]
        }
        
        for integration in context_clues.integration_patterns:
            if integration in integration_tech_map:
                for tech, confidence in integration_tech_map[integration]:
                    contextual_techs[tech] = max(contextual_techs.get(tech, 0), confidence)
        
        # Map programming languages to frameworks
        language_framework_map = {
            'python': [('FastAPI', 0.8), ('Django', 0.7), ('Flask', 0.6)],
            'javascript': [('Express.js', 0.8), ('React', 0.7), ('Vue.js', 0.6)],
            'java': [('Spring Boot', 0.8), ('Spring Framework', 0.7)],
            'csharp': [('ASP.NET Core', 0.8), ('.NET', 0.7)]
        }
        
        for language in context_clues.programming_languages:
            if language in language_framework_map:
                for tech, confidence in language_framework_map[language]:
                    contextual_techs[tech] = max(contextual_techs.get(tech, 0), confidence)
        
        # Map deployment preferences to technologies
        deployment_tech_map = {
            'containerized': [('Docker', 0.9), ('Kubernetes', 0.8)],
            'serverless': [('AWS Lambda', 0.8), ('Azure Functions', 0.7)],
            'cloud_native': [('Kubernetes', 0.8), ('Docker', 0.7)]
        }
        
        for deployment in context_clues.deployment_preferences:
            if deployment in deployment_tech_map:
                for tech, confidence in deployment_tech_map[deployment]:
                    contextual_techs[tech] = max(contextual_techs.get(tech, 0), confidence)
        
        # Map data patterns to technologies
        data_tech_map = {
            'structured_data': [('PostgreSQL', 0.8), ('MySQL', 0.7)],
            'unstructured_data': [('MongoDB', 0.8), ('Elasticsearch', 0.7)],
            'time_series': [('InfluxDB', 0.8), ('Prometheus', 0.7)],
            'big_data': [('Apache Spark', 0.8), ('Apache Kafka', 0.7)],
            'real_time': [('Apache Kafka', 0.8), ('Redis', 0.7)]
        }
        
        for data_pattern in context_clues.data_patterns:
            if data_pattern in data_tech_map:
                for tech, confidence in data_tech_map[data_pattern]:
                    contextual_techs[tech] = max(contextual_techs.get(tech, 0), confidence)
        
        return contextual_techs
    
    def _build_integration_requirements(self, 
                                      context_clues: ContextClues, 
                                      constraints) -> List[str]:
        """Build integration requirements from context clues and constraints.
        
        Args:
            context_clues: Context clues from requirements
            constraints: Requirement constraints
            
        Returns:
            List of integration requirements
        """
        integrations = []
        
        # Add from context clues
        integrations.extend(context_clues.integration_patterns)
        
        # Add from constraints
        integrations.extend(constraints.required_integrations)
        
        # Deduplicate
        return list(set(integrations))
    
    def _calculate_priority_weights(self, 
                                  explicit_technologies: Dict[str, float],
                                  contextual_technologies: Dict[str, float],
                                  domain_context: DomainContext) -> Dict[str, float]:
        """Calculate priority weights for technologies.
        
        Args:
            explicit_technologies: Explicitly mentioned technologies
            contextual_technologies: Contextually inferred technologies
            domain_context: Domain context information
            
        Returns:
            Dictionary mapping technology names to priority weights
        """
        weights = {}
        
        # Explicit technologies get weight 1.0
        for tech in explicit_technologies:
            weights[tech] = 1.0
        
        # Contextual technologies get weight based on confidence
        for tech, confidence in contextual_technologies.items():
            if tech not in weights:
                weights[tech] = confidence
        
        # Apply complexity-based weights
        if domain_context.complexity_indicators:
            complexity_boost = len(domain_context.complexity_indicators) * 0.1
            
            # Boost enterprise-grade technologies
            enterprise_techs = {
                'Kubernetes', 'PostgreSQL', 'Redis', 'Prometheus', 'Grafana',
                'Apache Kafka', 'Elasticsearch', 'Nginx'
            }
            
            for tech in enterprise_techs:
                if tech in weights:
                    weights[tech] = min(weights[tech] + complexity_boost, 1.0)
        
        return weights
    
    def _init_technology_aliases(self) -> None:
        """Initialize comprehensive technology alias mappings for fuzzy matching."""
        self.technology_aliases = {
            # AWS Services - Full names and common aliases
            'Amazon Connect': ['amazon connect', 'connect', 'aws connect', 'connect service'],
            'Amazon Connect SDK': ['amazon connect sdk', 'connect sdk', 'aws connect sdk'],
            'Amazon S3': ['amazon s3', 's3', 'aws s3', 'simple storage service'],
            'AWS Lambda': ['aws lambda', 'lambda', 'amazon lambda', 'lambda functions'],
            'AWS Comprehend': ['aws comprehend', 'comprehend', 'amazon comprehend'],
            'AWS Bedrock': ['aws bedrock', 'bedrock', 'amazon bedrock'],
            'Amazon DynamoDB': ['amazon dynamodb', 'dynamodb', 'dynamo db', 'aws dynamodb'],
            'Amazon RDS': ['amazon rds', 'rds', 'aws rds', 'relational database service'],
            'Amazon EC2': ['amazon ec2', 'ec2', 'aws ec2', 'elastic compute cloud'],
            'Amazon ECS': ['amazon ecs', 'ecs', 'aws ecs', 'elastic container service'],
            'Amazon EKS': ['amazon eks', 'eks', 'aws eks', 'elastic kubernetes service'],
            'Amazon CloudWatch': ['amazon cloudwatch', 'cloudwatch', 'aws cloudwatch'],
            'Amazon SNS': ['amazon sns', 'sns', 'aws sns', 'simple notification service'],
            'Amazon SQS': ['amazon sqs', 'sqs', 'aws sqs', 'simple queue service'],
            'AWS API Gateway': ['aws api gateway', 'api gateway', 'amazon api gateway'],
            'AWS Step Functions': ['aws step functions', 'step functions', 'amazon step functions'],
            
            # Azure Services
            'Azure Cognitive Services': ['azure cognitive services', 'cognitive services', 'azure cognitive', 'azure ai'],
            'Azure App Service': ['azure app service', 'app service', 'azure web apps'],
            'Azure Functions': ['azure functions', 'functions', 'azure serverless'],
            'Azure Cosmos DB': ['azure cosmos db', 'cosmos db', 'azure cosmos', 'cosmosdb'],
            'Azure SQL Database': ['azure sql database', 'azure sql', 'sql database', 'azure sql db'],
            'Azure Storage Account': ['azure storage account', 'azure storage', 'storage account', 'azure blob'],
            'Azure Service Bus': ['azure service bus', 'service bus', 'azure messaging'],
            'Azure Event Grid': ['azure event grid', 'event grid', 'azure events'],
            'Azure Monitor': ['azure monitor', 'azure monitoring', 'azure logs'],
            'Azure Key Vault': ['azure key vault', 'key vault', 'azure secrets'],
            'Azure Active Directory': ['azure active directory', 'azure ad', 'active directory', 'aad'],
            
            # Google Cloud Services
            'Google Cloud Functions': ['google cloud functions', 'cloud functions', 'google functions', 'gcp functions'],
            'Google Cloud Run': ['google cloud run', 'cloud run', 'gcp run'],
            'Google BigQuery': ['google bigquery', 'bigquery', 'big query', 'gcp bigquery'],
            'Google Firestore': ['google firestore', 'firestore', 'gcp firestore'],
            'Google Cloud Storage': ['google cloud storage', 'gcs', 'cloud storage', 'google storage', 'gcp storage'],
            'Google Pub/Sub': ['google pub/sub', 'pubsub', 'pub/sub', 'google pubsub', 'gcp pubsub'],
            'Google Kubernetes Engine': ['google kubernetes engine', 'gke', 'google kubernetes', 'gcp kubernetes'],
            
            # Programming Languages & Frameworks
            'Python': ['python', 'py', 'python3'],
            'JavaScript': ['javascript', 'js', 'ecmascript'],
            'TypeScript': ['typescript', 'ts'],
            'Node.js': ['node.js', 'node', 'nodejs'],
            'React': ['react', 'reactjs', 'react.js'],
            'Vue.js': ['vue.js', 'vue', 'vuejs'],
            'Angular': ['angular', 'angularjs'],
            'Django': ['django', 'django framework'],
            'Flask': ['flask', 'flask framework'],
            'FastAPI': ['fastapi', 'fast api'],
            'Express.js': ['express.js', 'express', 'expressjs'],
            'Spring Framework': ['spring framework', 'spring'],
            'Spring Boot': ['spring boot', 'springboot'],
            'ASP.NET Core': ['asp.net core', 'asp.net', 'aspnet', 'dotnet core'],
            '.NET': ['.net', 'dotnet', 'dot net'],
            
            # Databases
            'PostgreSQL': ['postgresql', 'postgres', 'pg'],
            'MySQL': ['mysql', 'my sql'],
            'MongoDB': ['mongodb', 'mongo', 'mongo db'],
            'Redis': ['redis', 'redis cache'],
            'Elasticsearch': ['elasticsearch', 'elastic search', 'elastic', 'es'],
            'InfluxDB': ['influxdb', 'influx db', 'influx'],
            'SQLite': ['sqlite', 'sqlite3', 'sql lite'],
            
            # Container & Orchestration
            'Docker': ['docker', 'docker container'],
            'Kubernetes': ['kubernetes', 'k8s', 'kube'],
            'Docker Compose': ['docker compose', 'docker-compose', 'compose'],
            
            # Monitoring & Observability
            'Prometheus': ['prometheus', 'prom'],
            'Grafana': ['grafana'],
            'Jaeger': ['jaeger', 'jaeger tracing'],
            'Zipkin': ['zipkin', 'zipkin tracing'],
            'New Relic': ['new relic', 'newrelic'],
            'Datadog': ['datadog', 'data dog'],
            
            # Message Queues & Streaming
            'Apache Kafka': ['apache kafka', 'kafka'],
            'RabbitMQ': ['rabbitmq', 'rabbit mq', 'rabbit'],
            'Celery': ['celery', 'celery worker'],
            'Apache Pulsar': ['apache pulsar', 'pulsar'],
            
            # AI/ML Technologies
            'OpenAI API': ['openai api', 'openai', 'open ai', 'gpt', 'chatgpt'],
            'Anthropic Claude': ['anthropic claude', 'claude', 'anthropic'],
            'Hugging Face': ['hugging face', 'huggingface', 'hf'],
            'Hugging Face Transformers': ['hugging face transformers', 'transformers', 'hf transformers', 'huggingface transformers'],
            'LangChain': ['langchain', 'lang chain'],
            'LangGraph': ['langgraph', 'lang graph'],
            'Pandas': ['pandas', 'pd'],
            'NumPy': ['numpy', 'np'],
            'Scikit-learn': ['scikit-learn', 'sklearn', 'scikit learn'],
            'TensorFlow': ['tensorflow', 'tf'],
            'PyTorch': ['pytorch', 'torch'],
            'Keras': ['keras'],
            'FAISS': ['faiss', 'facebook ai similarity search'],
            
            # Web Servers & Proxies
            'Nginx': ['nginx', 'nginx server'],
            'Apache HTTP Server': ['apache http server', 'apache', 'apache http', 'httpd'],
            'Gunicorn': ['gunicorn', 'green unicorn'],
            'Uvicorn': ['uvicorn'],
            'Traefik': ['traefik'],
            
            # Testing Frameworks
            'pytest': ['pytest', 'py.test'],
            'Jest': ['jest', 'jest testing'],
            'JUnit': ['junit', 'junit testing'],
            'Mocha': ['mocha', 'mocha testing'],
            'Cypress': ['cypress', 'cypress testing'],
            'Selenium': ['selenium', 'selenium webdriver'],
            
            # Build Tools & Package Managers
            'Webpack': ['webpack', 'web pack'],
            'Vite': ['vite', 'vitejs'],
            'Apache Maven': ['apache maven', 'maven', 'mvn'],
            'Gradle': ['gradle'],
            'npm': ['npm', 'node package manager'],
            'Yarn': ['yarn', 'yarn package manager'],
            'pip': ['pip', 'python package installer'],
            
            # Version Control & CI/CD
            'Git': ['git', 'git version control'],
            'GitHub': ['github', 'git hub'],
            'GitLab': ['gitlab', 'git lab'],
            'Jenkins': ['jenkins', 'jenkins ci'],
            'GitHub Actions': ['github actions', 'gh actions'],
            'CircleCI': ['circleci', 'circle ci'],
            'Travis CI': ['travis ci', 'travis'],
            
            # Security & Authentication
            'HashiCorp Vault': ['hashicorp vault', 'vault', 'hc vault'],
            'OAuth 2.0': ['oauth 2.0', 'oauth', 'oauth2'],
            'JWT': ['jwt', 'json web token'],
            'Auth0': ['auth0', 'auth zero'],
            'Okta': ['okta'],
            
            # Infrastructure as Code
            'Terraform': ['terraform', 'tf'],
            'AWS CloudFormation': ['aws cloudformation', 'cloudformation', 'cfn'],
            'Ansible': ['ansible'],
            'Pulumi': ['pulumi'],
            
            # API & Communication
            'GraphQL': ['graphql', 'graph ql'],
            'gRPC': ['grpc', 'g rpc'],
            'Socket.IO': ['socket.io', 'socketio', 'socket io'],
            'WebSocket': ['websocket', 'web socket'],
            
            # Caching & Session Storage
            'Memcached': ['memcached', 'memcache'],
            'Hazelcast': ['hazelcast'],
            
            # Search & Analytics
            'Apache Solr': ['apache solr', 'solr'],
            'Algolia': ['algolia'],
            
            # Content Management
            'Strapi': ['strapi'],
            'Contentful': ['contentful'],
            'Sanity': ['sanity', 'sanity cms']
        }
        
        # Create reverse mapping for faster lookup
        self.alias_to_canonical = {}
        for canonical, aliases in self.technology_aliases.items():
            for alias in aliases:
                self.alias_to_canonical[alias.lower()] = canonical
    
    def resolve_alias_with_fuzzy_matching(self, tech_name: str, context: str = "") -> Optional[Tuple[str, float]]:
        """Resolve technology alias using fuzzy matching.
        
        Args:
            tech_name: Technology name to resolve
            context: Context for disambiguation
            
        Returns:
            Tuple of (canonical_name, confidence_score) if found, None otherwise
        """
        if not tech_name:
            return None
        
        tech_lower = tech_name.lower().strip()
        
        # First try exact match
        if tech_lower in self.alias_to_canonical:
            return self.alias_to_canonical[tech_lower], 1.0
        
        # If fuzzy matching is not available, return None
        if not FUZZY_AVAILABLE:
            self.logger.warning("Fuzzy matching not available - install fuzzywuzzy for better alias resolution")
            return None
        
        # Try fuzzy matching against all aliases
        all_aliases = list(self.alias_to_canonical.keys())
        
        # Get best matches using fuzzy matching
        matches = process.extract(tech_lower, all_aliases, limit=3, scorer=fuzz.ratio)
        
        best_match = None
        best_score = 0
        
        for match_alias, score in matches:
            if score >= self.fuzzy_threshold:
                canonical = self.alias_to_canonical[match_alias]
                
                # Apply context-based scoring boost
                context_boost = self._calculate_context_boost(canonical, context)
                adjusted_score = min(score + context_boost, 100) / 100.0
                
                if adjusted_score > best_score:
                    best_match = canonical
                    best_score = adjusted_score
        
        if best_match:
            self.logger.debug(f"Fuzzy matched '{tech_name}' to '{best_match}' with confidence {best_score:.2f}")
            return best_match, best_score
        
        return None
    
    def _calculate_context_boost(self, canonical_name: str, context: str) -> float:
        """Calculate context-based boost for fuzzy matching.
        
        Args:
            canonical_name: Canonical technology name
            context: Context string
            
        Returns:
            Boost score (0-20 points)
        """
        if not context:
            return 0.0
        
        context_lower = context.lower()
        boost = 0.0
        
        # Boost for ecosystem consistency
        if canonical_name.startswith('Amazon ') or canonical_name.startswith('AWS '):
            if any(term in context_lower for term in ['aws', 'amazon', 'cloud']):
                boost += 10.0
        elif canonical_name.startswith('Azure '):
            if any(term in context_lower for term in ['azure', 'microsoft']):
                boost += 10.0
        elif canonical_name.startswith('Google '):
            if any(term in context_lower for term in ['google', 'gcp', 'cloud']):
                boost += 10.0
        
        # Boost for domain consistency
        if 'database' in context_lower and canonical_name in ['PostgreSQL', 'MySQL', 'MongoDB']:
            boost += 5.0
        elif 'api' in context_lower and canonical_name in ['FastAPI', 'Express.js', 'Spring Boot']:
            boost += 5.0
        elif 'container' in context_lower and canonical_name in ['Docker', 'Kubernetes']:
            boost += 5.0
        elif 'monitoring' in context_lower and canonical_name in ['Prometheus', 'Grafana']:
            boost += 5.0
        
        return boost
    
    def find_similar_technologies(self, tech_name: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Find similar technologies using fuzzy matching.
        
        Args:
            tech_name: Technology name to find similarities for
            limit: Maximum number of results
            
        Returns:
            List of (canonical_name, similarity_score) tuples
        """
        if not FUZZY_AVAILABLE:
            return []
        
        tech_lower = tech_name.lower().strip()
        all_canonicals = list(self.technology_aliases.keys())
        
        # Get fuzzy matches against canonical names
        matches = process.extract(tech_lower, all_canonicals, limit=limit, scorer=fuzz.ratio)
        
        results = []
        for canonical, score in matches:
            if score >= 60:  # Lower threshold for similarity search
                results.append((canonical, score / 100.0))
        
        return results
    
    def get_technology_suggestions(self, partial_name: str, context: str = "", limit: int = 10) -> List[Dict[str, any]]:
        """Get technology suggestions based on partial name and context.
        
        Args:
            partial_name: Partial technology name
            context: Context for better suggestions
            limit: Maximum number of suggestions
            
        Returns:
            List of suggestion dictionaries with name, confidence, and reason
        """
        suggestions = []
        
        if not partial_name:
            return suggestions
        
        # Try fuzzy matching
        fuzzy_result = self.resolve_alias_with_fuzzy_matching(partial_name, context)
        if fuzzy_result:
            canonical, confidence = fuzzy_result
            suggestions.append({
                'name': canonical,
                'confidence': confidence,
                'reason': 'Fuzzy match',
                'aliases': self.technology_aliases.get(canonical, [])
            })
        
        # Find similar technologies
        similar = self.find_similar_technologies(partial_name, limit)
        for canonical, similarity in similar:
            if not any(s['name'] == canonical for s in suggestions):
                suggestions.append({
                    'name': canonical,
                    'confidence': similarity,
                    'reason': 'Similar name',
                    'aliases': self.technology_aliases.get(canonical, [])
                })
        
        # Sort by confidence and limit results
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions[:limit]