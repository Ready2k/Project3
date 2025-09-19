"""Agentic technology catalog focused on autonomous agent frameworks and reasoning engines."""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app.utils.imports import require_service


class TechnologyCategory(Enum):
    AGENTIC_FRAMEWORK = "agentic_framework"
    REASONING_ENGINE = "reasoning_engine"
    DECISION_MAKING = "decision_making"
    LEARNING_SYSTEM = "learning_system"
    COMMUNICATION = "communication"
    ORCHESTRATION = "orchestration"
    MONITORING = "monitoring"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class AutonomySupport(Enum):
    LOW = "low"          # 0.0-0.4
    MEDIUM = "medium"    # 0.4-0.7
    HIGH = "high"        # 0.7-0.9
    VERY_HIGH = "very_high"  # 0.9-1.0


@dataclass
class AgenticTechnology:
    name: str
    category: TechnologyCategory
    description: str
    autonomy_support: float  # 0.0-1.0
    reasoning_capabilities: List[str]
    decision_making_level: str  # low, medium, high, full
    multi_agent_support: bool
    learning_mechanisms: List[str]
    integration_complexity: str  # simple, moderate, complex
    maturity_level: str  # experimental, beta, stable, mature
    license_type: str
    documentation_quality: str  # poor, fair, good, excellent
    community_support: str  # low, medium, high
    use_cases: List[str]
    alternatives: List[str]
    pros: List[str]
    cons: List[str]


class AgenticTechnologyCatalog:
    """Catalog of technologies focused on autonomous agent capabilities."""
    
    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or Path("data/agentic_technologies.json")
        self.technologies = {}
        
        # Get logger from service registry
        self.logger = require_service('logger', context='AgenticTechnologyCatalog')
        
        self._load_catalog()
    
    def _load_catalog(self):
        """Load the agentic technology catalog."""
        
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, 'r') as f:
                    catalog_data = json.load(f)
                    self._parse_catalog_data(catalog_data)
                self.logger.info(f"Loaded {len(self.technologies)} agentic technologies")
            except Exception as e:
                self.logger.error(f"Failed to load agentic catalog: {e}")
                self._create_default_catalog()
        else:
            self.logger.info("Creating default agentic technology catalog")
            self._create_default_catalog()
    
    def _parse_catalog_data(self, catalog_data: Dict[str, Any]):
        """Parse catalog data into AgenticTechnology objects."""
        
        for tech_name, tech_data in catalog_data.items():
            try:
                technology = AgenticTechnology(
                    name=tech_name,
                    category=TechnologyCategory(tech_data.get("category", "agentic_framework")),
                    description=tech_data.get("description", ""),
                    autonomy_support=float(tech_data.get("autonomy_support", 0.5)),
                    reasoning_capabilities=tech_data.get("reasoning_capabilities", []),
                    decision_making_level=tech_data.get("decision_making", "medium"),
                    multi_agent_support=tech_data.get("multi_agent_support", False),
                    learning_mechanisms=tech_data.get("learning_mechanisms", []),
                    integration_complexity=tech_data.get("integration_complexity", "moderate"),
                    maturity_level=tech_data.get("maturity_level", "stable"),
                    license_type=tech_data.get("license_type", "open_source"),
                    documentation_quality=tech_data.get("documentation_quality", "good"),
                    community_support=tech_data.get("community_support", "medium"),
                    use_cases=tech_data.get("use_cases", []),
                    alternatives=tech_data.get("alternatives", []),
                    pros=tech_data.get("pros", []),
                    cons=tech_data.get("cons", [])
                )
                self.technologies[tech_name] = technology
            except Exception as e:
                self.logger.error(f"Failed to parse technology {tech_name}: {e}")
    
    def _create_default_catalog(self):
        """Create default agentic technology catalog."""
        
        default_technologies = {
            "LangChain": AgenticTechnology(
                name="LangChain",
                category=TechnologyCategory.AGENTIC_FRAMEWORK,
                description="Comprehensive framework for building applications with large language models, featuring agent capabilities, memory, and tool integration",
                autonomy_support=0.9,
                reasoning_capabilities=["chain_of_thought", "react", "plan_and_execute", "self_ask"],
                decision_making_level="high",
                multi_agent_support=True,
                learning_mechanisms=["few_shot", "retrieval_augmented", "memory_persistence"],
                integration_complexity="moderate",
                maturity_level="stable",
                license_type="MIT",
                documentation_quality="excellent",
                community_support="high",
                use_cases=["conversational_ai", "document_analysis", "code_generation", "research_assistance"],
                alternatives=["LlamaIndex", "Haystack", "Semantic Kernel"],
                pros=["Extensive ecosystem", "Active development", "Good documentation", "Flexible architecture"],
                cons=["Learning curve", "Rapid API changes", "Performance overhead"]
            ),
            
            "AutoGPT": AgenticTechnology(
                name="AutoGPT",
                category=TechnologyCategory.AGENTIC_FRAMEWORK,
                description="Autonomous AI agent that can perform tasks independently by breaking them down into sub-tasks and executing them iteratively",
                autonomy_support=0.95,
                reasoning_capabilities=["goal_decomposition", "self_reflection", "iterative_improvement"],
                decision_making_level="very_high",
                multi_agent_support=False,
                learning_mechanisms=["memory_persistence", "self_improvement", "experience_replay"],
                integration_complexity="simple",
                maturity_level="beta",
                license_type="MIT",
                documentation_quality="good",
                community_support="high",
                use_cases=["autonomous_research", "content_creation", "task_automation", "problem_solving"],
                alternatives=["AgentGPT", "BabyAGI", "SuperAGI"],
                pros=["High autonomy", "Self-directed", "Minimal setup", "Goal-oriented"],
                cons=["Limited control", "Resource intensive", "Unpredictable behavior"]
            ),
            
            "CrewAI": AgenticTechnology(
                name="CrewAI",
                category=TechnologyCategory.AGENTIC_FRAMEWORK,
                description="Multi-agent framework for orchestrating role-playing autonomous AI agents to work together on complex tasks",
                autonomy_support=0.85,
                reasoning_capabilities=["collaborative_reasoning", "role_specialization", "consensus_building"],
                decision_making_level="high",
                multi_agent_support=True,
                learning_mechanisms=["collective_learning", "role_adaptation", "performance_feedback"],
                integration_complexity="moderate",
                maturity_level="stable",
                license_type="MIT",
                documentation_quality="good",
                community_support="medium",
                use_cases=["content_creation", "research_projects", "business_analysis", "creative_tasks"],
                alternatives=["AutoGen", "LangChain Multi-Agent", "MetaGPT"],
                pros=["Role-based agents", "Collaborative workflows", "Easy setup", "Flexible roles"],
                cons=["Limited reasoning depth", "Coordination overhead", "Role conflicts"]
            ),
            
            "Microsoft Semantic Kernel": AgenticTechnology(
                name="Microsoft Semantic Kernel",
                category=TechnologyCategory.AGENTIC_FRAMEWORK,
                description="Enterprise-grade SDK for integrating AI services with conventional programming languages, featuring planning and plugin capabilities",
                autonomy_support=0.8,
                reasoning_capabilities=["sequential_planning", "stepwise_planning", "function_calling"],
                decision_making_level="high",
                multi_agent_support=True,
                learning_mechanisms=["plugin_learning", "context_adaptation", "skill_composition"],
                integration_complexity="moderate",
                maturity_level="stable",
                license_type="MIT",
                documentation_quality="excellent",
                community_support="high",
                use_cases=["enterprise_automation", "business_workflows", "data_analysis", "customer_service"],
                alternatives=["LangChain", "Haystack", "OpenAI Assistants API"],
                pros=["Enterprise ready", "Multi-language support", "Microsoft ecosystem", "Strong planning"],
                cons=["Microsoft-centric", "Complex setup", "Limited community plugins"]
            ),
            
            "OpenAI Assistants API": AgenticTechnology(
                name="OpenAI Assistants API",
                category=TechnologyCategory.AGENTIC_FRAMEWORK,
                description="OpenAI's managed service for building AI assistants with persistent threads, file handling, and function calling",
                autonomy_support=0.75,
                reasoning_capabilities=["function_calling", "code_interpretation", "file_analysis"],
                decision_making_level="medium",
                multi_agent_support=False,
                learning_mechanisms=["conversation_memory", "file_learning", "function_adaptation"],
                integration_complexity="simple",
                maturity_level="stable",
                license_type="proprietary",
                documentation_quality="excellent",
                community_support="high",
                use_cases=["customer_support", "data_analysis", "code_assistance", "document_processing"],
                alternatives=["Anthropic Claude", "Google Bard", "Custom LangChain"],
                pros=["Managed service", "Reliable", "Good documentation", "Built-in capabilities"],
                cons=["Vendor lock-in", "Limited customization", "Cost scaling", "API dependencies"]
            ),
            
            "Neo4j": AgenticTechnology(
                name="Neo4j",
                category=TechnologyCategory.KNOWLEDGE_GRAPH,
                description="Graph database platform optimized for storing and querying highly connected data with powerful graph algorithms",
                autonomy_support=0.7,
                reasoning_capabilities=["graph_traversal", "pattern_matching", "relationship_inference"],
                decision_making_level="medium",
                multi_agent_support=True,
                learning_mechanisms=["graph_learning", "pattern_discovery", "relationship_evolution"],
                integration_complexity="moderate",
                maturity_level="mature",
                license_type="dual_license",
                documentation_quality="excellent",
                community_support="high",
                use_cases=["knowledge_graphs", "recommendation_engines", "fraud_detection", "network_analysis"],
                alternatives=["Amazon Neptune", "ArangoDB", "TigerGraph"],
                pros=["Mature platform", "Rich query language", "Graph algorithms", "Scalable"],
                cons=["Learning curve", "Memory intensive", "Licensing costs", "Complex modeling"]
            ),
            
            "Prolog": AgenticTechnology(
                name="Prolog",
                category=TechnologyCategory.REASONING_ENGINE,
                description="Logic programming language designed for artificial intelligence and computational linguistics with built-in reasoning capabilities",
                autonomy_support=0.8,
                reasoning_capabilities=["logical_inference", "backward_chaining", "constraint_solving"],
                decision_making_level="high",
                multi_agent_support=False,
                learning_mechanisms=["rule_learning", "constraint_adaptation", "knowledge_refinement"],
                integration_complexity="complex",
                maturity_level="mature",
                license_type="open_source",
                documentation_quality="good",
                community_support="medium",
                use_cases=["expert_systems", "natural_language_processing", "automated_reasoning", "constraint_solving"],
                alternatives=["CLIPS", "Drools", "Answer Set Programming"],
                pros=["Pure logic", "Powerful reasoning", "Declarative", "Proven technology"],
                cons=["Steep learning curve", "Performance limitations", "Limited ecosystem", "Integration challenges"]
            ),
            
            "Apache Jena": AgenticTechnology(
                name="Apache Jena",
                category=TechnologyCategory.REASONING_ENGINE,
                description="Java framework for building Semantic Web and Linked Data applications with RDF processing and SPARQL querying",
                autonomy_support=0.65,
                reasoning_capabilities=["rdf_reasoning", "ontology_inference", "rule_based_reasoning"],
                decision_making_level="medium",
                multi_agent_support=True,
                learning_mechanisms=["ontology_learning", "rule_discovery", "semantic_adaptation"],
                integration_complexity="moderate",
                maturity_level="mature",
                license_type="Apache_2.0",
                documentation_quality="good",
                community_support="medium",
                use_cases=["semantic_web", "knowledge_management", "data_integration", "ontology_reasoning"],
                alternatives=["RDF4J", "Stardog", "GraphDB"],
                pros=["Standards compliant", "Mature", "Java ecosystem", "Reasoning capabilities"],
                cons=["Java dependency", "Complex setup", "Performance overhead", "Learning curve"]
            ),
            
            "Drools": AgenticTechnology(
                name="Drools",
                category=TechnologyCategory.DECISION_MAKING,
                description="Business rules management system with forward and backward chaining inference based rule engine",
                autonomy_support=0.75,
                reasoning_capabilities=["rule_based_reasoning", "forward_chaining", "pattern_matching"],
                decision_making_level="high",
                multi_agent_support=True,
                learning_mechanisms=["rule_learning", "pattern_adaptation", "decision_optimization"],
                integration_complexity="moderate",
                maturity_level="mature",
                license_type="Apache_2.0",
                documentation_quality="good",
                community_support="medium",
                use_cases=["business_rules", "decision_automation", "compliance_checking", "workflow_management"],
                alternatives=["CLIPS", "Jess", "OpenRules"],
                pros=["Business friendly", "Mature", "Performance", "Integration"],
                cons=["Java dependency", "Complex rules", "Maintenance overhead", "Learning curve"]
            ),
            
            "Ray": AgenticTechnology(
                name="Ray",
                category=TechnologyCategory.ORCHESTRATION,
                description="Distributed computing framework for scaling AI and machine learning workloads with actor-based programming model",
                autonomy_support=0.6,
                reasoning_capabilities=["distributed_reasoning", "parallel_processing", "resource_optimization"],
                decision_making_level="medium",
                multi_agent_support=True,
                learning_mechanisms=["distributed_learning", "resource_adaptation", "performance_optimization"],
                integration_complexity="complex",
                maturity_level="stable",
                license_type="Apache_2.0",
                documentation_quality="good",
                community_support="high",
                use_cases=["distributed_ai", "hyperparameter_tuning", "reinforcement_learning", "data_processing"],
                alternatives=["Dask", "Celery", "Kubernetes"],
                pros=["Scalable", "Python native", "ML focused", "Actor model"],
                cons=["Complex setup", "Resource intensive", "Learning curve", "Debugging challenges"]
            )
        }
        
        self.technologies = default_technologies
        self._save_catalog()
    
    def get_technologies_by_category(self, category: TechnologyCategory) -> List[AgenticTechnology]:
        """Get all technologies in a specific category."""
        
        return [tech for tech in self.technologies.values() if tech.category == category]
    
    def get_technologies_by_autonomy_level(self, min_autonomy: float) -> List[AgenticTechnology]:
        """Get technologies that meet minimum autonomy requirements."""
        
        return [tech for tech in self.technologies.values() if tech.autonomy_support >= min_autonomy]
    
    def get_multi_agent_technologies(self) -> List[AgenticTechnology]:
        """Get technologies that support multi-agent systems."""
        
        return [tech for tech in self.technologies.values() if tech.multi_agent_support]
    
    def recommend_technologies_for_requirements(self, 
                                              requirements: Dict[str, Any],
                                              top_k: int = 5) -> List[Tuple[AgenticTechnology, float]]:
        """Recommend technologies based on requirements with scoring."""
        
        scored_technologies = []
        
        for tech in self.technologies.values():
            score = self._score_technology_for_requirements(tech, requirements)
            scored_technologies.append((tech, score))
        
        # Sort by score (highest first)
        scored_technologies.sort(key=lambda x: x[1], reverse=True)
        
        return scored_technologies[:top_k]
    
    def _score_technology_for_requirements(self, 
                                         tech: AgenticTechnology,
                                         requirements: Dict[str, Any]) -> float:
        """Score a technology based on how well it matches requirements."""
        
        score = 0.0
        
        # Base score from autonomy support (40% weight)
        score += tech.autonomy_support * 0.4
        
        # Reasoning capabilities match (25% weight)
        required_reasoning = requirements.get("reasoning_types", [])
        if required_reasoning:
            reasoning_match = len(set(tech.reasoning_capabilities) & set(required_reasoning))
            reasoning_score = reasoning_match / len(required_reasoning)
            score += reasoning_score * 0.25
        
        # Decision making level (20% weight)
        required_decision_level = requirements.get("decision_authority_level", "medium")
        decision_levels = {"low": 0.25, "medium": 0.5, "high": 0.75, "full": 1.0}
        tech_decision_score = decision_levels.get(tech.decision_making_level, 0.5)
        required_decision_score = decision_levels.get(required_decision_level, 0.5)
        
        if tech_decision_score >= required_decision_score:
            score += 0.2
        else:
            score += (tech_decision_score / required_decision_score) * 0.2
        
        # Multi-agent support (10% weight)
        if requirements.get("multi_agent_required", False):
            if tech.multi_agent_support:
                score += 0.1
        else:
            score += 0.05  # Slight bonus even if not required
        
        # Maturity and reliability (5% weight)
        maturity_scores = {"experimental": 0.2, "beta": 0.5, "stable": 0.8, "mature": 1.0}
        maturity_score = maturity_scores.get(tech.maturity_level, 0.5)
        score += maturity_score * 0.05
        
        return min(1.0, score)
    
    def get_technology_by_name(self, name: str) -> Optional[AgenticTechnology]:
        """Get a specific technology by name."""
        
        return self.technologies.get(name)
    
    def get_alternatives_for_technology(self, tech_name: str) -> List[AgenticTechnology]:
        """Get alternative technologies for a given technology."""
        
        tech = self.get_technology_by_name(tech_name)
        if not tech:
            return []
        
        alternatives = []
        for alt_name in tech.alternatives:
            alt_tech = self.get_technology_by_name(alt_name)
            if alt_tech:
                alternatives.append(alt_tech)
        
        return alternatives
    
    def get_technology_stack_recommendation(self, 
                                          requirements: Dict[str, Any]) -> Dict[str, List[AgenticTechnology]]:
        """Get a complete technology stack recommendation organized by category."""
        
        stack = {}
        
        # Get recommendations for each category
        for category in TechnologyCategory:
            category_techs = self.get_technologies_by_category(category)
            if category_techs:
                # Score and select top technologies for this category
                scored_techs = []
                for tech in category_techs:
                    score = self._score_technology_for_requirements(tech, requirements)
                    scored_techs.append((tech, score))
                
                scored_techs.sort(key=lambda x: x[1], reverse=True)
                
                # Include top 2-3 technologies per category
                stack[category.value] = [tech for tech, score in scored_techs[:3] if score > 0.5]
        
        return stack
    
    def add_technology(self, technology: AgenticTechnology) -> None:
        """Add a new technology to the catalog."""
        
        self.technologies[technology.name] = technology
        self._save_catalog()
        self.logger.info(f"Added technology: {technology.name}")
    
    def update_technology(self, tech_name: str, updates: Dict[str, Any]) -> None:
        """Update an existing technology in the catalog."""
        
        if tech_name in self.technologies:
            tech = self.technologies[tech_name]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(tech, field):
                    setattr(tech, field, value)
            
            self._save_catalog()
            self.logger.info(f"Updated technology: {tech_name}")
        else:
            self.logger.warning(f"Technology not found for update: {tech_name}")
    
    def remove_technology(self, tech_name: str) -> None:
        """Remove a technology from the catalog."""
        
        if tech_name in self.technologies:
            del self.technologies[tech_name]
            self._save_catalog()
            self.logger.info(f"Removed technology: {tech_name}")
        else:
            self.logger.warning(f"Technology not found for removal: {tech_name}")
    
    def _save_catalog(self):
        """Save the catalog to file."""
        
        try:
            catalog_data = {}
            for tech_name, tech in self.technologies.items():
                catalog_data[tech_name] = {
                    "category": tech.category.value,
                    "description": tech.description,
                    "autonomy_support": tech.autonomy_support,
                    "reasoning_capabilities": tech.reasoning_capabilities,
                    "decision_making": tech.decision_making_level,
                    "multi_agent_support": tech.multi_agent_support,
                    "learning_mechanisms": tech.learning_mechanisms,
                    "integration_complexity": tech.integration_complexity,
                    "maturity_level": tech.maturity_level,
                    "license_type": tech.license_type,
                    "documentation_quality": tech.documentation_quality,
                    "community_support": tech.community_support,
                    "use_cases": tech.use_cases,
                    "alternatives": tech.alternatives,
                    "pros": tech.pros,
                    "cons": tech.cons
                }
            
            # Ensure directory exists
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.catalog_path, 'w') as f:
                json.dump(catalog_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save agentic catalog: {e}")
    
    def get_catalog_statistics(self) -> Dict[str, Any]:
        """Get statistics about the technology catalog."""
        
        stats = {
            "total_technologies": len(self.technologies),
            "by_category": {},
            "by_autonomy_level": {"high": 0, "medium": 0, "low": 0},
            "multi_agent_capable": 0,
            "by_maturity": {"experimental": 0, "beta": 0, "stable": 0, "mature": 0}
        }
        
        for tech in self.technologies.values():
            # Category stats
            category = tech.category.value
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            # Autonomy level stats
            if tech.autonomy_support >= 0.7:
                stats["by_autonomy_level"]["high"] += 1
            elif tech.autonomy_support >= 0.4:
                stats["by_autonomy_level"]["medium"] += 1
            else:
                stats["by_autonomy_level"]["low"] += 1
            
            # Multi-agent stats
            if tech.multi_agent_support:
                stats["multi_agent_capable"] += 1
            
            # Maturity stats
            stats["by_maturity"][tech.maturity_level] += 1
        
        return stats