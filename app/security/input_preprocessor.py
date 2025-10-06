"""Input preprocessing and normalization for advanced prompt attack defense."""

import re
import base64
import urllib.parse
import unicodedata
from typing import List, Tuple, Dict
from dataclasses import dataclass
from app.utils.logger import app_logger


@dataclass
class ProcessedInput:
    """Input after preprocessing and normalization."""
    original_text: str
    normalized_text: str
    decoded_content: List[str]
    extracted_urls: List[str]
    detected_encodings: List[str]
    language: str
    length_stats: Dict[str, int]
    zero_width_chars_removed: bool
    confusable_chars_normalized: bool


class InputPreprocessor:
    """Preprocesses input to normalize and decode obfuscation attempts."""
    
    def __init__(self):
        # Zero-width characters that can be used for obfuscation
        self.zero_width_chars = [
            '\u200B',  # Zero Width Space
            '\u200C',  # Zero Width Non-Joiner
            '\u200D',  # Zero Width Joiner
            '\u2060',  # Word Joiner
            '\uFEFF',  # Zero Width No-Break Space (BOM)
            '\u180E',  # Mongolian Vowel Separator
        ]
        
        # Common Unicode confusable characters used in attacks
        # Maps confusable characters to their ASCII equivalents
        self.confusable_map = {
            # Cyrillic lookalikes
            'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'у': 'y',
            'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O', 
            'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X', 'У': 'Y',
            # Greek lookalikes
            'α': 'a', 'β': 'b', 'γ': 'y', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'n',
            'θ': 'o', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'u', 'ν': 'v', 'ξ': 'e',
            'ο': 'o', 'π': 'n', 'ρ': 'p', 'σ': 's', 'τ': 't', 'υ': 'u', 'φ': 'f',
            'χ': 'x', 'ψ': 'w', 'ω': 'w',
            'Α': 'A', 'Β': 'B', 'Γ': 'T', 'Δ': 'A', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H',
            'Θ': 'O', 'Ι': 'I', 'Κ': 'K', 'Λ': 'A', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'E',
            'Ο': 'O', 'Π': 'N', 'Ρ': 'P', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Φ': 'F',
            'Χ': 'X', 'Ψ': 'W', 'Ω': 'O',
            # Small caps and other confusables from attack pattern #21
            'sʏstem': 'system', 'ɢᴇᴛ': 'get', 'ʏ': 'y', 'ɢ': 'g', 'ᴇ': 'e', 'ᴛ': 't',
            # Mathematical alphanumeric symbols
            '𝐚': 'a', '𝐛': 'b', '𝐜': 'c', '𝐝': 'd', '𝐞': 'e', '𝐟': 'f', '𝐠': 'g',
            '𝐡': 'h', '𝐢': 'i', '𝐣': 'j', '𝐤': 'k', '𝐥': 'l', '𝐦': 'm', '𝐧': 'n',
            '𝐨': 'o', '𝐩': 'p', '𝐪': 'q', '𝐫': 'r', '𝐬': 's', '𝐭': 't', '𝐮': 'u',
            '𝐯': 'v', '𝐰': 'w', '𝐱': 'x', '𝐲': 'y', '𝐳': 'z',
        }
        
        # Base64 detection patterns
        self.base64_pattern = re.compile(r'[A-Za-z0-9+/]{4,}={0,2}')
        
        # URL detection patterns
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+|'
            r'ftp://[^\s<>"{}|\\^`\[\]]+|'
            r'www\.[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )
        
        # Markdown link pattern for data exfiltration detection
        self.markdown_link_pattern = re.compile(
            r'\[([^\]]*)\]\(([^)]+)\)',
            re.IGNORECASE
        )
        
        # Template variable patterns in URLs (attack pattern #20)
        self.template_var_pattern = re.compile(
            r'\{\{[^}]+\}\}|'  # {{VARIABLE}}
            r'\$\{[^}]+\}|'    # ${VARIABLE}
            r'%[A-Z_]+%',      # %VARIABLE%
            re.IGNORECASE
        )
    
    def normalize_text(self, text: str) -> str:
        """Normalize Unicode, remove zero-width chars, decode common encodings."""
        if not text:
            return text
        
        # Step 1: Unicode normalization (NFC form)
        normalized = unicodedata.normalize('NFC', text)
        
        # Step 2: Remove zero-width characters
        for zwc in self.zero_width_chars:
            normalized = normalized.replace(zwc, '')
        
        # Step 3: Normalize confusable characters
        for confusable, replacement in self.confusable_map.items():
            normalized = normalized.replace(confusable, replacement)
        
        return normalized
    
    def detect_base64_content(self, text: str) -> List[Tuple[str, str]]:
        """Detect and decode base64 content. Returns list of (original, decoded) tuples."""
        decoded_content = []
        
        # Find potential base64 strings
        matches = self.base64_pattern.findall(text)
        
        for match in matches:
            # Skip very short matches that are likely false positives
            if len(match) < 8:
                continue
            
            try:
                # Try to decode as base64
                decoded_bytes = base64.b64decode(match, validate=True)
                decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
                
                # Only consider it valid if it contains meaningful text
                if len(decoded_str.strip()) > 0 and any(c.isalpha() for c in decoded_str):
                    decoded_content.append((match, decoded_str))
                    app_logger.info(f"Detected base64 content: {match[:20]}... -> {decoded_str[:50]}...")
                    
            except Exception:
                # Not valid base64, skip
                continue
        
        return decoded_content
    
    def detect_url_encoding(self, text: str) -> List[Tuple[str, str]]:
        """Detect and decode URL-encoded content. Returns list of (original, decoded) tuples."""
        decoded_content = []
        
        # Look for URL-encoded sequences (% followed by hex digits)
        url_encoded_pattern = re.compile(r'%[0-9A-Fa-f]{2}')
        
        if url_encoded_pattern.search(text):
            try:
                decoded = urllib.parse.unquote(text)
                if decoded != text:  # Only add if decoding changed something
                    decoded_content.append((text, decoded))
                    app_logger.info(f"Detected URL encoding: {text[:50]}... -> {decoded[:50]}...")
            except Exception as e:
                app_logger.warning(f"Failed to URL decode text: {e}")
        
        return decoded_content
    
    def extract_markdown_links(self, text: str) -> List[Dict[str, str]]:
        """Extract markdown links and check for data exfiltration patterns."""
        links = []
        
        matches = self.markdown_link_pattern.findall(text)
        
        for link_text, url in matches:
            link_info = {
                'text': link_text,
                'url': url,
                'has_template_vars': bool(self.template_var_pattern.search(url)),
                'suspicious': False
            }
            
            # Check for suspicious patterns in URLs
            url_lower = url.lower()
            suspicious_patterns = [
                'system_prompt', 'config', 'env', 'secret', 'key', 'token',
                'password', 'credential', 'api_key', 'private', 'internal'
            ]
            
            for pattern in suspicious_patterns:
                if pattern in url_lower:
                    link_info['suspicious'] = True
                    break
            
            # Check for template variables (attack pattern #20)
            if link_info['has_template_vars']:
                link_info['suspicious'] = True
                app_logger.warning(f"Detected markdown link with template variables: {url}")
            
            links.append(link_info)
        
        return links
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text."""
        return self.url_pattern.findall(text)
    
    def detect_language(self, text: str) -> str:
        """Simple language detection based on character sets."""
        if not text:
            return 'unknown'
        
        # Count different character types
        latin_chars = sum(1 for c in text if ord(c) < 256 and c.isalpha())
        cyrillic_chars = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF)
        chinese_chars = sum(1 for c in text if 0x4E00 <= ord(c) <= 0x9FFF)
        arabic_chars = sum(1 for c in text if 0x0600 <= ord(c) <= 0x06FF)
        
        total_chars = latin_chars + cyrillic_chars + chinese_chars + arabic_chars
        
        if total_chars == 0:
            return 'unknown'
        
        # Determine primary language
        if cyrillic_chars / total_chars > 0.3:
            return 'cyrillic'
        elif chinese_chars / total_chars > 0.3:
            return 'chinese'
        elif arabic_chars / total_chars > 0.3:
            return 'arabic'
        else:
            return 'latin'
    
    def decode_obfuscation(self, text: str) -> Tuple[str, List[str]]:
        """Detect and decode base64, URL encoding, Unicode confusables."""
        decoded_texts = []
        
        # Detect base64 content
        base64_content = self.detect_base64_content(text)
        for original, decoded in base64_content:
            decoded_texts.append(f"Base64 decoded: {decoded}")
        
        # Detect URL encoding
        url_encoded_content = self.detect_url_encoding(text)
        for original, decoded in url_encoded_content:
            decoded_texts.append(f"URL decoded: {decoded}")
        
        # Normalize the text
        normalized = self.normalize_text(text)
        
        return normalized, decoded_texts
    
    def extract_hidden_content(self, text: str) -> List[str]:
        """Extract content from markdown links, embedded data, etc."""
        hidden_content = []
        
        # Extract markdown links
        markdown_links = self.extract_markdown_links(text)
        for link in markdown_links:
            if link['suspicious']:
                hidden_content.append(f"Suspicious markdown link: {link['url']}")
        
        # Look for other hidden content patterns
        # Check for HTML comments
        html_comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
        html_comments = html_comment_pattern.findall(text)
        for comment in html_comments:
            hidden_content.append(f"HTML comment: {comment}")
        
        return hidden_content
    
    def get_length_stats(self, text: str) -> Dict[str, int]:
        """Get length statistics for the text."""
        return {
            'total_chars': len(text),
            'total_words': len(text.split()),
            'total_lines': len(text.splitlines()),
            'non_ascii_chars': sum(1 for c in text if ord(c) > 127),
            'whitespace_chars': sum(1 for c in text if c.isspace()),
        }
    
    def preprocess_input(self, user_input: str) -> ProcessedInput:
        """Main preprocessing function that applies all normalization and detection."""
        if not user_input:
            return ProcessedInput(
                original_text="",
                normalized_text="",
                decoded_content=[],
                extracted_urls=[],
                detected_encodings=[],
                language="unknown",
                length_stats={},
                zero_width_chars_removed=False,
                confusable_chars_normalized=False
            )
        
        app_logger.info(f"Preprocessing input of length {len(user_input)}")
        
        # Check for zero-width characters
        zero_width_removed = any(zwc in user_input for zwc in self.zero_width_chars)
        
        # Check for confusable characters
        confusable_normalized = any(conf in user_input for conf in self.confusable_map.keys())
        
        # Normalize text and decode obfuscation
        normalized_text, decoded_content = self.decode_obfuscation(user_input)
        
        # Extract URLs
        extracted_urls = self.extract_urls(user_input)
        
        # Extract hidden content
        hidden_content = self.extract_hidden_content(user_input)
        decoded_content.extend(hidden_content)
        
        # Detect encodings used
        detected_encodings = []
        if self.detect_base64_content(user_input):
            detected_encodings.append("base64")
        if self.detect_url_encoding(user_input):
            detected_encodings.append("url_encoding")
        
        # Detect language
        language = self.detect_language(normalized_text)
        
        # Get length statistics
        length_stats = self.get_length_stats(user_input)
        
        result = ProcessedInput(
            original_text=user_input,
            normalized_text=normalized_text,
            decoded_content=decoded_content,
            extracted_urls=extracted_urls,
            detected_encodings=detected_encodings,
            language=language,
            length_stats=length_stats,
            zero_width_chars_removed=zero_width_removed,
            confusable_chars_normalized=confusable_normalized
        )
        
        app_logger.info(f"Preprocessing complete: language={language}, encodings={detected_encodings}, "
                       f"urls={len(extracted_urls)}, hidden_content={len(hidden_content)}")
        
        return result