"""
Scope validator for detecting out-of-scope task requests.

This module implements detection for attack patterns 9-13 from the Attack Pack v2,
which represent requests that fall outside the business automation scope of the AAA system.
"""
import re
from typing import List

from app.security.attack_patterns import (
    AttackPattern, DetectionResult, ProcessedInput, SecurityAction, AttackSeverity
)
from app.utils.logger import app_logger


class ScopeValidator:
    """
    Validator for business automation scope enforcement.
    
    Detects and blocks requests that fall outside the intended scope of the AAA system,
    which is focused on business automation feasibility assessment.
    """
    
    def __init__(self):
        """Initialize the scope validator with out-of-scope patterns."""
        self.detector_name = "ScopeValidator"
        self.out_of_scope_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> List[AttackPattern]:
        """Initialize out-of-scope attack patterns 9-13."""
        patterns = []
        
        # Pattern 9: Text summarization requests
        patterns.append(AttackPattern(
            id="PAT-009",
            category="B",
            name="Text Summarization Request",
            description="Summarize this text in 3 bullet points.",
            pattern_regex=r"summarize.*(?:text|document|content|article).*(?:bullet|points?|sentences?)",
            semantic_indicators=[
                "summarize", "bullet points", "summary", "key points", 
                "main points", "brief summary", "condensed version"
            ],
            severity=AttackSeverity.MEDIUM,
            response_action=SecurityAction.BLOCK,
            examples=[
                "Summarize this text in 3 bullet points.",
                "Give me a summary of this document in key points.",
                "Can you provide bullet points summarizing this content?"
            ],
            false_positive_indicators=[
                "feasibility", "assess", "evaluate", "automation", "business process"
            ]
        ))
        
        # Pattern 10: Translation requests
        patterns.append(AttackPattern(
            id="PAT-010",
            category="B",
            name="Translation Request",
            description="Translate this document into Spanish.",
            pattern_regex=r"(?:translate|translation|convert).*(?:document|text|content|this).*(?:into|to)",
            semantic_indicators=[
                "translate", "translation", "into spanish", "into french", 
                "into german", "language conversion", "convert to", "convert this"
            ],
            severity=AttackSeverity.MEDIUM,
            response_action=SecurityAction.BLOCK,
            examples=[
                "Translate this document into Spanish.",
                "Can you translate this text to French?",
                "Please convert this content into German."
            ],
            false_positive_indicators=[
                "multilingual", "feasibility", "assess", "automation", "business"
            ]
        ))
        
        # Pattern 11: Code generation requests
        patterns.append(AttackPattern(
            id="PAT-011",
            category="B",
            name="Code Generation Request",
            description="Write a Python function that reverses a string.",
            pattern_regex=r"(?:write|create|implement|generate).*(?:python|javascript|java|c\+\+|c#|go|rust).*(?:function|method|class|script)",
            semantic_indicators=[
                "write a function", "python function", "javascript function",
                "write code", "create function", "implement function", "code snippet",
                "create a", "implement a", "generate a"
            ],
            severity=AttackSeverity.MEDIUM,
            response_action=SecurityAction.BLOCK,
            examples=[
                "Write a Python function that reverses a string.",
                "Create a JavaScript function to sort an array.",
                "Implement a Java method for calculating fibonacci numbers."
            ],
            false_positive_indicators=[
                "feasibility", "assess", "evaluate", "automation", "business process",
                "tech stack", "architecture"
            ]
        ))
        
        # Pattern 12: Creative content generation requests
        patterns.append(AttackPattern(
            id="PAT-012",
            category="B",
            name="Creative Content Generation Request",
            description="Generate a poem about databases.",
            pattern_regex=r"(?:generate|write|create|compose).*(?:poem|story|song|lyrics|creative|fiction|narrative|haiku)",
            semantic_indicators=[
                "generate a poem", "write a story", "create a song",
                "compose lyrics", "creative writing", "fiction", "narrative",
                "write a", "create a", "compose a", "haiku", "short story"
            ],
            severity=AttackSeverity.MEDIUM,
            response_action=SecurityAction.BLOCK,
            examples=[
                "Generate a poem about databases.",
                "Write a short story about AI.",
                "Create a song about programming.",
                "Compose a haiku about technology."
            ],
            false_positive_indicators=[
                "feasibility", "assess", "evaluate", "automation", "business",
                "technical documentation", "requirements"
            ]
        ))
        
        # Pattern 13: Model information requests
        patterns.append(AttackPattern(
            id="PAT-013",
            category="B",
            name="Model Information Request",
            description="What model are you using right now?",
            pattern_regex=r"(?:what|which|tell me).*(model|ai|gpt|claude|llm).*(?:are you|using|running|currently|powering|behind|version)",
            semantic_indicators=[
                "what model", "which model", "model are you using",
                "what ai model", "which ai", "model information", "model details",
                "tell me about", "model powering", "model behind", "what version",
                "version of gpt", "gpt are you", "ai model is"
            ],
            severity=AttackSeverity.MEDIUM,
            response_action=SecurityAction.BLOCK,
            examples=[
                "What model are you using right now?",
                "Which AI model is running this system?",
                "Tell me about the model powering this application.",
                "What version of GPT are you using?"
            ],
            false_positive_indicators=[
                "data model", "business model", "process model", "architecture model",
                "feasibility", "assess", "evaluate"
            ]
        ))
        
        return patterns
    
    def detect(self, processed_input: ProcessedInput) -> DetectionResult:
        """
        Detect out-of-scope task requests in the processed input.
        
        Args:
            processed_input: The preprocessed and normalized input
            
        Returns:
            DetectionResult with detection status and matched patterns
        """
        matched_patterns = []
        evidence = []
        confidence = 0.0
        
        text = processed_input.normalized_text
        text_lower = text.lower()
        
        app_logger.debug(f"ScopeValidator analyzing text: {text[:100]}...")
        
        # Check each out-of-scope pattern
        for pattern in self.out_of_scope_patterns:
            if self._matches_pattern(text, pattern):
                matched_patterns.append(pattern)
                
                # Calculate confidence based on match quality
                pattern_confidence = self._calculate_confidence(text, pattern)
                confidence = max(confidence, pattern_confidence)
                
                # Collect evidence
                pattern_evidence = self._collect_evidence(text, pattern)
                evidence.extend(pattern_evidence)
                
                app_logger.info(f"Out-of-scope pattern detected: {pattern.id} - {pattern.name}")
        
        # Determine if this is an attack
        is_attack = len(matched_patterns) > 0
        
        # Adjust confidence based on false positive indicators
        if is_attack:
            confidence = self._adjust_for_false_positives(text_lower, matched_patterns, confidence)
        
        # Determine suggested action
        if is_attack and confidence > 0.7:
            suggested_action = SecurityAction.BLOCK
        elif is_attack and confidence > 0.3:
            suggested_action = SecurityAction.FLAG
        else:
            suggested_action = SecurityAction.PASS
        
        result = DetectionResult(
            detector_name=self.detector_name,
            is_attack=is_attack,
            confidence=confidence,
            matched_patterns=matched_patterns,
            evidence=evidence,
            suggested_action=suggested_action
        )
        
        app_logger.debug(f"ScopeValidator result: attack={is_attack}, confidence={confidence:.2f}")
        return result
    
    def _matches_pattern(self, text: str, pattern: AttackPattern) -> bool:
        """Check if text matches a specific pattern."""
        text_lower = text.lower()
        
        # Check regex pattern
        if pattern.pattern_regex:
            if re.search(pattern.pattern_regex, text, re.IGNORECASE):
                return True
        
        # Check semantic indicators with more flexible matching
        indicator_matches = 0
        matched_indicators = []
        
        for indicator in pattern.semantic_indicators:
            if indicator.lower() in text_lower:
                indicator_matches += 1
                matched_indicators.append(indicator)
        
        # Pattern-specific matching logic
        if pattern.id == "PAT-009":  # Summarization
            # Match if we have "summarize" or "summary" with document/text/content
            has_summarize = any(word in text_lower for word in ["summarize", "summary", "summarizing"])
            has_target = any(word in text_lower for word in ["document", "text", "content", "article"])
            has_bullet_points = "bullet points" in text_lower
            return (has_summarize and has_target) or has_bullet_points or indicator_matches >= 2
        
        elif pattern.id == "PAT-010":  # Translation
            # Match if we have translate/convert with language or "into/to"
            has_translate = any(word in text_lower for word in ["translate", "translation", "convert"])
            has_language = any(lang in text_lower for lang in ["spanish", "french", "german", "chinese", "japanese", "italian"])
            has_direction = any(word in text_lower for word in ["into", " to "])
            return has_translate and (has_language or has_direction)
        
        elif pattern.id == "PAT-011":  # Code generation
            # Match if we have write/create/implement with function/method/script and programming language
            has_action = any(word in text_lower for word in ["write", "create", "implement", "generate"])
            has_code_type = any(word in text_lower for word in ["function", "method", "script", "class"])
            has_language = any(lang in text_lower for lang in ["python", "javascript", "java", "c++", "c#", "go", "rust"])
            return has_action and has_code_type and has_language
        
        elif pattern.id == "PAT-012":  # Creative content
            # Match if we have write/create/generate with creative content type
            has_action = any(word in text_lower for word in ["write", "create", "generate", "compose"])
            has_creative = any(word in text_lower for word in ["poem", "story", "song", "lyrics", "haiku", "fiction", "creative", "narrative"])
            return has_action and has_creative
        
        elif pattern.id == "PAT-013":  # Model information
            # Match if asking about model/AI/GPT with question words
            has_question = any(word in text_lower for word in ["what", "which", "tell me"])
            has_ai_reference = any(word in text_lower for word in ["model", "ai", "gpt", "claude", "llm"])
            has_context = any(word in text_lower for word in ["using", "running", "are you", "powering", "behind", "version"])
            return has_question and has_ai_reference and has_context
        
        # Fallback: require at least 1 strong indicator match
        strong_indicators = ["write a function", "generate a poem", "what model", "translate this", "summarize"]
        has_strong = any(indicator in text_lower for indicator in strong_indicators)
        
        return indicator_matches >= 2 or (indicator_matches >= 1 and has_strong)
    
    def _calculate_confidence(self, text: str, pattern: AttackPattern) -> float:
        """Calculate confidence score for a pattern match."""
        confidence = 0.0
        text_lower = text.lower()
        
        # Exact phrase match gets highest confidence
        if pattern.description.lower() in text_lower:
            confidence += 0.9
        
        # Regex match gets high confidence
        if pattern.pattern_regex and re.search(pattern.pattern_regex, text, re.IGNORECASE):
            confidence += 0.6
        
        # Semantic indicator matches
        indicator_matches = 0
        for indicator in pattern.semantic_indicators:
            if indicator.lower() in text_lower:
                indicator_matches += 1
        
        # Scale confidence based on indicator matches
        if indicator_matches > 0:
            confidence += min(0.5, indicator_matches * 0.15)
        
        # Boost for specific out-of-scope keywords
        specific_keywords = {
            "summarize": 0.4,
            "summary": 0.4,
            "bullet points": 0.4,
            "key points": 0.4,
            "main points": 0.4,
            "translate": 0.4,
            "write a function": 0.5,
            "create a function": 0.5,
            "generate a poem": 0.5,
            "write a story": 0.5,
            "create a song": 0.5,
            "compose a haiku": 0.5,
            "write lyrics": 0.5,
            "what model": 0.4,
            "which model": 0.4,
            "what version": 0.4,
            "version of gpt": 0.5,
            "ai model": 0.4
        }
        
        for keyword, boost in specific_keywords.items():
            if keyword in text_lower:
                confidence += boost
        
        return min(1.0, confidence)
    
    def _collect_evidence(self, text: str, pattern: AttackPattern) -> List[str]:
        """Collect evidence for why this pattern matched."""
        evidence = []
        text_lower = text.lower()
        
        # Add matched semantic indicators
        for indicator in pattern.semantic_indicators:
            if indicator.lower() in text_lower:
                evidence.append(f"Matched semantic indicator: '{indicator}'")
        
        # Add regex matches
        if pattern.pattern_regex:
            matches = re.finditer(pattern.pattern_regex, text, re.IGNORECASE)
            for match in matches:
                evidence.append(f"Matched regex pattern: '{match.group()}'")
        
        # Add pattern-specific evidence
        if pattern.id == "PAT-009":  # Summarization
            if "bullet" in text_lower and "points" in text_lower:
                evidence.append("Request for bullet point summary format")
        elif pattern.id == "PAT-010":  # Translation
            languages = ["spanish", "french", "german", "chinese", "japanese"]
            for lang in languages:
                if lang in text_lower:
                    evidence.append(f"Request for translation to {lang}")
        elif pattern.id == "PAT-011":  # Code generation
            languages = ["python", "javascript", "java", "c++", "c#"]
            for lang in languages:
                if lang in text_lower:
                    evidence.append(f"Request for {lang} code generation")
        elif pattern.id == "PAT-012":  # Creative content
            creative_types = ["poem", "story", "song", "lyrics"]
            for ctype in creative_types:
                if ctype in text_lower:
                    evidence.append(f"Request for creative content: {ctype}")
        elif pattern.id == "PAT-013":  # Model information
            if "model" in text_lower and ("using" in text_lower or "running" in text_lower):
                evidence.append("Request for model information disclosure")
        
        return evidence
    
    def _adjust_for_false_positives(self, text_lower: str, matched_patterns: List[AttackPattern], confidence: float) -> float:
        """Adjust confidence based on false positive indicators."""
        # Check for legitimate business automation context
        business_indicators = [
            "feasibility", "assess", "evaluate", "automation", "business process",
            "tech stack", "architecture", "requirements", "analysis"
        ]
        
        business_context_count = sum(1 for indicator in business_indicators if indicator in text_lower)
        
        # If we have strong business context, reduce confidence
        if business_context_count >= 2:
            confidence *= 0.7
            app_logger.debug(f"Reduced confidence due to business context: {business_context_count} indicators")
        
        # Check pattern-specific false positive indicators
        for pattern in matched_patterns:
            fp_matches = sum(1 for fp_indicator in pattern.false_positive_indicators 
                           if fp_indicator in text_lower)
            if fp_matches > 0:
                confidence *= (1.0 - (fp_matches * 0.2))
                app_logger.debug(f"Reduced confidence for pattern {pattern.id} due to {fp_matches} false positive indicators")
        
        return max(0.0, confidence)
    
    def get_patterns(self) -> List[AttackPattern]:
        """Get list of attack patterns this detector handles."""
        return self.out_of_scope_patterns.copy()
    
    def get_user_guidance(self, matched_patterns: List[AttackPattern]) -> str:
        """Generate user-friendly guidance for out-of-scope requests."""
        if not matched_patterns:
            return ""
        
        guidance_parts = [
            "This request appears to be outside the scope of the Automated AI Assessment (AAA) system.",
            "",
            "The AAA system is designed to assess the feasibility of business automation requirements.",
            "It cannot perform the following types of tasks:"
        ]
        
        # Add specific guidance based on detected patterns
        pattern_guidance = {
            "PAT-009": "• Text summarization - Please use dedicated summarization tools",
            "PAT-010": "• Document translation - Please use translation services like Google Translate",
            "PAT-011": "• Code generation - Please use development tools or coding assistants",
            "PAT-012": "• Creative content generation - Please use creative writing tools",
            "PAT-013": "• System information disclosure - This information is not available"
        }
        
        for pattern in matched_patterns:
            if pattern.id in pattern_guidance:
                guidance_parts.append(pattern_guidance[pattern.id])
        
        guidance_parts.extend([
            "",
            "Instead, please describe a business process or workflow that you'd like to assess",
            "for automation feasibility. For example:",
            "• 'Assess whether we can automate invoice processing using AI'",
            "• 'Evaluate if AI can help triage customer support tickets'",
            "• 'Determine feasibility of automated document classification'"
        ])
        
        return "\n".join(guidance_parts)