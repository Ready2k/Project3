"""PII redaction utilities."""

import re
from typing import Dict, Pattern


class PIIRedactor:
    """Redacts personally identifiable information from text."""
    
    def __init__(self):
        self.patterns: Dict[str, Pattern[str]] = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'api_key': re.compile(r'\bsk-[A-Za-z0-9]{16,}\b')
        }
    
    def redact(self, text: str) -> str:
        """Redact PII from the given text."""
        if not text:
            return text
            
        result = text
        for pattern_name, pattern in self.patterns.items():
            result = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', result)
        
        return result