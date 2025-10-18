"""
Intelligent Security Feedback System

Provides specific, actionable feedback to users when security violations are detected,
without exposing potentially malicious content to LLMs.
"""

import re
from typing import Dict, List, Tuple


class SecurityFeedbackGenerator:
    """Generates intelligent, specific feedback for security violations."""

    def __init__(self):
        # Safe word mappings for common security terms that might be legitimate
        self.safe_alternatives = {
            "breach": [
                "threshold violation",
                "limit exceeded",
                "threshold crossed",
                "alert condition",
            ],
            "attack": ["approach", "strategy", "method", "technique"],
            "exploit": ["utilize", "leverage", "use", "take advantage of"],
            "hack": ["workaround", "solution", "fix", "modification"],
            "vulnerability": ["weakness", "gap", "issue", "concern"],
            "penetration": ["integration", "implementation", "deployment"],
            "security test": [
                "system validation",
                "compliance check",
                "system verification",
            ],
            "security audit": [
                "compliance review",
                "system assessment",
                "quality review",
            ],
            "scan": ["check", "review", "analyze", "examine"],
        }

        # Context-aware explanations for why certain terms trigger security
        self.term_explanations = {
            "breach": "The word 'breach' is often associated with security incidents. For monitoring and alerting, consider using 'threshold violation', 'limit exceeded', or 'alert condition'.",
            "attack": "The word 'attack' has security implications. For business processes, try 'approach', 'strategy', or 'method'.",
            "exploit": "The word 'exploit' can indicate malicious intent. For legitimate use, try 'utilize', 'leverage', or 'use'.",
            "hack": "The word 'hack' suggests unauthorized access. For legitimate modifications, use 'workaround', 'solution', or 'fix'.",
            "vulnerability": "The word 'vulnerability' relates to security weaknesses. For business contexts, try 'weakness', 'gap', or 'concern'.",
            "penetration": "The term 'penetration' often relates to security testing. For business integration, use 'integration', 'implementation', or 'deployment'.",
            "security test": "Security testing terminology is restricted. For system validation, use 'compliance check' or 'system verification'.",
            "security audit": "Security audit terminology is restricted. For reviews, use 'compliance review' or 'quality assessment'.",
            "scan": "The word 'scan' can indicate reconnaissance activities. For legitimate analysis, use 'check', 'review', or 'examine'.",
        }

    def generate_feedback(self, violations: Dict[str, List[str]]) -> str:
        """Generate specific, actionable feedback for security violations."""

        if "malicious_intent" in violations:
            return self._generate_malicious_intent_feedback(
                violations["malicious_intent"]
            )
        elif "out_of_scope" in violations:
            return self._generate_out_of_scope_feedback(violations["out_of_scope"])
        elif "ssrf" in violations:
            return self._generate_ssrf_feedback()
        elif "formula_injection" in violations:
            return self._generate_formula_injection_feedback()
        else:
            return "Your request contains content that appears to be security-related rather than business automation. Please rephrase using business-focused language."

    def _generate_malicious_intent_feedback(self, detected_terms: List[str]) -> str:
        """Generate specific feedback for malicious intent violations."""

        feedback_parts = [
            "🔒 **Security Notice**: Your request contains terminology that's associated with security testing rather than business automation.",
            "",
            "**Detected terms that need rewording:**",
        ]

        # Group similar terms and provide specific suggestions
        term_suggestions = {}
        for term in detected_terms:
            term_lower = term.lower().strip()

            # Find the best match for suggestions
            best_match = None
            for safe_term in self.safe_alternatives:
                if safe_term in term_lower or term_lower in safe_term:
                    best_match = safe_term
                    break

            if best_match:
                if best_match not in term_suggestions:
                    term_suggestions[best_match] = {
                        "found_terms": [],
                        "alternatives": self.safe_alternatives[best_match],
                        "explanation": self.term_explanations.get(
                            best_match, "This term has security implications."
                        ),
                    }
                term_suggestions[best_match]["found_terms"].append(f"'{term}'")

        # Generate specific suggestions
        for safe_term, info in term_suggestions.items():
            feedback_parts.extend(
                [
                    "",
                    f"• **{', '.join(info['found_terms'])}**",
                    f"  - {info['explanation']}",
                    f"  - **Suggested alternatives**: {', '.join(info['alternatives'][:3])}",
                ]
            )

        # Add general guidance
        feedback_parts.extend(
            [
                "",
                "**💡 Tips for business automation requests:**",
                "• Focus on the business process you want to automate",
                "• Describe the desired outcome rather than technical methods",
                "• Use business-friendly terminology (monitoring, alerting, workflow)",
                "• Emphasize legitimate operational needs",
                "",
                "**Example transformation:**",
                "❌ 'Test for security breaches in the API'",
                "✅ 'Monitor API health and alert on threshold violations'",
            ]
        )

        return "\n".join(feedback_parts)

    def _generate_out_of_scope_feedback(self, detected_terms: List[str]) -> str:
        """Generate feedback for out-of-scope requests."""

        feedback_parts = [
            "🔒 **Out of Scope**: This system is designed for business process automation, not code generation or security testing.",
            "",
        ]

        # Show the specific problematic text
        if detected_terms:
            feedback_parts.extend(["**Problematic text detected:**"])

            for term in detected_terms[:5]:  # Limit to first 5 matches
                # Clean up the term for display
                clean_term = term.strip()
                if clean_term:
                    feedback_parts.append(f'• "{clean_term}"')

            if len(detected_terms) > 5:
                feedback_parts.append(f"• ... and {len(detected_terms) - 5} more")

            feedback_parts.append("")

        feedback_parts.extend(
            [
                "**To get help with your request:**",
                "• Rephrase your requirement to focus on business automation needs",
                "• Describe operational processes you want to streamline",
                "• Emphasize monitoring, alerting, or workflow automation",
                "• Avoid requesting executable code or security testing",
                "",
                "**Examples of valid requests:**",
                "✅ 'Automate user onboarding workflow'",
                "✅ 'Monitor system performance and create alerts'",
                "✅ 'Streamline approval processes'",
                "✅ 'Generate automated reports'",
                "",
                "**Examples of invalid requests:**",
                "❌ 'Write Python code for me'",
                "❌ 'Generate a script I can run'",
                "❌ 'Test security vulnerabilities'",
            ]
        )

        return "\n".join(feedback_parts)

    def _generate_ssrf_feedback(self) -> str:
        """Generate feedback for SSRF attempts."""

        return """🔒 **Network Security**: Your request contains references to internal network addresses or cloud metadata services.

**For legitimate automation needs:**
• Use public APIs and documented endpoints
• Avoid internal IP addresses (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
• Don't reference cloud metadata services
• Focus on business-accessible systems and services"""

    def _generate_formula_injection_feedback(self) -> str:
        """Generate feedback for formula injection attempts."""

        return """🔒 **Content Security**: Your request contains spreadsheet formulas or executable content.

**For data processing automation:**
• Describe the business logic you want to implement
• Focus on data transformation needs
• Avoid executable formulas or scripts
• Emphasize legitimate data processing workflows"""

    def extract_problematic_phrases(
        self, text: str, violations: Dict[str, List[str]]
    ) -> List[Tuple[str, str]]:
        """Extract problematic phrases with context for user guidance."""

        problematic_phrases = []

        if "malicious_intent" in violations:
            for term in violations["malicious_intent"]:
                # Find the term in context (surrounding words)
                pattern = re.compile(rf"\b\w*{re.escape(term)}\w*\b", re.IGNORECASE)
                matches = pattern.finditer(text)

                for match in matches:
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end].strip()

                    # Suggest alternatives
                    term_lower = term.lower()
                    alternatives = []
                    for safe_term, alts in self.safe_alternatives.items():
                        if safe_term in term_lower:
                            alternatives = alts[:2]  # Top 2 alternatives
                            break

                    suggestion = (
                        f"Try: {', '.join(alternatives)}"
                        if alternatives
                        else "Use business-friendly terminology"
                    )
                    problematic_phrases.append((f"...{context}...", suggestion))

        return problematic_phrases
