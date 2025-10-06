"""
Advanced Prompt Defender - Main orchestrator for advanced prompt attack detection.

This class coordinates all specialized detectors to provide comprehensive protection
against the 42 attack patterns identified in the Prompt Attack Pack v2.
"""

import asyncio
import time
from typing import List, Dict, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.security.attack_patterns import (
    AttackPattern, ProcessedInput, DetectionResult, SecurityDecision, SecurityAction,
    AttackPatternDatabase
)
from app.security.defense_config import get_defense_config, AdvancedPromptDefenseConfig
from app.security.input_preprocessor import InputPreprocessor
from app.security.overt_injection_detector import OvertInjectionDetector
from app.security.covert_injection_detector import CovertInjectionDetector
from app.security.scope_validator import ScopeValidator
from app.security.data_egress_detector import DataEgressDetector
from app.security.protocol_tampering_detector import ProtocolTamperingDetector
from app.security.context_attack_detector import ContextAttackDetector
from app.security.multilingual_attack_detector import MultilingualAttackDetector
from app.security.business_logic_protector import BusinessLogicProtector
from app.security.security_event_logger import SecurityEventLogger, AlertSeverity
from app.security.user_education import UserEducationSystem, UserGuidanceMessage
from app.security.performance_optimizer import (
    PerformanceOptimizer, performance_monitor
)
from app.utils.logger import app_logger





class AdvancedPromptDefender:
    """Main orchestrator for advanced prompt attack detection."""
    
    def __init__(self, config: Optional[AdvancedPromptDefenseConfig] = None):
        """Initialize the Advanced Prompt Defender."""
        self.config = config or get_defense_config()
        self.preprocessor = InputPreprocessor()
        self.attack_db = AttackPatternDatabase()
        self.logger = SecurityEventLogger()
        self.user_education = UserEducationSystem()
        
        # Initialize all detectors
        self.detectors = self._initialize_detectors()
        
        # Performance optimization system
        if self.config.enable_caching or self.config.parallel_detection:
            self.performance_optimizer = PerformanceOptimizer(
                cache_size=self.config.cache_size,
                cache_ttl=self.config.cache_ttl_seconds,
                max_workers=self.config.max_workers,
                timeout_ms=self.config.max_validation_time_ms,
                max_memory_mb=self.config.max_memory_mb
            )
            
            # Register performance alert callback
            if self.config.enable_performance_monitoring:
                self.performance_optimizer.register_alert_callback(self._handle_performance_alert)
        else:
            self.performance_optimizer = None
        
        # Legacy thread pool (kept for backward compatibility)
        self.executor = None
        if self.config.parallel_detection and not self.performance_optimizer:
            try:
                self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
            except Exception as e:
                app_logger.warning(f"Failed to create thread pool executor: {e}")
                self.executor = None
        
        # Register detectors with performance optimizer
        if self.performance_optimizer:
            for detector in self.detectors:
                self.performance_optimizer.register_detector(detector)
        
        app_logger.info(f"AdvancedPromptDefender initialized with {len(self.detectors)} detectors, "
                       f"performance optimization: {self.performance_optimizer is not None}")
    
    def _initialize_detectors(self) -> List:
        """Initialize all specialized attack detectors."""
        detectors = []
        
        # Initialize each detector if enabled
        if self.config.overt_injection.enabled:
            detectors.append(OvertInjectionDetector())
        
        if self.config.covert_injection.enabled:
            detectors.append(CovertInjectionDetector())
        
        if self.config.scope_validator.enabled:
            detectors.append(ScopeValidator())
        
        if self.config.data_egress_detector.enabled:
            detectors.append(DataEgressDetector())
        
        if self.config.protocol_tampering_detector.enabled:
            detectors.append(ProtocolTamperingDetector())
        
        if self.config.context_attack_detector.enabled:
            detectors.append(ContextAttackDetector())
        
        if self.config.multilingual_attack.enabled:
            detectors.append(MultilingualAttackDetector())
        
        if self.config.business_logic.enabled:
            detectors.append(BusinessLogicProtector())
        
        app_logger.info(f"Initialized {len(detectors)} enabled detectors")
        return detectors
    
    @performance_monitor
    async def validate_input(self, user_input: str, session_id: str = "unknown",
                          metadata: Optional[Dict[str, Any]] = None) -> SecurityDecision:
        """Validate input through all security layers."""
        if not self.config.enabled:
            return SecurityDecision(
                action=SecurityAction.PASS,
                confidence=0.0,
                detected_attacks=[],
                user_message="Security validation disabled",
                technical_details="Advanced prompt defense is disabled in configuration"
            )
        
        start_time = time.time()
        
        try:
            # Step 1: Preprocess input
            processed_input = await self._preprocess_input(user_input)
            
            # Step 2: Run all detectors with performance optimization
            detection_results = await self._run_detectors_optimized(processed_input)
            
            # Step 3: Aggregate results and make security decision
            decision = self._make_security_decision(detection_results, processed_input)
            
            # Step 4: Generate user guidance if needed
            if decision.action != SecurityAction.PASS:
                guidance = self.user_education.generate_user_guidance(decision, session_id)
                decision.user_message = self._format_guidance_message(guidance)
                decision.guidance_data = guidance
            
            # Step 5: Log the decision with comprehensive monitoring
            processing_time = (time.time() - start_time) * 1000
            await self.logger.log_security_decision(
                decision, user_input, processing_time, session_id, metadata
            )
            
            return decision
            
        except Exception as e:
            app_logger.error(f"Error in security validation: {e}")
            # Fail secure - block on error
            error_decision = SecurityDecision(
                action=SecurityAction.BLOCK,
                confidence=1.0,
                detected_attacks=[],
                user_message="Security validation failed. Please try again.",
                technical_details=f"Internal security error: {str(e)}"
            )
            
            # Log the error decision
            try:
                processing_time = (time.time() - start_time) * 1000
                await self.logger.log_security_decision(
                    error_decision, user_input, processing_time, session_id, 
                    {**(metadata or {}), "error": str(e)}
                )
            except Exception:
                pass  # Don't let logging errors prevent security response
            
            return error_decision
    
    async def _preprocess_input(self, user_input: str) -> ProcessedInput:
        """Preprocess user input for security analysis."""
        try:
            # Run preprocessing in thread pool to avoid blocking
            if self.executor:
                loop = asyncio.get_event_loop()
                processed = await loop.run_in_executor(
                    self.executor, 
                    self.preprocessor.preprocess_input, 
                    user_input
                )
            else:
                processed = self.preprocessor.preprocess_input(user_input)
            
            return processed
            
        except Exception as e:
            app_logger.error(f"Error in input preprocessing: {e}")
            # Return basic processed input on error
            return ProcessedInput(
                original_text=user_input,
                normalized_text=user_input,
                decoded_content=[],
                extracted_urls=[],
                detected_encodings=[],
                language="en",
                length_stats={"original_length": len(user_input)}
            )
    
    async def _run_detectors(self, processed_input: ProcessedInput) -> List[DetectionResult]:
        """Run all enabled detectors on the processed input."""
        detection_results = []
        
        if self.config.parallel_detection and self.executor:
            # Run detectors in parallel
            future_to_detector = {}
            
            for detector in self.detectors:
                future = self.executor.submit(detector.detect, processed_input)
                future_to_detector[future] = detector
            
            # Collect results with timeout
            timeout_seconds = self.config.max_validation_time_ms / 1000.0
            
            for future in as_completed(future_to_detector, timeout=timeout_seconds):
                detector = future_to_detector[future]
                try:
                    result = future.result()
                    detection_results.append(result)
                except Exception as e:
                    app_logger.error(f"Error in detector {detector.__class__.__name__}: {e}")
                    # Add error result
                    detection_results.append(DetectionResult(
                        detector_name=detector.__class__.__name__,
                        is_attack=False,
                        confidence=0.0,
                        matched_patterns=[],
                        evidence=[f"Detector error: {str(e)}"],
                        suggested_action=SecurityAction.PASS
                    ))
        else:
            # Run detectors sequentially
            for detector in self.detectors:
                try:
                    result = detector.detect(processed_input)
                    detection_results.append(result)
                except Exception as e:
                    app_logger.error(f"Error in detector {detector.__class__.__name__}: {e}")
                    # Add error result
                    detection_results.append(DetectionResult(
                        detector_name=detector.__class__.__name__,
                        is_attack=False,
                        confidence=0.0,
                        matched_patterns=[],
                        evidence=[f"Detector error: {str(e)}"],
                        suggested_action=SecurityAction.PASS
                    ))
        
        return detection_results
    
    async def _run_detectors_optimized(self, processed_input: ProcessedInput) -> List[DetectionResult]:
        """Run detectors with performance optimization."""
        if not self.performance_optimizer:
            # Fall back to legacy method
            return await self._run_detectors(processed_input)
        
        # Generate configuration hash for cache invalidation
        config_hash = self._generate_config_hash()
        
        # Prepare detector functions for parallel execution
        detector_funcs = []
        for detector in self.detectors:
            detector_funcs.append((detector.detect, detector.__class__.__name__))
        
        # Run with performance optimization
        if self.config.parallel_detection and len(detector_funcs) > 1:
            results = await self.performance_optimizer.parallel_detection(
                detector_funcs, processed_input, config_hash
            )
        else:
            # Sequential execution with caching
            results = []
            for detector_func, detector_name in detector_funcs:
                try:
                    result = await self.performance_optimizer.cached_detection(
                        detector_func, processed_input, detector_name, config_hash
                    )
                    results.append(result)
                except Exception as e:
                    app_logger.error(f"Error in detector {detector_name}: {e}")
                    results.append(DetectionResult(
                        detector_name=detector_name,
                        is_attack=False,
                        confidence=0.0,
                        matched_patterns=[],
                        evidence=[f"Detector error: {str(e)}"],
                        suggested_action=SecurityAction.PASS
                    ))
        
        # Periodic cache optimization
        if (self.performance_optimizer.metrics.total_validations % 
            self.config.cache_optimization_interval == 0):
            self.performance_optimizer.optimize_cache()
        
        return results
    
    def _generate_config_hash(self) -> str:
        """Generate hash of current configuration for cache invalidation."""
        try:
            import hashlib
            config_str = f"{self.config.attack_pack_version}:{self.config.detection_confidence_threshold}"
            for detector in self.detectors:
                if hasattr(detector, 'get_config_hash'):
                    config_str += f":{detector.get_config_hash()}"
                else:
                    config_str += f":{detector.__class__.__name__}"
            
            return hashlib.md5(config_str.encode()).hexdigest()[:16]
        except Exception:
            return "default"
    
    def _handle_performance_alert(self, alert_type: str, alert_data: Dict[str, Any]) -> None:
        """Handle performance alerts."""
        app_logger.warning(f"Performance alert [{alert_type}]: {alert_data.get('message', 'Unknown issue')}")
        
        # Take corrective actions based on alert type
        if alert_type == 'high_latency' and self.performance_optimizer:
            # Optimize cache to improve performance
            self.performance_optimizer.optimize_cache()
        
        elif alert_type == 'high_memory_usage' and self.performance_optimizer:
            # Clear cache to free memory
            app_logger.info("Clearing cache due to high memory usage")
            self.performance_optimizer.clear_cache()
        
        elif alert_type == 'timeout_errors':
            # Consider disabling parallel processing temporarily
            if self.config.parallel_detection:
                app_logger.warning("Consider disabling parallel detection due to timeout errors")
        
        # Log to security event logger for monitoring
        try:
            asyncio.create_task(self.logger.log_performance_alert(alert_type, alert_data))
        except Exception as e:
            app_logger.error(f"Failed to log performance alert: {e}")
    
    def _make_security_decision(self, detection_results: List[DetectionResult], 
                              processed_input: ProcessedInput) -> SecurityDecision:
        """Aggregate detection results and make final security decision."""
        
        # Collect all detected attacks and evidence
        all_detected_patterns = []
        all_evidence = []
        max_confidence = 0.0
        suggested_actions = []
        
        for result in detection_results:
            if result.is_attack:
                all_detected_patterns.extend(result.matched_patterns)
                if isinstance(result.evidence, list):
                    all_evidence.extend(result.evidence)
                else:
                    all_evidence.append(str(result.evidence))
                
                max_confidence = max(max_confidence, result.confidence)
                suggested_actions.append(result.suggested_action)
        
        # Remove duplicate patterns
        unique_patterns = []
        seen_pattern_ids = set()
        for pattern in all_detected_patterns:
            if pattern.id not in seen_pattern_ids:
                unique_patterns.append(pattern)
                seen_pattern_ids.add(pattern.id)
        
        # Determine final action based on thresholds and pattern severity
        final_action = self._determine_final_action(
            unique_patterns, max_confidence, suggested_actions
        )
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            detection_results, max_confidence
        )
        
        # Generate technical details
        technical_details = self._generate_technical_details(
            detection_results, unique_patterns, processed_input
        )
        
        # Determine if input should be sanitized
        sanitized_input = None
        if final_action == SecurityAction.FLAG:
            sanitized_input = self._sanitize_input(processed_input, unique_patterns)
        
        return SecurityDecision(
            action=final_action,
            confidence=overall_confidence,
            detected_attacks=unique_patterns,
            sanitized_input=sanitized_input,
            user_message="",  # Will be filled by generate_user_guidance
            technical_details=technical_details,
            detection_results=detection_results
        )
    
    def _determine_final_action(self, patterns: List[AttackPattern], 
                              max_confidence: float, 
                              suggested_actions: List[SecurityAction]) -> SecurityAction:
        """Determine the final security action based on patterns and confidence."""
        
        if not patterns or max_confidence < self.config.flag_threshold:
            return SecurityAction.PASS
        
        # Check if any pattern requires blocking
        for pattern in patterns:
            if pattern.response_action == SecurityAction.BLOCK:
                if max_confidence >= self.config.block_threshold:
                    return SecurityAction.BLOCK
        
        # Check confidence thresholds
        if max_confidence >= self.config.block_threshold:
            # High confidence - check if any detector suggests blocking
            if SecurityAction.BLOCK in suggested_actions:
                return SecurityAction.BLOCK
        
        if max_confidence >= self.config.flag_threshold:
            return SecurityAction.FLAG
        
        return SecurityAction.PASS
    
    def _calculate_overall_confidence(self, detection_results: List[DetectionResult], 
                                    max_confidence: float) -> float:
        """Calculate overall confidence score from all detection results."""
        if not detection_results:
            return 0.0
        
        # Use weighted average of detector confidences
        total_weight = 0.0
        weighted_sum = 0.0
        
        # Weight detectors by their importance and reliability
        detector_weights = {
            "OvertInjectionDetector": 1.0,
            "CovertInjectionDetector": 1.0,
            "DataEgressDetector": 1.2,  # Higher weight for data protection
            "BusinessLogicProtector": 1.2,  # Higher weight for system protection
            "ScopeValidator": 0.8,  # Lower weight for scope validation
            "ProtocolTamperingDetector": 0.9,
            "ContextAttackDetector": 1.0,
            "MultilingualAttackDetector": 0.9
        }
        
        for result in detection_results:
            weight = detector_weights.get(result.detector_name, 1.0)
            weighted_sum += result.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return max_confidence
        
        # Combine weighted average with max confidence
        weighted_avg = weighted_sum / total_weight
        
        # Use the higher of weighted average or max confidence, but cap at 1.0
        return min(1.0, max(weighted_avg, max_confidence * 0.8))
    
    def _generate_technical_details(self, detection_results: List[DetectionResult],
                                  patterns: List[AttackPattern],
                                  processed_input: ProcessedInput) -> str:
        """Generate technical details about the security decision."""
        details = []
        
        # Input processing details
        details.append(f"Input length: {len(processed_input.original_text)} characters")
        details.append(f"Language detected: {processed_input.language}")
        
        if processed_input.decoded_content:
            details.append(f"Decoded content found: {len(processed_input.decoded_content)} items")
        
        if processed_input.detected_encodings:
            details.append(f"Encodings detected: {', '.join(processed_input.detected_encodings)}")
        
        # Detection results summary
        active_detectors = [r for r in detection_results if r.is_attack]
        if active_detectors:
            details.append(f"Active detectors: {len(active_detectors)}/{len(detection_results)}")
            
            for result in active_detectors:
                pattern_ids = [p.id for p in result.matched_patterns]
                details.append(
                    f"- {result.detector_name}: {result.confidence:.2f} confidence, "
                    f"patterns {pattern_ids}"
                )
        
        # Pattern details
        if patterns:
            details.append(f"Attack patterns detected: {len(patterns)}")
            for pattern in patterns[:5]:  # Limit to first 5 patterns
                details.append(f"- {pattern.id}: {pattern.name} ({pattern.severity.value})")
        
        return "\n".join(details)
    
    def _sanitize_input(self, processed_input: ProcessedInput, 
                       patterns: List[AttackPattern]) -> Optional[str]:
        """Attempt to sanitize flagged input by removing malicious content."""
        try:
            sanitized = processed_input.normalized_text
            
            # Remove content that matches attack patterns
            for pattern in patterns:
                if pattern.pattern_regex:
                    import re
                    sanitized = re.sub(
                        pattern.pattern_regex, 
                        "[REMOVED]", 
                        sanitized, 
                        flags=re.IGNORECASE | re.MULTILINE
                    )
            
            # Remove common attack indicators
            attack_indicators = [
                r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions?",
                r"system\s*:\s*.*enable",
                r"switch\s+roles",
                r"reveal.*configuration",
                r"base64.*payload"
            ]
            
            for indicator in attack_indicators:
                import re
                sanitized = re.sub(indicator, "[REMOVED]", sanitized, flags=re.IGNORECASE)
            
            # Clean up multiple spaces and empty lines
            import re
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()
            sanitized = re.sub(r'\[REMOVED\]\s*', '', sanitized)
            
            # Only return sanitized version if it's substantially different and not empty
            if sanitized and len(sanitized) > 10 and sanitized != processed_input.normalized_text:
                return sanitized
            
            return None
            
        except Exception as e:
            app_logger.error(f"Error sanitizing input: {e}")
            return None
    
    def _format_guidance_message(self, guidance: UserGuidanceMessage) -> str:
        """Format a UserGuidanceMessage into a string for backward compatibility."""
        if not self.config.provide_user_guidance:
            return "Request blocked by security system."
        
        parts = [f"**{guidance.title}**", "", guidance.content]
        
        if guidance.action_items:
            parts.extend(["", "**Action Items:**"])
            for item in guidance.action_items:
                parts.append(f"• {item}")
        
        if guidance.appeal_info:
            parts.extend(["", "**Appeal Information:**", guidance.appeal_info])
        
        return "\n".join(parts)
    
    def _generate_user_guidance(self, decision: SecurityDecision) -> str:
        """Generate helpful user guidance for blocked or flagged requests (legacy method)."""
        if not self.config.provide_user_guidance:
            return "Request blocked by security system."
        
        if decision.action == SecurityAction.BLOCK:
            return self._generate_block_guidance(decision)
        elif decision.action == SecurityAction.FLAG:
            return self._generate_flag_guidance(decision)
        else:
            return ""
    
    def _generate_block_guidance(self, decision: SecurityDecision) -> str:
        """Generate guidance for blocked requests."""
        messages = [
            "Your request has been blocked by our security system."
        ]
        
        # Categorize the types of attacks detected
        attack_categories = set()
        for pattern in decision.detected_attacks:
            if pattern.category in ['C', 'D']:  # Injection attacks
                attack_categories.add("prompt_injection")
            elif pattern.category == 'B':  # Out of scope
                attack_categories.add("out_of_scope")
            elif pattern.category in ['F', 'M']:  # Data egress
                attack_categories.add("data_extraction")
            elif pattern.category == 'K':  # Business logic
                attack_categories.add("system_manipulation")
            elif pattern.category == 'E':  # Tool abuse
                attack_categories.add("tool_abuse")
        
        # Provide specific guidance based on attack types
        if "out_of_scope" in attack_categories:
            messages.append(
                "This system is designed for business automation feasibility assessment. "
                "Please focus your request on evaluating whether a business process "
                "can be automated with AI."
            )
        
        if "prompt_injection" in attack_categories:
            messages.append(
                "Your request appears to contain instructions that could manipulate "
                "the system's behavior. Please rephrase your request using natural language "
                "to describe your business automation needs."
            )
        
        if "data_extraction" in attack_categories:
            messages.append(
                "Your request appears to be attempting to extract system information. "
                "This system only provides business automation assessments and cannot "
                "share internal configuration or data."
            )
        
        if "system_manipulation" in attack_categories:
            messages.append(
                "Your request appears to be attempting to modify system settings. "
                "Please focus on describing your business process for automation assessment."
            )
        
        # Add general guidance
        messages.append(
            "To use this system effectively, please describe:\n"
            "• The business process you want to automate\n"
            "• Current manual steps involved\n"
            "• Expected outcomes and success criteria\n"
            "• Any specific requirements or constraints"
        )
        
        if self.config.appeal_mechanism:
            messages.append(
                "If you believe this was flagged in error, please contact support "
                "with a description of your legitimate business use case."
            )
        
        return "\n\n".join(messages)
    
    def _generate_flag_guidance(self, decision: SecurityDecision) -> str:
        """Generate guidance for flagged requests."""
        messages = [
            "Your request has been flagged for review by our security system."
        ]
        
        if decision.sanitized_input:
            messages.append(
                "We've attempted to process a cleaned version of your request. "
                "If the results don't meet your needs, please rephrase your request "
                "more clearly."
            )
        else:
            messages.append(
                "Please review your request and ensure it clearly describes your "
                "business automation needs without ambiguous instructions."
            )
        
        messages.append(
            "For best results, please:\n"
            "• Use clear, direct language\n"
            "• Focus on business outcomes\n"
            "• Avoid technical jargon or system commands\n"
            "• Describe the process you want to automate"
        )
        
        return "\n\n".join(messages)
    
    def get_user_guidance(self, decision: SecurityDecision) -> str:
        """Generate helpful user guidance for blocked/flagged requests."""
        return self._generate_user_guidance(decision)
    
    def get_attack_patterns(self) -> List[AttackPattern]:
        """Get all attack patterns from the database."""
        return self.attack_db.get_all_patterns()
    
    def get_detector_status(self) -> Dict[str, Dict]:
        """Get status information for all detectors."""
        status = {}
        
        for detector in self.detectors:
            detector_name = detector.__class__.__name__
            status[detector_name] = {
                "enabled": hasattr(detector, 'is_enabled') and detector.is_enabled(),
                "patterns": len(detector.get_patterns()) if hasattr(detector, 'get_patterns') else 0,
                "confidence_threshold": (
                    detector.get_confidence_threshold() 
                    if hasattr(detector, 'get_confidence_threshold') 
                    else 0.5
                )
            }
        
        return status
    
    def update_config(self, config: AdvancedPromptDefenseConfig) -> None:
        """Update the defender configuration."""
        self.config = config
        
        # Reinitialize detectors with new config
        self.detectors = self._initialize_detectors()
        
        app_logger.info("AdvancedPromptDefender configuration updated")
    
    def get_security_metrics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive security metrics."""
        return {
            'current_metrics': self.logger.get_security_metrics(time_window_hours),
            'attack_statistics': self.logger.get_attack_statistics(time_window_hours),
            'progressive_response_status': self.logger.get_progressive_response_status(),
            'detector_status': self.get_detector_status()
        }
    
    def get_recent_security_events(self, limit: int = 100, 
                                 action_filter: Optional[SecurityAction] = None) -> List[Dict[str, Any]]:
        """Get recent security events."""
        return self.logger.get_recent_events(limit, action_filter)
    
    def register_security_alert_callback(self, callback: callable) -> None:
        """Register callback for security alerts."""
        self.logger.register_alert_callback(callback)
    
    def reset_user_progressive_response(self, user_identifier: str) -> bool:
        """Reset progressive response for a user (admin function)."""
        return self.logger.reset_progressive_response(user_identifier)
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for security monitoring dashboard."""
        return {
            'metrics': self.get_security_metrics(),
            'recent_events': self.get_recent_security_events(50),
            'high_severity_events': self.logger.get_recent_events(
                20, severity_filter=AlertSeverity.HIGH
            ),
            'critical_events': self.logger.get_recent_events(
                10, severity_filter=AlertSeverity.CRITICAL
            ),
            'system_status': {
                'enabled': self.config.enabled,
                'detectors_active': len(self.detectors),
                'parallel_detection': self.config.parallel_detection,
                'logging_enabled': self.config.log_all_detections,
                'alerting_enabled': self.config.alert_on_attacks
            },
            'user_education_stats': self.user_education.get_guidance_statistics()
        }
    
    def get_educational_content(self, topic: str = "all") -> Dict[str, str]:
        """Get educational content about system usage."""
        return self.user_education.get_educational_content(topic)
    
    def get_acceptable_examples(self, category: str = "all") -> Dict[str, List[str]]:
        """Get examples of acceptable business automation requests."""
        return self.user_education.get_acceptable_examples(category)
    
    def submit_user_appeal(self, request_id: str, original_input: str,
                          user_explanation: str, business_justification: str,
                          contact_info: str) -> str:
        """Submit an appeal for a misclassified request."""
        return self.user_education.submit_appeal(
            request_id, original_input, user_explanation, 
            business_justification, contact_info
        )
    
    def get_appeal_status(self, appeal_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an appeal request."""
        return self.user_education.get_appeal_status(appeal_id)
    
    def process_appeal(self, appeal_id: str, decision: str, 
                      reviewer_notes: str = "") -> bool:
        """Process an appeal request (admin function)."""
        return self.user_education.process_appeal(appeal_id, decision, reviewer_notes)
    
    def get_pending_appeals(self) -> List[Dict[str, Any]]:
        """Get all pending appeal requests (admin function)."""
        return self.user_education.get_pending_appeals()
    
    def generate_system_documentation(self) -> str:
        """Generate comprehensive system documentation for users."""
        return self.user_education.generate_system_documentation()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        if self.performance_optimizer:
            return self.performance_optimizer.get_performance_metrics()
        else:
            return {
                'validation_metrics': {'total_validations': 0, 'avg_latency_ms': 0},
                'cache_metrics': {'hit_rate_percent': 0, 'total_hits': 0, 'total_misses': 0},
                'execution_metrics': {'parallel_executions': 0, 'sequential_executions': 0},
                'resource_metrics': {'current_memory_mb': 0},
                'system_status': {'performance_optimization_enabled': False}
            }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Manually trigger performance optimization."""
        if self.performance_optimizer:
            self.performance_optimizer.optimize_cache()
            return {
                'status': 'success',
                'message': 'Performance optimization completed',
                'metrics': self.performance_optimizer.get_performance_metrics()
            }
        else:
            return {
                'status': 'disabled',
                'message': 'Performance optimization is not enabled'
            }
    
    def clear_performance_cache(self) -> Dict[str, str]:
        """Clear the performance cache."""
        if self.performance_optimizer:
            self.performance_optimizer.clear_cache()
            return {'status': 'success', 'message': 'Performance cache cleared'}
        else:
            return {'status': 'disabled', 'message': 'Performance optimization is not enabled'}
    
    def reset_performance_metrics(self) -> Dict[str, str]:
        """Reset performance metrics."""
        if self.performance_optimizer:
            self.performance_optimizer.reset_metrics()
            return {'status': 'success', 'message': 'Performance metrics reset'}
        else:
            return {'status': 'disabled', 'message': 'Performance optimization is not enabled'}
    
    def register_performance_alert_callback(self, callback: Callable[[str, Dict], None]) -> None:
        """Register callback for performance alerts."""
        if self.performance_optimizer:
            self.performance_optimizer.register_alert_callback(callback)
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'performance_optimizer') and self.performance_optimizer:
            try:
                self.performance_optimizer.shutdown()
            except Exception:
                pass  # Ignore cleanup errors
        
        if hasattr(self, 'executor') and self.executor:
            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass  # Ignore cleanup errors