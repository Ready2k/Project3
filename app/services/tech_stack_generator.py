"""Intelligent tech stack generation service using LLM analysis."""

from typing import Dict, List, Any, Optional, Set, Tuple
import json
from pathlib import Path
import uuid
import time

from app.pattern.matcher import MatchResult
from app.llm.base import LLMProvider
from app.utils.imports import require_service
from app.utils.audit import log_llm_call
from datetime import datetime
import shutil

# Import enhanced parsing and context components
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.context_extractor import TechnologyContextExtractor
from app.services.requirement_parsing.context_prioritizer import RequirementContextPrioritizer
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.context_aware_prompt_generator import ContextAwareLLMPromptGenerator
from app.services.validation.compatibility_validator import TechnologyCompatibilityValidator
from app.services.requirement_parsing.base import ParsedRequirements, TechContext

# Import comprehensive logging services
from app.services.tech_logging.tech_stack_logger import TechStackLogger, LogCategory
from app.services.tech_logging.decision_logger import DecisionLogger
from app.services.tech_logging.llm_interaction_logger import LLMInteractionLogger
from app.services.tech_logging.error_context_logger import ErrorContextLogger, ErrorSeverity, ErrorCategory
from app.services.tech_logging.debug_tracer import DebugTracer, TraceLevel
from app.services.tech_logging.performance_monitor import PerformanceMonitor

# Import ecosystem intelligence
from app.services.ecosystem.intelligence import EcosystemIntelligence


class TechStackGenerator:
    """Service for generating intelligent, context-aware technology stacks."""
    
    def __init__(self, 
                 llm_provider: Optional[LLMProvider] = None, 
                 auto_update_catalog: bool = True,
                 enhanced_parser: Optional[EnhancedRequirementParser] = None,
                 context_extractor: Optional[TechnologyContextExtractor] = None,
                 context_prioritizer: Optional[RequirementContextPrioritizer] = None,
                 catalog_manager: Optional[IntelligentCatalogManager] = None,
                 prompt_generator: Optional[ContextAwareLLMPromptGenerator] = None,
                 compatibility_validator: Optional[TechnologyCompatibilityValidator] = None,
                 ecosystem_intelligence: Optional[EcosystemIntelligence] = None,
                 enable_debug_logging: bool = False):
        """Initialize enhanced tech stack generator.
        
        Args:
            llm_provider: LLM provider for intelligent analysis
            auto_update_catalog: Whether to automatically update catalog with new technologies
            enhanced_parser: Enhanced requirement parser
            context_extractor: Technology context extractor
            context_prioritizer: Requirement context prioritizer
            catalog_manager: Intelligent catalog manager
            prompt_generator: Context-aware prompt generator
            compatibility_validator: Technology compatibility validator
            ecosystem_intelligence: Ecosystem intelligence service
            enable_debug_logging: Whether to enable comprehensive debug logging
        """
        self.llm_provider = llm_provider
        self.auto_update_catalog = auto_update_catalog
        
        # Initialize comprehensive logging system
        self._setup_logging_system(enable_debug_logging)
        
        # Get basic logger from service registry for backward compatibility
        try:
            self.logger = require_service('logger', context='TechStackGenerator')
        except:
            # Fallback to basic logging if service registry not available
            import logging
            self.logger = logging.getLogger('TechStackGenerator')
        
        # Initialize enhanced components
        self.enhanced_parser = enhanced_parser or EnhancedRequirementParser()
        self.context_extractor = context_extractor or TechnologyContextExtractor()
        self.context_prioritizer = context_prioritizer or RequirementContextPrioritizer()
        self.catalog_manager = catalog_manager or IntelligentCatalogManager()
        self.prompt_generator = prompt_generator or ContextAwareLLMPromptGenerator(self.catalog_manager)
        self.compatibility_validator = compatibility_validator or TechnologyCompatibilityValidator()
        
        # Load technology catalog (maintain backward compatibility)
        self.technology_catalog = self._load_technology_catalog()
        self.available_technologies = self._build_category_index()
        
        # Track generation metrics
        self.generation_metrics = {
            'total_generations': 0,
            'explicit_tech_inclusion_rate': 0.0,
            'context_aware_selections': 0,
            'catalog_auto_additions': 0
        }
        
        # Log initialization
        self.tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TechStackGenerator",
            "initialize",
            "Tech stack generator initialized with comprehensive logging",
            {
                'auto_update_catalog': auto_update_catalog,
                'debug_logging_enabled': enable_debug_logging,
                'catalog_size': len(self.technology_catalog.get('technologies', {})),
                'components_initialized': [
                    'enhanced_parser', 'context_extractor', 'context_prioritizer',
                    'catalog_manager', 'prompt_generator', 'compatibility_validator'
                ]
            }
        )
    
    def _setup_logging_system(self, enable_debug: bool = False) -> None:
        """Setup comprehensive logging system for tech stack generation.
        
        Args:
            enable_debug: Whether to enable debug-level logging
        """
        # Initialize main tech stack logger
        logger_config = {
            'log_level': 'DEBUG' if enable_debug else 'INFO',
            'output_format': 'structured',
            'enable_console': True,
            'enable_debug_mode': enable_debug,
            'buffer_size': 500,
            'auto_flush': True
        }
        
        self.tech_logger = TechStackLogger(logger_config)
        self.tech_logger.initialize()
        
        # Initialize specialized loggers
        self.decision_logger = DecisionLogger(self.tech_logger)
        self.llm_logger = LLMInteractionLogger(self.tech_logger)
        self.error_logger = ErrorContextLogger(self.tech_logger)
        self.debug_tracer = DebugTracer(self.tech_logger)
        self.performance_monitor = PerformanceMonitor(self.tech_logger)
        
        # Enable debug tracing if requested
        if enable_debug:
            self.debug_tracer.enable_tracing(TraceLevel.DETAILED)
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring(
            interval_seconds=10.0,
            enable_resource_monitoring=True
        )
        
        # Set performance thresholds
        self.performance_monitor.set_threshold(
            "tech_stack_generation_duration", "max", 30000.0, "warning"  # 30 seconds
        )
        self.performance_monitor.set_threshold(
            "tech_stack_generation_duration", "max", 60000.0, "critical"  # 60 seconds
        )
        self.performance_monitor.set_threshold(
            "cpu_percent", "max", 80.0, "warning"
        )
        self.performance_monitor.set_threshold(
            "memory_percent", "max", 85.0, "critical"
        )
        
    def _load_technology_catalog(self) -> Dict[str, Any]:
        """Load technology catalog from JSON file.
        
        Returns:
            Technology catalog dictionary
        """
        catalog_path = Path("data/technologies.json")
        
        if not catalog_path.exists():
            self.logger.warning("Technology catalog not found, falling back to pattern extraction")
            return self._fallback_to_pattern_extraction()
        
        try:
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
            
            tech_count = len(catalog.get("technologies", {}))
            self.logger.info(f"Loaded {tech_count} available technologies from catalog")
            return catalog
            
        except Exception as e:
            self.logger.error(f"Failed to load technology catalog: {e}")
            return self._fallback_to_pattern_extraction()
    
    def _build_category_index(self) -> Dict[str, Set[str]]:
        """Build category index from technology catalog.
        
        Returns:
            Dictionary mapping categories to sets of technology IDs
        """
        categories = {}
        
        # Initialize categories from catalog
        for category_id, category_info in self.technology_catalog.get("categories", {}).items():
            categories[category_id] = set(category_info.get("technologies", []))
        
        return categories
    
    def _fallback_to_pattern_extraction(self) -> Dict[str, Any]:
        """Fallback method to extract technologies from patterns if catalog is missing.
        
        Returns:
            Basic catalog structure from pattern extraction
        """
        technologies = {}
        
        # Load from pattern library
        pattern_dir = Path("data/patterns")
        if pattern_dir.exists():
            for pattern_file in pattern_dir.glob("*.json"):
                try:
                    with open(pattern_file, 'r') as f:
                        pattern = json.load(f)
                    
                    tech_stack = pattern.get("tech_stack", [])
                    for tech in tech_stack:
                        tech_id = tech.lower().replace(" ", "_").replace("/", "_")
                        technologies[tech_id] = {
                            "name": tech,
                            "category": "tools",  # Default category
                            "description": f"Technology component: {tech}",
                            "tags": [],
                            "maturity": "unknown",
                            "license": "unknown"
                        }
                        
                except Exception as e:
                    self.logger.warning(f"Failed to load pattern {pattern_file}: {e}")
        
        self.logger.info(f"Extracted {len(technologies)} technologies from patterns")
        
        return {
            "metadata": {"version": "fallback", "total_technologies": len(technologies)},
            "technologies": technologies,
            "categories": {"tools": {"name": "Tools", "technologies": list(technologies.keys())}}
        }
    
    def get_technology_info(self, tech_id: str) -> Dict[str, Any]:
        """Get detailed information about a technology.
        
        Args:
            tech_id: Technology identifier
            
        Returns:
            Technology information dictionary
        """
        return self.technology_catalog.get("technologies", {}).get(tech_id, {
            "name": tech_id,
            "category": "unknown",
            "description": f"Technology: {tech_id}",
            "tags": [],
            "maturity": "unknown",
            "license": "unknown"
        })
    
    def find_technology_by_name(self, name: str) -> Optional[str]:
        """Find technology ID by name (case-insensitive).
        
        Args:
            name: Technology name to search for
            
        Returns:
            Technology ID if found, None otherwise
        """
        name_lower = name.lower()
        
        for tech_id, tech_info in self.technology_catalog.get("technologies", {}).items():
            if tech_info.get("name", "").lower() == name_lower:
                return tech_id
            
            # Also check if the name contains the tech name
            if name_lower in tech_info.get("name", "").lower() or tech_info.get("name", "").lower() in name_lower:
                return tech_id
        
        return None
    
    async def generate_tech_stack(self, 
                                matches: List[MatchResult], 
                                requirements: Dict[str, Any],
                                constraints: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate intelligent tech stack based on requirements and constraints.
        
        Args:
            matches: Pattern matching results
            requirements: User requirements
            constraints: Constraints including banned tools
            
        Returns:
            List of recommended technologies
        """
        # Initialize monitoring integration
        monitoring_session = None
        try:
            from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService
            monitoring_service = require_service('tech_stack_monitoring_integration', context='TechStackGenerator')
            
            # Start monitoring session
            monitoring_session = monitoring_service.start_generation_monitoring(
                requirements=requirements,
                metadata={
                    'matches_count': len(matches),
                    'has_constraints': constraints is not None,
                    'generator_version': '2.0_enhanced'
                }
            )
            
            session_id = monitoring_session.session_id
            self.logger.info(f"Started monitoring session: {session_id}")
            
        except Exception as monitoring_error:
            self.logger.debug(f"Monitoring integration not available: {monitoring_error}")
            # Generate unique session and request IDs for tracking (fallback)
            session_id = str(uuid.uuid4())
        
        request_id = f"tech_stack_gen_{int(time.time())}"
        
        # Set logging context
        self.tech_logger.set_session_context(session_id, {
            'operation': 'tech_stack_generation',
            'matches_count': len(matches),
            'has_constraints': constraints is not None
        })
        self.tech_logger.set_request_context(request_id, {
            'requirements_keys': list(requirements.keys()),
            'constraints': constraints
        })
        
        # Start debug tracing
        trace_id = self.debug_tracer.start_trace(
            session_id,
            "TechStackGenerator",
            "generate_tech_stack",
            {
                'matches_count': len(matches),
                'requirements_size': len(str(requirements)),
                'constraints': constraints
            }
        )
        
        # Start performance monitoring
        self.performance_monitor.start_performance_tracking(request_id)
        
        self.tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TechStackGenerator",
            "generate_tech_stack",
            "Starting enhanced tech stack generation",
            {
                'session_id': session_id,
                'request_id': request_id,
                'matches_count': len(matches),
                'requirements_keys': list(requirements.keys()),
                'has_constraints': constraints is not None
            }
        )
        
        self.generation_metrics['total_generations'] += 1
        
        try:
            with self.debug_tracer.trace_step(trace_id, "requirement_parsing", {'requirements': requirements}):
                # Step 1: Enhanced requirement parsing
                parsing_start_time = time.time()
                parsed_requirements = await self._parse_requirements_enhanced(requirements, constraints)
                parsing_duration_ms = (time.time() - parsing_start_time) * 1000
                
                # Track parsing step in monitoring
                if monitoring_session:
                    try:
                        await monitoring_service.track_parsing_step(
                            session_id=session_id,
                            step_name='enhanced_requirement_parsing',
                            input_data={
                                'requirements_keys': list(requirements.keys()),
                                'constraints': constraints,
                                'requirements_size': len(str(requirements))
                            },
                            output_data={
                                'explicit_technologies': [t.name for t in parsed_requirements.explicit_technologies],
                                'confidence_score': parsed_requirements.confidence_score,
                                'context_clues': len(parsed_requirements.context_clues.domain_indicators),
                                'integration_patterns': len(parsed_requirements.integration_patterns)
                            },
                            duration_ms=parsing_duration_ms,
                            success=True
                        )
                    except Exception as track_error:
                        self.logger.debug(f"Could not track parsing step: {track_error}")
                
                self.tech_logger.log_info(
                    LogCategory.REQUIREMENT_PARSING,
                    "TechStackGenerator",
                    "parse_requirements",
                    f"Parsed requirements: {len(parsed_requirements.explicit_technologies)} explicit technologies found",
                    {
                        'explicit_technologies': [t.name for t in parsed_requirements.explicit_technologies],
                        'context_clues': len(parsed_requirements.context_clues.domain_indicators),
                        'integration_patterns': len(parsed_requirements.integration_patterns),
                        'parsing_duration_ms': parsing_duration_ms
                    }
                )
            
            with self.debug_tracer.trace_step(trace_id, "context_extraction", {'parsed_requirements': len(parsed_requirements.explicit_technologies)}):
                # Step 2: Build technology context
                extraction_start_time = time.time()
                tech_context = self.context_extractor.build_context(parsed_requirements)
                extraction_duration_ms = (time.time() - extraction_start_time) * 1000
                
                # Track extraction step in monitoring
                if monitoring_session:
                    try:
                        extracted_technologies = list(tech_context.explicit_technologies.keys()) + list(tech_context.contextual_technologies.keys())
                        confidence_scores = {**tech_context.explicit_technologies, **tech_context.contextual_technologies}
                        
                        await monitoring_service.track_extraction_step(
                            session_id=session_id,
                            extraction_type='context_aware_extraction',
                            extracted_technologies=extracted_technologies,
                            confidence_scores=confidence_scores,
                            context_data={
                                'ecosystem_preference': tech_context.ecosystem_preference,
                                'domain_context': str(tech_context.domain_context),
                                'explicit_count': len(tech_context.explicit_technologies),
                                'contextual_count': len(tech_context.contextual_technologies)
                            },
                            duration_ms=extraction_duration_ms,
                            success=True
                        )
                    except Exception as track_error:
                        self.logger.debug(f"Could not track extraction step: {track_error}")
                
                self.tech_logger.log_info(
                    LogCategory.CONTEXT_ANALYSIS,
                    "TechStackGenerator",
                    "build_context",
                    f"Built technology context with {len(tech_context.explicit_technologies)} explicit and {len(tech_context.contextual_technologies)} contextual technologies",
                    {
                        'explicit_technologies': list(tech_context.explicit_technologies.keys()),
                        'contextual_technologies': list(tech_context.contextual_technologies.keys()),
                        'ecosystem_preference': tech_context.ecosystem_preference,
                        'domain_context': tech_context.domain_context.__dict__ if hasattr(tech_context.domain_context, '__dict__') else str(tech_context.domain_context),
                        'extraction_duration_ms': extraction_duration_ms
                    }
                )
            
            with self.debug_tracer.trace_step(trace_id, "technology_prioritization"):
                # Step 3: Enhanced context-aware prioritization
                context_weights = self.context_prioritizer.calculate_context_weights(parsed_requirements, tech_context)
                
                # Detect and handle ambiguities
                ambiguities = self.context_prioritizer.detect_requirement_ambiguity(parsed_requirements)
                if ambiguities:
                    self.tech_logger.log_warning(
                        LogCategory.REQUIREMENT_PARSING,
                        "TechStackGenerator",
                        "detect_ambiguity",
                        f"Detected {len(ambiguities)} requirement ambiguities",
                        {
                            'ambiguities': [
                                {
                                    'type': amb.ambiguity_type.value,
                                    'description': amb.description,
                                    'impact': amb.impact_level,
                                    'confidence': amb.confidence
                                }
                                for amb in ambiguities
                            ]
                        }
                    )
                    
                    # Resolve conflicts using context-based tie-breaking
                    resolutions = self.context_prioritizer.resolve_technology_conflicts(ambiguities, tech_context)
                    if resolutions:
                        self.tech_logger.log_info(
                            LogCategory.CONTEXT_ANALYSIS,
                            "TechStackGenerator",
                            "resolve_conflicts",
                            f"Resolved {len(resolutions)} technology conflicts",
                            {'resolutions': resolutions}
                        )
                
                # Apply domain-specific preferences
                domain_preferences = self.context_prioritizer.implement_domain_specific_preferences(
                    tech_context, parsed_requirements.domain_context
                )
                
                # Convert context weights to prioritized technologies for backward compatibility
                prioritized_technologies = {
                    tech: weight.final_weight 
                    for tech, weight in context_weights.items()
                }
                
                # Get prioritization summary
                prioritization_summary = self.context_prioritizer.get_prioritization_summary(context_weights)
                
                self.tech_logger.log_info(
                    LogCategory.TECHNOLOGY_EXTRACTION,
                    "TechStackGenerator",
                    "prioritize_technologies",
                    f"Enhanced prioritization completed: {prioritization_summary['total_technologies']} technologies processed",
                    {
                        'prioritization_summary': prioritization_summary,
                        'domain_preferences_applied': len(domain_preferences),
                        'ambiguities_detected': len(ambiguities),
                        'high_priority_count': prioritization_summary['weight_distribution']['critical'] + prioritization_summary['weight_distribution']['high']
                    }
                )
            
            # Step 4: Generate tech stack using context-aware LLM prompts
            if self.llm_provider:
                try:
                    with self.debug_tracer.trace_step(trace_id, "llm_generation"):
                        # Set session context for LLM generation
                        self._current_session_id = session_id
                        if monitoring_session:
                            self._monitoring_service = monitoring_service
                        
                        tech_stack = await self._generate_context_aware_llm_tech_stack(
                            parsed_requirements, tech_context, prioritized_technologies, matches
                        )
                    
                    with self.debug_tracer.trace_step(trace_id, "validation_and_enforcement"):
                        # Step 5: Validate and enforce explicit technology inclusion
                        validated_stack = await self._validate_and_enforce_explicit_inclusion(
                            tech_stack, parsed_requirements, tech_context
                        )
                    
                    with self.debug_tracer.trace_step(trace_id, "catalog_auto_addition"):
                        # Step 6: Auto-add missing technologies to catalog
                        if self.auto_update_catalog:
                            await self._auto_add_missing_technologies(validated_stack, tech_context)
                    
                    with self.debug_tracer.trace_step(trace_id, "final_validation"):
                        # Step 7: Final compatibility validation
                        final_stack = await self._perform_final_validation(validated_stack, tech_context)
                    
                    # Update metrics
                    self._update_generation_metrics(parsed_requirements, final_stack)
                    
                    # Record performance metrics
                    duration_ms = self.performance_monitor.end_performance_tracking(
                        request_id,
                        LogCategory.PERFORMANCE,
                        "TechStackGenerator",
                        "generate_tech_stack"
                    )
                    
                    # Complete monitoring session
                    if monitoring_session:
                        try:
                            explicit_inclusion_rate = self._calculate_explicit_inclusion_rate(parsed_requirements, final_stack)
                            
                            await monitoring_service.complete_generation_monitoring(
                                session_id=session_id,
                                final_tech_stack=final_stack,
                                generation_metrics={
                                    'extraction_accuracy': parsed_requirements.confidence_score,
                                    'explicit_inclusion_rate': explicit_inclusion_rate,
                                    'context_aware_selections': len([t for t in final_stack if t in tech_context.contextual_technologies]),
                                    'total_processing_time_ms': duration_ms,
                                    'generation_method': 'llm_enhanced',
                                    'explicit_technologies': [t.name for t in parsed_requirements.explicit_technologies],
                                    'final_stack_size': len(final_stack)
                                },
                                success=True
                            )
                        except Exception as complete_error:
                            self.logger.debug(f"Could not complete monitoring session: {complete_error}")
                    
                    # Log successful completion
                    self.tech_logger.log_info(
                        LogCategory.TECHNOLOGY_EXTRACTION,
                        "TechStackGenerator",
                        "generate_tech_stack",
                        f"Successfully generated tech stack with {len(final_stack)} technologies in {duration_ms:.2f}ms",
                        {
                            'final_stack': final_stack,
                            'duration_ms': duration_ms,
                            'explicit_inclusion_rate': self._calculate_explicit_inclusion_rate(parsed_requirements, final_stack),
                            'generation_method': 'llm_enhanced'
                        }
                    )
                    
                    # End debug trace
                    self.debug_tracer.end_trace(trace_id, success=True)
                    
                    return final_stack
                    
                except Exception as e:
                    # Log LLM generation failure
                    error_id = self.error_logger.log_llm_error(
                        "TechStackGenerator",
                        "generate_context_aware_llm_tech_stack",
                        self.llm_provider.__class__.__name__ if self.llm_provider else "unknown",
                        "unknown",  # model would need to be passed from provider
                        "Tech stack generation prompt",
                        e
                    )
                    
                    self.tech_logger.log_warning(
                        LogCategory.LLM_INTERACTION,
                        "TechStackGenerator",
                        "generate_tech_stack",
                        f"LLM generation failed, falling back to rule-based generation. Error ID: {error_id}",
                        {'error_id': error_id, 'fallback_method': 'rule_based'}
                    )
                    
                    # Fall back to enhanced rule-based generation
                    with self.debug_tracer.trace_step(trace_id, "fallback_rule_based_generation"):
                        return await self._generate_enhanced_rule_based_tech_stack(
                            parsed_requirements, tech_context, prioritized_technologies, matches
                        )
            else:
                # Use enhanced rule-based generation
                with self.debug_tracer.trace_step(trace_id, "rule_based_generation"):
                    return await self._generate_enhanced_rule_based_tech_stack(
                        parsed_requirements, tech_context, prioritized_technologies, matches
                    )
                
        except Exception as e:
            # Log critical error
            error_id = self.error_logger.log_error_with_context(
                "TechStackGenerator",
                "generate_tech_stack",
                e,
                ErrorSeverity.CRITICAL,
                ErrorCategory.SYSTEM_ERROR,
                input_data={
                    'requirements': requirements,
                    'constraints': constraints,
                    'matches_count': len(matches)
                },
                suggested_fixes=[
                    "Check requirement format and structure",
                    "Verify LLM provider configuration",
                    "Check technology catalog availability",
                    "Review system logs for detailed error information"
                ]
            )
            
            self.tech_logger.log_error(
                LogCategory.ERROR_HANDLING,
                "TechStackGenerator",
                "generate_tech_stack",
                f"Critical error in tech stack generation. Error ID: {error_id}",
                {
                    'error_id': error_id,
                    'session_id': session_id,
                    'request_id': request_id,
                    'fallback_method': 'legacy'
                },
                exception=e
            )
            
            # Complete monitoring session with error
            if monitoring_session:
                try:
                    await monitoring_service.complete_generation_monitoring(
                        session_id=session_id,
                        final_tech_stack=[],
                        generation_metrics={
                            'error': True,
                            'error_message': str(e),
                            'generation_method': 'failed'
                        },
                        success=False,
                        error_message=str(e)
                    )
                except Exception as complete_error:
                    self.logger.debug(f"Could not complete monitoring session with error: {complete_error}")
            
            # End debug trace with error
            self.debug_tracer.end_trace(trace_id, success=False, error_message=str(e))
            
            # Fallback to original method for backward compatibility
            return await self._generate_legacy_tech_stack(matches, requirements, constraints)
        
        finally:
            # Clear request context
            self.tech_logger.clear_request_context()
    
    async def _parse_requirements_enhanced(self, 
                                         requirements: Dict[str, Any], 
                                         constraints: Optional[Dict[str, Any]] = None) -> ParsedRequirements:
        """Parse requirements using enhanced parser.
        
        Args:
            requirements: User requirements
            constraints: Additional constraints
            
        Returns:
            ParsedRequirements object
        """
        # Merge constraints into requirements for parsing
        enhanced_requirements = requirements.copy()
        if constraints:
            enhanced_requirements['constraints'] = constraints
        
        parsed_req = self.enhanced_parser.parse_requirements(enhanced_requirements)
        
        self.logger.debug(f"Parsed {len(parsed_req.explicit_technologies)} explicit technologies "
                         f"with confidence {parsed_req.confidence_score:.2f}")
        
        return parsed_req
    
    async def _generate_context_aware_llm_tech_stack(self,
                                                   parsed_req: ParsedRequirements,
                                                   tech_context: TechContext,
                                                   prioritized_techs: Dict[str, float],
                                                   matches: List[MatchResult]) -> List[str]:
        """Generate tech stack using context-aware LLM prompts.
        
        Args:
            parsed_req: Parsed requirements
            tech_context: Technology context
            prioritized_techs: Prioritized technologies
            matches: Pattern matching results
            
        Returns:
            Generated tech stack
        """
        # Generate context-aware prompt
        prompt = self.prompt_generator.generate_tech_stack_prompt(
            tech_context, parsed_req, prioritized_techs, matches
        )
        
        # Validate prompt effectiveness
        validation_result = self.prompt_generator.validate_prompt(prompt, tech_context)
        if not validation_result.is_valid:
            self.logger.warning(f"Prompt validation issues: {validation_result.issues}")
            # Apply suggestions to improve prompt
            prompt = self.prompt_generator.apply_prompt_improvements(prompt, validation_result.suggestions)
        
        # Generate response using LLM
        start_time = datetime.now()
        
        try:
            response = await self.llm_provider.generate(prompt, purpose="enhanced_tech_stack_generation")
            
            # Calculate latency
            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Parse and validate LLM response
            tech_stack = self._parse_llm_response(response)
            
            # Track LLM interaction in monitoring (if available)
            session_id = getattr(self, '_current_session_id', 'enhanced_tech_stack_generation')
            monitoring_service = getattr(self, '_monitoring_service', None)
            
            if monitoring_service and hasattr(monitoring_service, 'track_llm_interaction'):
                try:
                    # Extract token usage if available
                    token_usage = {}
                    if hasattr(response, 'usage'):
                        token_usage = {
                            'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                            'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
                            'total_tokens': getattr(response.usage, 'total_tokens', 0)
                        }
                    elif isinstance(response, dict) and 'usage' in response:
                        token_usage = response['usage']
                    
                    await monitoring_service.track_llm_interaction(
                        session_id=session_id,
                        provider=self.llm_provider.__class__.__name__,
                        model=getattr(self.llm_provider, 'model', 'unknown'),
                        prompt_data={
                            'prompt_type': 'context_aware_tech_stack_generation',
                            'context_size': len(prompt),
                            'explicit_technologies': list(tech_context.explicit_technologies.keys()),
                            'contextual_technologies': list(tech_context.contextual_technologies.keys()),
                            'prompt_validated': validation_result.is_valid if 'validation_result' in locals() else True
                        },
                        response_data={
                            'generated_technologies': tech_stack,
                            'response_type': type(response).__name__,
                            'tech_stack_size': len(tech_stack)
                        },
                        token_usage=token_usage,
                        duration_ms=float(latency_ms),
                        success=True
                    )
                except Exception as track_error:
                    self.logger.debug(f"Could not track LLM interaction: {track_error}")
            
            # Log the LLM call for audit
            await log_llm_call(
                session_id=session_id,
                provider=self.llm_provider.__class__.__name__,
                model=getattr(self.llm_provider, 'model', 'unknown'),
                latency_ms=latency_ms,
                prompt=prompt,
                response=json.dumps(response) if isinstance(response, dict) else str(response),
                purpose="enhanced_tech_stack_generation"
            )
            
            self.generation_metrics['context_aware_selections'] += 1
            return tech_stack
            
        except Exception as e:
            # Track failed LLM interaction
            if monitoring_service and hasattr(monitoring_service, 'track_llm_interaction'):
                try:
                    await monitoring_service.track_llm_interaction(
                        session_id=session_id,
                        provider=self.llm_provider.__class__.__name__,
                        model=getattr(self.llm_provider, 'model', 'unknown'),
                        prompt_data={
                            'prompt_type': 'context_aware_tech_stack_generation',
                            'context_size': len(prompt),
                            'error_occurred': True
                        },
                        response_data={},
                        duration_ms=float((datetime.now() - start_time).total_seconds() * 1000),
                        success=False,
                        error_message=str(e)
                    )
                except Exception as track_error:
                    self.logger.debug(f"Could not track failed LLM interaction: {track_error}")
            
            self.logger.error(f"LLM generation failed: {e}")
            raise
    
    async def _validate_and_enforce_explicit_inclusion(self,
                                                     tech_stack: List[str],
                                                     parsed_req: ParsedRequirements,
                                                     tech_context: TechContext) -> List[str]:
        """Validate tech stack and enforce 70% explicit technology inclusion.
        
        Args:
            tech_stack: Generated tech stack
            parsed_req: Parsed requirements
            tech_context: Technology context
            
        Returns:
            Validated tech stack with enforced explicit inclusion
        """
        validation_start_time = time.time()
        session_id = getattr(self, '_current_session_id', 'unknown')
        monitoring_service = getattr(self, '_monitoring_service', None)
        
        if not parsed_req.explicit_technologies:
            # Track validation step for empty explicit technologies
            if monitoring_service and hasattr(monitoring_service, 'track_validation_step'):
                try:
                    await monitoring_service.track_validation_step(
                        session_id=session_id,
                        validation_type='explicit_technology_inclusion',
                        input_technologies=tech_stack,
                        validation_results={
                            'explicit_technologies_count': 0,
                            'inclusion_rate': 1.0,
                            'enforcement_applied': False,
                            'technologies_added': 0
                        },
                        conflicts_detected=[],
                        resolutions_applied=[],
                        duration_ms=(time.time() - validation_start_time) * 1000,
                        success=True
                    )
                except Exception as track_error:
                    self.logger.debug(f"Could not track validation step: {track_error}")
            
            return tech_stack
        
        # Calculate explicit technology inclusion rate
        explicit_tech_names = {tech.canonical_name or tech.name for tech in parsed_req.explicit_technologies}
        included_explicit = set(tech_stack) & explicit_tech_names
        inclusion_rate = len(included_explicit) / len(explicit_tech_names)
        
        self.logger.info(f"Explicit technology inclusion rate: {inclusion_rate:.2%}")
        
        conflicts_detected = []
        resolutions_applied = []
        technologies_added = 0
        
        # Enforce 70% minimum requirement
        if inclusion_rate < 0.7:
            self.logger.warning(f"Inclusion rate {inclusion_rate:.2%} below 70% threshold, enforcing explicit technologies")
            
            # Record conflict for monitoring
            conflicts_detected.append({
                'type': 'explicit_inclusion_rate_low',
                'description': f'Explicit technology inclusion rate {inclusion_rate:.2%} below 70% threshold',
                'severity': 'warning',
                'technologies': list(explicit_tech_names - set(tech_stack))
            })
            
            # Add missing explicit technologies
            missing_explicit = explicit_tech_names - set(tech_stack)
            
            # Prioritize by confidence score
            missing_with_confidence = []
            for tech in parsed_req.explicit_technologies:
                tech_name = tech.canonical_name or tech.name
                if tech_name in missing_explicit:
                    missing_with_confidence.append((tech_name, tech.confidence))
            
            # Sort by confidence and add highest confidence technologies
            missing_with_confidence.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate how many to add to reach 70%
            import math
            target_count = max(1, math.ceil(len(explicit_tech_names) * 0.7))
            current_explicit_count = len(included_explicit)
            needed_count = target_count - current_explicit_count
            
            for tech_name, confidence in missing_with_confidence[:needed_count]:
                # Check if technology exists in catalog or can be auto-added
                if self.catalog_manager.lookup_technology(tech_name) or self.auto_update_catalog:
                    tech_stack.append(tech_name)
                    technologies_added += 1
                    self.logger.info(f"Added explicit technology: {tech_name} (confidence: {confidence:.2f})")
                    
                    # Record resolution for monitoring
                    resolutions_applied.append({
                        'type': 'explicit_technology_addition',
                        'description': f'Added explicit technology: {tech_name}',
                        'technology': tech_name,
                        'confidence': confidence
                    })
        
        validation_duration_ms = (time.time() - validation_start_time) * 1000
        final_inclusion_rate = len(set(tech_stack) & explicit_tech_names) / len(explicit_tech_names)
        
        # Track validation step in monitoring
        if monitoring_service and hasattr(monitoring_service, 'track_validation_step'):
            try:
                await monitoring_service.track_validation_step(
                    session_id=session_id,
                    validation_type='explicit_technology_inclusion',
                    input_technologies=tech_stack,
                    validation_results={
                        'explicit_technologies_count': len(explicit_tech_names),
                        'initial_inclusion_rate': inclusion_rate,
                        'final_inclusion_rate': final_inclusion_rate,
                        'enforcement_applied': inclusion_rate < 0.7,
                        'technologies_added': technologies_added,
                        'threshold_met': final_inclusion_rate >= 0.7
                    },
                    conflicts_detected=conflicts_detected,
                    resolutions_applied=resolutions_applied,
                    duration_ms=validation_duration_ms,
                    success=True
                )
            except Exception as track_error:
                self.logger.debug(f"Could not track validation step: {track_error}")
        
        return tech_stack
    
    async def _auto_add_missing_technologies(self, tech_stack: List[str], tech_context: TechContext) -> None:
        """Auto-add missing technologies to catalog.
        
        Args:
            tech_stack: Generated tech stack
            tech_context: Technology context
        """
        if not self.auto_update_catalog:
            return
        
        auto_add_start_time = time.time()
        session_id = getattr(self, '_current_session_id', 'unknown')
        monitoring_service = getattr(self, '_monitoring_service', None)
        
        technologies_added = []
        technologies_failed = []
        
        for tech_name in tech_stack:
            if not self.catalog_manager.lookup_technology(tech_name):
                try:
                    # Auto-add technology with context
                    context_info = {
                        'source': 'llm_generation',
                        'domain': tech_context.domain_context.primary_domain if tech_context.domain_context else None,
                        'ecosystem': tech_context.ecosystem_preference,
                        'generation_timestamp': datetime.now().isoformat()
                    }
                    
                    tech_entry = self.catalog_manager.auto_add_technology(tech_name, context_info)
                    self.logger.info(f"Auto-added technology to catalog: {tech_name}")
                    self.generation_metrics['catalog_auto_additions'] += 1
                    technologies_added.append({
                        'technology': tech_name,
                        'context': context_info,
                        'entry_id': tech_entry.id if hasattr(tech_entry, 'id') else None
                    })
                    
                except Exception as e:
                    self.logger.error(f"Failed to auto-add technology {tech_name}: {e}")
                    technologies_failed.append({
                        'technology': tech_name,
                        'error': str(e)
                    })
        
        auto_add_duration_ms = (time.time() - auto_add_start_time) * 1000
        
        # Track catalog auto-addition step in monitoring
        if monitoring_service and hasattr(monitoring_service, 'track_validation_step'):
            try:
                await monitoring_service.track_validation_step(
                    session_id=session_id,
                    validation_type='catalog_auto_addition',
                    input_technologies=tech_stack,
                    validation_results={
                        'technologies_processed': len(tech_stack),
                        'technologies_added': len(technologies_added),
                        'technologies_failed': len(technologies_failed),
                        'auto_update_enabled': self.auto_update_catalog,
                        'success_rate': len(technologies_added) / max(1, len(technologies_added) + len(technologies_failed))
                    },
                    conflicts_detected=[],
                    resolutions_applied=[{
                        'type': 'catalog_addition',
                        'description': f'Auto-added technology: {tech["technology"]}',
                        'technology': tech['technology']
                    } for tech in technologies_added],
                    duration_ms=auto_add_duration_ms,
                    success=len(technologies_failed) == 0
                )
            except Exception as track_error:
                self.logger.debug(f"Could not track catalog auto-addition step: {track_error}")
    
    async def _perform_final_validation(self, tech_stack: List[str], tech_context: TechContext) -> List[str]:
        """Perform final compatibility validation on tech stack.
        
        Args:
            tech_stack: Tech stack to validate
            tech_context: Technology context
            
        Returns:
            Validated and potentially modified tech stack
        """
        validation_start_time = time.time()
        session_id = getattr(self, '_current_session_id', 'unknown')
        monitoring_service = getattr(self, '_monitoring_service', None)
        
        try:
            validation_report = self.compatibility_validator.validate_tech_stack(
                tech_stack, tech_context.priority_weights
            )
            
            compatibility_result = validation_report.compatibility_result
            validation_duration_ms = (time.time() - validation_start_time) * 1000
            
            conflicts_detected = []
            resolutions_applied = []
            
            if not compatibility_result.is_compatible:
                self.logger.warning(f"Tech stack validation issues: {len(compatibility_result.conflicts)} conflicts found")
                
                # Log conflicts for debugging and monitoring
                for conflict in compatibility_result.conflicts:
                    self.logger.warning(f"Conflict: {conflict.description} ({conflict.severity.value})")
                    conflicts_detected.append({
                        'type': conflict.conflict_type.value if hasattr(conflict, 'conflict_type') else 'unknown',
                        'description': conflict.description,
                        'severity': conflict.severity.value,
                        'technologies': getattr(conflict, 'technologies', [])
                    })
                
                # Use the validated tech stack from the report
                # The validator has already applied fixes and removed incompatible technologies
                validated_stack = validation_report.validated_tech_stack
                
                if len(validated_stack) != len(tech_stack):
                    removed_count = len(tech_stack) - len(validated_stack)
                    removed_techs = set(tech_stack) - set(validated_stack)
                    self.logger.info(f"Validation removed {removed_count} incompatible technologies: {removed_techs}")
                    
                    # Record resolutions applied
                    for tech in removed_techs:
                        resolutions_applied.append({
                            'type': 'technology_removal',
                            'description': f'Removed incompatible technology: {tech}',
                            'technology': tech
                        })
                
                final_stack = validated_stack
            else:
                final_stack = tech_stack
            
            # Track validation step in monitoring
            if monitoring_service and hasattr(monitoring_service, 'track_validation_step'):
                try:
                    await monitoring_service.track_validation_step(
                        session_id=session_id,
                        validation_type='final_compatibility_validation',
                        input_technologies=tech_stack,
                        validation_results={
                            'is_compatible': compatibility_result.is_compatible,
                            'conflicts_count': len(compatibility_result.conflicts),
                            'technologies_removed': len(tech_stack) - len(final_stack),
                            'ecosystem_consistent': getattr(compatibility_result, 'ecosystem_consistent', True),
                            'compatibility_score': getattr(compatibility_result, 'compatibility_score', 1.0)
                        },
                        conflicts_detected=conflicts_detected,
                        resolutions_applied=resolutions_applied,
                        duration_ms=validation_duration_ms,
                        success=True
                    )
                except Exception as track_error:
                    self.logger.debug(f"Could not track validation step: {track_error}")
            
            return final_stack
            
        except Exception as e:
            validation_duration_ms = (time.time() - validation_start_time) * 1000
            
            # Track failed validation step
            if monitoring_service and hasattr(monitoring_service, 'track_validation_step'):
                try:
                    await monitoring_service.track_validation_step(
                        session_id=session_id,
                        validation_type='final_compatibility_validation',
                        input_technologies=tech_stack,
                        validation_results={'error': True},
                        conflicts_detected=[],
                        resolutions_applied=[],
                        duration_ms=validation_duration_ms,
                        success=False,
                        error_message=str(e)
                    )
                except Exception as track_error:
                    self.logger.debug(f"Could not track failed validation step: {track_error}")
            
            self.logger.error(f"Final validation failed: {e}")
            return tech_stack
    
    async def _generate_enhanced_rule_based_tech_stack(self,
                                                     parsed_req: ParsedRequirements,
                                                     tech_context: TechContext,
                                                     prioritized_techs: Dict[str, float],
                                                     matches: List[MatchResult]) -> List[str]:
        """Generate tech stack using enhanced rule-based approach.
        
        Args:
            parsed_req: Parsed requirements
            tech_context: Technology context
            prioritized_techs: Prioritized technologies
            matches: Pattern matching results
            
        Returns:
            Rule-based tech stack
        """
        rule_based_start_time = time.time()
        session_id = getattr(self, '_current_session_id', 'unknown')
        monitoring_service = getattr(self, '_monitoring_service', None)
        
        tech_stack = []
        
        # Start with explicit technologies (highest priority)
        for tech in parsed_req.explicit_technologies:
            tech_name = tech.canonical_name or tech.name
            if tech_name not in tech_context.banned_tools:
                tech_stack.append(tech_name)
        
        # Add contextual technologies based on priority
        sorted_contextual = sorted(
            tech_context.contextual_technologies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for tech_name, confidence in sorted_contextual:
            if (tech_name not in tech_stack and 
                tech_name not in tech_context.banned_tools and 
                len(tech_stack) < 12):  # Limit total technologies
                tech_stack.append(tech_name)
        
        # Add pattern-based technologies if needed
        pattern_technologies = self._extract_pattern_technologies(matches)
        for tech in pattern_technologies.get("high_confidence", []):
            if (tech not in tech_stack and 
                tech not in tech_context.banned_tools and 
                len(tech_stack) < 12):
                tech_stack.append(tech)
        
        rule_based_duration_ms = (time.time() - rule_based_start_time) * 1000
        
        # Track rule-based generation in monitoring
        if monitoring_service and hasattr(monitoring_service, 'track_llm_interaction'):
            try:
                await monitoring_service.track_llm_interaction(
                    session_id=session_id,
                    provider='rule_based_generator',
                    model='enhanced_rule_based',
                    prompt_data={
                        'generation_type': 'rule_based',
                        'explicit_technologies': [t.name for t in parsed_req.explicit_technologies],
                        'contextual_technologies': list(tech_context.contextual_technologies.keys()),
                        'pattern_matches': len(matches)
                    },
                    response_data={
                        'generated_technologies': tech_stack,
                        'tech_stack_size': len(tech_stack),
                        'explicit_included': len([t for t in tech_stack if t in [tech.name for tech in parsed_req.explicit_technologies]]),
                        'contextual_included': len([t for t in tech_stack if t in tech_context.contextual_technologies])
                    },
                    duration_ms=rule_based_duration_ms,
                    success=True
                )
            except Exception as track_error:
                self.logger.debug(f"Could not track rule-based generation: {track_error}")
        
        self.logger.info(f"Generated enhanced rule-based tech stack with {len(tech_stack)} technologies")
        return tech_stack
    
    def _validate_monitoring_data(self, session_id: str, data: Dict[str, Any], operation: str) -> bool:
        """Validate monitoring data for quality and completeness.
        
        Args:
            session_id: Session identifier
            data: Monitoring data to validate
            operation: Operation being monitored
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['session_id', 'timestamp', 'operation']
            for field in required_fields:
                if field not in data and field != 'session_id':  # session_id is passed separately
                    self.logger.warning(f"Missing required field '{field}' in monitoring data for {operation}")
                    return False
            
            # Validate session_id format
            if not session_id or not isinstance(session_id, str):
                self.logger.warning(f"Invalid session_id format in monitoring data for {operation}")
                return False
            
            # Validate data types and ranges
            if 'duration_ms' in data:
                duration = data['duration_ms']
                if not isinstance(duration, (int, float)) or duration < 0:
                    self.logger.warning(f"Invalid duration_ms value in monitoring data for {operation}: {duration}")
                    return False
                
                # Check for unreasonable durations (> 5 minutes)
                if duration > 300000:
                    self.logger.warning(f"Unusually high duration_ms in monitoring data for {operation}: {duration}ms")
            
            # Validate confidence scores
            if 'confidence_scores' in data:
                scores = data['confidence_scores']
                if isinstance(scores, dict):
                    for tech, score in scores.items():
                        if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                            self.logger.warning(f"Invalid confidence score for {tech} in {operation}: {score}")
                            return False
            
            # Validate technology lists
            for field in ['extracted_technologies', 'final_tech_stack', 'input_technologies']:
                if field in data:
                    tech_list = data[field]
                    if not isinstance(tech_list, list):
                        self.logger.warning(f"Invalid {field} format in monitoring data for {operation}")
                        return False
                    
                    # Check for empty technology names
                    for tech in tech_list:
                        if not tech or not isinstance(tech, str):
                            self.logger.warning(f"Invalid technology name in {field} for {operation}: {tech}")
                            return False
            
            # Validate success/error states
            if 'success' in data:
                success = data['success']
                if not isinstance(success, bool):
                    self.logger.warning(f"Invalid success value in monitoring data for {operation}: {success}")
                    return False
                
                # If success is False, error_message should be present
                if not success and 'error_message' not in data:
                    self.logger.warning(f"Missing error_message for failed operation {operation}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating monitoring data for {operation}: {e}")
            return False
    
    def _calculate_explicit_inclusion_rate(self, parsed_req: ParsedRequirements, tech_stack: List[str]) -> float:
        """Calculate the rate of explicit technology inclusion in the tech stack.
        
        Args:
            parsed_req: Parsed requirements with explicit technologies
            tech_stack: Generated tech stack
            
        Returns:
            Inclusion rate as a float between 0.0 and 1.0
        """
        if not parsed_req.explicit_technologies:
            return 1.0  # Perfect score when no explicit technologies exist
        
        explicit_tech_names = {tech.canonical_name or tech.name for tech in parsed_req.explicit_technologies}
        included_explicit = set(tech_stack) & explicit_tech_names
        
        return len(included_explicit) / len(explicit_tech_names)
    
    async def _generate_legacy_tech_stack(self,
                                        matches: List[MatchResult],
                                        requirements: Dict[str, Any],
                                        constraints: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate tech stack using legacy method for backward compatibility.
        
        Args:
            matches: Pattern matching results
            requirements: User requirements
            constraints: Constraints including banned tools
            
        Returns:
            Legacy tech stack
        """
        self.logger.info("Using legacy tech stack generation for backward compatibility")
        
        # Extract constraint information
        banned_tools = set()
        required_integrations = []
        
        if constraints:
            banned_tools.update(constraints.get("banned_tools", []))
            required_integrations.extend(constraints.get("required_integrations", []))
        
        # Add banned tools from patterns
        for match in matches:
            if hasattr(match, 'constraints') and match.constraints:
                banned_tools.update(match.constraints.get("banned_tools", []))
        
        # Get available technologies from patterns
        pattern_technologies = self._extract_pattern_technologies(matches)
        
        # Use original LLM method if available
        if self.llm_provider:
            try:
                llm_tech_stack = await self._generate_llm_tech_stack(
                    requirements, pattern_technologies, banned_tools, required_integrations, constraints
                )
                if llm_tech_stack:
                    return llm_tech_stack
            except Exception as e:
                self.logger.error(f"Legacy LLM tech stack generation failed: {e}")
        
        # Fallback to original rule-based generation
        return self._generate_rule_based_tech_stack(
            matches, requirements, pattern_technologies, banned_tools, required_integrations
        )
    
    def _parse_llm_response(self, response: Any) -> List[str]:
        """Parse LLM response to extract tech stack.
        
        Args:
            response: LLM response (dict or string)
            
        Returns:
            List of technology names
        """
        try:
            if isinstance(response, dict):
                # Handle structured response
                if 'tech_stack' in response:
                    tech_stack = response['tech_stack']
                    if isinstance(tech_stack, list):
                        # Handle list of dicts or strings
                        technologies = []
                        for item in tech_stack:
                            if isinstance(item, dict):
                                technologies.append(item.get('name', str(item)))
                            else:
                                technologies.append(str(item))
                        return technologies
                    else:
                        return [str(tech_stack)]
                else:
                    # Try to extract from other fields
                    for key in ['technologies', 'recommendations', 'stack']:
                        if key in response:
                            return [str(tech) for tech in response[key]]
            
            elif isinstance(response, str):
                # Try to parse JSON from string
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return self._parse_llm_response(parsed)
                else:
                    # Extract technology names from text
                    return self._extract_technologies_from_text(response)
            
            # Fallback
            return [str(response)]
            
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            return []
    
    def _extract_technologies_from_text(self, text: str) -> List[str]:
        """Extract technology names from text response.
        
        Args:
            text: Text to extract technologies from
            
        Returns:
            List of extracted technology names
        """
        # Simple extraction - could be enhanced
        technologies = []
        
        # Look for common patterns
        import re
        
        # Pattern for bullet points or numbered lists
        patterns = [
            r'[-*•]\s*([A-Za-z][A-Za-z0-9\s\./_-]+)',
            r'\d+\.\s*([A-Za-z][A-Za-z0-9\s\./_-]+)',
            r'([A-Z][A-Za-z0-9\s\./_-]+)(?:\s*[-:]\s*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                tech_name = match.strip()
                if len(tech_name) > 2 and len(tech_name) < 50:  # Reasonable length
                    technologies.append(tech_name)
        
        return technologies[:10]  # Limit to 10 technologies
    
    def _update_generation_metrics(self, parsed_req: ParsedRequirements, final_stack: List[str]) -> None:
        """Update generation metrics.
        
        Args:
            parsed_req: Parsed requirements
            final_stack: Final generated tech stack
        """
        if parsed_req.explicit_technologies:
            explicit_tech_names = {tech.canonical_name or tech.name for tech in parsed_req.explicit_technologies}
            included_explicit = set(final_stack) & explicit_tech_names
            inclusion_rate = len(included_explicit) / len(explicit_tech_names)
            
            # Update running average
            total_gens = self.generation_metrics['total_generations']
            current_avg = self.generation_metrics['explicit_tech_inclusion_rate']
            new_avg = ((current_avg * (total_gens - 1)) + inclusion_rate) / total_gens
            self.generation_metrics['explicit_tech_inclusion_rate'] = new_avg
    
    def get_generation_metrics(self) -> Dict[str, Any]:
        """Get current generation metrics.
        
        Returns:
            Dictionary of generation metrics
        """
        return self.generation_metrics.copy()
    
    def learn_from_user_feedback(self, 
                                selected_technologies: List[str],
                                rejected_technologies: List[str],
                                domain: str,
                                context_patterns: List[str]) -> None:
        """Learn from user feedback to improve future recommendations.
        
        Args:
            selected_technologies: Technologies user selected/approved
            rejected_technologies: Technologies user rejected/removed
            domain: Domain context for the session
            context_patterns: Context patterns from the requirements
        """
        try:
            # Use context prioritizer to learn preferences
            self.context_prioritizer.learn_user_preferences(
                selected_technologies,
                rejected_technologies,
                domain,
                context_patterns
            )
            
            self.tech_logger.log_info(
                LogCategory.CONTEXT_ANALYSIS,
                "TechStackGenerator",
                "learn_user_preferences",
                f"Learned preferences from user feedback in {domain} domain",
                {
                    'selected_count': len(selected_technologies),
                    'rejected_count': len(rejected_technologies),
                    'domain': domain,
                    'context_patterns': context_patterns,
                    'selected_technologies': selected_technologies,
                    'rejected_technologies': rejected_technologies
                }
            )
            
        except Exception as e:
            self.error_logger.log_error(
                ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.MEDIUM,
                "TechStackGenerator",
                "learn_user_preferences",
                f"Failed to learn from user feedback: {e}",
                {'error': str(e), 'domain': domain}
            )
    
    def _extract_pattern_technologies(self, matches: List[MatchResult]) -> Dict[str, List[str]]:
        """Extract technologies from matched patterns.
        
        Args:
            matches: Pattern matching results
            
        Returns:
            Dictionary with pattern technologies organized by confidence
        """
        high_confidence = []  # > 0.8
        medium_confidence = []  # 0.5 - 0.8
        low_confidence = []  # < 0.5
        
        for match in matches:
            tech_stack = match.tech_stack or []
            
            if match.blended_score > 0.8:
                high_confidence.extend(tech_stack)
            elif match.blended_score > 0.5:
                medium_confidence.extend(tech_stack)
            else:
                low_confidence.extend(tech_stack)
        
        return {
            "high_confidence": list(set(high_confidence)),
            "medium_confidence": list(set(medium_confidence)),
            "low_confidence": list(set(low_confidence))
        }
    
    async def _generate_llm_tech_stack(self, 
                                     requirements: Dict[str, Any],
                                     pattern_technologies: Dict[str, List[str]],
                                     banned_tools: Set[str],
                                     required_integrations: List[str],
                                     constraints: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
        """Generate tech stack using LLM analysis.
        
        Args:
            requirements: User requirements
            pattern_technologies: Technologies from matched patterns
            banned_tools: Tools that cannot be used
            required_integrations: Required integration types
            
        Returns:
            LLM-generated tech stack or None if failed
        """
        # Prepare context for LLM
        available_tech_summary = self._summarize_available_technologies()
        pattern_tech_summary = self._summarize_pattern_technologies(pattern_technologies)
        
        prompt = f"""You are a senior software architect specializing in automation and AI systems. 
Your task is to recommend the most appropriate technology stack for a given automation requirement.

Consider:
1. The specific requirements and constraints
2. Technologies used in similar patterns (if any)
3. Available technologies in the organization
4. Banned/prohibited technologies
5. Required integrations
6. Performance, scalability, and maintainability

Provide a focused, practical tech stack - avoid generic or unnecessary technologies.
Focus on technologies that directly address the requirements.

**Requirements:**
- Description: {requirements.get('description', 'Not specified')}
- Domain: {requirements.get('domain', 'Not specified')}
- Volume: {requirements.get('volume', {})}
- Integrations needed: {requirements.get('integrations', [])}
- Data sensitivity: {requirements.get('data_sensitivity', 'Not specified')}
- Compliance: {requirements.get('compliance', [])}
- SLA requirements: {requirements.get('sla', {})}

**Available Technologies from Similar Patterns:**
{pattern_tech_summary}

**Available Technologies in Organization (PREFER THESE):**
{available_tech_summary}

**CRITICAL CONSTRAINTS (MUST BE ENFORCED):**
- Banned/Prohibited Technologies: {list(banned_tools) if banned_tools else 'None'}
- Required Integrations: {required_integrations if required_integrations else 'None'}
- Compliance Requirements: {constraints.get('compliance_requirements', []) if constraints else 'None'}
- Data Sensitivity Level: {constraints.get('data_sensitivity', 'Not specified') if constraints else 'Not specified'}
- Budget Constraints: {constraints.get('budget_constraints', 'Not specified') if constraints else 'Not specified'}
- Deployment Preference: {constraints.get('deployment_preference', 'Not specified') if constraints else 'Not specified'}

**CRITICAL INSTRUCTIONS:**
1. Analyze the requirements carefully
2. **STRONGLY PREFER technologies from "Available Technologies in Organization" list above**
3. **NEVER recommend any technology listed in "Banned/Prohibited Technologies"**
4. **MUST include all "Required Integrations" in your recommendations**
5. Consider compliance requirements when selecting technologies
6. Respect data sensitivity level and deployment preferences
7. Consider budget constraints (prefer open source if specified)
8. Select technologies that directly address the needs
9. Prefer technologies from similar patterns when suitable
10. Only suggest technologies that are necessary and justified
11. Provide 5-12 technologies maximum
12. **Use EXACT technology names from the "Available Technologies" list when possible**

**TECHNOLOGY SELECTION PRIORITY:**
1. First choice: Technologies from "Available Technologies in Organization" 
2. Second choice: Technologies from "Available Technologies from Similar Patterns"
3. Last resort: Other well-known technologies (but these will be categorized as "Other")

**CONSTRAINT ENFORCEMENT:**
- If a technology is banned, find suitable alternatives from the available technologies list
- If budget is "Low (Open source preferred)", prioritize open source solutions from available list
- If deployment is "On-premises only", avoid cloud-only services
- If data sensitivity is "Confidential" or "Restricted", prioritize secure, enterprise-grade solutions

**IMPORTANT:** Use exact technology names from the lists above. For example:
- Use "Prometheus" not "PrometheusClient" 
- Use "GitHub Actions" not "Github Actions"
- Use "HashiCorp Vault" not "Vault"
- Use "Grafana Loki" not "Loki"
- Use "Slack API" not "Slack"
- Use "LangGraph" not "Langgraph"
- Use "Jaeger" not "Jaeger Tracing"
- Use "Jira API" not "JIRA API"

Respond with a JSON object containing:
{{
    "tech_stack": ["Technology1", "Technology2", ...],
    "reasoning": "Brief explanation of why these technologies were chosen",
    "alternatives": ["Alt1", "Alt2", ...] // Optional alternatives if primary choices aren't available
}}"""
        
        try:
            # Log the LLM call for audit trail
            start_time = datetime.now()
            
            # Ensure prompt is a string (defensive programming)
            if not isinstance(prompt, str):
                self.logger.error(f"ERROR: Prompt is not a string! Type: {type(prompt)}")
                prompt = str(prompt)
                self.logger.info("Converted prompt to string")
            
            response = await self.llm_provider.generate(prompt, purpose="tech_stack_generation")
            
            # Calculate latency
            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Parse JSON response
            if isinstance(response, dict):
                # Response is already a dict (from fake provider)
                result = response
                response_str = json.dumps(result)
            elif isinstance(response, str):
                # Try to extract JSON from string response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response_str = json_match.group()
                    result = json.loads(response_str)
                else:
                    result = {"error": "Could not parse JSON from response"}
                    response_str = response
            else:
                # Fallback for unexpected response types
                self.logger.warning(f"Unexpected response type: {type(response)}")
                return None
            
            tech_stack = result.get("tech_stack", [])
            reasoning = result.get("reasoning", "")
            
            # Log the successful response
            await log_llm_call(
                session_id="tech_stack_generation",
                provider=self.llm_provider.__class__.__name__,
                model=getattr(self.llm_provider, 'model', 'unknown'),
                latency_ms=latency_ms,
                prompt=prompt,  # Now guaranteed to be a string
                response=response_str
            )
            
            # Update catalog with new technologies before validation (if enabled)
            if self.auto_update_catalog:
                await self._update_catalog_with_new_technologies(tech_stack)
            
            # Validate and filter tech stack
            validated_tech_stack = self._validate_tech_stack(tech_stack, banned_tools)
            
            self.logger.info(f"LLM tech stack reasoning: {reasoning}")
            return validated_tech_stack
            
        except Exception as e:
            self.logger.error(f"Failed to parse LLM tech stack response: {e}")
            
            # Try to log the failed LLM call for debugging
            try:
                end_time = datetime.now()
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                await log_llm_call(
                    session_id="tech_stack_generation",
                    provider=self.llm_provider.__class__.__name__,
                    model=getattr(self.llm_provider, 'model', 'unknown'),
                    latency_ms=latency_ms,
                    prompt=prompt,  # Now guaranteed to be a string
                    response=f"ERROR: {str(e)}",
                    purpose="tech_stack_generation_failed"
                )
            except Exception as log_error:
                self.logger.warning(f"Failed to log failed LLM call: {log_error}")
            
            return None
    
    def _summarize_available_technologies(self) -> str:
        """Summarize available technologies for LLM context.
        
        Returns:
            Formatted summary of available technologies
        """
        summary_parts = []
        
        categories = self.technology_catalog.get("categories", {})
        technologies = self.technology_catalog.get("technologies", {})
        
        for category_id, category_info in categories.items():
            category_name = category_info.get("name", category_id.title())
            tech_ids = category_info.get("technologies", [])
            
            if tech_ids:
                # Get actual technology names
                tech_names = []
                for tech_id in tech_ids[:10]:  # Limit to 10 per category
                    tech_info = technologies.get(tech_id, {})
                    tech_names.append(tech_info.get("name", tech_id))
                
                tech_list = ", ".join(tech_names)
                if len(tech_ids) > 10:
                    tech_list += f" (and {len(tech_ids) - 10} others)"
                
                summary_parts.append(f"- {category_name}: {tech_list}")
        
        return "\n".join(summary_parts) if summary_parts else "No specific technologies catalogued"
    
    def _summarize_pattern_technologies(self, pattern_technologies: Dict[str, List[str]]) -> str:
        """Summarize pattern technologies for LLM context.
        
        Args:
            pattern_technologies: Technologies organized by confidence
            
        Returns:
            Formatted summary
        """
        summary_parts = []
        
        if pattern_technologies.get("high_confidence"):
            summary_parts.append(f"- High confidence matches: {', '.join(pattern_technologies['high_confidence'])}")
        
        if pattern_technologies.get("medium_confidence"):
            summary_parts.append(f"- Medium confidence matches: {', '.join(pattern_technologies['medium_confidence'])}")
        
        if pattern_technologies.get("low_confidence"):
            summary_parts.append(f"- Low confidence matches: {', '.join(pattern_technologies['low_confidence'])}")
        
        return "\n".join(summary_parts) if summary_parts else "No similar patterns found"
    
    def _validate_tech_stack(self, tech_stack: List[str], banned_tools: Set[str]) -> List[str]:
        """Validate and filter tech stack against constraints.
        
        Args:
            tech_stack: Proposed tech stack
            banned_tools: Tools that cannot be used
            
        Returns:
            Validated tech stack
        """
        validated = []
        
        for tech in tech_stack:
            # Ensure tech is a string (handle cases where LLM returns dicts)
            if isinstance(tech, dict):
                # If it's a dict, try to extract the name
                tech_name = tech.get('name') or tech.get('technology') or str(tech)
                self.logger.warning(f"Tech stack item was dict, extracted name: {tech_name}")
                tech = tech_name
            elif not isinstance(tech, str):
                # Convert to string if it's not already
                tech = str(tech)
                self.logger.warning(f"Tech stack item was {type(tech)}, converted to string: {tech}")
            
            # Check if technology is banned (exact match or word boundary match)
            tech_lower = tech.lower()
            is_banned = False
            
            for banned in banned_tools:
                banned_lower = banned.lower()
                # Check for exact match first
                if tech_lower == banned_lower:
                    is_banned = True
                    break
                # Check if banned tool is a complete word within the tech name
                import re
                if re.search(r'\b' + re.escape(banned_lower) + r'\b', tech_lower):
                    is_banned = True
                    break
            
            if is_banned:
                self.logger.warning(f"Skipping banned technology: {tech}")
                continue
            
            validated.append(tech)
        
        return validated
    
    def _generate_rule_based_tech_stack(self, 
                                      matches: List[MatchResult],
                                      requirements: Dict[str, Any],
                                      pattern_technologies: Dict[str, List[str]],
                                      banned_tools: Set[str],
                                      required_integrations: List[str]) -> List[str]:
        """Generate tech stack using rule-based approach as fallback.
        
        Args:
            matches: Pattern matching results
            requirements: User requirements
            pattern_technologies: Technologies from patterns
            banned_tools: Banned technologies
            required_integrations: Required integrations
            
        Returns:
            Rule-based tech stack
        """
        tech_stack = []
        
        # Start with high-confidence pattern technologies
        tech_stack.extend(pattern_technologies.get("high_confidence", []))
        
        # Add medium-confidence if we don't have enough
        if len(tech_stack) < 3:
            tech_stack.extend(pattern_technologies.get("medium_confidence", []))
        
        # Add requirement-specific technologies
        domain = str(requirements.get("domain", "")).lower()
        description = str(requirements.get("description", "")).lower()
        
        # Domain-specific additions
        if "data" in domain or "processing" in description:
            tech_stack.extend(["pandas", "numpy"])
        
        if "api" in domain or "integration" in description:
            tech_stack.extend(["FastAPI", "httpx"])
        
        if "web" in domain or "scraping" in description:
            tech_stack.extend(["requests", "BeautifulSoup"])
        
        # Integration-specific additions
        for integration in required_integrations:
            if "database" in integration.lower():
                tech_stack.append("SQLAlchemy")
            elif "queue" in integration.lower():
                tech_stack.append("Celery")
            elif "monitoring" in integration.lower():
                tech_stack.append("Prometheus")
        
        # Remove banned technologies and duplicates
        validated_tech_stack = []
        seen = set()
        
        for tech in tech_stack:
            # Ensure tech is a string (handle cases where it might be a dict)
            if isinstance(tech, dict):
                tech_name = tech.get('name') or tech.get('technology') or str(tech)
                self.logger.warning(f"Tech stack item was dict, extracted name: {tech_name}")
                tech = tech_name
            elif not isinstance(tech, str):
                tech = str(tech)
                self.logger.warning(f"Tech stack item was {type(tech)}, converted to string: {tech}")
            
            # Check if technology is banned (exact match or word boundary match)
            tech_lower = tech.lower()
            is_banned = False
            
            for banned in banned_tools:
                banned_lower = banned.lower()
                # Check for exact match first
                if tech_lower == banned_lower:
                    is_banned = True
                    break
                # Check if banned tool is a complete word within the tech name
                import re
                if re.search(r'\b' + re.escape(banned_lower) + r'\b', tech_lower):
                    is_banned = True
                    break
            
            if tech not in seen and not is_banned:
                validated_tech_stack.append(tech)
                seen.add(tech)
        
        return validated_tech_stack[:10]  # Limit to 10 technologies
    
    def categorize_tech_stack_with_descriptions(self, tech_stack: List[str]) -> Dict[str, Dict[str, Any]]:
        """Categorize tech stack with descriptions and explanations using catalog.
        
        Args:
            tech_stack: List of technology names
            
        Returns:
            Dictionary with categorized technologies and descriptions
        """
        result_categories = {}
        uncategorized = []
        
        catalog_categories = self.technology_catalog.get("categories", {})
        catalog_technologies = self.technology_catalog.get("technologies", {})
        
        # Process each technology in the stack
        for tech_name in tech_stack:
            # Ensure tech_name is a string (handle cases where it might be a dict)
            if isinstance(tech_name, dict):
                tech_name = tech_name.get('name') or tech_name.get('technology') or str(tech_name)
                self.logger.warning(f"Tech stack item was dict in categorization, extracted name: {tech_name}")
            elif not isinstance(tech_name, str):
                tech_name = str(tech_name)
                self.logger.warning(f"Tech stack item was {type(tech_name)} in categorization, converted to string: {tech_name}")
            
            # Find the technology in catalog
            tech_id = self.find_technology_by_name(tech_name)
            
            if tech_id and tech_id in catalog_technologies:
                tech_info = catalog_technologies[tech_id]
                category_id = tech_info.get("category", "unknown")
                
                # Find the category info
                category_info = None
                for cat_id, cat_data in catalog_categories.items():
                    if cat_id == category_id or tech_id in cat_data.get("technologies", []):
                        category_info = cat_data
                        break
                
                if category_info:
                    category_name = category_info.get("name", category_id.title())
                    category_desc = category_info.get("description", f"{category_name} technologies")
                    
                    if category_name not in result_categories:
                        result_categories[category_name] = {
                            "description": category_desc,
                            "technologies": []
                        }
                    
                    # Add technology with its description
                    tech_entry = {
                        "name": tech_info.get("name", tech_name),
                        "description": tech_info.get("description", f"Technology: {tech_name}"),
                        "tags": tech_info.get("tags", []),
                        "maturity": tech_info.get("maturity", "unknown")
                    }
                    result_categories[category_name]["technologies"].append(tech_entry)
                else:
                    uncategorized.append(tech_name)
            else:
                uncategorized.append(tech_name)
        
        # Add uncategorized technologies
        if uncategorized:
            result_categories["Other Technologies"] = {
                "description": "Additional specialized tools and technologies",
                "technologies": [
                    {
                        "name": tech,
                        "description": f"Technology component: {tech}",
                        "tags": [],
                        "maturity": "unknown"
                    } for tech in uncategorized
                ]
            }
        
        return result_categories
    
    def get_technology_description(self, tech: str) -> str:
        """Get a brief description of what a technology does.
        
        Args:
            tech: Technology name
            
        Returns:
            Brief description of the technology
        """
        tech_id = self.find_technology_by_name(tech)
        
        if tech_id:
            tech_info = self.get_technology_info(tech_id)
            return tech_info.get("description", f"Technology component: {tech}")
        
        return f"Technology component: {tech}"
    
    async def _update_catalog_with_new_technologies(self, tech_stack: List[str]) -> None:
        """Update technology catalog with new technologies from LLM suggestions.
        
        Args:
            tech_stack: List of technology names from LLM
        """
        new_technologies = []
        catalog_updated = False
        
        for tech_name in tech_stack:
            # Check if technology already exists in catalog
            tech_id = self.find_technology_by_name(tech_name)
            
            if not tech_id:
                # This is a new technology, add it to catalog
                new_tech_id = self._generate_tech_id(tech_name)
                new_tech_info = self._infer_technology_info(tech_name)
                
                # Add to in-memory catalog
                self.technology_catalog.setdefault("technologies", {})[new_tech_id] = new_tech_info
                
                # Add to appropriate category
                category_id = new_tech_info.get("category", "integration")
                self.technology_catalog.setdefault("categories", {}).setdefault(category_id, {
                    "name": category_id.replace("_", " ").title(),
                    "description": f"{category_id.replace('_', ' ').title()} technologies",
                    "technologies": []
                })
                
                if new_tech_id not in self.technology_catalog["categories"][category_id]["technologies"]:
                    self.technology_catalog["categories"][category_id]["technologies"].append(new_tech_id)
                
                new_technologies.append(tech_name)
                catalog_updated = True
                
                self.logger.info(f"Added new technology to catalog: {tech_name} -> {new_tech_id}")
        
        # Save updated catalog to file if changes were made
        if catalog_updated:
            await self._save_catalog_to_file()
            
            # Update metadata
            total_techs = len(self.technology_catalog.get("technologies", {}))
            self.technology_catalog.setdefault("metadata", {}).update({
                "total_technologies": total_techs,
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "last_auto_update": datetime.now().isoformat()
            })
            
            self.logger.info(f"Catalog updated with {len(new_technologies)} new technologies: {', '.join(new_technologies)}")
    
    def _generate_tech_id(self, tech_name: str) -> str:
        """Generate a consistent technology ID from name.
        
        Args:
            tech_name: Technology name
            
        Returns:
            Technology ID (lowercase, underscores)
        """
        # Clean and normalize the name
        tech_id = tech_name.lower()
        tech_id = tech_id.replace(" ", "_")
        tech_id = tech_id.replace("/", "_")
        tech_id = tech_id.replace("-", "_")
        tech_id = tech_id.replace(".", "_")
        tech_id = tech_id.replace("(", "").replace(")", "")
        
        # Remove common suffixes/prefixes
        tech_id = tech_id.replace("_api", "").replace("api_", "")
        tech_id = tech_id.replace("_service", "").replace("service_", "")
        
        # Handle duplicates by checking existing IDs
        base_id = tech_id
        counter = 1
        while tech_id in self.technology_catalog.get("technologies", {}):
            tech_id = f"{base_id}_{counter}"
            counter += 1
        
        return tech_id
    
    def _infer_technology_info(self, tech_name: str) -> Dict[str, Any]:
        """Infer technology information from name using heuristics.
        
        Args:
            tech_name: Technology name
            
        Returns:
            Technology information dictionary
        """
        tech_lower = tech_name.lower()
        
        # Infer category based on name patterns
        category = "integration"  # Default
        tags = []
        
        if any(keyword in tech_lower for keyword in ["python", "java", "javascript", "node", "go", "rust", "c#"]):
            category = "languages"
            tags = ["programming", "language"]
        elif any(keyword in tech_lower for keyword in ["api", "rest", "graphql", "webhook"]):
            category = "integration"
            tags = ["api", "integration"]
        elif any(keyword in tech_lower for keyword in ["database", "db", "sql", "mongo", "redis", "elastic"]):
            category = "databases"
            tags = ["database", "storage"]
        elif any(keyword in tech_lower for keyword in ["aws", "azure", "gcp", "cloud", "lambda", "function"]):
            category = "cloud"
            tags = ["cloud", "infrastructure"]
        elif any(keyword in tech_lower for keyword in ["docker", "kubernetes", "k8s", "container"]):
            category = "infrastructure"
            tags = ["containers", "devops"]
        elif any(keyword in tech_lower for keyword in ["kafka", "rabbitmq", "queue", "celery"]):
            category = "processing"
            tags = ["messaging", "queue"]
        elif any(keyword in tech_lower for keyword in ["ai", "ml", "nlp", "gpt", "claude", "openai"]):
            category = "ai"
            tags = ["ai", "ml", "nlp"]
        elif any(keyword in tech_lower for keyword in ["auth", "oauth", "jwt", "security"]):
            category = "security"
            tags = ["security", "authentication"]
        elif any(keyword in tech_lower for keyword in ["test", "pytest", "jest", "selenium"]):
            category = "testing"
            tags = ["testing", "qa"]
        elif any(keyword in tech_lower for keyword in ["framework", "django", "flask", "express", "spring"]):
            category = "frameworks"
            tags = ["framework", "web"]
        
        return {
            "name": tech_name,
            "category": category,
            "description": f"Technology component: {tech_name}",
            "tags": tags,
            "maturity": "unknown",
            "license": "unknown",
            "alternatives": [],
            "integrates_with": [],
            "use_cases": [],
            "auto_generated": True,
            "added_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    async def _save_catalog_to_file(self) -> None:
        """Save the updated catalog back to the JSON file.
        
        This method handles file I/O safely with backup and error handling.
        """
        catalog_path = Path("data/technologies.json")
        backup_path = Path("data/technologies.json.backup")
        
        try:
            # Create backup of existing catalog
            if catalog_path.exists():
                import shutil
                shutil.copy2(catalog_path, backup_path)
            
            # Write updated catalog
            with open(catalog_path, 'w') as f:
                json.dump(self.technology_catalog, f, indent=2, sort_keys=True)
            
            self.logger.info(f"Technology catalog saved to {catalog_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save technology catalog: {e}")
            
            # Restore from backup if write failed
            if backup_path.exists():
                try:
                    import shutil
                    shutil.copy2(backup_path, catalog_path)
                    self.logger.info("Restored catalog from backup after write failure")
                except Exception as restore_error:
                    self.logger.error(f"Failed to restore catalog from backup: {restore_error}")
    
    async def add_technology_to_catalog(self, tech_name: str, tech_info: Optional[Dict[str, Any]] = None) -> str:
        """Manually add a technology to the catalog.
        
        Args:
            tech_name: Technology name
            tech_info: Optional technology information (will be inferred if not provided)
            
        Returns:
            Technology ID that was created
        """
        # Check if already exists
        existing_id = self.find_technology_by_name(tech_name)
        if existing_id:
            self.logger.info(f"Technology {tech_name} already exists as {existing_id}")
            return existing_id
        
        # Generate new technology entry
        tech_id = self._generate_tech_id(tech_name)
        
        if tech_info is None:
            tech_info = self._infer_technology_info(tech_name)
        else:
            # Ensure required fields are present
            tech_info.setdefault("name", tech_name)
            tech_info.setdefault("category", "integration")
            tech_info.setdefault("description", f"Technology component: {tech_name}")
            tech_info.setdefault("tags", [])
            tech_info.setdefault("maturity", "unknown")
            tech_info.setdefault("license", "unknown")
            tech_info.setdefault("added_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Add to catalog
        self.technology_catalog.setdefault("technologies", {})[tech_id] = tech_info
        
        # Add to category
        category_id = tech_info.get("category", "integration")
        self.technology_catalog.setdefault("categories", {}).setdefault(category_id, {
            "name": category_id.replace("_", " ").title(),
            "description": f"{category_id.replace('_', ' ').title()} technologies",
            "technologies": []
        })
        
        if tech_id not in self.technology_catalog["categories"][category_id]["technologies"]:
            self.technology_catalog["categories"][category_id]["technologies"].append(tech_id)
        
        # Save to file
        await self._save_catalog_to_file()
        
        self.logger.info(f"Manually added technology: {tech_name} -> {tech_id}")
    
    def _calculate_explicit_inclusion_rate(self, parsed_req: ParsedRequirements, final_stack: List[str]) -> float:
        """Calculate the rate of explicit technology inclusion.
        
        Args:
            parsed_req: Parsed requirements with explicit technologies
            final_stack: Final generated tech stack
            
        Returns:
            Inclusion rate as a float between 0 and 1
        """
        if not parsed_req.explicit_technologies:
            return 1.0  # No explicit technologies to include
        
        explicit_tech_names = {tech.canonical_name or tech.name for tech in parsed_req.explicit_technologies}
        included_explicit = set(final_stack) & explicit_tech_names
        return len(included_explicit) / len(explicit_tech_names)
    
    def get_logging_summary(self) -> Dict[str, Any]:
        """Get comprehensive logging summary for debugging and monitoring.
        
        Returns:
            Dictionary containing logging statistics and summaries
        """
        try:
            # Get performance summary
            performance_summary = self.performance_monitor.get_performance_summary()
            
            # Get decision summary
            decision_summary = self.decision_logger.get_decision_summary(
                component="TechStackGenerator"
            )
            
            # Get LLM interaction summary
            llm_summary = self.llm_logger.get_interaction_summary()
            
            # Get error summary
            error_summary = self.error_logger.get_error_summary()
            
            # Get debug trace summary
            trace_summary = self.debug_tracer.get_performance_summary()
            
            # Get recent alerts
            recent_alerts = self.performance_monitor.get_alerts(limit=10)
            
            return {
                'performance': performance_summary,
                'decisions': decision_summary,
                'llm_interactions': llm_summary,
                'errors': error_summary,
                'debug_traces': trace_summary,
                'recent_alerts': [
                    {
                        'alert_id': alert.alert_id,
                        'metric_name': alert.metric_name,
                        'severity': alert.severity,
                        'message': alert.message,
                        'timestamp': alert.timestamp
                    }
                    for alert in recent_alerts
                ],
                'generation_metrics': self.generation_metrics
            }
        except Exception as e:
            self.tech_logger.log_error(
                LogCategory.ERROR_HANDLING,
                "TechStackGenerator",
                "get_logging_summary",
                f"Failed to generate logging summary: {e}",
                {},
                exception=e
            )
            return {'error': str(e)}
    
    def export_logs(self, 
                   file_path: str,
                   format: str = 'json',
                   include_traces: bool = True,
                   include_performance: bool = True) -> bool:
        """Export comprehensive logs to file.
        
        Args:
            file_path: Output file path
            format: Export format (json, csv, text)
            include_traces: Whether to include debug traces
            include_performance: Whether to include performance data
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Export main logs
            self.tech_logger.export_logs(file_path, format)
            
            # Export traces if requested
            if include_traces:
                traces = self.debug_tracer.get_traces(
                    component="TechStackGenerator",
                    limit=50
                )
                
                if traces:
                    trace_file = file_path.replace('.', '_traces.')
                    for i, trace in enumerate(traces):
                        trace_path = trace_file.replace('.', f'_{i}.')
                        self.debug_tracer.export_trace(trace.trace_id, trace_path, format)
            
            # Export performance data if requested
            if include_performance:
                perf_summary = self.performance_monitor.get_performance_metrics()
                if perf_summary:
                    perf_file = file_path.replace('.', '_performance.')
                    with open(perf_file, 'w') as f:
                        if format == 'json':
                            import json
                            json.dump(perf_summary, f, indent=2, default=str)
                        else:
                            f.write(str(perf_summary))
            
            self.tech_logger.log_info(
                LogCategory.DEBUG_TRACE,
                "TechStackGenerator",
                "export_logs",
                f"Successfully exported logs to {file_path}",
                {
                    'file_path': file_path,
                    'format': format,
                    'include_traces': include_traces,
                    'include_performance': include_performance
                }
            )
            
            return True
            
        except Exception as e:
            self.tech_logger.log_error(
                LogCategory.ERROR_HANDLING,
                "TechStackGenerator",
                "export_logs",
                f"Failed to export logs: {e}",
                {
                    'file_path': file_path,
                    'format': format
                },
                exception=e
            )
            return False
    
    def enable_debug_mode(self, enabled: bool = True) -> None:
        """Enable or disable debug mode for comprehensive logging.
        
        Args:
            enabled: Whether to enable debug mode
        """
        self.tech_logger.enable_debug_mode(enabled)
        
        if enabled:
            self.debug_tracer.enable_tracing(TraceLevel.DETAILED)
        else:
            self.debug_tracer.disable_tracing()
        
        self.tech_logger.log_info(
            LogCategory.DEBUG_TRACE,
            "TechStackGenerator",
            "enable_debug_mode",
            f"Debug mode {'enabled' if enabled else 'disabled'}",
            {'debug_mode': enabled}
        )
    
    def get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations.
        
        Returns:
            List of performance recommendations
        """
        recommendations = []
        
        # Get recommendations from performance monitor
        perf_recommendations = self.performance_monitor.get_performance_recommendations()
        recommendations.extend(perf_recommendations)
        
        # Add tech stack specific recommendations
        metrics = self.generation_metrics
        
        if metrics['total_generations'] > 0:
            if metrics['explicit_tech_inclusion_rate'] < 0.7:
                recommendations.append(
                    f"Low explicit technology inclusion rate ({metrics['explicit_tech_inclusion_rate']:.1%}) - "
                    "review requirement parsing and context extraction"
                )
            
            if metrics['catalog_auto_additions'] > metrics['total_generations'] * 0.5:
                recommendations.append(
                    "High catalog auto-addition rate - consider pre-populating catalog with common technologies"
                )
        
        # Check for frequent errors
        error_summary = self.error_logger.get_error_summary()
        if error_summary.get('total_errors', 0) > 10:
            recommendations.append(
                f"High error count ({error_summary['total_errors']}) - investigate error patterns and root causes"
            )
        
        return recommendations
    
    def shutdown_logging(self) -> None:
        """Shutdown logging services gracefully."""
        try:
            self.performance_monitor.stop_monitoring()
            self.tech_logger.flush_logs()
            self.tech_logger.shutdown()
            
            self.tech_logger.log_info(
                LogCategory.DEBUG_TRACE,
                "TechStackGenerator",
                "shutdown_logging",
                "Logging services shutdown completed",
                {}
            )
        except Exception as e:
            # Use basic logging as fallback
            import logging
            logging.error(f"Error during logging shutdown: {e}")
        return tech_id