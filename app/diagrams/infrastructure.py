"""
Infrastructure diagram generation using mingrammer/diagrams.
Supports AWS, GCP, Azure, Kubernetes, On-Prem, and SaaS components.
Uses dynamic component mapping for extensibility.
"""

import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

from .dynamic_component_mapper import DynamicComponentMapper

try:
    from diagrams import Diagram, Cluster, Edge
    from diagrams.aws import compute as aws_compute
    from diagrams.aws import database as aws_database
    from diagrams.aws import network as aws_network
    from diagrams.aws import storage as aws_storage
    from diagrams.aws import integration as aws_integration
    from diagrams.aws import security as aws_security
    from diagrams.aws import analytics as aws_analytics
    from diagrams.aws import ml as aws_ml
    
    from diagrams.gcp import compute as gcp_compute
    from diagrams.gcp import database as gcp_database
    from diagrams.gcp import network as gcp_network
    from diagrams.gcp import storage as gcp_storage
    from diagrams.gcp import analytics as gcp_analytics
    from diagrams.gcp import ml as gcp_ml
    
    from diagrams.azure import compute as azure_compute
    from diagrams.azure import database as azure_database
    from diagrams.azure import network as azure_network
    from diagrams.azure import storage as azure_storage
    from diagrams.azure import analytics as azure_analytics
    from diagrams.azure import ml as azure_ml
    
    from diagrams.k8s import compute as k8s_compute
    from diagrams.k8s import network as k8s_network
    from diagrams.k8s import storage as k8s_storage
    
    from diagrams.onprem import compute as onprem_compute
    from diagrams.onprem import database as onprem_database
    from diagrams.onprem import network as onprem_network
    from diagrams.onprem import analytics as onprem_analytics
    
    from diagrams.saas import analytics as saas_analytics
    from diagrams.saas import chat as saas_chat
    from diagrams.saas import identity as saas_identity
    
    DIAGRAMS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Diagrams library not available: {e}")
    DIAGRAMS_AVAILABLE = False


class InfrastructureDiagramGenerator:
    """Generate infrastructure diagrams using mingrammer/diagrams."""
    
    def __init__(self):
        self.component_mapping = self._build_component_mapping()
        self.dynamic_mapper = DynamicComponentMapper()
    
    def _build_component_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Build mapping from component types to diagrams classes."""
        if not DIAGRAMS_AVAILABLE:
            return {}
        
        return {
            "aws": {
                # Compute
                "lambda": aws_compute.Lambda,
                "ec2": aws_compute.EC2,
                "ecs": aws_compute.ECS,
                "fargate": aws_compute.Fargate,
                "batch": aws_compute.Batch,
                
                # Database
                "rds": aws_database.RDS,
                "dynamodb": aws_database.Dynamodb,
                "redshift": aws_database.Redshift,
                "elasticache": aws_database.Elasticache,
                
                # Storage
                "s3": aws_storage.S3,
                "efs": aws_storage.EFS,
                
                # Network
                "apigateway": aws_network.APIGateway,
                "cloudfront": aws_network.CloudFront,
                "elb": aws_network.ELB,
                "vpc": aws_network.VPC,
                
                # Integration
                "sqs": aws_integration.SQS,
                "sns": aws_integration.SNS,
                "eventbridge": aws_integration.Eventbridge,
                
                # Security
                "iam": aws_security.IAM,
                "cognito": aws_security.Cognito,
                
                # Analytics
                "kinesis": aws_analytics.Kinesis,
                "glue": aws_analytics.Glue,
                
                # ML
                "sagemaker": aws_ml.Sagemaker,
            },
            "gcp": {
                # Compute
                "functions": gcp_compute.Functions,
                "gce": gcp_compute.GCE,
                "gke": gcp_compute.GKE,
                "run": gcp_compute.Run,
                
                # Database
                "sql": gcp_database.SQL,
                "firestore": gcp_database.Firestore,
                "bigtable": gcp_database.Bigtable,
                
                # Storage
                "gcs": gcp_storage.GCS,
                
                # Network
                "loadbalancing": gcp_network.LoadBalancing,
                "cdn": gcp_network.CDN,
                
                # Analytics
                "bigquery": gcp_analytics.Bigquery,
                "dataflow": gcp_analytics.Dataflow,
                
                # ML
                "aiplatform": gcp_ml.AIPlatform,
                "automl": gcp_ml.AutoML,
            },
            "azure": {
                # Compute
                "functions": azure_compute.FunctionApps,
                "vm": azure_compute.VM,
                "aks": azure_compute.AKS,
                "containerinstances": azure_compute.ContainerInstances,
                
                # Database
                "sql": azure_database.SQLDatabases,
                "cosmosdb": azure_database.CosmosDb,
                
                # Storage
                "storage": azure_storage.BlobStorage,
                
                # Network
                "loadbalancer": azure_network.LoadBalancers,
                "applicationgateway": azure_network.ApplicationGateway,
                
                # Analytics
                "synapse": azure_analytics.SynapseAnalytics,
                
                # ML
                "machinelearning": azure_ml.MachineLearningServiceWorkspaces,
                "cognitiveservices": azure_ml.CognitiveServices,
            },
            "k8s": {
                # Compute
                "pod": k8s_compute.Pod,
                "deployment": k8s_compute.Deployment,
                "job": k8s_compute.Job,
                
                # Network
                "service": k8s_network.Service,
                "ingress": k8s_network.Ingress,
                
                # Storage
                "pv": k8s_storage.PV,
                "pvc": k8s_storage.PVC,
            },
            "onprem": {
                # Compute
                "server": onprem_compute.Server,
                
                # Database
                "postgresql": onprem_database.PostgreSQL,
                "mysql": onprem_database.MySQL,
                "mongodb": onprem_database.MongoDB,
                "mariadb": onprem_database.MariaDB,
                
                # Network
                "nginx": onprem_network.Nginx,
                
                # Analytics
                "spark": onprem_analytics.Spark,
            },
            "saas": {
                # Identity
                "auth0": saas_identity.Auth0,
                "okta": saas_identity.Okta,
                
                # Chat
                "slack": saas_chat.Slack,
                "teams": saas_chat.Teams,
                
                # Analytics
                "snowflake": saas_analytics.Snowflake,
                "stitch": saas_analytics.Stitch,
                
                # AI/ML Services
                "openai_api": saas_analytics.Snowflake,  # Use generic SaaS icon
                "claude_api": saas_analytics.Snowflake,  # Use generic SaaS icon
                "salesforce_api": saas_analytics.Snowflake,  # Use generic SaaS icon
                "semantic_kernel": saas_analytics.Snowflake,  # Use generic SaaS icon
                "assistants_api": saas_analytics.Snowflake,  # Use generic SaaS icon
            },
            "agentic": {
                # AI Agent Orchestration
                "langchain_orchestrator": onprem_compute.Server,  # Use server icon for orchestrators
                "crewai_coordinator": onprem_compute.Server,  # Use server icon for coordinators
                "agent_memory": onprem_database.MongoDB,  # Use database icon for memory
                "semantic_kernel": onprem_compute.Server,  # Use server icon for kernel
                
                # AI Model Services
                "openai_api": saas_analytics.Snowflake,  # Use SaaS icon for APIs
                "claude_api": saas_analytics.Snowflake,  # Use SaaS icon for APIs
                "assistants_api": saas_analytics.Snowflake,  # Use SaaS icon for APIs
                
                # Knowledge & Data
                "vector_db": onprem_database.MongoDB,  # Use database icon for vector DBs
                "knowledge_base": onprem_database.PostgreSQL,  # Use database icon for knowledge
                
                # Rules & Workflow
                "rule_engine": onprem_compute.Server,  # Use server icon for rule engines
                "workflow_engine": onprem_compute.Server,  # Use server icon for workflow
                
                # Integration
                "salesforce_api": saas_analytics.Snowflake,  # Use SaaS icon for external APIs
            }
        }
    
    def generate_diagram(self, diagram_spec: Dict[str, Any], output_path: str, 
                        format: str = "png") -> Tuple[str, str]:
        """
        Generate infrastructure diagram from specification.
        
        Args:
            diagram_spec: JSON specification with clusters, nodes, and edges
            output_path: Path to save the diagram (without extension)
            format: Output format ('png' or 'svg')
            
        Returns:
            Tuple of (diagram_path, python_code)
        """
        if not DIAGRAMS_AVAILABLE:
            raise ImportError("Diagrams library not available. Install with: pip install diagrams")
        
        # Generate Python code
        python_code = self._generate_python_code(diagram_spec)
        
        # Execute the code to generate the diagram
        diagram_path = self._execute_diagram_code(python_code, output_path, format)
        
        return diagram_path, python_code
    
    def _generate_python_code(self, spec: Dict[str, Any]) -> str:
        """Generate Python code for the diagram specification."""
        lines = [
            "import os",
            "import tempfile",
            "from diagrams import Diagram, Cluster, Edge",
            "from diagrams.aws import compute as aws_compute, database as aws_database, network as aws_network, storage as aws_storage, integration as aws_integration, security as aws_security, analytics as aws_analytics, ml as aws_ml",
            "from diagrams.gcp import compute as gcp_compute, database as gcp_database, network as gcp_network, storage as gcp_storage, analytics as gcp_analytics, ml as gcp_ml",
            "from diagrams.azure import compute as azure_compute, database as azure_database, network as azure_network, storage as azure_storage, analytics as azure_analytics, ml as azure_ml",
            "from diagrams.k8s import compute as k8s_compute, network as k8s_network, storage as k8s_storage",
            "from diagrams.onprem import compute as onprem_compute, database as onprem_database, network as onprem_network, analytics as onprem_analytics",
            "from diagrams.saas import analytics as saas_analytics, chat as saas_chat, identity as saas_identity",
            "",
            f'with Diagram("{spec.get("title", "Infrastructure Diagram")}", show=False, filename="diagram", direction="TB"):',
        ]
        
        # Track all nodes for edge creation
        all_nodes = {}
        
        # Generate clusters and nodes
        clusters = spec.get("clusters", [])
        for cluster in clusters:
            cluster_name = cluster.get("name", "Cluster")
            provider = cluster.get("provider", "aws")
            
            lines.append(f'    with Cluster("{cluster_name}"):')
            
            # Generate nodes within cluster
            nodes = cluster.get("nodes", [])
            cluster_has_nodes = False
            
            for node in nodes:
                node_id = node.get("id")
                node_type = node.get("type")
                label = node.get("label", node_id)
                
                # Map type to diagrams class
                component_class = self._get_component_class(provider, node_type)
                if component_class:
                    lines.append(f'        {node_id} = {component_class}("{label}")')
                    all_nodes[node_id] = node_id
                    cluster_has_nodes = True
                else:
                    logger.warning(f"Unknown component type: {provider}.{node_type}")
            
            # Add pass statement if cluster has no valid nodes
            if not cluster_has_nodes:
                lines.append('        pass  # Empty cluster')
        
        # Generate standalone nodes (not in clusters)
        standalone_nodes = spec.get("nodes", [])
        for node in standalone_nodes:
            node_id = node.get("id")
            node_type = node.get("type")
            label = node.get("label", node_id)
            provider = node.get("provider", "aws")
            
            component_class = self._get_component_class(provider, node_type)
            if component_class:
                lines.append(f'    {node_id} = {component_class}("{label}")')
                all_nodes[node_id] = node_id
        
        # Generate edges
        edges = spec.get("edges", [])
        for edge in edges:
            if len(edge) >= 2:
                source = edge[0]
                target = edge[1]
                label = edge[2] if len(edge) > 2 else ""
                
                if source in all_nodes and target in all_nodes:
                    if label:
                        lines.append(f'    {source} >> Edge(label="{label}") >> {target}')
                    else:
                        lines.append(f'    {source} >> {target}')
        
        # Ensure the diagram block has content
        if len([line for line in lines if line.startswith('    ') and not line.strip().startswith('with Diagram')]) == 0:
            lines.append('    pass  # Empty diagram')
        
        return "\n".join(lines)
    
    def _get_component_class(self, provider: str, component_type: str) -> Optional[str]:
        """Get the diagrams class name for a component type."""
        # First try static mapping for backward compatibility
        provider_mapping = self.component_mapping.get(provider, {})
        component_class = provider_mapping.get(component_type.lower())
        
        if component_class:
            # Get the actual module and class name from the component class
            module_path = component_class.__module__
            class_name = component_class.__name__
            
            # Extract the actual provider and module from the module path
            # e.g., 'diagrams.onprem.compute' -> 'onprem_compute'
            if 'diagrams.' in module_path:
                parts = module_path.split('.')
                if len(parts) >= 3:
                    actual_provider = parts[1]  # e.g., 'onprem'
                    actual_module = parts[2]    # e.g., 'compute'
                    return f"{actual_provider}_{actual_module}.{class_name}"
            
            # Fallback for any edge cases
            return f"{provider}_{component_class.__module__.split('.')[-1]}.{class_name}"
        
        # If not found in static mapping, try dynamic mapping
        try:
            dynamic_provider, dynamic_component = self.dynamic_mapper.map_technology_to_component(
                f"{provider}.{component_type}", provider_hint=provider
            )
            
            # Map to actual component class
            dynamic_mapping = self.component_mapping.get(dynamic_provider, {})
            dynamic_class = dynamic_mapping.get(dynamic_component.lower())
            
            if dynamic_class:
                module_path = dynamic_class.__module__
                class_name = dynamic_class.__name__
                
                if 'diagrams.' in module_path:
                    parts = module_path.split('.')
                    if len(parts) >= 3:
                        actual_provider = parts[1]
                        actual_module = parts[2]
                        logger.info(f"Dynamic mapping: {provider}.{component_type} -> {actual_provider}_{actual_module}.{class_name}")
                        return f"{actual_provider}_{actual_module}.{class_name}"
                        
        except Exception as e:
            logger.warning(f"Dynamic mapping failed for {provider}.{component_type}: {e}")
        
        return None
    
    def _execute_diagram_code(self, python_code: str, output_path: str, format: str) -> str:
        """Execute the Python code to generate the diagram."""
        # Create temporary directory for execution
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the Python code to a temporary file
            code_file = os.path.join(temp_dir, "generate_diagram.py")
            with open(code_file, 'w') as f:
                f.write(python_code)
            
            # Change to temp directory and execute
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Execute the code with proper namespace
                import builtins
                namespace = {
                    '__builtins__': builtins,
                    'os': os,
                    'tempfile': tempfile,
                }
                
                try:
                    exec(compile(open(code_file).read(), code_file, 'exec'), namespace)
                except Exception as exec_error:
                    logger.error(f"Failed to execute diagram code: {exec_error}")
                    logger.error(f"Generated Python code:\n{python_code}")
                    raise RuntimeError(f"Diagram code execution failed: {exec_error}")
                
                # Find the generated diagram file
                diagram_file = None
                
                # List all files in temp directory for debugging
                temp_files = os.listdir(temp_dir)
                logger.info(f"Files in temp directory: {temp_files}")
                
                for ext in ['.png', '.svg']:
                    potential_file = os.path.join(temp_dir, f"diagram{ext}")
                    logger.info(f"Checking for file: {potential_file}")
                    if os.path.exists(potential_file):
                        diagram_file = potential_file
                        logger.info(f"Found diagram file: {diagram_file}")
                        break
                
                if diagram_file:
                    # Copy to output path
                    final_path = f"{output_path}.{format}"
                    
                    # Ensure the output directory exists
                    output_dir = os.path.dirname(final_path)
                    if output_dir:
                        os.makedirs(output_dir, exist_ok=True)
                    
                    import shutil
                    shutil.copy2(diagram_file, final_path)
                    
                    # Verify the file was created successfully
                    if not os.path.exists(final_path):
                        raise FileNotFoundError(f"Failed to create output file: {final_path}")
                    
                    return final_path
                else:
                    raise FileNotFoundError("Generated diagram file not found in temporary directory")
                    
            finally:
                os.chdir(original_cwd)


def create_sample_infrastructure_spec() -> Dict[str, Any]:
    """Create a sample infrastructure specification for testing."""
    return {
        "title": "Sample Web Application Infrastructure",
        "clusters": [
            {
                "provider": "aws",
                "name": "AWS Cloud",
                "nodes": [
                    {"id": "api_gateway", "type": "apigateway", "label": "API Gateway"},
                    {"id": "lambda_func", "type": "lambda", "label": "Lambda Function"},
                    {"id": "dynamodb", "type": "dynamodb", "label": "DynamoDB"},
                    {"id": "s3_bucket", "type": "s3", "label": "S3 Storage"}
                ]
            }
        ],
        "nodes": [
            {"id": "user", "type": "server", "provider": "onprem", "label": "User"}
        ],
        "edges": [
            ["user", "api_gateway", "HTTPS"],
            ["api_gateway", "lambda_func", "invoke"],
            ["lambda_func", "dynamodb", "query"],
            ["lambda_func", "s3_bucket", "store"]
        ]
    }


async def generate_infrastructure_diagram_from_llm(requirement: str, recommendations: List[Dict]) -> Dict[str, Any]:
    """
    Generate infrastructure diagram specification using LLM.
    This would be called by the main application to get the JSON spec.
    """
    # This is a placeholder - in the real implementation, this would call the LLM
    # to generate the infrastructure specification based on the requirement and recommendations
    
    # For now, return a sample spec
    return create_sample_infrastructure_spec()