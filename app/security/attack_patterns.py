"""
Attack pattern database and data models for advanced prompt defense.
"""
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.utils.logger import app_logger


class SecurityAction(Enum):
    """Security actions for detected attacks."""
    PASS = "pass"
    FLAG = "flag"
    BLOCK = "block"


class AttackSeverity(Enum):
    """Severity levels for attack patterns."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AttackPattern:
    """Represents a specific attack pattern from the Attack Pack."""
    id: str
    category: str  # A, B, C, D, E, F, G, H, I, J, K, L, M from Attack Pack
    name: str
    description: str
    pattern_regex: str
    semantic_indicators: List[str]
    severity: AttackSeverity
    response_action: SecurityAction
    examples: List[str]
    false_positive_indicators: List[str] = field(default_factory=list)
    
    def matches_text(self, text: str) -> bool:
        """Check if this pattern matches the given text."""
        # Check regex pattern
        if self.pattern_regex and re.search(self.pattern_regex, text, re.IGNORECASE):
            return True
        
        # Check semantic indicators
        text_lower = text.lower()
        for indicator in self.semantic_indicators:
            if indicator.lower() in text_lower:
                return True
        
        return False


@dataclass
class ProcessedInput:
    """Input after preprocessing and normalization."""
    original_text: str
    normalized_text: str
    decoded_content: List[str] = field(default_factory=list)
    extracted_urls: List[str] = field(default_factory=list)
    detected_encodings: List[str] = field(default_factory=list)
    language: str = "en"
    length_stats: Dict[str, int] = field(default_factory=dict)
    zero_width_chars_removed: bool = False
    confusable_chars_normalized: bool = False


@dataclass
class DetectionResult:
    """Result from individual attack detector."""
    detector_name: str
    is_attack: bool
    confidence: float
    matched_patterns: List[AttackPattern]
    evidence: List[str]
    suggested_action: SecurityAction


@dataclass
class SecurityDecision:
    """Result of security validation."""
    action: SecurityAction
    confidence: float
    detected_attacks: List[AttackPattern]
    sanitized_input: Optional[str] = None
    user_message: str = ""
    technical_details: str = ""
    detection_results: List[DetectionResult] = field(default_factory=list)
    guidance_data: Optional[Any] = None


class AttackPatternDatabase:
    """Database of known attack patterns with versioning and updates."""
    
    def __init__(self, attack_pack_file: Optional[str] = None):
        """Initialize the attack pattern database."""
        self.patterns: Dict[str, AttackPattern] = {}
        self.custom_patterns: Dict[str, AttackPattern] = {}
        self.version = "v2"
        self.last_updated = datetime.now()
        
        # Load patterns from attack pack
        if attack_pack_file:
            self.load_from_attack_pack(attack_pack_file)
        else:
            # Load default attack pack
            default_pack = Path("examples/prompt_attack_pack_v2.txt")
            if default_pack.exists():
                self.load_from_attack_pack(str(default_pack))
    
    def load_from_attack_pack(self, attack_pack_file: str) -> None:
        """Load attack patterns from the Attack Pack v2 file."""
        try:
            with open(attack_pack_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the attack pack content
            patterns = self._parse_attack_pack(content)
            
            for pattern in patterns:
                self.patterns[pattern.id] = pattern
            
            app_logger.info(f"Loaded {len(patterns)} attack patterns from {attack_pack_file}")
            
        except Exception as e:
            app_logger.error(f"Failed to load attack pack from {attack_pack_file}: {e}")
            raise
    
    def _parse_attack_pack(self, content: str) -> List[AttackPattern]:
        """Parse the attack pack content and create AttackPattern objects."""
        patterns = []
        
        # Define category mappings
        category_info = {
            'A': ('In-Scope Feasibility', SecurityAction.PASS, AttackSeverity.LOW),
            'B': ('Out-of-Scope Tasking', SecurityAction.BLOCK, AttackSeverity.MEDIUM),
            'C': ('Overt Prompt Injection', SecurityAction.BLOCK, AttackSeverity.HIGH),
            'D': ('Covert/Obfuscated Injection', SecurityAction.FLAG, AttackSeverity.HIGH),
            'E': ('Tool Abuse/SSRF', SecurityAction.BLOCK, AttackSeverity.CRITICAL),
            'F': ('Data Egress Probes', SecurityAction.BLOCK, AttackSeverity.CRITICAL),
            'G': ('Protocol/Schema Tampering', SecurityAction.FLAG, AttackSeverity.MEDIUM),
            'H': ('Long-Context Burying', SecurityAction.BLOCK, AttackSeverity.HIGH),
            'I': ('Multilingual', SecurityAction.PASS, AttackSeverity.MEDIUM),  # Mixed, will override per pattern
            'J': ('CSV/Excel Dangerous Content', SecurityAction.BLOCK, AttackSeverity.HIGH),
            'K': ('Business-Logic/Safety Toggles', SecurityAction.BLOCK, AttackSeverity.CRITICAL),
            'L': ('Stressful but In-Scope', SecurityAction.PASS, AttackSeverity.LOW),
            'M': ('Canary Coverage', SecurityAction.BLOCK, AttackSeverity.CRITICAL)
        }
        
        # Extract numbered patterns from content
        pattern_regex = r'(\d+)\)\s*"([^"]+)"\s*\[(\w+)\]'
        matches = re.findall(pattern_regex, content)
        
        for match in matches:
            pattern_num, description, action_str = match
            pattern_id = f"PAT-{int(pattern_num):03d}"
            
            # Determine category based on pattern number
            category = self._get_category_for_pattern(int(pattern_num))
            category_name, default_action, severity = category_info.get(category, ('Unknown', SecurityAction.FLAG, AttackSeverity.MEDIUM))
            
            # Override action based on explicit marking in attack pack
            if action_str == "PASS":
                action = SecurityAction.PASS
            elif action_str == "FLAG":
                action = SecurityAction.FLAG
            elif action_str == "BLOCK":
                action = SecurityAction.BLOCK
            else:
                action = default_action
            
            # Generate semantic indicators and regex patterns
            semantic_indicators = self._extract_semantic_indicators(description)
            pattern_regex = self._generate_pattern_regex(description, semantic_indicators)
            
            pattern = AttackPattern(
                id=pattern_id,
                category=category,
                name=f"{category_name} - Pattern {pattern_num}",
                description=description,
                pattern_regex=pattern_regex,
                semantic_indicators=semantic_indicators,
                severity=severity,
                response_action=action,
                examples=[description],
                false_positive_indicators=self._get_false_positive_indicators(category)
            )
            
            patterns.append(pattern)
        
        return patterns
    
    def _get_category_for_pattern(self, pattern_num: int) -> str:
        """Map pattern number to category letter."""
        if 1 <= pattern_num <= 8:
            return 'A'
        elif 9 <= pattern_num <= 13:
            return 'B'
        elif 14 <= pattern_num <= 17:
            return 'C'
        elif 18 <= pattern_num <= 21:
            return 'D'
        elif 22 <= pattern_num <= 25:
            return 'E'
        elif 26 <= pattern_num <= 28:
            return 'F'
        elif 29 <= pattern_num <= 32:
            return 'G'
        elif pattern_num == 33:
            return 'H'
        elif 34 <= pattern_num <= 35:
            return 'I'
        elif 36 <= pattern_num <= 37:
            return 'J'
        elif 38 <= pattern_num <= 39:
            return 'K'
        elif 40 <= pattern_num <= 41:
            return 'L'
        elif pattern_num == 42:
            return 'M'
        else:
            return 'Unknown'
    
    def _extract_semantic_indicators(self, description: str) -> List[str]:
        """Extract key semantic indicators from pattern description."""
        indicators = []
        
        # Common attack indicators
        attack_keywords = [
            "ignore", "previous", "instructions", "system", "prompt", "reveal", "configuration",
            "safety", "rules", "switch", "roles", "model", "user", "enable", "disable",
            "web", "tool", "http", "fetch", "shell", "command", "environment", "variable",
            "json", "base64", "decode", "hidden", "zero-width", "markdown", "confusable",
            "unicode", "ssrf", "meta-data", "admin", "egress", "extract", "canary",
            "webservice", "formula", "sum", "provider", "tokens", "timeout", "safety=off",
            "summarize", "translate", "write", "generate", "function", "poem", "python"
        ]
        
        description_lower = description.lower()
        for keyword in attack_keywords:
            if keyword in description_lower:
                indicators.append(keyword)
        
        # Extract quoted strings as potential indicators
        quoted_strings = re.findall(r'"([^"]+)"', description)
        indicators.extend(quoted_strings)
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', description)
        indicators.extend(urls)
        
        return list(set(indicators))  # Remove duplicates
    
    def _generate_pattern_regex(self, description: str, semantic_indicators: List[str]) -> str:
        """Generate regex pattern for matching similar attacks."""
        # Create a flexible regex based on key terms
        key_terms = []
        
        # Extract important phrases
        if "ignore" in description.lower() and "previous" in description.lower():
            key_terms.append(r"ignore.*previous.*instructions?")
        
        if "system" in description.lower() and ("prompt" in description.lower() or "owner" in description.lower()):
            key_terms.append(r"system.*(prompt|owner)")
        
        if "switch" in description.lower() and "role" in description.lower():
            key_terms.append(r"switch.*roles?")
        
        if "base64" in description.lower():
            key_terms.append(r"base64.*payload")
        
        if "environment" in description.lower() and "variable" in description.lower():
            key_terms.append(r"environment.*variable")
        
        if "json" in description.lower():
            key_terms.append(r'json.*\{.*\}')
        
        # Out-of-scope task patterns
        if "summarize" in description.lower():
            key_terms.append(r"summarize.*text")
        
        if "translate" in description.lower():
            key_terms.append(r"translate.*document")
        
        if "write" in description.lower() and "function" in description.lower():
            key_terms.append(r"write.*function")
        
        if "generate" in description.lower() and "poem" in description.lower():
            key_terms.append(r"generate.*poem")
        
        if "model" in description.lower() and ("using" in description.lower() or "are you" in description.lower()):
            key_terms.append(r"(what|which).*model.*using")
        
        if key_terms:
            return "|".join(f"({term})" for term in key_terms)
        
        # Fallback: create regex from semantic indicators
        if semantic_indicators:
            escaped_indicators = [re.escape(indicator) for indicator in semantic_indicators[:5]]  # Limit to avoid overly complex regex
            return "|".join(escaped_indicators)
        
        return ""
    
    def _get_false_positive_indicators(self, category: str) -> List[str]:
        """Get false positive indicators for a category."""
        false_positive_indicators = {
            'A': ['feasibility', 'assess', 'evaluate', 'analyze', 'determine', 'business'],
            'B': ['summarize', 'translate', 'generate', 'write', 'function'],
            'I': ['spanish', 'french', 'german', 'multilingual', 'language']
        }
        return false_positive_indicators.get(category, [])
    
    def match_patterns(self, text: str, category: Optional[str] = None) -> List[AttackPattern]:
        """Match text against attack patterns in specific category or all categories."""
        matched_patterns = []
        
        patterns_to_check = self.patterns.values()
        if category:
            patterns_to_check = [p for p in patterns_to_check if p.category == category]
        
        # Score patterns by match quality
        pattern_scores = []
        
        for pattern in patterns_to_check:
            if pattern.matches_text(text):
                score = self._calculate_match_score(text, pattern)
                pattern_scores.append((pattern, score))
        
        # Sort by score (higher is better) and return patterns
        pattern_scores.sort(key=lambda x: x[1], reverse=True)
        matched_patterns = [pattern for pattern, score in pattern_scores]
        
        return matched_patterns
    
    def _calculate_match_score(self, text: str, pattern: AttackPattern) -> float:
        """Calculate match score for a pattern against text."""
        score = 0.0
        text_lower = text.lower()
        
        # Exact phrase match gets highest score
        if pattern.description.lower() in text_lower or text_lower in pattern.description.lower():
            score += 10.0
        
        # Regex match gets high score
        if pattern.pattern_regex and re.search(pattern.pattern_regex, text, re.IGNORECASE):
            score += 5.0
        
        # Semantic indicator matches
        for indicator in pattern.semantic_indicators:
            if indicator.lower() in text_lower:
                score += 1.0
        
        # Penalize false positive indicators
        for fp_indicator in pattern.false_positive_indicators:
            if fp_indicator.lower() in text_lower:
                score -= 2.0
        
        # Boost score for more specific patterns (fewer semantic indicators = more specific)
        if len(pattern.semantic_indicators) > 0:
            score += 5.0 / len(pattern.semantic_indicators)
        
        return score
    
    def get_patterns_by_category(self, category: str) -> List[AttackPattern]:
        """Get all patterns for a specific category."""
        return [p for p in self.patterns.values() if p.category == category]
    
    def get_patterns_by_action(self, action: SecurityAction) -> List[AttackPattern]:
        """Get all patterns with a specific response action."""
        return [p for p in self.patterns.values() if p.response_action == action]
    
    def add_pattern(self, pattern: AttackPattern) -> None:
        """Add new attack pattern to database."""
        if pattern.id.startswith("CUSTOM-"):
            self.custom_patterns[pattern.id] = pattern
        else:
            self.patterns[pattern.id] = pattern
        
        app_logger.info(f"Added attack pattern: {pattern.id}")
    
    def update_from_attack_pack(self, attack_pack_file: str) -> None:
        """Update patterns from new attack pack version."""
        old_count = len(self.patterns)
        self.load_from_attack_pack(attack_pack_file)
        new_count = len(self.patterns)
        
        app_logger.info(f"Updated attack patterns: {old_count} -> {new_count}")
        self.last_updated = datetime.now()
    
    def get_all_patterns(self) -> List[AttackPattern]:
        """Get all patterns (built-in and custom)."""
        all_patterns = list(self.patterns.values()) + list(self.custom_patterns.values())
        return sorted(all_patterns, key=lambda p: p.id)
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[AttackPattern]:
        """Get a specific pattern by ID."""
        return self.patterns.get(pattern_id) or self.custom_patterns.get(pattern_id)
    
    def export_patterns(self, file_path: str) -> None:
        """Export all patterns to JSON file."""
        export_data = {
            'version': self.version,
            'last_updated': self.last_updated.isoformat(),
            'patterns': {}
        }
        
        for pattern_id, pattern in {**self.patterns, **self.custom_patterns}.items():
            export_data['patterns'][pattern_id] = {
                'id': pattern.id,
                'category': pattern.category,
                'name': pattern.name,
                'description': pattern.description,
                'pattern_regex': pattern.pattern_regex,
                'semantic_indicators': pattern.semantic_indicators,
                'severity': pattern.severity.value,
                'response_action': pattern.response_action.value,
                'examples': pattern.examples,
                'false_positive_indicators': pattern.false_positive_indicators
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        app_logger.info(f"Exported {len(export_data['patterns'])} patterns to {file_path}")