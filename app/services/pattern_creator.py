"""Pattern creation service for generating new patterns when no existing patterns match."""

from typing import Dict, List, Any, Optional
from pathlib import Path

from app.llm.base import LLMProvider
from app.services.tech_stack_generator import TechStackGenerator
from app.services.pattern_name_manager import PatternNameManager
from app.services.pattern_deduplication_service import PatternDeduplicationService
from app.utils.imports import require_service

# Import enhanced components for integration
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.context_extractor import (
    TechnologyContextExtractor,
)
from app.services.catalog.intelligent_manager import IntelligentCatalogManager


class PatternCreator:
    """Service for creating new automation patterns based on requirements."""

    def __init__(
        self, pattern_library_path: Path, llm_provider: Optional[LLMProvider] = None
    ):
        """Initialize pattern creator.

        Args:
            pattern_library_path: Path to pattern library directory
            llm_provider: LLM provider for generating pattern details
        """
        self.pattern_library_path = pattern_library_path
        self.llm_provider = llm_provider

        # Get logger from service registry
        self.logger = require_service("logger", context="PatternCreator")

        # Initialize enhanced components for better tech stack generation
        self.enhanced_parser = EnhancedRequirementParser()
        self.context_extractor = TechnologyContextExtractor()
        self.catalog_manager = IntelligentCatalogManager()

        # Initialize enhanced tech stack generator with new capabilities
        self.tech_stack_generator = TechStackGenerator(
            llm_provider=llm_provider,
            auto_update_catalog=True,
            enhanced_parser=self.enhanced_parser,
            context_extractor=self.context_extractor,
            catalog_manager=self.catalog_manager,
            enable_debug_logging=False,
        )
        
        # Initialize pattern name manager to prevent duplicates
        self.name_manager = PatternNameManager(pattern_library_path)
        
        # Initialize deduplication service to prevent identical patterns
        self.deduplication_service = PatternDeduplicationService(pattern_library_path)

    async def create_pattern_from_requirements(
        self, requirements: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Create a new pattern based on user requirements with comprehensive error handling.

        Args:
            requirements: User requirements dictionary
            session_id: Session ID for tracking

        Returns:
            New pattern dictionary

        Raises:
            ValueError: If pattern creation fails due to validation or security issues
            RuntimeError: If critical pattern creation steps fail
        """
        try:
            self.logger.info(f"Creating new pattern for session {session_id}")

            # Validate input requirements
            if not requirements:
                raise ValueError("Requirements dictionary cannot be empty")

            if not session_id or session_id.strip() == "":
                raise ValueError("Session ID cannot be empty")

            # Generate unique pattern ID with duplicate validation
            try:
                pattern_id = self._generate_pattern_id()
                self.logger.info(f"Generated pattern ID: {pattern_id}")
            except Exception as e:
                self.logger.error(f"Failed to generate unique pattern ID: {e}")
                raise RuntimeError(f"Pattern ID generation failed: {e}")

            # Extract key information from requirements with error handling
            try:
                description = str(requirements.get("description", "")).lower()
                domain = requirements.get("domain", "general")

                if not description.strip():
                    self.logger.warning("Empty description provided, using fallback")
                    description = "automated process"

            except Exception as e:
                self.logger.error(f"Error extracting basic requirements: {e}")
                raise ValueError(f"Invalid requirements format: {e}")

            # Enhanced physical task detection with digital alternative check
            try:
                physical_keywords = [
                    "feed",
                    "feeding",
                    "water",
                    "watering",
                    "walk",
                    "walking",
                    "pet",
                    "animal",
                    "snail",
                    "paint",
                    "painting",
                    "build",
                    "construction",
                    "repair",
                    "fix",
                    "install",
                    "clean",
                    "cleaning",
                    "move",
                    "transport",
                    "deliver",
                    "physical",
                    "manual",
                    "pick up",
                    "pickup",
                    "carry",
                    "carrying",
                    "lift",
                    "lifting",
                    "hardware",
                    "mechanical",
                    "electrical wiring",
                    "plumbing",
                    "carpentry",
                    "landscaping",
                    "gardening",
                    "cooking",
                    "driving",
                    "walking",
                    "running",
                ]

                digital_keywords = [
                    "remind",
                    "notification",
                    "alert",
                    "schedule",
                    "track",
                    "monitor",
                    "api",
                    "webhook",
                    "database",
                    "software",
                    "app",
                    "system",
                    "digital",
                    "online",
                    "email",
                    "sms",
                    "order",
                    "purchase",
                    "automate",
                    "automatic",
                ]

                physical_count = sum(
                    1 for keyword in physical_keywords if keyword in description
                )
                digital_count = sum(
                    1 for keyword in digital_keywords if keyword in description
                )

                # If clearly physical with minimal digital indicators, create "Not Automatable" pattern
                if physical_count >= 1 and digital_count == 0:
                    self.logger.info(
                        f"🚫 SCOPE GATE: Detected physical task - '{description[:100]}...' (physical:{physical_count}, digital:{digital_count})"
                    )
                    return await self._create_physical_task_pattern(
                        pattern_id, requirements, session_id
                    )

            except Exception as e:
                self.logger.warning(f"Error in physical task detection: {e}")
                # Continue with normal pattern creation if detection fails

            # Analyze requirements to determine pattern characteristics using LLM
            try:
                pattern_analysis = await self._analyze_requirements(requirements)
                self.logger.info(
                    f"Successfully analyzed requirements for pattern {pattern_id}"
                )
            except Exception as e:
                self.logger.error(f"LLM analysis failed for pattern {pattern_id}: {e}")
                # Use fallback analysis
                pattern_analysis = self._create_fallback_analysis(requirements)
                self.logger.info(f"Using fallback analysis for pattern {pattern_id}")

            # Extract values from LLM analysis or use fallbacks with error handling
            try:
                proposed_name = pattern_analysis.get(
                    "pattern_name"
                ) or self._generate_pattern_name(requirements, pattern_analysis)
                
                # Ensure unique pattern name using name manager
                name_validation = self.name_manager.validate_and_suggest_name(
                    proposed_name, requirements, pattern_analysis
                )
                
                if not name_validation['is_unique'] or not name_validation['is_valid']:
                    pattern_name = name_validation['suggested_name']
                    self.logger.info(
                        f"Pattern name adjusted for uniqueness: '{proposed_name}' → '{pattern_name}'"
                    )
                else:
                    pattern_name = proposed_name
                
                feasibility = pattern_analysis.get(
                    "feasibility"
                ) or self._determine_feasibility(requirements, pattern_analysis)
                pattern_types = pattern_analysis.get(
                    "pattern_types"
                ) or self._generate_pattern_types(requirements, pattern_analysis)
                input_requirements = pattern_analysis.get(
                    "input_requirements"
                ) or self._generate_input_requirements(requirements, pattern_analysis)
                confidence_score = pattern_analysis.get(
                    "confidence_score"
                ) or self._calculate_pattern_confidence(requirements, pattern_analysis)
                complexity = pattern_analysis.get(
                    "complexity"
                ) or self._estimate_complexity(requirements, pattern_analysis)
                estimated_effort = pattern_analysis.get(
                    "estimated_effort"
                ) or self._estimate_effort(complexity, pattern_analysis)

                # Validate extracted values
                if not pattern_name or pattern_name.strip() == "":
                    pattern_name = self.name_manager.generate_unique_name(
                        f"Automated Process {pattern_id}", requirements, pattern_analysis
                    )

                if feasibility not in [
                    "Automatable",
                    "Partially Automatable",
                    "Not Automatable",
                ]:
                    self.logger.warning(
                        f"Invalid feasibility '{feasibility}', defaulting to 'Automatable'"
                    )
                    feasibility = "Automatable"

                if not isinstance(pattern_types, list):
                    pattern_types = ["general_automation"]

                if not isinstance(confidence_score, (int, float)) or not (
                    0 <= confidence_score <= 1
                ):
                    confidence_score = 0.7

            except Exception as e:
                self.logger.error(f"Error extracting pattern values: {e}")
                raise RuntimeError(f"Pattern value extraction failed: {e}")

            # Generate tech stack with error handling
            try:
                tech_stack = pattern_analysis.get(
                    "tech_stack"
                ) or await self._generate_intelligent_tech_stack(
                    requirements, pattern_analysis
                )
                if not isinstance(tech_stack, list):
                    tech_stack = []
                    self.logger.warning("Invalid tech stack format, using empty list")
            except Exception as e:
                self.logger.error(f"Tech stack generation failed: {e}")
                tech_stack = self._generate_fallback_tech_stack(
                    requirements, pattern_analysis
                )

            # Extract domain from analysis, with fallback
            try:
                analyzed_domain = pattern_analysis.get("domain")
                if analyzed_domain and analyzed_domain not in [
                    "None",
                    "none",
                    "general",
                    "",
                ]:
                    domain = analyzed_domain
            except Exception as e:
                self.logger.warning(f"Error extracting domain: {e}")
                # Keep original domain

            # Get pattern description from LLM analysis with fallback
            try:
                pattern_description = pattern_analysis.get(
                    "pattern_description"
                ) or self._generate_pattern_description(requirements, pattern_analysis)
                if not pattern_description or pattern_description.strip() == "":
                    pattern_description = (
                        f"Automated processing system for {description[:100]}..."
                    )
            except Exception as e:
                self.logger.warning(f"Error generating pattern description: {e}")
                pattern_description = (
                    f"Automated processing system for {description[:100]}..."
                )

            # Extract enhanced constraint information from LLM analysis with error handling
            try:
                banned_tools_suggestions = pattern_analysis.get(
                    "banned_tools_suggestions", []
                )
                required_integrations_suggestions = pattern_analysis.get(
                    "required_integrations_suggestions", []
                )
                compliance_considerations = pattern_analysis.get(
                    "compliance_considerations", []
                )

                # Ensure they are lists
                if not isinstance(banned_tools_suggestions, list):
                    banned_tools_suggestions = []
                if not isinstance(required_integrations_suggestions, list):
                    required_integrations_suggestions = []
                if not isinstance(compliance_considerations, list):
                    compliance_considerations = []

            except Exception as e:
                self.logger.warning(f"Error extracting constraint information: {e}")
                banned_tools_suggestions = []
                required_integrations_suggestions = []
                compliance_considerations = []

            # Combine LLM suggestions with extracted requirements
            try:
                all_required_integrations = list(
                    set(
                        self._extract_required_integrations(requirements)
                        + required_integrations_suggestions
                    )
                )
            except Exception as e:
                self.logger.warning(f"Error combining integrations: {e}")
                all_required_integrations = required_integrations_suggestions

            # Create pattern dictionary with comprehensive error handling
            try:
                new_pattern = {
                    "pattern_id": pattern_id,
                    "name": pattern_name,
                    "description": pattern_description,
                    "feasibility": feasibility,
                    "pattern_type": pattern_types,
                    "input_requirements": input_requirements,
                    "tech_stack": tech_stack,
                    "related_patterns": [],  # Will be populated later if needed
                    "confidence_score": confidence_score,
                    "constraints": {
                        "banned_tools": banned_tools_suggestions,
                        "required_integrations": all_required_integrations,
                        "compliance_requirements": compliance_considerations,
                    },
                    "domain": domain,
                    "complexity": complexity,
                    "estimated_effort": estimated_effort,
                    "effort_breakdown": pattern_analysis.get(
                        "effort_breakdown", estimated_effort
                    ),
                    "created_from_session": session_id,
                    "auto_generated": True,
                    # Add LLM-enhanced fields with better separation
                    "llm_insights": pattern_analysis.get("key_challenges", []),
                    "llm_challenges": pattern_analysis.get("key_challenges", []),
                    "llm_recommended_approach": pattern_analysis.get(
                        "recommended_approach", ""
                    ),
                    "enhanced_by_llm": True,
                    "enhanced_from_session": session_id,
                    # Add metadata for better pattern matching
                    "automation_metadata": {
                        "data_flow": pattern_analysis.get("data_flow", "on_demand"),
                        "user_interaction": pattern_analysis.get(
                            "user_interaction", "semi_automated"
                        ),
                        "processing_type": pattern_analysis.get(
                            "processing_type", "basic_processing"
                        ),
                        "scalability_needs": pattern_analysis.get(
                            "scalability_needs", "low_scale"
                        ),
                        "security_requirements": pattern_analysis.get(
                            "security_requirements", []
                        ),
                    },
                }

                self.logger.info(
                    f"Successfully created pattern dictionary for {pattern_id}"
                )

            except Exception as e:
                self.logger.error(f"Error creating pattern dictionary: {e}")
                raise RuntimeError(f"Pattern dictionary creation failed: {e}")

            # Save pattern to library with security validation and comprehensive error handling
            try:
                success, message = await self._save_pattern_securely(new_pattern)
                if not success:
                    self.logger.error(
                        f"Failed to save pattern due to security validation: {message}"
                    )
                    raise ValueError(f"Pattern creation blocked: {message}")

                self.logger.info(
                    f"Successfully saved pattern {pattern_id}: {pattern_name}"
                )

            except ValueError:
                # Re-raise security validation errors
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error saving pattern: {e}")
                raise RuntimeError(f"Pattern save operation failed: {e}")

            self.logger.info(f"Created new pattern {pattern_id}: {pattern_name}")
            return new_pattern

        except (ValueError, RuntimeError):
            # Re-raise expected exceptions
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in pattern creation: {e}")
            raise RuntimeError(f"Pattern creation failed with unexpected error: {e}")

    def _generate_pattern_id(self) -> str:
        """Generate a unique pattern ID with duplicate validation.

        Returns:
            Unique pattern ID in format PAT-XXX

        Raises:
            ValueError: If unable to generate unique ID after multiple attempts
        """
        try:
            # Find the highest existing pattern number from files
            existing_patterns = list(self.pattern_library_path.glob("PAT-*.json"))
            max_num = 0
            existing_ids = set()

            for pattern_file in existing_patterns:
                try:
                    pattern_id = pattern_file.stem
                    existing_ids.add(pattern_id)

                    # Extract number for max calculation
                    num_str = pattern_id.split("-")[1]
                    num = int(num_str)
                    max_num = max(max_num, num)
                except (IndexError, ValueError) as e:
                    self.logger.warning(
                        f"Could not parse pattern ID from file {pattern_file}: {e}"
                    )
                    continue

            # Also check loaded patterns to ensure no conflicts
            try:
                from app.pattern.loader import PatternLoader

                pattern_loader = PatternLoader(self.pattern_library_path)
                loaded_patterns = pattern_loader.load_patterns()

                for pattern in loaded_patterns:
                    pattern_id = pattern.get("pattern_id")
                    if pattern_id:
                        existing_ids.add(pattern_id)
                        try:
                            num_str = pattern_id.split("-")[1]
                            num = int(num_str)
                            max_num = max(max_num, num)
                        except (IndexError, ValueError):
                            continue

            except Exception as e:
                self.logger.warning(
                    f"Could not load existing patterns for ID validation: {e}"
                )

            # Generate new ID and validate uniqueness
            max_attempts = 100  # Prevent infinite loop
            for attempt in range(max_attempts):
                new_id = f"PAT-{max_num + 1 + attempt:03d}"

                if new_id not in existing_ids:
                    self.logger.info(f"Generated unique pattern ID: {new_id}")
                    return new_id

                self.logger.warning(
                    f"Pattern ID {new_id} already exists, trying next number"
                )

            # If we get here, we couldn't generate a unique ID
            raise ValueError(
                f"Unable to generate unique pattern ID after {max_attempts} attempts"
            )

        except Exception as e:
            self.logger.error(f"Error generating pattern ID: {e}")
            # Fallback to UUID-based ID to ensure uniqueness
            import uuid

            fallback_id = f"PAT-{str(uuid.uuid4())[:8].upper()}"
            self.logger.warning(f"Using fallback UUID-based pattern ID: {fallback_id}")
            return fallback_id

    async def _analyze_requirements(
        self, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze requirements to extract pattern characteristics using LLM.

        Args:
            requirements: User requirements

        Returns:
            Analysis results dictionary
        """
        # Use LLM for comprehensive analysis if available
        if self.llm_provider:
            try:
                return await self._llm_analyze_requirements(requirements)
            except Exception as e:
                self.logger.warning(f"LLM analysis failed: {e}")

        # Fallback to rule-based analysis
        description = requirements.get("description", "")

        analysis = {
            "automation_type": self._detect_automation_type(description, requirements),
            "data_flow": self._detect_data_flow(description, requirements),
            "integration_points": self._detect_integration_points(
                description, requirements
            ),
            "user_interaction": self._detect_user_interaction(
                description, requirements
            ),
            "processing_type": self._detect_processing_type(description, requirements),
            "scalability_needs": self._detect_scalability_needs(
                description, requirements
            ),
            "security_requirements": self._detect_security_requirements(
                description, requirements
            ),
        }

        return analysis

    def _detect_automation_type(
        self, description: str, requirements: Dict[str, Any]
    ) -> str:
        """Detect the type of automation needed."""
        desc_lower = description.lower()

        if any(
            word in desc_lower for word in ["scan", "barcode", "qr", "image", "photo"]
        ):
            return "scanning_automation"
        elif any(
            word in desc_lower for word in ["translate", "translation", "language"]
        ):
            return "translation_automation"
        elif any(word in desc_lower for word in ["document", "pdf", "file", "extract"]):
            return "document_processing"
        elif any(
            word in desc_lower for word in ["api", "integrate", "connect", "sync"]
        ):
            return "api_integration"
        elif any(
            word in desc_lower for word in ["monitor", "alert", "notify", "watch"]
        ):
            return "monitoring_automation"
        elif any(
            word in desc_lower for word in ["schedule", "batch", "periodic", "cron"]
        ):
            return "scheduled_automation"
        elif any(
            word in desc_lower for word in ["workflow", "process", "step", "sequence"]
        ):
            return "workflow_automation"
        else:
            return "general_automation"

    def _detect_data_flow(self, description: str, requirements: Dict[str, Any]) -> str:
        """Detect data flow patterns."""
        desc_lower = description.lower()

        if any(
            word in desc_lower for word in ["real-time", "realtime", "live", "instant"]
        ):
            return "real_time"
        elif any(
            word in desc_lower for word in ["batch", "bulk", "scheduled", "periodic"]
        ):
            return "batch"
        elif any(word in desc_lower for word in ["stream", "continuous", "ongoing"]):
            return "streaming"
        else:
            return "on_demand"

    def _detect_integration_points(
        self, description: str, requirements: Dict[str, Any]
    ) -> List[str]:
        """Detect integration points mentioned in requirements."""
        desc_lower = description.lower()
        integrations = []

        # Common integration patterns
        integration_keywords = {
            "database": ["database", "db", "sql", "mysql", "postgresql", "mongodb"],
            "api": ["api", "rest", "graphql", "endpoint", "service"],
            "file_system": ["file", "folder", "directory", "storage"],
            "email": ["email", "smtp", "mail"],
            "messaging": ["queue", "message", "kafka", "rabbitmq", "sqs"],
            "cloud": ["aws", "azure", "gcp", "cloud", "s3", "lambda"],
            "mobile": ["mobile", "app", "device", "phone", "tablet"],
            "web": ["web", "browser", "website", "portal"],
            "crm": ["crm", "salesforce", "hubspot"],
            "erp": ["erp", "sap", "oracle"],
            "communication": ["slack", "teams", "discord", "chat"],
        }

        for integration_type, keywords in integration_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                integrations.append(integration_type)

        # Check specific mentions
        if "amazon connect" in desc_lower:
            integrations.append("amazon_connect")
        if "supplier" in desc_lower:
            integrations.append("supplier_systems")
        if "inventory" in desc_lower:
            integrations.append("inventory_management")

        return integrations

    def _detect_user_interaction(
        self, description: str, requirements: Dict[str, Any]
    ) -> str:
        """Detect level of user interaction required."""
        desc_lower = description.lower()

        if any(
            word in desc_lower
            for word in ["automatic", "automated", "no user", "unattended"]
        ):
            return "fully_automated"
        elif any(
            word in desc_lower for word in ["review", "approve", "confirm", "manual"]
        ):
            return "human_in_loop"
        elif any(
            word in desc_lower for word in ["trigger", "initiate", "start", "click"]
        ):
            return "user_initiated"
        else:
            return "semi_automated"

    def _detect_processing_type(
        self, description: str, requirements: Dict[str, Any]
    ) -> str:
        """Detect type of processing required."""
        desc_lower = description.lower()

        if any(
            word in desc_lower
            for word in ["ml", "ai", "machine learning", "predict", "classify"]
        ):
            return "ml_processing"
        elif any(
            word in desc_lower for word in ["transform", "convert", "parse", "extract"]
        ):
            return "data_transformation"
        elif any(
            word in desc_lower for word in ["validate", "verify", "check", "audit"]
        ):
            return "validation"
        elif any(
            word in desc_lower for word in ["aggregate", "sum", "count", "calculate"]
        ):
            return "aggregation"
        else:
            return "basic_processing"

    def _detect_scalability_needs(
        self, description: str, requirements: Dict[str, Any]
    ) -> str:
        """Detect scalability requirements."""
        volume = requirements.get("volume", {})
        daily_volume = volume.get("daily", 0)

        if daily_volume > 100000:
            return "high_scale"
        elif daily_volume > 10000:
            return "medium_scale"
        elif daily_volume > 1000:
            return "low_scale"
        else:
            return "minimal_scale"

    def _detect_security_requirements(
        self, description: str, requirements: Dict[str, Any]
    ) -> List[str]:
        """Detect security requirements."""
        desc_lower = description.lower()
        security_reqs = []

        if any(
            word in desc_lower
            for word in ["encrypt", "secure", "private", "confidential"]
        ):
            security_reqs.append("encryption")
        if any(
            word in desc_lower for word in ["auth", "login", "permission", "access"]
        ):
            security_reqs.append("authentication")
        if any(word in desc_lower for word in ["audit", "log", "track", "monitor"]):
            security_reqs.append("audit_logging")
        if any(
            word in desc_lower for word in ["gdpr", "hipaa", "compliance", "regulation"]
        ):
            security_reqs.append("compliance")

        return security_reqs

    def _create_fallback_analysis(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis when LLM analysis fails.

        Args:
            requirements: User requirements

        Returns:
            Basic analysis dictionary with fallback values
        """
        try:
            description = requirements.get("description", "")
            domain = requirements.get("domain", "general")

            # Use rule-based analysis methods
            automation_type = self._detect_automation_type(description, requirements)
            data_flow = self._detect_data_flow(description, requirements)
            integration_points = self._detect_integration_points(
                description, requirements
            )
            user_interaction = self._detect_user_interaction(description, requirements)
            processing_type = self._detect_processing_type(description, requirements)
            scalability_needs = self._detect_scalability_needs(
                description, requirements
            )
            security_requirements = self._detect_security_requirements(
                description, requirements
            )

            # Generate basic pattern information
            pattern_name = (
                f"{domain.title()} {automation_type.replace('_', ' ').title()}"
            )

            # Determine feasibility based on complexity
            complexity_factors = len(integration_points) + len(security_requirements)
            if complexity_factors > 5:
                feasibility = "Partially Automatable"
                complexity = "High"
            elif complexity_factors > 2:
                feasibility = "Automatable"
                complexity = "Medium"
            else:
                feasibility = "Automatable"
                complexity = "Low"

            # Generate pattern types
            pattern_types = [automation_type]
            if integration_points:
                pattern_types.append("integration")
            if security_requirements:
                pattern_types.append("security")

            # Generate basic tech stack
            tech_stack = ["Python", "FastAPI"]
            if "database" in integration_points:
                tech_stack.append("PostgreSQL")
            if "api" in integration_points:
                tech_stack.append("REST API")
            if "cloud" in integration_points:
                tech_stack.append("AWS")

            fallback_analysis = {
                "pattern_name": pattern_name,
                "pattern_description": f"Automated {automation_type.replace('_', ' ')} system with {data_flow} processing",
                "feasibility": feasibility,
                "pattern_types": pattern_types,
                "domain": domain,
                "complexity": complexity,
                "automation_type": automation_type,
                "data_flow": data_flow,
                "user_interaction": user_interaction,
                "processing_type": processing_type,
                "scalability_needs": scalability_needs,
                "security_requirements": security_requirements,
                "integration_points": integration_points,
                "input_requirements": ["User input", "System configuration"],
                "tech_stack": tech_stack,
                "estimated_effort": (
                    "3-6 weeks" if complexity == "High" else "1-2 weeks"
                ),
                "effort_breakdown": f"MVP: 1 week, Full implementation: {'4 weeks' if complexity == 'High' else '2 weeks'}",
                "key_challenges": ["Integration complexity", "Error handling"],
                "recommended_approach": f"Implement {automation_type.replace('_', ' ')} using standard patterns",
                "confidence_score": 0.7,
                "banned_tools_suggestions": [],
                "required_integrations_suggestions": integration_points,
                "compliance_considerations": security_requirements,
            }

            self.logger.info(f"Created fallback analysis: {pattern_name}")
            return fallback_analysis

        except Exception as e:
            self.logger.error(f"Error creating fallback analysis: {e}")
            # Return minimal fallback
            return {
                "pattern_name": "General Automation Pattern",
                "pattern_description": "General purpose automation system",
                "feasibility": "Automatable",
                "pattern_types": ["general_automation"],
                "domain": "general",
                "complexity": "Medium",
                "automation_type": "general_automation",
                "data_flow": "on_demand",
                "user_interaction": "semi_automated",
                "processing_type": "basic_processing",
                "scalability_needs": "low_scale",
                "security_requirements": [],
                "integration_points": [],
                "input_requirements": ["User input"],
                "tech_stack": ["Python", "FastAPI"],
                "estimated_effort": "1-2 weeks",
                "effort_breakdown": "MVP: 1 week, Full implementation: 2 weeks",
                "key_challenges": ["Implementation"],
                "recommended_approach": "Standard automation approach",
                "confidence_score": 0.6,
                "banned_tools_suggestions": [],
                "required_integrations_suggestions": [],
                "compliance_considerations": [],
            }

    async def _llm_analyze_requirements(
        self, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to comprehensively analyze requirements and generate pattern details."""
        description = requirements.get("description", "")
        domain = requirements.get("domain", "")
        volume = requirements.get("volume", {})
        integrations = requirements.get("integrations", [])

        # Extract constraints from nested structure
        constraints = requirements.get("constraints", {})
        banned_tools = constraints.get("banned_tools", [])
        required_integrations = constraints.get("required_integrations", [])
        compliance_requirements = constraints.get("compliance_requirements", [])
        data_sensitivity = constraints.get("data_sensitivity", "")
        budget_constraints = constraints.get("budget_constraints", "")
        deployment_preference = constraints.get("deployment_preference", "")

        prompt = f"""You are a senior software-based AI agents and Agentic AI architect. Analyze the following requirement and generate a comprehensive automation pattern.
You analyze the requirements to determine whether they can be architect to work with agentic systems
that reason, plan, and act within digital environments (not physical/industrial automation).

SCOPE GATE (read carefully):
- If the requirement primarily involves physical-world manipulation (e.g., washing a car, cleaning a room, warehouse picking, walking a dog, feeding pets, watering plants) 
  and does NOT present a fully digital control surface (APIs, RPA on software UIs, webhooks, queues) that the agent can operate end-to-end,
  then respond with EXACTLY an empty JSON array: []
- Only if there is a clear, software-only execution path should you proceed.

CRITICAL: "Feed my pet snail" = PHYSICAL TASK = RETURN [] (empty array)
DIGITAL ALTERNATIVE: "Send me reminders to feed my pet" = DIGITAL TASK = PROCEED

DIGITAL WORKFLOWS (PROCEED WITH ANALYSIS):
- Email processing, data extraction, spreadsheet updates = DIGITAL
- Invoice processing, payment automation via APIs = DIGITAL  
- Document processing, data validation, notifications = DIGITAL
- Banking operations via Open Banking APIs = DIGITAL

**Requirement Details:**
- Description: {description}
- Domain: {domain}
- Volume: {volume}
- Required Integrations: {integrations}

**CRITICAL CONSTRAINTS:**
- Banned/Prohibited Technologies: {banned_tools if banned_tools else 'None'}
- Required System Integrations: {required_integrations if required_integrations else 'None'}
- Compliance Requirements: {compliance_requirements if compliance_requirements else 'None'}
- Data Sensitivity Level: {data_sensitivity if data_sensitivity else 'Not specified'}
- Budget Constraints: {budget_constraints if budget_constraints else 'Not specified'}
- Deployment Preference: {deployment_preference if deployment_preference else 'Not specified'}

**Instructions:**
Generate a complete automation pattern analysis. Be specific to this exact requirement - avoid generic responses.

**CRITICAL CONSISTENCY RULES:**
1. If you mention "human oversight", "manual review", or "human-in-loop" in your approach, set feasibility to "Partially Automatable"
2. If the domain involves sensitive data (legal, healthcare, finance), consider privacy constraints
3. Effort estimates should reflect MVP vs full implementation complexity
4. Pattern types should include broader categories for better matching (e.g., "nlp_processing", "api_integration")
5. **NEVER include any technology listed in "Banned/Prohibited Technologies" in your tech_stack**
6. **MUST include all "Required System Integrations" in your tech_stack or constraints**
7. Consider compliance requirements when selecting technologies and approaches
8. Respect data sensitivity level and deployment preferences in your recommendations

**NAMING REQUIREMENTS:**
- Pattern names MUST be specific and descriptive, not generic
- AVOID generic names like "Multi-Agent System", "Coordinator System", "Automation Pattern"
- INCLUDE the specific use case/domain in the name (e.g., "Investment Portfolio Rebalancing System", "Customer Support Ticket Router")
- For multi-agent systems, specify the agent count and purpose (e.g., "5-Agent Customer Support System")
- Names should be unique and immediately convey what the system does

Respond with ONLY a valid JSON object:
{{
    "pattern_name": "Specific descriptive name that includes the use case/domain (NOT generic like 'Multi-Agent System')",
    "pattern_description": "Detailed description of what this pattern automates and how",
    "feasibility": "Automatable|Partially Automatable|Not Automatable",
    "pattern_types": ["specific", "pattern", "types", "broader_categories"],
    "domain": "specific_domain_name",
    "complexity": "Low|Medium|High",
    "automation_type": "specific_automation_category",
    "data_flow": "real_time|batch|streaming|on_demand",
    "user_interaction": "fully_automated|human_in_loop|user_initiated|semi_automated",
    "processing_type": "ml_processing|data_transformation|validation|aggregation|basic_processing",
    "scalability_needs": "minimal_scale|low_scale|medium_scale|high_scale",
    "security_requirements": ["encryption", "authentication", "audit_logging", "compliance"],
    "integration_points": ["database", "api", "cloud", "mobile", "messaging"],
    "input_requirements": ["specific", "requirements", "for", "this", "automation"],
    "tech_stack": ["Technology1", "Technology2", "Technology3", "..."],
    "estimated_effort": "1-2 weeks|3-6 weeks|6-12 weeks|3+ months",
    "effort_breakdown": "MVP: X weeks, Full implementation: Y weeks",
    "key_challenges": ["challenge1", "challenge2"],
    "recommended_approach": "Detailed approach for implementing this specific automation",
    "confidence_score": 0.85,
    "banned_tools_suggestions": ["tools", "to", "avoid", "for", "privacy"],
    "required_integrations_suggestions": ["common", "system", "integrations"],
    "compliance_considerations": ["gdpr", "hipaa", "sox", "etc"]
}}

IMPORTANT: 
- Be specific to the actual requirement, not generic
- Choose appropriate technologies for this exact use case
- Ensure feasibility matches your recommended approach (if you mention human oversight, use "Partially Automatable")
- Include broader pattern types for better future matching
- Consider domain-specific compliance and privacy requirements
- Provide realistic effort estimates with MVP vs full breakdown"""

        try:
            response = await self.llm_provider.generate(
                prompt, purpose="pattern_analysis"
            )

            # Parse JSON response with better error handling
            import re
            import json

            # Clean the response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = (
                    cleaned_response.replace("```json", "").replace("```", "").strip()
                )
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.replace("```", "").strip()

            # Try to extract JSON
            json_match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                analysis = json.loads(json_str)
                self.logger.info(
                    f"LLM generated comprehensive pattern analysis: {analysis.get('pattern_name', 'Unknown')}"
                )
                return analysis
            else:
                raise ValueError("No JSON object found in LLM response")

        except Exception as e:
            self.logger.error(f"LLM pattern analysis failed: {e}")
            raise e

    def _generate_pattern_name(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """Generate a descriptive pattern name."""
        automation_type = analysis.get("automation_type", "general_automation")
        domain = requirements.get("domain", "general")

        # Create name based on automation type and domain
        type_names = {
            "scanning_automation": "Barcode/QR Scanning",
            "translation_automation": "Real-time Translation",
            "document_processing": "Document Processing",
            "api_integration": "API Integration",
            "monitoring_automation": "Monitoring & Alerting",
            "scheduled_automation": "Scheduled Processing",
            "workflow_automation": "Workflow Automation",
            "general_automation": "Process Automation",
        }

        base_name = type_names.get(automation_type, "Process Automation")

        # Add domain context if specific and valid
        if domain and domain not in ["general", "None", "none", ""]:
            domain_formatted = domain.replace("_", " ").title()
            return f"{domain_formatted} {base_name}"

        return base_name

    def _generate_pattern_description(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """Generate a comprehensive pattern description."""
        requirements.get("description", "")
        automation_type = analysis.get("automation_type", "general_automation")
        data_flow = analysis.get("data_flow", "on_demand")
        integrations = analysis.get("integration_points", [])

        # Create a more generic description based on the specific requirement
        description_templates = {
            "scanning_automation": "Automated scanning and processing system using barcode/QR code recognition with mobile device integration and real-time data processing",
            "translation_automation": "Real-time language translation system with bidirectional communication support and user preference integration",
            "document_processing": "Automated document processing pipeline with extraction, validation, and integration capabilities",
            "api_integration": "Automated API integration workflow with data transformation, error handling, and synchronization",
            "monitoring_automation": "Automated monitoring and alerting system with threshold-based triggers and notification management",
            "scheduled_automation": "Scheduled batch processing system with automated execution and result management",
            "workflow_automation": "Multi-step workflow automation with conditional logic and integration points",
            "general_automation": "General purpose automation system with configurable processing and integration capabilities",
        }

        base_desc = description_templates.get(
            automation_type, description_templates["general_automation"]
        )

        # Add data flow context
        if data_flow == "real_time":
            base_desc += " with real-time processing capabilities"
        elif data_flow == "batch":
            base_desc += " with batch processing optimization"
        elif data_flow == "streaming":
            base_desc += " with continuous streaming support"

        # Add integration context
        if integrations:
            integration_desc = ", ".join(integrations[:3])  # Limit to first 3
            base_desc += f" and integration with {integration_desc}"

        return base_desc

    def _determine_feasibility(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """Determine feasibility of the new pattern."""
        automation_type = analysis.get("automation_type", "general_automation")
        user_interaction = analysis.get("user_interaction", "semi_automated")
        security_reqs = analysis.get("security_requirements", [])

        # High feasibility patterns
        high_feasibility_types = [
            "api_integration",
            "scheduled_automation",
            "monitoring_automation",
            "scanning_automation",
        ]

        # Medium feasibility patterns
        medium_feasibility_types = [
            "document_processing",
            "workflow_automation",
            "translation_automation",
        ]

        if (
            automation_type in high_feasibility_types
            and user_interaction != "human_in_loop"
        ):
            return "Automatable"
        elif automation_type in medium_feasibility_types or len(security_reqs) > 2:
            return "Partially Automatable"
        else:
            return "Automatable"  # Default to automatable for new patterns

    async def _generate_intelligent_tech_stack(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate intelligent tech stack using the enhanced TechStackGenerator.

        Args:
            requirements: User requirements
            analysis: Pattern analysis results

        Returns:
            List of recommended technologies
        """
        try:
            # Use enhanced parsing to extract technology context
            parsed_requirements = self.enhanced_parser.parse_requirements(requirements)
            tech_context = self.context_extractor.build_context(parsed_requirements)

            self.logger.info(
                f"Extracted technology context: explicit={len(tech_context.explicit_technologies)}, "
                f"contextual={len(tech_context.contextual_technologies)}"
            )

            # Create a mock match result for context (since we're creating a new pattern)
            from app.pattern.matcher import MatchResult

            mock_match = MatchResult(
                pattern_id="NEW-PATTERN",
                pattern_name="New Pattern",
                feasibility=analysis.get("feasibility", "Automatable"),
                tech_stack=[],  # Empty since we're generating it
                confidence=0.8,
                tag_score=0.8,
                vector_score=0.8,
                blended_score=0.8,
                rationale="New pattern being created",
            )

            # Extract constraints from requirements and analysis
            constraints = {
                "banned_tools": requirements.get("banned_tools", [])
                + analysis.get("banned_tools_suggestions", []),
                "required_integrations": requirements.get("integrations", [])
                + analysis.get("required_integrations_suggestions", []),
            }

            # Generate intelligent tech stack with enhanced context awareness
            tech_stack = await self.tech_stack_generator.generate_tech_stack(
                [mock_match], requirements, constraints
            )

            # Auto-add any missing technologies to catalog if enabled
            if self.tech_stack_generator.auto_update_catalog:
                for tech in tech_context.explicit_technologies:
                    if not self.catalog_manager.lookup_technology(tech):
                        self.logger.info(
                            f"Auto-adding missing technology to catalog: {tech}"
                        )
                        self.catalog_manager.auto_add_technology(
                            tech,
                            {
                                "source": "pattern_creation",
                                "confidence": tech_context.explicit_technologies[tech],
                            },
                        )

            self.logger.info(
                f"Generated enhanced tech stack for new pattern: {tech_stack}"
            )
            return tech_stack

        except Exception as e:
            self.logger.error(
                f"Failed to generate enhanced tech stack for new pattern: {e}"
            )

            # Fallback to basic tech stack
            return self._generate_fallback_tech_stack(requirements, analysis)

    def _generate_fallback_tech_stack(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate basic fallback tech stack when intelligent generation fails.

        Args:
            requirements: User requirements
            analysis: Pattern analysis results

        Returns:
            Basic tech stack
        """
        automation_type = analysis.get("automation_type", "general_automation")

        # Basic tech stack based on automation type
        type_tech = {
            "scanning_automation": ["Python", "OpenCV", "mobile app framework"],
            "translation_automation": ["Python", "Google Translate API", "WebSocket"],
            "document_processing": ["Python", "PyPDF2", "Tesseract"],
            "api_integration": ["Python", "FastAPI", "httpx"],
            "monitoring_automation": ["Python", "Prometheus", "APScheduler"],
            "scheduled_automation": ["Python", "Celery", "APScheduler"],
            "workflow_automation": ["Python", "Celery", "SQLAlchemy"],
            "general_automation": ["Python", "FastAPI", "SQLAlchemy"],
        }

        return type_tech.get(automation_type, ["Python", "FastAPI"])

    def _generate_pattern_types(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate pattern type tags."""
        automation_type = analysis.get("automation_type", "general_automation")
        integrations = analysis.get("integration_points", [])

        pattern_types = [automation_type]

        # Add integration-based types
        if "api" in integrations:
            pattern_types.append("api_integration")
        if "database" in integrations:
            pattern_types.append("data_processing")
        if "mobile" in integrations:
            pattern_types.append("mobile_integration")
        if "cloud" in integrations:
            pattern_types.append("cloud_integration")

        # Add processing types
        processing_type = analysis.get("processing_type", "basic_processing")
        if processing_type != "basic_processing":
            pattern_types.append(processing_type)

        return pattern_types

    def _generate_input_requirements(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate input requirements for the pattern."""
        automation_type = analysis.get("automation_type", "general_automation")
        integrations = analysis.get("integration_points", [])

        input_reqs = []

        # Base requirements
        input_reqs.append("Clear process definition and requirements")
        input_reqs.append("Access to target systems and APIs")

        # Type-specific requirements
        type_requirements = {
            "scanning_automation": [
                "Mobile device with camera capability",
                "Barcode/QR code standards and formats",
                "Inventory database schema and access",
            ],
            "translation_automation": [
                "Source and target language specifications",
                "Translation service API credentials",
                "User preference management system",
            ],
            "document_processing": [
                "Document types and formats",
                "Extraction requirements and templates",
                "Quality validation criteria",
            ],
            "api_integration": [
                "API documentation and credentials",
                "Data mapping specifications",
                "Error handling requirements",
            ],
            "monitoring_automation": [
                "Monitoring targets and metrics",
                "Alert thresholds and conditions",
                "Notification channels and recipients",
            ],
        }

        input_reqs.extend(type_requirements.get(automation_type, []))

        # Integration-specific requirements
        if "database" in integrations:
            input_reqs.append("Database schema and connection details")
        if "cloud" in integrations:
            input_reqs.append("Cloud service credentials and configuration")
        if "mobile" in integrations:
            input_reqs.append(
                "Mobile platform specifications and deployment requirements"
            )

        return input_reqs

    def _calculate_pattern_confidence(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the new pattern."""
        # Base confidence for auto-generated patterns
        base_confidence = 0.7

        # Adjust based on requirement completeness
        description = requirements.get("description", "")
        if len(description) > 100:
            base_confidence += 0.1
        if len(description) > 200:
            base_confidence += 0.1

        # Adjust based on domain specificity
        domain = requirements.get("domain", "")
        if domain and domain != "general":
            base_confidence += 0.05

        # Adjust based on analysis completeness
        if len(analysis.get("integration_points", [])) > 0:
            base_confidence += 0.05
        if analysis.get("automation_type") != "general_automation":
            base_confidence += 0.05

        return min(0.95, base_confidence)  # Cap at 95% for auto-generated patterns

    def _estimate_complexity(
        self, requirements: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """Estimate implementation complexity."""
        integrations = analysis.get("integration_points", [])
        automation_type = analysis.get("automation_type", "general_automation")
        security_reqs = analysis.get("security_requirements", [])
        scalability = analysis.get("scalability_needs", "minimal_scale")

        complexity_score = 0

        # Base complexity by type
        type_complexity = {
            "scanning_automation": 2,
            "translation_automation": 3,
            "document_processing": 3,
            "api_integration": 1,
            "monitoring_automation": 2,
            "scheduled_automation": 1,
            "workflow_automation": 2,
            "general_automation": 1,
        }

        complexity_score += type_complexity.get(automation_type, 1)

        # Add for integrations
        complexity_score += len(integrations)

        # Add for security requirements
        complexity_score += len(security_reqs)

        # Add for scalability
        if scalability == "high_scale":
            complexity_score += 2
        elif scalability == "medium_scale":
            complexity_score += 1

        # Determine complexity level
        if complexity_score <= 3:
            return "Low"
        elif complexity_score <= 6:
            return "Medium"
        else:
            return "High"

    def _estimate_effort(self, complexity: str, analysis: Dict[str, Any]) -> str:
        """Estimate implementation effort."""
        base_effort = {"Low": "1-2 weeks", "Medium": "3-6 weeks", "High": "6-12 weeks"}

        return base_effort.get(complexity, "3-6 weeks")

    def _extract_required_integrations(self, requirements: Dict[str, Any]) -> List[str]:
        """Extract required integrations from requirements."""
        integrations = requirements.get("integrations", [])
        if isinstance(integrations, str):
            integrations = [integrations]

        # Add common integrations based on description
        description = str(requirements.get("description", "")).lower()

        if "database" in description:
            integrations.append("database")
        if "api" in description:
            integrations.append("api")
        if "mobile" in description:
            integrations.append("mobile")
        if "email" in description or "notification" in description:
            integrations.append("notification")

        return list(set(integrations))  # Remove duplicates

    async def _create_physical_task_pattern(
        self, pattern_id: str, requirements: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Create a pattern for physical tasks that are not automatable."""
        description = requirements.get("description", "")

        # Create a pattern that clearly indicates this is not automatable
        physical_pattern = {
            "pattern_id": pattern_id,
            "name": "Physical Task - Not Automatable",
            "description": f"Physical task requiring manual intervention: {description}",
            "feasibility": "Not Automatable",
            "pattern_type": ["physical_task", "manual_process"],
            "input_requirements": [
                "Physical presence required",
                "Manual tools and equipment",
                "Human skills and judgment",
            ],
            "tech_stack": [],  # No tech stack for physical tasks
            "related_patterns": [],
            "confidence_score": 0.95,  # High confidence that it's not automatable
            "constraints": {"banned_tools": [], "required_integrations": []},
            "domain": "physical_world",
            "complexity": "High",  # Physical tasks are inherently complex for automation
            "estimated_effort": "Not applicable - requires physical intervention",
            "created_from_session": session_id,
            "auto_generated": True,
        }

        # Save the pattern
        await self._save_pattern(physical_pattern)

        self.logger.info(
            f"Created physical task pattern {pattern_id} for non-automatable task"
        )
        return physical_pattern

    async def _save_pattern_securely(self, pattern: Dict[str, Any]) -> tuple[bool, str]:
        """Save pattern to the library with security validation, name uniqueness, and deduplication checks."""
        from app.pattern.loader import PatternLoader
        from app.services.pattern_name_validator import PatternNameValidator

        # 1. Check for duplicate patterns first
        duplicate_check = self.deduplication_service.check_pattern_before_save(pattern)
        
        if duplicate_check['is_duplicate']:
            self.logger.warning(
                f"Pattern creation blocked - duplicate detected: {duplicate_check['message']}"
            )
            return False, f"Duplicate pattern detected: {duplicate_check['message']}"
        
        if duplicate_check['similar_patterns']:
            self.logger.info(
                f"Pattern has {len(duplicate_check['similar_patterns'])} similar patterns but proceeding with save"
            )
            for similar in duplicate_check['similar_patterns']:
                self.logger.info(
                    f"  Similar to {similar['pattern_id']} ({similar['pattern_name']}) - "
                    f"{similar['similarity']:.1%} similarity"
                )

        # 2. Validate and fix pattern name if needed
        validator = PatternNameValidator(self.pattern_library_path)
        name_check = validator.check_pattern_name_before_save(pattern)
        
        if name_check['modified']:
            self.logger.info(
                f"Pattern name adjusted before save: '{name_check['old_name']}' → '{name_check['new_name']}' "
                f"(reason: {name_check['reason']})"
            )
            pattern = name_check['pattern']  # Use the updated pattern
            
            # Invalidate name manager cache since we're adding a new pattern
            self.name_manager.invalidate_cache()

        # 3. Use PatternLoader's secure save method
        pattern_loader = PatternLoader(self.pattern_library_path)
        success, message = pattern_loader.save_pattern(pattern)

        if success:
            self.logger.info(f"Securely saved pattern: {pattern['pattern_id']}")
        else:
            self.logger.error(f"Pattern save blocked by security validation: {message}")

        return success, message
