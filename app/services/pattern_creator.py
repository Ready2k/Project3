"""Pattern creation service for generating new patterns when no existing patterns match."""

import json
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.llm.base import LLMProvider
from app.services.tech_stack_generator import TechStackGenerator
from app.utils.logger import app_logger


class PatternCreator:
    """Service for creating new automation patterns based on requirements."""
    
    def __init__(self, pattern_library_path: Path, llm_provider: Optional[LLMProvider] = None):
        """Initialize pattern creator.
        
        Args:
            pattern_library_path: Path to pattern library directory
            llm_provider: LLM provider for generating pattern details
        """
        self.pattern_library_path = pattern_library_path
        self.llm_provider = llm_provider
        self.tech_stack_generator = TechStackGenerator(llm_provider)
    
    async def create_pattern_from_requirements(self, 
                                             requirements: Dict[str, Any],
                                             session_id: str) -> Dict[str, Any]:
        """Create a new pattern based on user requirements.
        
        Args:
            requirements: User requirements dictionary
            session_id: Session ID for tracking
            
        Returns:
            New pattern dictionary
        """
        app_logger.info(f"Creating new pattern for session {session_id}")
        
        # Generate pattern ID
        pattern_id = self._generate_pattern_id()
        
        # Extract key information from requirements
        description = requirements.get("description", "").lower()
        domain = requirements.get("domain", "general")
        
        # Check for physical tasks that shouldn't have patterns created
        physical_keywords = [
            "paint", "painting", "build", "construction", "repair", "fix", "install",
            "clean", "cleaning", "move", "transport", "deliver", "physical", "manual",
            "hardware", "mechanical", "electrical wiring", "plumbing", "carpentry",
            "landscaping", "gardening", "cooking", "driving", "walking", "running"
        ]
        
        physical_count = sum(1 for keyword in physical_keywords if keyword in description)
        if physical_count > 0:
            app_logger.info(f"Detected physical task in description, creating 'Not Automatable' pattern")
            # Create a pattern that explicitly marks this as not automatable
            return await self._create_physical_task_pattern(pattern_id, requirements, session_id)
        
        # Analyze requirements to determine pattern characteristics
        pattern_analysis = await self._analyze_requirements(requirements)
        
        # Generate pattern name
        pattern_name = self._generate_pattern_name(requirements, pattern_analysis)
        
        # Determine feasibility
        feasibility = self._determine_feasibility(requirements, pattern_analysis)
        
        # Generate intelligent tech stack
        tech_stack = await self._generate_intelligent_tech_stack(requirements, pattern_analysis)
        
        # Generate pattern types
        pattern_types = self._generate_pattern_types(requirements, pattern_analysis)
        
        # Generate input requirements
        input_requirements = self._generate_input_requirements(requirements, pattern_analysis)
        
        # Calculate confidence score
        confidence_score = self._calculate_pattern_confidence(requirements, pattern_analysis)
        
        # Estimate complexity and effort
        complexity = self._estimate_complexity(requirements, pattern_analysis)
        estimated_effort = self._estimate_effort(complexity, pattern_analysis)
        
        # Create pattern dictionary
        new_pattern = {
            "pattern_id": pattern_id,
            "name": pattern_name,
            "description": self._generate_pattern_description(requirements, pattern_analysis),
            "feasibility": feasibility,
            "pattern_type": pattern_types,
            "input_requirements": input_requirements,
            "tech_stack": tech_stack,
            "related_patterns": [],  # Will be populated later if needed
            "confidence_score": confidence_score,
            "constraints": {
                "banned_tools": [],
                "required_integrations": self._extract_required_integrations(requirements)
            },
            "domain": domain,
            "complexity": complexity,
            "estimated_effort": estimated_effort,
            "created_from_session": session_id,
            "auto_generated": True
        }
        
        # Save pattern to library
        await self._save_pattern(new_pattern)
        
        app_logger.info(f"Created new pattern {pattern_id}: {pattern_name}")
        return new_pattern
    
    def _generate_pattern_id(self) -> str:
        """Generate a unique pattern ID."""
        # Find the highest existing pattern number
        existing_patterns = list(self.pattern_library_path.glob("PAT-*.json"))
        max_num = 0
        
        for pattern_file in existing_patterns:
            try:
                num_str = pattern_file.stem.split("-")[1]
                num = int(num_str)
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue
        
        return f"PAT-{max_num + 1:03d}"
    
    async def _analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze requirements to extract pattern characteristics.
        
        Args:
            requirements: User requirements
            
        Returns:
            Analysis results dictionary
        """
        description = requirements.get("description", "")
        
        # Analyze description for key concepts
        analysis = {
            "automation_type": self._detect_automation_type(description, requirements),
            "data_flow": self._detect_data_flow(description, requirements),
            "integration_points": self._detect_integration_points(description, requirements),
            "user_interaction": self._detect_user_interaction(description, requirements),
            "processing_type": self._detect_processing_type(description, requirements),
            "scalability_needs": self._detect_scalability_needs(description, requirements),
            "security_requirements": self._detect_security_requirements(description, requirements)
        }
        
        # Use LLM for deeper analysis if available
        if self.llm_provider:
            try:
                llm_analysis = await self._llm_analyze_requirements(requirements)
                analysis.update(llm_analysis)
            except Exception as e:
                app_logger.warning(f"LLM analysis failed: {e}")
        
        return analysis
    
    def _detect_automation_type(self, description: str, requirements: Dict[str, Any]) -> str:
        """Detect the type of automation needed."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["scan", "barcode", "qr", "image", "photo"]):
            return "scanning_automation"
        elif any(word in desc_lower for word in ["translate", "translation", "language"]):
            return "translation_automation"
        elif any(word in desc_lower for word in ["document", "pdf", "file", "extract"]):
            return "document_processing"
        elif any(word in desc_lower for word in ["api", "integrate", "connect", "sync"]):
            return "api_integration"
        elif any(word in desc_lower for word in ["monitor", "alert", "notify", "watch"]):
            return "monitoring_automation"
        elif any(word in desc_lower for word in ["schedule", "batch", "periodic", "cron"]):
            return "scheduled_automation"
        elif any(word in desc_lower for word in ["workflow", "process", "step", "sequence"]):
            return "workflow_automation"
        else:
            return "general_automation"
    
    def _detect_data_flow(self, description: str, requirements: Dict[str, Any]) -> str:
        """Detect data flow patterns."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["real-time", "realtime", "live", "instant"]):
            return "real_time"
        elif any(word in desc_lower for word in ["batch", "bulk", "scheduled", "periodic"]):
            return "batch"
        elif any(word in desc_lower for word in ["stream", "continuous", "ongoing"]):
            return "streaming"
        else:
            return "on_demand"
    
    def _detect_integration_points(self, description: str, requirements: Dict[str, Any]) -> List[str]:
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
            "communication": ["slack", "teams", "discord", "chat"]
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
    
    def _detect_user_interaction(self, description: str, requirements: Dict[str, Any]) -> str:
        """Detect level of user interaction required."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["automatic", "automated", "no user", "unattended"]):
            return "fully_automated"
        elif any(word in desc_lower for word in ["review", "approve", "confirm", "manual"]):
            return "human_in_loop"
        elif any(word in desc_lower for word in ["trigger", "initiate", "start", "click"]):
            return "user_initiated"
        else:
            return "semi_automated"
    
    def _detect_processing_type(self, description: str, requirements: Dict[str, Any]) -> str:
        """Detect type of processing required."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["ml", "ai", "machine learning", "predict", "classify"]):
            return "ml_processing"
        elif any(word in desc_lower for word in ["transform", "convert", "parse", "extract"]):
            return "data_transformation"
        elif any(word in desc_lower for word in ["validate", "verify", "check", "audit"]):
            return "validation"
        elif any(word in desc_lower for word in ["aggregate", "sum", "count", "calculate"]):
            return "aggregation"
        else:
            return "basic_processing"
    
    def _detect_scalability_needs(self, description: str, requirements: Dict[str, Any]) -> str:
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
    
    def _detect_security_requirements(self, description: str, requirements: Dict[str, Any]) -> List[str]:
        """Detect security requirements."""
        desc_lower = description.lower()
        security_reqs = []
        
        if any(word in desc_lower for word in ["encrypt", "secure", "private", "confidential"]):
            security_reqs.append("encryption")
        if any(word in desc_lower for word in ["auth", "login", "permission", "access"]):
            security_reqs.append("authentication")
        if any(word in desc_lower for word in ["audit", "log", "track", "monitor"]):
            security_reqs.append("audit_logging")
        if any(word in desc_lower for word in ["gdpr", "hipaa", "compliance", "regulation"]):
            security_reqs.append("compliance")
        
        return security_reqs
    
    async def _llm_analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze requirements for deeper insights."""
        description = requirements.get("description", "")
        
        prompt = f"""
        Analyze the following automation requirement and provide insights:
        
        Requirement: {description}
        
        Please analyze and provide:
        1. Primary automation goal
        2. Key technical challenges
        3. Recommended approach
        4. Potential risks or limitations
        
        Respond in JSON format with keys: goal, challenges, approach, risks
        """
        
        try:
            response = await self.llm_provider.generate_text(prompt)
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            app_logger.debug(f"LLM analysis parsing failed: {e}")
        
        return {}
    
    def _generate_pattern_name(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> str:
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
            "general_automation": "Process Automation"
        }
        
        base_name = type_names.get(automation_type, "Process Automation")
        
        # Add domain context if specific and valid
        if domain and domain not in ["general", "None", "none", ""]:
            domain_formatted = domain.replace("_", " ").title()
            return f"{domain_formatted} {base_name}"
        
        return base_name
    
    def _generate_pattern_description(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive pattern description."""
        base_description = requirements.get("description", "")
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
            "general_automation": "General purpose automation system with configurable processing and integration capabilities"
        }
        
        base_desc = description_templates.get(automation_type, description_templates["general_automation"])
        
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
    
    def _determine_feasibility(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Determine feasibility of the new pattern."""
        automation_type = analysis.get("automation_type", "general_automation")
        user_interaction = analysis.get("user_interaction", "semi_automated")
        security_reqs = analysis.get("security_requirements", [])
        
        # High feasibility patterns
        high_feasibility_types = [
            "api_integration", "scheduled_automation", "monitoring_automation", "scanning_automation"
        ]
        
        # Medium feasibility patterns
        medium_feasibility_types = [
            "document_processing", "workflow_automation", "translation_automation"
        ]
        
        if automation_type in high_feasibility_types and user_interaction != "human_in_loop":
            return "Automatable"
        elif automation_type in medium_feasibility_types or len(security_reqs) > 2:
            return "Partially Automatable"
        else:
            return "Automatable"  # Default to automatable for new patterns
    
    async def _generate_intelligent_tech_stack(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate intelligent tech stack using the TechStackGenerator.
        
        Args:
            requirements: User requirements
            analysis: Pattern analysis results
            
        Returns:
            List of recommended technologies
        """
        try:
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
                rationale="New pattern being created"
            )
            
            # Extract constraints
            constraints = {
                "banned_tools": requirements.get("banned_tools", []),
                "required_integrations": requirements.get("integrations", [])
            }
            
            # Generate intelligent tech stack
            tech_stack = await self.tech_stack_generator.generate_tech_stack(
                [mock_match], requirements, constraints
            )
            
            app_logger.info(f"Generated intelligent tech stack for new pattern: {tech_stack}")
            return tech_stack
            
        except Exception as e:
            app_logger.error(f"Failed to generate intelligent tech stack for new pattern: {e}")
            
            # Fallback to basic tech stack
            return self._generate_fallback_tech_stack(requirements, analysis)
    
    def _generate_fallback_tech_stack(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
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
            "general_automation": ["Python", "FastAPI", "SQLAlchemy"]
        }
        
        return type_tech.get(automation_type, ["Python", "FastAPI"])
    
    def _generate_pattern_types(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
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
    
    def _generate_input_requirements(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
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
                "Inventory database schema and access"
            ],
            "translation_automation": [
                "Source and target language specifications",
                "Translation service API credentials",
                "User preference management system"
            ],
            "document_processing": [
                "Document types and formats",
                "Extraction requirements and templates",
                "Quality validation criteria"
            ],
            "api_integration": [
                "API documentation and credentials",
                "Data mapping specifications",
                "Error handling requirements"
            ],
            "monitoring_automation": [
                "Monitoring targets and metrics",
                "Alert thresholds and conditions",
                "Notification channels and recipients"
            ]
        }
        
        input_reqs.extend(type_requirements.get(automation_type, []))
        
        # Integration-specific requirements
        if "database" in integrations:
            input_reqs.append("Database schema and connection details")
        if "cloud" in integrations:
            input_reqs.append("Cloud service credentials and configuration")
        if "mobile" in integrations:
            input_reqs.append("Mobile platform specifications and deployment requirements")
        
        return input_reqs
    
    def _calculate_pattern_confidence(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> float:
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
    
    def _estimate_complexity(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> str:
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
            "general_automation": 1
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
        base_effort = {
            "Low": "1-2 weeks",
            "Medium": "3-6 weeks", 
            "High": "6-12 weeks"
        }
        
        return base_effort.get(complexity, "3-6 weeks")
    
    def _extract_required_integrations(self, requirements: Dict[str, Any]) -> List[str]:
        """Extract required integrations from requirements."""
        integrations = requirements.get("integrations", [])
        if isinstance(integrations, str):
            integrations = [integrations]
        
        # Add common integrations based on description
        description = requirements.get("description", "").lower()
        
        if "database" in description:
            integrations.append("database")
        if "api" in description:
            integrations.append("api")
        if "mobile" in description:
            integrations.append("mobile")
        if "email" in description or "notification" in description:
            integrations.append("notification")
        
        return list(set(integrations))  # Remove duplicates
    
    async def _create_physical_task_pattern(self, pattern_id: str, requirements: Dict[str, Any], session_id: str) -> Dict[str, Any]:
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
                "Human skills and judgment"
            ],
            "tech_stack": [],  # No tech stack for physical tasks
            "related_patterns": [],
            "confidence_score": 0.95,  # High confidence that it's not automatable
            "constraints": {
                "banned_tools": [],
                "required_integrations": []
            },
            "domain": "physical_world",
            "complexity": "High",  # Physical tasks are inherently complex for automation
            "estimated_effort": "Not applicable - requires physical intervention",
            "created_from_session": session_id,
            "auto_generated": True
        }
        
        # Save the pattern
        await self._save_pattern(physical_pattern)
        
        app_logger.info(f"Created physical task pattern {pattern_id} for non-automatable task")
        return physical_pattern
    
    async def _save_pattern(self, pattern: Dict[str, Any]) -> None:
        """Save the new pattern to the pattern library."""
        pattern_file = self.pattern_library_path / f"{pattern['pattern_id']}.json"
        
        # Ensure directory exists
        self.pattern_library_path.mkdir(parents=True, exist_ok=True)
        
        # Save pattern
        with open(pattern_file, 'w', encoding='utf-8') as f:
            json.dump(pattern, f, indent=2, ensure_ascii=False)
        
        app_logger.info(f"Saved new pattern to {pattern_file}")