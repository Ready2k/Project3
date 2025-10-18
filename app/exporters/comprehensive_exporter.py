"""Comprehensive export functionality that includes all page data."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from app.exporters.base import BaseExporter
from app.state.store import SessionState
from app.services.architecture_explainer import ArchitectureExplainer
from app.utils.logger import app_logger


class ComprehensiveExporter(BaseExporter):
    """Exports complete session results including all analysis and explanations."""

    def __init__(
        self, export_path: Path, base_url: Optional[str] = None, llm_provider=None
    ):
        super().__init__(export_path, base_url)
        self.llm_provider = llm_provider

    def get_file_extension(self) -> str:
        """Get file extension for comprehensive exports."""
        return "md"

    async def export_session_async(self, session: SessionState) -> str:
        """Export comprehensive session report with all analysis (async version).

        Args:
            session: Session state to export

        Returns:
            Path to the exported file

        Raises:
            ValueError: If session data is invalid for export
        """
        # Validate session data
        if not session.session_id:
            raise ValueError("Session ID is required for export")

        # Generate comprehensive content
        content = await self._generate_comprehensive_report(session)

        # Validate content is not empty
        if not content.strip():
            raise ValueError("Generated comprehensive report content is empty")

        # Generate filename with "comprehensive" prefix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_report_{session.session_id}_{timestamp}.md"
        file_path = self.export_path / filename

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)

    def export_session(self, session: SessionState) -> str:
        """Export comprehensive session report with all analysis (sync wrapper).

        Args:
            session: Session state to export

        Returns:
            Path to the exported file

        Raises:
            ValueError: If session data is invalid for export
        """
        # For now, generate a synchronous version without LLM analysis
        # This ensures compatibility with the existing export interface
        content = self._generate_sync_comprehensive_report(session)

        # Validate content is not empty
        if not content.strip():
            raise ValueError("Generated comprehensive report content is empty")

        # Generate filename with "comprehensive" prefix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_report_{session.session_id}_{timestamp}.md"
        file_path = self.export_path / filename

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)

    async def _generate_comprehensive_report(self, session: SessionState) -> str:
        """Generate comprehensive report with all analysis and explanations."""
        lines = []

        # Header with executive summary
        lines.append("# 📊 Comprehensive Automation Assessment Report")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")

        # Overall assessment
        overall_feasibility = self._get_overall_feasibility(session)
        feasibility_emoji = self._get_feasibility_emoji(overall_feasibility)
        confidence = self._get_overall_confidence(session)

        lines.append(
            f"**Assessment Result:** {feasibility_emoji} **{overall_feasibility}**"
        )
        lines.append(f"**Overall Confidence:** {confidence:.1%}")
        lines.append("")

        # Quick stats
        lines.append("### Quick Statistics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Session ID | `{session.session_id}` |")
        lines.append(f"| Generated | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
        lines.append(f"| Processing Phase | {session.phase.value} |")
        lines.append(f"| Progress | {session.progress}% |")
        lines.append(f"| Patterns Analyzed | {len(session.matches)} |")
        lines.append(f"| Recommendations | {len(session.recommendations)} |")
        lines.append(f"| Q&A Rounds | {len(session.qa_history)} |")
        lines.append("")

        # Table of Contents
        lines.append("## 📋 Table of Contents")
        lines.append("")
        lines.append("1. [Original Requirements](#1-original-requirements)")
        lines.append("2. [Feasibility Assessment](#2-feasibility-assessment)")
        lines.append("3. [Recommended Solutions](#3-recommended-solutions)")
        lines.append("4. [Technical Analysis](#4-technical-analysis)")
        lines.append("5. [Pattern Matches](#5-pattern-matches)")
        lines.append("6. [Questions & Answers](#6-questions--answers)")
        lines.append("7. [Implementation Guidance](#7-implementation-guidance)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. Original Requirements
        lines.append("## 1. 📝 Original Requirements")
        lines.append("")
        await self._add_requirements_section(lines, session)

        # 2. Feasibility Assessment
        lines.append("## 2. ⚖️ Feasibility Assessment")
        lines.append("")
        await self._add_feasibility_section(lines, session)

        # 3. Recommended Solutions
        lines.append("## 3. 🎯 Recommended Solutions")
        lines.append("")
        await self._add_recommendations_section(lines, session)

        # 4. Technical Analysis
        lines.append("## 4. 🔧 Technical Analysis")
        lines.append("")
        await self._add_technical_analysis_section(lines, session)

        # 5. Pattern Matches
        lines.append("## 5. 🔍 Pattern Matches")
        lines.append("")
        await self._add_pattern_matches_section(lines, session)

        # 6. Questions & Answers
        lines.append("## 6. ❓ Questions & Answers")
        lines.append("")
        await self._add_qa_section(lines, session)

        # 7. Implementation Guidance
        lines.append("## 7. 🚀 Implementation Guidance")
        lines.append("")
        await self._add_implementation_guidance(lines, session)

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("## 📄 Report Information")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append("| Report Type | Comprehensive Assessment |")
        lines.append("| Generated By | Automated AI Assessment (AAA) System |")
        lines.append("| Version | 2.1.0 |")
        lines.append(
            f"| Export Time | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} |"
        )
        lines.append("")
        lines.append(
            "*This report contains AI-generated analysis and recommendations. Please review and validate all suggestions before implementation.*"
        )
        lines.append("")

        return "\n".join(lines)

    def _generate_sync_comprehensive_report(self, session: SessionState) -> str:
        """Generate comprehensive report synchronously (without LLM analysis)."""
        lines = []

        # Validate session data consistency first
        validation_issues = self._validate_session_consistency(session)

        # Header with executive summary
        lines.append("# 📊 Comprehensive Automation Assessment Report")
        lines.append("")

        # Show validation warnings if any
        if validation_issues:
            lines.append("## ⚠️ Data Validation Warnings")
            lines.append("")
            for issue in validation_issues:
                lines.append(f"- **{issue['severity']}**: {issue['message']}")
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("## Executive Summary")
        lines.append("")

        # Overall assessment
        overall_feasibility = self._get_overall_feasibility(session)
        feasibility_emoji = self._get_feasibility_emoji(overall_feasibility)
        confidence = self._get_overall_confidence(session)

        lines.append(
            f"**Assessment Result:** {feasibility_emoji} **{overall_feasibility}**"
        )
        lines.append(f"**Overall Confidence:** {confidence:.1%}")
        lines.append("")

        # Quick stats with data quality indicators
        lines.append("### Quick Statistics")
        lines.append("")
        lines.append("| Metric | Value | Status |")
        lines.append("|--------|-------|--------|")
        lines.append(f"| Session ID | `{session.session_id}` | ✅ |")

        # Use UTC for consistency
        utc_time = datetime.utcnow()
        lines.append(
            f"| Generated | {utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')} | ✅ |"
        )
        lines.append(
            f"| Processing Phase | {session.phase.value} | {'✅' if session.phase.value == 'DONE' else '⚠️'} |"
        )
        lines.append(
            f"| Progress | {session.progress}% | {'✅' if session.progress == 100 else '⚠️'} |"
        )

        # Pattern analysis status
        pattern_status = "✅" if len(session.matches) > 0 else "❌"
        lines.append(
            f"| Patterns Analyzed | {len(session.matches)} | {pattern_status} |"
        )

        # Recommendation status
        rec_status = "✅" if len(session.recommendations) > 0 else "❌"
        lines.append(
            f"| Recommendations | {len(session.recommendations)} | {rec_status} |"
        )

        # Q&A status
        qa_status = "✅" if len(session.qa_history) > 0 else "⚠️"
        lines.append(f"| Q&A Rounds | {len(session.qa_history)} | {qa_status} |")
        lines.append("")

        # Table of Contents
        lines.append("## 📋 Table of Contents")
        lines.append("")
        lines.append("1. [Original Requirements](#1-original-requirements)")
        lines.append("2. [Feasibility Assessment](#2-feasibility-assessment)")
        lines.append("3. [Recommended Solutions](#3-recommended-solutions)")
        lines.append("4. [Technical Analysis](#4-technical-analysis)")
        lines.append("5. [Pattern Matches](#5-pattern-matches)")
        lines.append("6. [Questions & Answers](#6-questions--answers)")
        lines.append("7. [Implementation Guidance](#7-implementation-guidance)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. Original Requirements
        lines.append("## 1. 📝 Original Requirements")
        lines.append("")
        self._add_requirements_section_sync(lines, session)

        # 2. Feasibility Assessment
        lines.append("## 2. ⚖️ Feasibility Assessment")
        lines.append("")
        self._add_feasibility_section_sync(lines, session)

        # 3. Recommended Solutions
        lines.append("## 3. 🎯 Recommended Solutions")
        lines.append("")
        self._add_recommendations_section_sync(lines, session)

        # 4. Technical Analysis
        lines.append("## 4. 🔧 Technical Analysis")
        lines.append("")
        self._add_technical_analysis_section_sync(lines, session)

        # 5. Pattern Matches
        lines.append("## 5. 🔍 Pattern Matches")
        lines.append("")
        self._add_pattern_matches_section_sync(lines, session)

        # 6. Questions & Answers
        lines.append("## 6. ❓ Questions & Answers")
        lines.append("")
        self._add_qa_section_sync(lines, session)

        # 7. Implementation Guidance
        lines.append("## 7. 🚀 Implementation Guidance")
        lines.append("")
        self._add_implementation_guidance_sync(lines, session)

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("## 📄 Report Information")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append("| Report Type | Comprehensive Assessment |")
        lines.append("| Generated By | Automated AI Assessment (AAA) System |")
        lines.append("| Version | 2.1.0 |")
        lines.append(
            f"| Export Time (UTC) | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} |"
        )
        lines.append(
            f"| Session Created | {session.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if session.created_at else 'Unknown'} |"
        )
        lines.append(
            f"| Last Updated | {session.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC') if session.updated_at else 'Unknown'} |"
        )
        lines.append("")

        # Add data quality disclaimer if there were validation issues
        validation_issues = self._validate_session_consistency(session)
        if validation_issues:
            lines.append("**⚠️ Data Quality Notice:**")
            lines.append(
                "This report contains validation warnings. Please review the data validation section at the top of this report for details."
            )
            lines.append("")

        lines.append(
            "*This report contains AI-generated analysis and recommendations. Please review and validate all suggestions before implementation.*"
        )
        lines.append("")

        return "\n".join(lines)

    async def _add_requirements_section(self, lines: List[str], session: SessionState):
        """Add detailed requirements section."""
        description = session.requirements.get("description", "No description provided")
        lines.append("### Original Description")
        lines.append("")
        lines.append(f"> {description}")
        lines.append("")

        # Requirements breakdown
        lines.append("### Requirements Breakdown")
        lines.append("")
        lines.append("| Attribute | Value |")
        lines.append("|-----------|-------|")

        req_fields = [
            ("Domain", "domain"),
            ("Frequency", "frequency"),
            ("Criticality", "criticality"),
            ("Pattern Types", "pattern_types"),
            ("Business Impact", "business_impact"),
            ("Technical Complexity", "technical_complexity"),
            ("Data Sensitivity", "data_sensitivity"),
            ("Compliance Requirements", "compliance_requirements"),
            ("Integration Requirements", "integration_requirements"),
            ("Budget Constraints", "budget_constraints"),
        ]

        for label, key in req_fields:
            value = session.requirements.get(key)
            if value:
                if isinstance(value, list):
                    value = ", ".join(value)
                lines.append(f"| {label} | {value} |")

        lines.append("")

        # Constraints if any
        constraints = session.requirements.get("constraints", {})
        if constraints:
            lines.append("### Constraints & Restrictions")
            lines.append("")

            if constraints.get("restricted_technologies"):
                lines.append("**Restricted Technologies:**")
                for tech in constraints["restricted_technologies"]:
                    lines.append(f"- ❌ {tech}")
                lines.append("")

            if constraints.get("required_integrations"):
                lines.append("**Required Integrations:**")
                for integration in constraints["required_integrations"]:
                    lines.append(f"- 🔗 {integration}")
                lines.append("")

            if constraints.get("compliance_requirements"):
                lines.append("**Compliance Requirements:**")
                for compliance in constraints["compliance_requirements"]:
                    lines.append(f"- 📋 {compliance}")
                lines.append("")

    async def _add_feasibility_section(self, lines: List[str], session: SessionState):
        """Add detailed feasibility assessment."""
        if not session.recommendations:
            lines.append("*No feasibility assessment available.*")
            lines.append("")
            return

        # Overall assessment
        overall_feasibility = self._get_overall_feasibility(session)
        overall_confidence = self._get_overall_confidence(session)

        lines.append("### Overall Assessment")
        lines.append("")
        lines.append(
            f"**Result:** {self._get_feasibility_emoji(overall_feasibility)} **{overall_feasibility}**"
        )
        lines.append(
            f"**Confidence Level:** {overall_confidence:.1%} {self._generate_confidence_bar(overall_confidence)}"
        )
        lines.append("")

        # Feasibility breakdown
        lines.append("### Feasibility Breakdown")
        lines.append("")

        feasibility_counts = {}
        for rec in session.recommendations:
            feasibility = rec.feasibility
            if feasibility not in feasibility_counts:
                feasibility_counts[feasibility] = 0
            feasibility_counts[feasibility] += 1

        lines.append("| Feasibility Level | Count | Percentage |")
        lines.append("|------------------|-------|------------|")

        total_recs = len(session.recommendations)
        for feasibility, count in feasibility_counts.items():
            percentage = (count / total_recs) * 100
            emoji = self._get_feasibility_emoji(feasibility)
            lines.append(f"| {emoji} {feasibility} | {count} | {percentage:.1f}% |")

        lines.append("")

        # Key factors
        lines.append("### Key Assessment Factors")
        lines.append("")

        # Analyze common themes in reasoning
        all_reasoning = [rec.reasoning for rec in session.recommendations]
        key_factors = self._extract_key_factors(all_reasoning)

        for factor in key_factors:
            lines.append(f"- {factor}")

        lines.append("")

    async def _add_recommendations_section(
        self, lines: List[str], session: SessionState
    ):
        """Add detailed recommendations with tech stacks and explanations."""
        if not session.recommendations:
            lines.append("*No recommendations available.*")
            lines.append("")
            return

        for i, rec in enumerate(session.recommendations, 1):
            lines.append(f"### Recommendation {i}: Pattern {rec.pattern_id}")
            lines.append("")

            # Basic info
            confidence_bar = self._generate_confidence_bar(rec.confidence)
            lines.append(
                f"**Feasibility:** {self._get_feasibility_emoji(rec.feasibility)} {rec.feasibility}"
            )
            lines.append(f"**Confidence:** {rec.confidence:.1%} {confidence_bar}")
            lines.append("")

            # Tech stack with enhanced details
            if rec.tech_stack:
                lines.append("#### 🛠️ Recommended Technology Stack")
                lines.append("")

                # Use stored enhanced data if available, otherwise generate new
                enhanced_tech_stack = (
                    getattr(rec, "enhanced_tech_stack", None) or rec.tech_stack
                )
                architecture_explanation = getattr(
                    rec, "architecture_explanation", None
                )

                # If no stored explanation, try to generate one
                if not architecture_explanation:
                    try:
                        enhanced_tech_stack, architecture_explanation = (
                            await self._generate_comprehensive_tech_stack_analysis(
                                rec.tech_stack, session
                            )
                        )
                        app_logger.info(
                            f"Generated new architecture explanation ({len(architecture_explanation)} chars)"
                        )
                    except Exception as e:
                        app_logger.error(f"Failed to generate tech stack analysis: {e}")
                        architecture_explanation = (
                            self._generate_detailed_fallback_explanation(
                                rec.tech_stack, session
                            )
                        )
                else:
                    app_logger.info(
                        f"Using stored architecture explanation ({len(architecture_explanation)} chars)"
                    )

                # Categorized tech stack with detailed descriptions
                categorized_stack = self._categorize_tech_stack_with_descriptions(
                    enhanced_tech_stack
                )

                for category, technologies in categorized_stack.items():
                    if technologies:
                        lines.append(f"**{category}:**")
                        for tech_info in technologies:
                            if isinstance(tech_info, dict):
                                tech_name = tech_info.get(
                                    "name", tech_info.get("technology", str(tech_info))
                                )
                                tech_desc = tech_info.get("description", "")
                                if tech_desc:
                                    lines.append(f"- **{tech_name}**: {tech_desc}")
                                else:
                                    lines.append(f"- `{tech_name}`")
                            else:
                                lines.append(f"- `{tech_info}`")
                        lines.append("")

                # Architecture explanation - use the stored or generated content
                lines.append("#### 🏗️ How It All Works Together")
                lines.append("")

                if architecture_explanation and architecture_explanation.strip():
                    # Clean up the explanation and format it properly
                    explanation_text = architecture_explanation.strip()

                    # Split into paragraphs and add proper spacing
                    paragraphs = [
                        p.strip() for p in explanation_text.split("\n\n") if p.strip()
                    ]
                    if not paragraphs:
                        # If no double newlines, split on single newlines but group sentences
                        sentences = [
                            s.strip() for s in explanation_text.split("\n") if s.strip()
                        ]
                        paragraphs = [" ".join(sentences)]

                    for paragraph in paragraphs:
                        lines.append(paragraph)
                        lines.append("")
                else:
                    # Final fallback
                    fallback_explanation = self._generate_detailed_fallback_explanation(
                        enhanced_tech_stack, session
                    )
                    lines.append(fallback_explanation)
                    lines.append("")

            # Detailed reasoning
            lines.append("#### 💭 Reasoning & Analysis")
            lines.append("")
            lines.append(rec.reasoning)
            lines.append("")

            # Implementation considerations
            lines.append("#### ⚠️ Implementation Considerations")
            lines.append("")
            considerations = self._generate_implementation_considerations(rec)
            for consideration in considerations:
                lines.append(f"- {consideration}")
            lines.append("")

            if i < len(session.recommendations):
                lines.append("---")
                lines.append("")

    async def _add_technical_analysis_section(
        self, lines: List[str], session: SessionState
    ):
        """Add comprehensive technical analysis."""
        if not session.recommendations:
            lines.append("*No technical analysis available.*")
            lines.append("")
            return

        # Aggregate all tech stacks
        all_tech = set()
        for rec in session.recommendations:
            all_tech.update(rec.tech_stack)

        if not all_tech:
            lines.append("*No technology stack information available.*")
            lines.append("")
            return

        # Technology overview
        lines.append("### Technology Overview")
        lines.append("")

        categorized_tech = self._categorize_tech_stack(list(all_tech))

        for category, technologies in categorized_tech.items():
            if technologies:
                lines.append(f"#### {category}")
                lines.append("")
                for tech in sorted(technologies):
                    description = self._get_technology_description(tech)
                    lines.append(f"- **{tech}**: {description}")
                lines.append("")

        # Architecture patterns
        lines.append("### Architecture Patterns")
        lines.append("")
        patterns = self._identify_architecture_patterns(session)
        for pattern in patterns:
            lines.append(f"- **{pattern['name']}**: {pattern['description']}")
        lines.append("")

        # Scalability considerations
        lines.append("### Scalability & Performance")
        lines.append("")
        scalability_notes = self._generate_scalability_analysis(list(all_tech))
        for note in scalability_notes:
            lines.append(f"- {note}")
        lines.append("")

        # Security considerations
        lines.append("### Security Considerations")
        lines.append("")
        security_notes = self._generate_security_analysis(list(all_tech))
        for note in security_notes:
            lines.append(f"- {note}")
        lines.append("")

    async def _add_pattern_matches_section(
        self, lines: List[str], session: SessionState
    ):
        """Add detailed pattern matching analysis."""
        if not session.matches:
            lines.append("*No pattern matches available.*")
            lines.append("")
            return

        lines.append("### Pattern Matching Results")
        lines.append("")
        lines.append("| Pattern ID | Match Score | Confidence | Analysis |")
        lines.append("|------------|-------------|------------|----------|")

        for match in sorted(session.matches, key=lambda x: x.score, reverse=True):
            score_bar = self._generate_confidence_bar(match.score)
            confidence_bar = self._generate_confidence_bar(match.confidence)

            # Truncate rationale for table
            short_rationale = (
                match.rationale[:100] + "..."
                if len(match.rationale) > 100
                else match.rationale
            )

            lines.append(
                f"| {match.pattern_id} | {match.score:.1%} {score_bar} | {match.confidence:.1%} {confidence_bar} | {short_rationale} |"
            )

        lines.append("")

        # Detailed analysis for top matches
        top_matches = sorted(session.matches, key=lambda x: x.score, reverse=True)[:3]

        lines.append("### Top Pattern Matches - Detailed Analysis")
        lines.append("")

        for i, match in enumerate(top_matches, 1):
            lines.append(f"#### {i}. Pattern {match.pattern_id}")
            lines.append("")
            lines.append(
                f"**Match Score:** {match.score:.1%} {self._generate_confidence_bar(match.score)}"
            )
            lines.append(
                f"**Confidence:** {match.confidence:.1%} {self._generate_confidence_bar(match.confidence)}"
            )
            lines.append("")
            lines.append("**Analysis:**")
            lines.append(f"> {match.rationale}")
            lines.append("")

    async def _add_qa_section(self, lines: List[str], session: SessionState):
        """Add Q&A history with analysis."""
        if not session.qa_history:
            lines.append("*No Q&A history available.*")
            lines.append("")
            return

        lines.append("### Question & Answer History")
        lines.append("")

        for i, qa in enumerate(session.qa_history, 1):
            lines.append(
                f"#### Round {i} - {qa.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            lines.append("")

            if qa.questions:
                lines.append("**Questions Asked:**")
                for j, question in enumerate(qa.questions, 1):
                    lines.append(f"{j}. {question}")
                lines.append("")

            if qa.answers:
                lines.append("**Responses Provided:**")
                lines.append("")
                lines.append("| Question | Response |")
                lines.append("|----------|----------|")

                for field, answer in qa.answers.items():
                    formatted_field = field.replace("_", " ").title()
                    # Truncate long answers for table
                    short_answer = answer[:100] + "..." if len(answer) > 100 else answer
                    lines.append(f"| {formatted_field} | {short_answer} |")
                lines.append("")

            if i < len(session.qa_history):
                lines.append("---")
                lines.append("")

    async def _add_implementation_guidance(
        self, lines: List[str], session: SessionState
    ):
        """Add implementation guidance and next steps."""
        lines.append("### Next Steps & Implementation Roadmap")
        lines.append("")

        if not session.recommendations:
            lines.append(
                "*Complete the assessment to receive implementation guidance.*"
            )
            lines.append("")
            return

        # Implementation phases
        lines.append("#### Phase 1: Planning & Design")
        lines.append("")
        lines.append("- [ ] Review and validate all recommendations")
        lines.append("- [ ] Conduct detailed technical architecture review")
        lines.append("- [ ] Define success criteria and KPIs")
        lines.append("- [ ] Create detailed project timeline")
        lines.append("- [ ] Identify required resources and skills")
        lines.append("")

        lines.append("#### Phase 2: Proof of Concept")
        lines.append("")
        lines.append("- [ ] Implement minimal viable automation")
        lines.append("- [ ] Test with limited dataset/scope")
        lines.append("- [ ] Validate technical assumptions")
        lines.append("- [ ] Measure performance and accuracy")
        lines.append("- [ ] Gather user feedback")
        lines.append("")

        lines.append("#### Phase 3: Full Implementation")
        lines.append("")
        lines.append("- [ ] Scale to production environment")
        lines.append("- [ ] Implement monitoring and alerting")
        lines.append("- [ ] Create user training materials")
        lines.append("- [ ] Establish maintenance procedures")
        lines.append("- [ ] Plan for continuous improvement")
        lines.append("")

        # Risk mitigation
        lines.append("### Risk Mitigation Strategies")
        lines.append("")
        risks = self._identify_implementation_risks(session)
        for risk in risks:
            lines.append(f"- **{risk['category']}**: {risk['description']}")
            lines.append(f"  - *Mitigation*: {risk['mitigation']}")
        lines.append("")

        # Success metrics
        lines.append("### Success Metrics")
        lines.append("")
        metrics = self._generate_success_metrics(session)
        for metric in metrics:
            lines.append(f"- **{metric['name']}**: {metric['description']}")
            lines.append(f"  - *Target*: {metric['target']}")
        lines.append("")

    # Helper methods for analysis and categorization

    async def _generate_tech_stack_analysis(
        self, tech_stack: List[str], session: SessionState
    ) -> Tuple[List[str], str]:
        """Generate enhanced tech stack analysis and architecture explanation."""
        if self.llm_provider:
            try:
                explainer = ArchitectureExplainer(self.llm_provider)
                requirements = session.requirements
                session_id = session.session_id

                enhanced_tech_stack, explanation = await explainer.explain_architecture(
                    tech_stack, requirements, session_id
                )

                return enhanced_tech_stack, explanation
            except Exception as e:
                app_logger.error(f"Failed to generate LLM tech stack analysis: {e}")

        # Fallback to basic analysis
        explanation = self._generate_fallback_architecture_explanation(tech_stack)
        return tech_stack, explanation

    async def _generate_comprehensive_tech_stack_analysis(
        self, tech_stack: List[str], session: SessionState
    ) -> Tuple[List[str], str]:
        """Generate comprehensive tech stack analysis with detailed explanations (same as UI)."""
        if self.llm_provider:
            try:
                explainer = ArchitectureExplainer(self.llm_provider)
                requirements = session.requirements
                session_id = session.session_id

                app_logger.info(
                    f"Generating comprehensive tech stack analysis for {len(tech_stack)} technologies"
                )

                # Use the same method as the UI to ensure consistency
                enhanced_tech_stack, explanation = await explainer.explain_architecture(
                    tech_stack, requirements, session_id
                )

                app_logger.info(
                    f"Generated comprehensive explanation ({len(explanation)} chars)"
                )
                return enhanced_tech_stack, explanation

            except Exception as e:
                app_logger.error(
                    f"Failed to generate comprehensive LLM tech stack analysis: {e}"
                )

        # Enhanced fallback with more detail than basic version
        app_logger.info("Using enhanced fallback for tech stack analysis")
        explanation = self._generate_detailed_fallback_explanation(tech_stack, session)
        return tech_stack, explanation

    def _categorize_tech_stack(self, tech_stack: List[str]) -> Dict[str, List[str]]:
        """Categorize technologies by type."""
        categories = {
            "Programming Languages": [],
            "Web Frameworks & APIs": [],
            "Databases & Storage": [],
            "Cloud & Infrastructure": [],
            "Communication & Integration": [],
            "Testing & Development Tools": [],
            "Data Processing & Analytics": [],
            "Monitoring & Operations": [],
            "Message Queues & Processing": [],
        }

        # Technology categorization mapping
        category_mapping = {
            # Programming Languages
            "Python": "Programming Languages",
            "JavaScript": "Programming Languages",
            "TypeScript": "Programming Languages",
            "Java": "Programming Languages",
            "C#": "Programming Languages",
            "Go": "Programming Languages",
            "Rust": "Programming Languages",
            # Web Frameworks & APIs
            "FastAPI": "Web Frameworks & APIs",
            "Django": "Web Frameworks & APIs",
            "Flask": "Web Frameworks & APIs",
            "Express.js": "Web Frameworks & APIs",
            "React": "Web Frameworks & APIs",
            "Vue.js": "Web Frameworks & APIs",
            "Angular": "Web Frameworks & APIs",
            "REST API": "Web Frameworks & APIs",
            "GraphQL": "Web Frameworks & APIs",
            # Databases & Storage
            "PostgreSQL": "Databases & Storage",
            "MySQL": "Databases & Storage",
            "MongoDB": "Databases & Storage",
            "Redis": "Databases & Storage",
            "Elasticsearch": "Databases & Storage",
            "DynamoDB": "Databases & Storage",
            "Cassandra": "Databases & Storage",
            "SQLite": "Databases & Storage",
            # Cloud & Infrastructure
            "AWS": "Cloud & Infrastructure",
            "Azure": "Cloud & Infrastructure",
            "GCP": "Cloud & Infrastructure",
            "Docker": "Cloud & Infrastructure",
            "Kubernetes": "Cloud & Infrastructure",
            "Terraform": "Cloud & Infrastructure",
            "Lambda": "Cloud & Infrastructure",
            "EC2": "Cloud & Infrastructure",
            # Communication & Integration
            "RabbitMQ": "Communication & Integration",
            "Apache Kafka": "Communication & Integration",
            "WebSocket": "Communication & Integration",
            "gRPC": "Communication & Integration",
            "MQTT": "Communication & Integration",
            # Testing & Development Tools
            "pytest": "Testing & Development Tools",
            "Jest": "Testing & Development Tools",
            "Selenium": "Testing & Development Tools",
            "Git": "Testing & Development Tools",
            "Jenkins": "Testing & Development Tools",
            "GitHub Actions": "Testing & Development Tools",
            # Data Processing & Analytics
            "Apache Spark": "Data Processing & Analytics",
            "Pandas": "Data Processing & Analytics",
            "NumPy": "Data Processing & Analytics",
            "Apache Airflow": "Data Processing & Analytics",
            "Jupyter": "Data Processing & Analytics",
            # Monitoring & Operations
            "Prometheus": "Monitoring & Operations",
            "Grafana": "Monitoring & Operations",
            "ELK Stack": "Monitoring & Operations",
            "New Relic": "Monitoring & Operations",
            "DataDog": "Monitoring & Operations",
        }

        for tech in tech_stack:
            category = category_mapping.get(tech, "Other Technologies")
            if category not in categories:
                categories["Other Technologies"] = []
            categories[category].append(tech)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def _categorize_tech_stack_with_descriptions(
        self, tech_stack: List[str]
    ) -> Dict[str, List[Dict[str, str]]]:
        """Categorize technologies by type with detailed descriptions."""
        categories = {
            "Programming Languages": [],
            "Web Frameworks & APIs": [],
            "Databases & Storage": [],
            "Cloud & Infrastructure": [],
            "Communication & Integration": [],
            "Testing & Development Tools": [],
            "Data Processing & Analytics": [],
            "Monitoring & Operations": [],
            "Message Queues & Processing": [],
            "Other Technologies": [],
        }

        # Technology categorization mapping with descriptions
        tech_info = {
            # Programming Languages
            "Python": {
                "category": "Programming Languages",
                "description": "High-level programming language ideal for automation, data processing, and AI applications",
            },
            "JavaScript": {
                "category": "Programming Languages",
                "description": "Versatile programming language for web development and server-side applications",
            },
            "TypeScript": {
                "category": "Programming Languages",
                "description": "Typed superset of JavaScript that compiles to plain JavaScript",
            },
            "Java": {
                "category": "Programming Languages",
                "description": "Enterprise-grade programming language with strong typing and cross-platform compatibility",
            },
            "C#": {
                "category": "Programming Languages",
                "description": "Microsoft's object-oriented programming language for .NET applications",
            },
            "Go": {
                "category": "Programming Languages",
                "description": "Fast, compiled language designed for concurrent programming and microservices",
            },
            "Rust": {
                "category": "Programming Languages",
                "description": "Systems programming language focused on safety, speed, and concurrency",
            },
            # Web Frameworks & APIs
            "FastAPI": {
                "category": "Web Frameworks & APIs",
                "description": "Modern, fast web framework for building APIs with Python based on standard Python type hints",
            },
            "Django": {
                "category": "Web Frameworks & APIs",
                "description": "High-level Python web framework that encourages rapid development and clean design",
            },
            "Flask": {
                "category": "Web Frameworks & APIs",
                "description": "Lightweight WSGI web application framework for Python",
            },
            "Express.js": {
                "category": "Web Frameworks & APIs",
                "description": "Fast, unopinionated, minimalist web framework for Node.js",
            },
            "React": {
                "category": "Web Frameworks & APIs",
                "description": "JavaScript library for building user interfaces with component-based architecture",
            },
            "Vue.js": {
                "category": "Web Frameworks & APIs",
                "description": "Progressive JavaScript framework for building user interfaces",
            },
            "Angular": {
                "category": "Web Frameworks & APIs",
                "description": "Platform and framework for building single-page client applications using HTML and TypeScript",
            },
            "REST API": {
                "category": "Web Frameworks & APIs",
                "description": "Architectural style for designing networked applications using HTTP methods",
            },
            "GraphQL": {
                "category": "Web Frameworks & APIs",
                "description": "Query language and runtime for APIs that provides a complete description of data",
            },
            # Databases & Storage
            "PostgreSQL": {
                "category": "Databases & Storage",
                "description": "Advanced open-source relational database with strong ACID compliance and extensibility",
            },
            "MySQL": {
                "category": "Databases & Storage",
                "description": "Popular open-source relational database management system",
            },
            "MongoDB": {
                "category": "Databases & Storage",
                "description": "Document-oriented NoSQL database designed for scalability and flexibility",
            },
            "Redis": {
                "category": "Databases & Storage",
                "description": "In-memory data structure store used as database, cache, and message broker",
            },
            "Elasticsearch": {
                "category": "Databases & Storage",
                "description": "Distributed search and analytics engine built on Apache Lucene",
            },
            "DynamoDB": {
                "category": "Databases & Storage",
                "description": "Amazon's fully managed NoSQL database service with fast performance",
            },
            "Cassandra": {
                "category": "Databases & Storage",
                "description": "Distributed NoSQL database designed for handling large amounts of data across commodity servers",
            },
            "SQLite": {
                "category": "Databases & Storage",
                "description": "Lightweight, serverless, self-contained SQL database engine",
            },
            # Cloud & Infrastructure
            "AWS": {
                "category": "Cloud & Infrastructure",
                "description": "Amazon Web Services - comprehensive cloud computing platform",
            },
            "AWS Lambda": {
                "category": "Cloud & Infrastructure",
                "description": "Serverless compute service that runs code in response to events",
            },
            "Azure": {
                "category": "Cloud & Infrastructure",
                "description": "Microsoft's cloud computing platform and infrastructure",
            },
            "GCP": {
                "category": "Cloud & Infrastructure",
                "description": "Google Cloud Platform - suite of cloud computing services",
            },
            "Docker": {
                "category": "Cloud & Infrastructure",
                "description": "Platform for developing, shipping, and running applications in containers",
            },
            "Kubernetes": {
                "category": "Cloud & Infrastructure",
                "description": "Container orchestration platform for automating deployment, scaling, and management",
            },
            "Terraform": {
                "category": "Cloud & Infrastructure",
                "description": "Infrastructure as code tool for building, changing, and versioning infrastructure",
            },
            "Lambda": {
                "category": "Cloud & Infrastructure",
                "description": "Serverless compute service for running code without managing servers",
            },
            "EC2": {
                "category": "Cloud & Infrastructure",
                "description": "Amazon Elastic Compute Cloud - scalable virtual servers in the cloud",
            },
            # Communication & Integration
            "RabbitMQ": {
                "category": "Communication & Integration",
                "description": "Message broker software that implements Advanced Message Queuing Protocol",
            },
            "Apache Kafka": {
                "category": "Communication & Integration",
                "description": "Distributed streaming platform for building real-time data pipelines",
            },
            "WebSocket": {
                "category": "Communication & Integration",
                "description": "Protocol for full-duplex communication channels over a single TCP connection",
            },
            "gRPC": {
                "category": "Communication & Integration",
                "description": "High-performance RPC framework that can run in any environment",
            },
            "MQTT": {
                "category": "Communication & Integration",
                "description": "Lightweight messaging protocol for small sensors and mobile devices",
            },
            "Twilio": {
                "category": "Communication & Integration",
                "description": "Cloud communications platform for SMS, voice, and messaging APIs",
            },
            # AI & Machine Learning
            "AWS Comprehend": {
                "category": "Data Processing & Analytics",
                "description": "Natural language processing service that uses machine learning to find insights in text",
            },
            "OpenAI": {
                "category": "Data Processing & Analytics",
                "description": "AI research company providing GPT models and APIs for natural language processing",
            },
            "Anthropic": {
                "category": "Data Processing & Analytics",
                "description": "AI safety company providing Claude models for conversational AI",
            },
            # Testing & Development Tools
            "pytest": {
                "category": "Testing & Development Tools",
                "description": "Testing framework for Python that makes it easy to write simple and scalable tests",
            },
            "Jest": {
                "category": "Testing & Development Tools",
                "description": "JavaScript testing framework with a focus on simplicity",
            },
            "Selenium": {
                "category": "Testing & Development Tools",
                "description": "Web browser automation tool for testing web applications",
            },
            "Git": {
                "category": "Testing & Development Tools",
                "description": "Distributed version control system for tracking changes in source code",
            },
            "Jenkins": {
                "category": "Testing & Development Tools",
                "description": "Open-source automation server for continuous integration and deployment",
            },
            "GitHub Actions": {
                "category": "Testing & Development Tools",
                "description": "CI/CD platform that allows automation of build, test, and deployment workflows",
            },
            # Data Processing & Analytics
            "Apache Spark": {
                "category": "Data Processing & Analytics",
                "description": "Unified analytics engine for large-scale data processing",
            },
            "Pandas": {
                "category": "Data Processing & Analytics",
                "description": "Data manipulation and analysis library for Python",
            },
            "NumPy": {
                "category": "Data Processing & Analytics",
                "description": "Fundamental package for scientific computing with Python",
            },
            "Apache Airflow": {
                "category": "Data Processing & Analytics",
                "description": "Platform to programmatically author, schedule, and monitor workflows",
            },
            "Jupyter": {
                "category": "Data Processing & Analytics",
                "description": "Interactive computing environment for creating and sharing documents with code and visualizations",
            },
            # Monitoring & Operations
            "Prometheus": {
                "category": "Monitoring & Operations",
                "description": "Open-source monitoring and alerting toolkit",
            },
            "Grafana": {
                "category": "Monitoring & Operations",
                "description": "Analytics and interactive visualization web application",
            },
            "ELK Stack": {
                "category": "Monitoring & Operations",
                "description": "Elasticsearch, Logstash, and Kibana for search, logging, and analytics",
            },
            "New Relic": {
                "category": "Monitoring & Operations",
                "description": "Application performance monitoring and observability platform",
            },
            "DataDog": {
                "category": "Monitoring & Operations",
                "description": "Monitoring and analytics platform for cloud applications",
            },
        }

        for tech in tech_stack:
            tech_data = tech_info.get(
                tech,
                {
                    "category": "Other Technologies",
                    "description": "Technology component for system implementation",
                },
            )

            category = tech_data["category"]
            if category not in categories:
                categories[category] = []

            categories[category].append(
                {"name": tech, "description": tech_data["description"]}
            )

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def _get_technology_description(self, tech: str) -> str:
        """Get description for a technology."""
        descriptions = {
            "Python": "High-level programming language ideal for automation and data processing",
            "FastAPI": "Modern, fast web framework for building APIs with automatic documentation",
            "PostgreSQL": "Advanced open-source relational database with excellent performance",
            "Redis": "In-memory data structure store used for caching and session management",
            "Docker": "Containerization platform for consistent deployment across environments",
            "AWS": "Comprehensive cloud computing platform with extensive service offerings",
            "React": "Popular JavaScript library for building interactive user interfaces",
            "MongoDB": "NoSQL document database for flexible, scalable data storage",
            "Kubernetes": "Container orchestration platform for automated deployment and scaling",
            "Elasticsearch": "Distributed search and analytics engine for large-scale data",
        }

        return descriptions.get(tech, "Technology component for system implementation")

    def _generate_fallback_architecture_explanation(self, tech_stack: List[str]) -> str:
        """Generate fallback architecture explanation."""
        if not tech_stack:
            return "No technology stack specified for this recommendation."

        return (
            f"This solution utilizes a modern technology stack including {', '.join(tech_stack[:3])}. "
            f"The architecture is designed to provide scalability, reliability, and maintainability. "
            f"Each component serves a specific purpose in the overall system integration, "
            f"data processing, and user interaction requirements."
        )

    def _extract_key_factors(self, reasoning_list: List[str]) -> List[str]:
        """Extract key factors from reasoning text."""
        # Simple keyword-based extraction
        factors = []

        common_themes = [
            ("automation potential", "High automation potential identified"),
            ("data processing", "Significant data processing requirements"),
            ("integration", "Multiple system integration needs"),
            ("scalability", "Scalability considerations important"),
            ("security", "Security requirements identified"),
            ("compliance", "Compliance and regulatory factors"),
            ("user interface", "User interface and experience factors"),
            ("performance", "Performance and efficiency requirements"),
        ]

        reasoning_text = " ".join(reasoning_list).lower()

        for keyword, factor in common_themes:
            if keyword in reasoning_text:
                factors.append(factor)

        return factors[:5]  # Return top 5 factors

    def _generate_implementation_considerations(self, recommendation) -> List[str]:
        """Generate implementation considerations for a recommendation."""
        considerations = []

        # Based on feasibility
        if recommendation.feasibility == "Automatable":
            considerations.extend(
                [
                    "Full automation implementation recommended",
                    "Consider phased rollout to minimize risk",
                    "Implement comprehensive testing and validation",
                ]
            )
        elif recommendation.feasibility == "Partially Automatable":
            considerations.extend(
                [
                    "Identify which components can be fully automated",
                    "Plan for human oversight and intervention points",
                    "Design clear handoff processes between automated and manual steps",
                ]
            )
        else:
            considerations.extend(
                [
                    "Focus on process optimization and tooling improvements",
                    "Consider workflow automation rather than full automation",
                    "Evaluate future automation opportunities as technology evolves",
                ]
            )

        # Based on confidence level
        if recommendation.confidence < 0.7:
            considerations.append(
                "Conduct additional analysis and validation before implementation"
            )

        # Based on tech stack complexity
        if len(recommendation.tech_stack) > 5:
            considerations.append(
                "Complex technology stack - ensure adequate technical expertise"
            )

        return considerations

    def _identify_architecture_patterns(
        self, session: SessionState
    ) -> List[Dict[str, str]]:
        """Identify common architecture patterns in recommendations."""
        patterns = []

        all_tech = set()
        for rec in session.recommendations:
            all_tech.update(rec.tech_stack)

        # Microservices pattern
        if any(tech in all_tech for tech in ["Docker", "Kubernetes", "API Gateway"]):
            patterns.append(
                {
                    "name": "Microservices Architecture",
                    "description": "Distributed system with independently deployable services",
                }
            )

        # Event-driven pattern
        if any(tech in all_tech for tech in ["Apache Kafka", "RabbitMQ", "Event Bus"]):
            patterns.append(
                {
                    "name": "Event-Driven Architecture",
                    "description": "Asynchronous communication through events and message queues",
                }
            )

        # Layered architecture
        if any(tech in all_tech for tech in ["FastAPI", "Django", "Express.js"]):
            patterns.append(
                {
                    "name": "Layered Architecture",
                    "description": "Traditional multi-tier architecture with clear separation of concerns",
                }
            )

        return patterns

    def _generate_scalability_analysis(self, tech_stack: List[str]) -> List[str]:
        """Generate scalability analysis notes."""
        notes = []

        if "Kubernetes" in tech_stack:
            notes.append(
                "Kubernetes provides excellent horizontal scaling capabilities"
            )

        if "Redis" in tech_stack:
            notes.append("Redis caching will improve performance under high load")

        if any(db in tech_stack for db in ["PostgreSQL", "MongoDB"]):
            notes.append(
                "Database optimization and indexing will be critical for scale"
            )

        if "Load Balancer" in tech_stack:
            notes.append("Load balancing ensures even distribution of traffic")

        return notes

    def _generate_security_analysis(self, tech_stack: List[str]) -> List[str]:
        """Generate security analysis notes."""
        notes = []

        if "OAuth2" in tech_stack:
            notes.append("OAuth2 provides secure authentication and authorization")

        if "HTTPS" in tech_stack:
            notes.append("HTTPS ensures encrypted communication")

        if any(cloud in tech_stack for cloud in ["AWS", "Azure", "GCP"]):
            notes.append("Cloud provider security features should be leveraged")

        notes.append(
            "Regular security audits and vulnerability assessments recommended"
        )
        notes.append("Implement proper input validation and sanitization")

        return notes

    def _identify_implementation_risks(
        self, session: SessionState
    ) -> List[Dict[str, str]]:
        """Identify potential implementation risks."""
        risks = []

        # Based on complexity
        if len(session.recommendations) > 3:
            risks.append(
                {
                    "category": "Complexity Risk",
                    "description": "Multiple solution options may lead to decision paralysis",
                    "mitigation": "Prioritize recommendations by confidence and business impact",
                }
            )

        # Based on tech stack
        all_tech = set()
        for rec in session.recommendations:
            all_tech.update(rec.tech_stack)

        if len(all_tech) > 10:
            risks.append(
                {
                    "category": "Technical Risk",
                    "description": "Large technology stack increases integration complexity",
                    "mitigation": "Phase implementation and focus on core technologies first",
                }
            )

        # Based on confidence levels
        low_confidence_recs = [
            rec for rec in session.recommendations if rec.confidence < 0.7
        ]
        if low_confidence_recs:
            risks.append(
                {
                    "category": "Uncertainty Risk",
                    "description": "Some recommendations have lower confidence levels",
                    "mitigation": "Conduct proof-of-concept testing for uncertain recommendations",
                }
            )

        return risks

    def _generate_success_metrics(self, session: SessionState) -> List[Dict[str, str]]:
        """Generate success metrics for implementation."""
        metrics = []

        # Standard automation metrics
        metrics.extend(
            [
                {
                    "name": "Process Automation Rate",
                    "description": "Percentage of manual tasks successfully automated",
                    "target": "≥80% of identified manual processes",
                },
                {
                    "name": "Processing Time Reduction",
                    "description": "Reduction in time required to complete processes",
                    "target": "≥50% reduction in processing time",
                },
                {
                    "name": "Error Rate Reduction",
                    "description": "Decrease in human errors through automation",
                    "target": "≥90% reduction in manual errors",
                },
                {
                    "name": "User Satisfaction",
                    "description": "User satisfaction with automated processes",
                    "target": "≥4.0/5.0 satisfaction rating",
                },
            ]
        )

        # Domain-specific metrics
        domain = session.requirements.get("domain", "")
        if "customer service" in domain.lower():
            metrics.append(
                {
                    "name": "Response Time",
                    "description": "Average time to respond to customer inquiries",
                    "target": "≤2 minutes for automated responses",
                }
            )

        return metrics

    # Utility methods from base exporter

    def _get_overall_feasibility(self, session: SessionState) -> str:
        """Determine overall feasibility from recommendations."""
        if not session.recommendations:
            return "Unknown"

        # Take the feasibility of the highest confidence recommendation
        best_rec = max(session.recommendations, key=lambda r: r.confidence)
        return best_rec.feasibility

    def _get_overall_confidence(self, session: SessionState) -> float:
        """Calculate overall confidence from recommendations."""
        if not session.recommendations:
            return 0.0

        # Weighted average by confidence
        total_weight = sum(rec.confidence for rec in session.recommendations)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(
            rec.confidence * rec.confidence for rec in session.recommendations
        )
        return weighted_sum / total_weight

    def _get_feasibility_emoji(self, feasibility: str) -> str:
        """Get emoji for feasibility status."""
        emoji_map = {
            "Automatable": "✅",
            "Partially Automatable": "⚠️",
            "Not Automatable": "❌",
            "Unknown": "❓",
        }
        return emoji_map.get(feasibility, "❓")

    def _generate_confidence_bar(self, confidence: float) -> str:
        """Generate a visual confidence bar using Unicode blocks."""
        if confidence < 0 or confidence > 1:
            return ""

        # Use Unicode block characters for visual representation
        filled_blocks = int(confidence * 10)
        empty_blocks = 10 - filled_blocks

        bar = "█" * filled_blocks + "░" * empty_blocks
        return f"`{bar}`"

    # Synchronous versions of section methods for compatibility

    def _add_requirements_section_sync(self, lines: List[str], session: SessionState):
        """Add detailed requirements section (sync version)."""
        description = session.requirements.get("description", "No description provided")
        lines.append("### Original Description")
        lines.append("")
        lines.append(f"> {self._escape_markdown_content(description)}")
        lines.append("")

        # Requirements breakdown
        req_fields = [
            ("Domain", "domain"),
            ("Frequency", "frequency"),
            ("Criticality", "criticality"),
            ("Pattern Types", "pattern_types"),
            ("Business Impact", "business_impact"),
            ("Technical Complexity", "technical_complexity"),
            ("Data Sensitivity", "data_sensitivity"),
            ("Compliance Requirements", "compliance_requirements"),
            ("Integration Requirements", "integration_requirements"),
            ("Budget Constraints", "budget_constraints"),
        ]

        # Check if we have any requirement data
        has_requirements = False
        requirement_data = []

        for label, key in req_fields:
            value = session.requirements.get(key)
            if value:
                has_requirements = True
                if isinstance(value, list):
                    value = ", ".join(value)
                requirement_data.append(
                    (label, self._escape_markdown_content(str(value)))
                )

        if has_requirements:
            lines.append("### Requirements Breakdown")
            lines.append("")
            lines.append("| Attribute | Value |")
            lines.append("|-----------|-------|")

            for label, value in requirement_data:
                lines.append(f"| {label} | {value} |")

            lines.append("")
        else:
            lines.append("### Requirements Breakdown")
            lines.append("")
            lines.append(
                "*No detailed requirements data available. Only basic description provided.*"
            )
            lines.append("")

        # Constraints if any
        constraints = session.requirements.get("constraints", {})
        if constraints:
            lines.append("### Constraints & Restrictions")
            lines.append("")

            if constraints.get("restricted_technologies"):
                lines.append("**Restricted Technologies:**")
                for tech in constraints["restricted_technologies"]:
                    lines.append(f"- ❌ {tech}")
                lines.append("")

            if constraints.get("required_integrations"):
                lines.append("**Required Integrations:**")
                for integration in constraints["required_integrations"]:
                    lines.append(f"- 🔗 {integration}")
                lines.append("")

            if constraints.get("compliance_requirements"):
                lines.append("**Compliance Requirements:**")
                for compliance in constraints["compliance_requirements"]:
                    lines.append(f"- 📋 {compliance}")
                lines.append("")

    def _add_feasibility_section_sync(self, lines: List[str], session: SessionState):
        """Add detailed feasibility assessment (sync version)."""
        if not session.recommendations:
            lines.append("*No feasibility assessment available.*")
            lines.append("")
            return

        # Overall assessment
        overall_feasibility = self._get_overall_feasibility(session)
        overall_confidence = self._get_overall_confidence(session)

        lines.append("### Overall Assessment")
        lines.append("")
        lines.append(
            f"**Result:** {self._get_feasibility_emoji(overall_feasibility)} **{overall_feasibility}**"
        )
        lines.append(
            f"**Confidence Level:** {overall_confidence:.1%} {self._generate_confidence_bar(overall_confidence)}"
        )
        lines.append("")

        # Feasibility breakdown
        lines.append("### Feasibility Breakdown")
        lines.append("")

        feasibility_counts = {}
        for rec in session.recommendations:
            feasibility = rec.feasibility
            if feasibility not in feasibility_counts:
                feasibility_counts[feasibility] = 0
            feasibility_counts[feasibility] += 1

        lines.append("| Feasibility Level | Count | Percentage |")
        lines.append("|------------------|-------|------------|")

        total_recs = len(session.recommendations)
        for feasibility, count in feasibility_counts.items():
            percentage = (count / total_recs) * 100
            emoji = self._get_feasibility_emoji(feasibility)
            lines.append(f"| {emoji} {feasibility} | {count} | {percentage:.1f}% |")

        lines.append("")

        # Key factors
        lines.append("### Key Assessment Factors")
        lines.append("")

        # Analyze common themes in reasoning
        all_reasoning = [rec.reasoning for rec in session.recommendations]
        key_factors = self._extract_key_factors(all_reasoning)

        for factor in key_factors:
            lines.append(f"- {factor}")

        lines.append("")

        # Add confidence analysis
        confidence_analysis = self._generate_confidence_analysis_section(session)
        lines.extend(confidence_analysis)

    def _add_recommendations_section_sync(
        self, lines: List[str], session: SessionState
    ):
        """Add detailed recommendations (sync version)."""
        if not session.recommendations:
            lines.append("*No recommendations available.*")
            lines.append("")
            return

        for i, rec in enumerate(session.recommendations, 1):
            lines.append(f"### Recommendation {i}: Pattern {rec.pattern_id}")
            lines.append("")

            # Basic info
            confidence_bar = self._generate_confidence_bar(rec.confidence)
            lines.append(
                f"**Feasibility:** {self._get_feasibility_emoji(rec.feasibility)} {rec.feasibility}"
            )
            lines.append(f"**Confidence:** {rec.confidence:.1%} {confidence_bar}")
            lines.append("")

            # Tech stack with detailed descriptions
            if rec.tech_stack:
                lines.append("#### 🛠️ Recommended Technology Stack")
                lines.append("")

                # Use stored enhanced data if available, otherwise use original
                enhanced_tech_stack = (
                    getattr(rec, "enhanced_tech_stack", None) or rec.tech_stack
                )
                architecture_explanation = getattr(
                    rec, "architecture_explanation", None
                )

                # Categorized tech stack with descriptions
                categorized_stack = self._categorize_tech_stack_with_descriptions(
                    enhanced_tech_stack
                )

                for category, technologies in categorized_stack.items():
                    if technologies:
                        lines.append(f"**{category}:**")
                        for tech_info in technologies:
                            if isinstance(tech_info, dict):
                                tech_name = tech_info.get(
                                    "name", tech_info.get("technology", str(tech_info))
                                )
                                tech_desc = tech_info.get("description", "")
                                if tech_desc:
                                    lines.append(f"- **{tech_name}**: {tech_desc}")
                                else:
                                    lines.append(f"- `{tech_name}`")
                            else:
                                lines.append(f"- `{tech_info}`")
                        lines.append("")

                # Architecture explanation - use stored data if available
                lines.append("#### 🏗️ How It All Works Together")
                lines.append("")

                if architecture_explanation and architecture_explanation.strip():
                    app_logger.info(
                        f"Using stored architecture explanation in sync export ({len(architecture_explanation)} chars)"
                    )
                    explanation_text = architecture_explanation.strip()

                    # Split into paragraphs and add proper spacing
                    paragraphs = [
                        p.strip() for p in explanation_text.split("\n\n") if p.strip()
                    ]
                    if not paragraphs:
                        # If no double newlines, split on single newlines but group sentences
                        sentences = [
                            s.strip() for s in explanation_text.split("\n") if s.strip()
                        ]
                        paragraphs = [" ".join(sentences)]

                    for paragraph in paragraphs:
                        lines.append(paragraph)
                        lines.append("")
                else:
                    # Generate detailed fallback explanation
                    app_logger.info(
                        "No stored explanation found, generating detailed fallback"
                    )
                    explanation = self._generate_detailed_fallback_explanation(
                        enhanced_tech_stack, session
                    )

                    # Split explanation into paragraphs for better formatting
                    if explanation and explanation.strip():
                        # Split into paragraphs and add proper spacing
                        paragraphs = [
                            p.strip() for p in explanation.split(". ") if p.strip()
                        ]

                        # Group sentences into paragraphs (every 2-3 sentences)
                        current_paragraph = []
                        for i, sentence in enumerate(paragraphs):
                            current_paragraph.append(
                                sentence if sentence.endswith(".") else sentence + "."
                            )

                            # Create paragraph break every 2-3 sentences or at logical breaks
                            if len(current_paragraph) >= 2 and (
                                i == len(paragraphs) - 1
                                or any(
                                    keyword in sentence.lower()
                                    for keyword in [
                                        "workflow",
                                        "components",
                                        "architecture",
                                        "system",
                                    ]
                                )
                            ):
                                lines.append(" ".join(current_paragraph))
                                lines.append("")
                                current_paragraph = []

                        # Add any remaining sentences
                        if current_paragraph:
                            lines.append(" ".join(current_paragraph))
                            lines.append("")
                    else:
                        lines.append(
                            "Technology components work together to provide a comprehensive automation solution."
                        )
                        lines.append("")

            # Detailed reasoning
            lines.append("#### 💭 Reasoning & Analysis")
            lines.append("")
            lines.append(rec.reasoning)
            lines.append("")

            # Implementation considerations
            lines.append("#### ⚠️ Implementation Considerations")
            lines.append("")
            considerations = self._generate_implementation_considerations(rec)
            for consideration in considerations:
                lines.append(f"- {consideration}")
            lines.append("")

            if i < len(session.recommendations):
                lines.append("---")
                lines.append("")

    def _add_technical_analysis_section_sync(
        self, lines: List[str], session: SessionState
    ):
        """Add comprehensive technical analysis (sync version)."""
        if not session.recommendations:
            lines.append(
                "*No technical analysis available - no recommendations found.*"
            )
            lines.append("")
            return

        # Aggregate all tech stacks
        all_tech = set()
        for rec in session.recommendations:
            all_tech.update(rec.tech_stack)

        if not all_tech:
            lines.append(
                "*No technology stack information available in recommendations.*"
            )
            lines.append("")
            return

        # Technology overview
        lines.append("### Technology Overview")
        lines.append("")

        categorized_tech = self._categorize_tech_stack(list(all_tech))

        has_tech_content = False
        for category, technologies in categorized_tech.items():
            if technologies:
                has_tech_content = True
                lines.append(f"#### {category}")
                lines.append("")
                for tech in sorted(technologies):
                    description = self._get_technology_description(tech)
                    lines.append(f"- **{tech}**: {description}")
                lines.append("")

        if not has_tech_content:
            lines.append("*No categorized technology information available.*")
            lines.append("")

        # Architecture patterns
        patterns = self._identify_architecture_patterns(session)
        if patterns:
            lines.append("### Architecture Patterns")
            lines.append("")
            for pattern in patterns:
                lines.append(f"- **{pattern['name']}**: {pattern['description']}")
            lines.append("")

        # Scalability considerations
        scalability_notes = self._generate_scalability_analysis(list(all_tech))
        if scalability_notes:
            lines.append("### Scalability & Performance")
            lines.append("")
            for note in scalability_notes:
                lines.append(f"- {note}")
            lines.append("")

        # Security considerations
        security_notes = self._generate_security_analysis(list(all_tech))
        if security_notes:
            lines.append("### Security Considerations")
            lines.append("")
            for note in security_notes:
                lines.append(f"- {note}")
            lines.append("")

    def _add_pattern_matches_section_sync(
        self, lines: List[str], session: SessionState
    ):
        """Add detailed pattern matching analysis (sync version)."""
        if not session.matches:
            lines.append("### Pattern Matching Results")
            lines.append("")
            lines.append("*No pattern matches available.*")
            lines.append("")

            # If we have recommendations but no matches, explain the discrepancy
            if session.recommendations:
                lines.append(
                    "**⚠️ Note:** Recommendations are present without pattern matches. This may indicate:"
                )
                lines.append("- Fallback recommendations were used")
                lines.append("- Pattern matching failed or was skipped")
                lines.append("- Recommendations were manually created")
                lines.append("")
            return

        lines.append("### Pattern Matching Results")
        lines.append("")
        lines.append("| Pattern ID | Match Score | Confidence | Analysis |")
        lines.append("|------------|-------------|------------|----------|")

        for match in sorted(session.matches, key=lambda x: x.score, reverse=True):
            score_bar = self._generate_confidence_bar(match.score)
            confidence_bar = self._generate_confidence_bar(match.confidence)

            # Use proper truncation method
            short_rationale = self._format_table_cell(match.rationale, 80)

            lines.append(
                f"| {match.pattern_id} | {match.score:.1%} {score_bar} | {match.confidence:.1%} {confidence_bar} | {short_rationale} |"
            )

        lines.append("")

        # Detailed analysis for top matches
        top_matches = sorted(session.matches, key=lambda x: x.score, reverse=True)[:3]

        lines.append("### Top Pattern Matches - Detailed Analysis")
        lines.append("")

        for i, match in enumerate(top_matches, 1):
            lines.append(f"#### {i}. Pattern {match.pattern_id}")
            lines.append("")
            lines.append(
                f"**Match Score:** {match.score:.1%} {self._generate_confidence_bar(match.score)}"
            )
            lines.append(
                f"**Confidence:** {match.confidence:.1%} {self._generate_confidence_bar(match.confidence)}"
            )
            lines.append("")
            lines.append("**Analysis:**")
            clean_rationale = self._escape_markdown_content(match.rationale)
            lines.append(f"> {clean_rationale}")
            lines.append("")

    def _add_qa_section_sync(self, lines: List[str], session: SessionState):
        """Add Q&A history (sync version)."""
        if not session.qa_history:
            lines.append("*No Q&A history available.*")
            lines.append("")
            return

        lines.append("### Question & Answer History")
        lines.append("")

        for i, qa in enumerate(session.qa_history, 1):
            # Use UTC for consistency
            timestamp_utc = qa.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            lines.append(f"#### Round {i} - {timestamp_utc}")
            lines.append("")

            if qa.questions:
                lines.append("**Questions Asked:**")
                for j, question in enumerate(qa.questions, 1):
                    clean_question = self._escape_markdown_content(question)
                    lines.append(f"{j}. {clean_question}")
                lines.append("")

            if qa.answers:
                lines.append("**Responses Provided:**")
                lines.append("")

                # Use a more readable format instead of table for long answers
                for field, answer in qa.answers.items():
                    formatted_field = field.replace("_", " ").title()
                    clean_answer = self._escape_markdown_content(str(answer))

                    lines.append(f"**{formatted_field}:**")
                    # If answer is long, use block format instead of table
                    if len(clean_answer) > 100:
                        lines.append(f"> {clean_answer}")
                    else:
                        lines.append(f"> {clean_answer}")
                    lines.append("")

            if i < len(session.qa_history):
                lines.append("---")
                lines.append("")

    def _add_implementation_guidance_sync(
        self, lines: List[str], session: SessionState
    ):
        """Add implementation guidance (sync version)."""
        lines.append("### Next Steps & Implementation Roadmap")
        lines.append("")

        if not session.recommendations:
            lines.append(
                "*Complete the assessment to receive implementation guidance.*"
            )
            lines.append("")
            return

        # Implementation phases
        lines.append("#### Phase 1: Planning & Design")
        lines.append("")
        lines.append("- [ ] Review and validate all recommendations")
        lines.append("- [ ] Conduct detailed technical architecture review")
        lines.append("- [ ] Define success criteria and KPIs")
        lines.append("- [ ] Create detailed project timeline")
        lines.append("- [ ] Identify required resources and skills")
        lines.append("")

        lines.append("#### Phase 2: Proof of Concept")
        lines.append("")
        lines.append("- [ ] Implement minimal viable automation")
        lines.append("- [ ] Test with limited dataset/scope")
        lines.append("- [ ] Validate technical assumptions")
        lines.append("- [ ] Measure performance and accuracy")
        lines.append("- [ ] Gather user feedback")
        lines.append("")

        lines.append("#### Phase 3: Full Implementation")
        lines.append("")
        lines.append("- [ ] Scale to production environment")
        lines.append("- [ ] Implement monitoring and alerting")
        lines.append("- [ ] Create user training materials")
        lines.append("- [ ] Establish maintenance procedures")
        lines.append("- [ ] Plan for continuous improvement")
        lines.append("")

        # Risk mitigation
        lines.append("### Risk Mitigation Strategies")
        lines.append("")
        risks = self._identify_implementation_risks(session)
        for risk in risks:
            lines.append(f"- **{risk['category']}**: {risk['description']}")
            lines.append(f"  - *Mitigation*: {risk['mitigation']}")
        lines.append("")

        # Success metrics
        lines.append("### Success Metrics")
        lines.append("")
        metrics = self._generate_success_metrics(session)
        for metric in metrics:
            lines.append(f"- **{metric['name']}**: {metric['description']}")
            lines.append(f"  - *Target*: {metric['target']}")
        lines.append("")

    def _validate_session_consistency(
        self, session: SessionState
    ) -> List[Dict[str, str]]:
        """Validate session data consistency and return issues."""
        issues = []

        # Check for recommendations without pattern matches
        if len(session.recommendations) > 0 and len(session.matches) == 0:
            issues.append(
                {
                    "severity": "WARNING",
                    "message": "Recommendations exist without pattern matches - this may indicate fallback data or incomplete analysis",
                }
            )

        # Check for incomplete processing
        if session.phase.value != "DONE" and len(session.recommendations) > 0:
            issues.append(
                {
                    "severity": "WARNING",
                    "message": f"Session in {session.phase.value} phase but has recommendations - processing may be incomplete",
                }
            )

        # Check for missing requirements data
        if not session.requirements or not session.requirements.get("description"):
            issues.append(
                {
                    "severity": "ERROR",
                    "message": "Missing or incomplete requirements data",
                }
            )

        # Enhanced confidence validation
        if len(session.recommendations) > 0:
            confidences = [rec.confidence for rec in session.recommendations]

            # Check for identical confidence values
            if len(session.recommendations) > 1 and len(set(confidences)) == 1:
                confidence_val = confidences[0]
                issues.append(
                    {
                        "severity": "WARNING",
                        "message": f"All recommendations have identical confidence ({confidence_val:.1%}) - may indicate template data",
                    }
                )

                # Check for specific suspicious values
                if confidence_val == 0.85:
                    issues.append(
                        {
                            "severity": "ERROR",
                            "message": "Confidence value 0.85 (85%) appears to be hard-coded - this is a common default/test value",
                        }
                    )

            # Check for other suspicious confidence patterns
            if all(c in [0.8, 0.85, 0.9] for c in confidences):
                issues.append(
                    {
                        "severity": "WARNING",
                        "message": "Confidence values appear to be rounded to common test values (0.8, 0.85, 0.9)",
                    }
                )

        # Enhanced tech stack validation
        if len(session.recommendations) > 1:
            tech_stacks = [set(rec.tech_stack) for rec in session.recommendations]

            # Check for identical tech stacks
            if len(tech_stacks) > 1:
                for i in range(len(tech_stacks)):
                    for j in range(i + 1, len(tech_stacks)):
                        if tech_stacks[i] == tech_stacks[j]:
                            issues.append(
                                {
                                    "severity": "ERROR",
                                    "message": f"Recommendations {i+1} and {j+1} have identical tech stacks - indicates template/copy-paste data",
                                }
                            )
                        else:
                            overlap = len(tech_stacks[i] & tech_stacks[j]) / len(
                                tech_stacks[i] | tech_stacks[j]
                            )
                            if overlap > 0.8:
                                issues.append(
                                    {
                                        "severity": "WARNING",
                                        "message": f"Recommendations {i+1} and {j+1} have {overlap:.1%} tech stack overlap - may indicate template data",
                                    }
                                )
                        break

            # Check for generic AWS-heavy stacks (common in templates)
            aws_heavy_count = 0
            for tech_stack in tech_stacks:
                aws_techs = [
                    tech for tech in tech_stack if "AWS" in tech or "Lambda" in tech
                ]
                if len(aws_techs) >= 2 and len(tech_stack) <= 4:
                    aws_heavy_count += 1

            if aws_heavy_count >= 2:
                issues.append(
                    {
                        "severity": "WARNING",
                        "message": f"{aws_heavy_count} recommendations use generic AWS-heavy tech stacks - may indicate template data",
                    }
                )

        # Check for domain mismatch between requirements and recommendations
        if session.requirements.get("description") and session.recommendations:
            description = session.requirements["description"].lower()

            # Define domain keywords
            domain_keywords = {
                "financial": [
                    "payment",
                    "credit card",
                    "balance",
                    "financial",
                    "money",
                    "transaction",
                ],
                "support": ["ticket", "support", "customer service", "help desk"],
                "document": ["invoice", "ocr", "document", "pdf", "scan"],
                "card": ["lost card", "card replacement", "card detection"],
            }

            # Detect requirement domain
            req_domain = None
            for domain, keywords in domain_keywords.items():
                if any(keyword in description for keyword in keywords):
                    req_domain = domain
                    break

            # Check if recommendations match the domain
            if req_domain:
                mismatched_patterns = []
                for rec in session.recommendations:
                    reasoning = rec.reasoning.lower()
                    pattern_id = rec.pattern_id

                    # Check for obvious domain mismatches
                    if req_domain == "financial" and (
                        "lost card" in reasoning
                        or "invoice" in reasoning
                        or "ticket" in reasoning
                    ):
                        mismatched_patterns.append(pattern_id)
                    elif req_domain == "support" and (
                        "invoice" in reasoning or "payment" in reasoning
                    ):
                        mismatched_patterns.append(pattern_id)

                if mismatched_patterns:
                    issues.append(
                        {
                            "severity": "ERROR",
                            "message": f"Domain mismatch: {req_domain} requirements but patterns {mismatched_patterns} are from different domains - indicates incorrect pattern matching",
                        }
                    )

        return issues

    def _escape_markdown_content(self, text: str) -> str:
        """Properly escape content for Markdown without HTML entities."""
        if not text:
            return ""

        # Replace HTML entities that might have been introduced
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        # Escape Markdown special characters only where needed
        # Don't escape in code blocks or when already properly formatted
        return text

    def _format_table_cell(self, text: str, max_length: int = 100) -> str:
        """Format text for table cells with proper truncation."""
        if not text:
            return "N/A"

        # Clean the text first
        clean_text = self._escape_markdown_content(str(text))

        # Truncate if needed, but try to break at word boundaries
        if len(clean_text) <= max_length:
            return clean_text

        # Find last space before max_length
        truncate_pos = clean_text.rfind(" ", 0, max_length - 3)
        if truncate_pos == -1:
            truncate_pos = max_length - 3

        return clean_text[:truncate_pos] + "..."

    def _analyze_confidence_patterns(self, session: SessionState) -> Dict[str, Any]:
        """Analyze confidence patterns to detect issues."""
        if not session.recommendations:
            return {"status": "no_data", "message": "No recommendations to analyze"}

        confidences = [rec.confidence for rec in session.recommendations]

        analysis = {
            "total_recommendations": len(confidences),
            "unique_confidence_values": len(set(confidences)),
            "confidence_range": (min(confidences), max(confidences)),
            "average_confidence": sum(confidences) / len(confidences),
            "issues": [],
        }

        # Check for hard-coded 0.85 (85%)
        if 0.85 in confidences:
            count_085 = confidences.count(0.85)
            analysis["issues"].append(
                {
                    "type": "hard_coded_value",
                    "message": f"{count_085}/{len(confidences)} recommendations have confidence 0.85 (85%) - common test/default value",
                    "severity": "HIGH" if count_085 == len(confidences) else "MEDIUM",
                }
            )

        # Check for identical values
        if len(set(confidences)) == 1:
            analysis["issues"].append(
                {
                    "type": "identical_values",
                    "message": f"All recommendations have identical confidence ({confidences[0]:.1%})",
                    "severity": "HIGH",
                }
            )

        # Check for rounded values
        rounded_values = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
        rounded_count = sum(1 for c in confidences if c in rounded_values)
        if rounded_count == len(confidences) and len(confidences) > 1:
            analysis["issues"].append(
                {
                    "type": "rounded_values",
                    "message": "All confidence values are rounded to common increments - may indicate manual/template data",
                    "severity": "MEDIUM",
                }
            )

        # Check for unrealistic precision
        high_precision = [c for c in confidences if len(str(c).split(".")[-1]) > 3]
        if high_precision:
            analysis["issues"].append(
                {
                    "type": "unrealistic_precision",
                    "message": f"{len(high_precision)} confidence values have >3 decimal places - may indicate calculation errors",
                    "severity": "LOW",
                }
            )

        return analysis

    def _generate_confidence_analysis_section(self, session: SessionState) -> List[str]:
        """Generate a detailed confidence analysis section."""
        lines = []
        analysis = self._analyze_confidence_patterns(session)

        if analysis.get("status") == "no_data":
            return lines

        lines.append("### 🔍 Confidence Analysis")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Recommendations | {analysis['total_recommendations']} |")
        lines.append(
            f"| Unique Confidence Values | {analysis['unique_confidence_values']} |"
        )
        lines.append(
            f"| Confidence Range | {analysis['confidence_range'][0]:.1%} - {analysis['confidence_range'][1]:.1%} |"
        )
        lines.append(f"| Average Confidence | {analysis['average_confidence']:.1%} |")
        lines.append("")

        if analysis["issues"]:
            lines.append("**⚠️ Confidence Issues Detected:**")
            lines.append("")
            for issue in analysis["issues"]:
                severity_emoji = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "ℹ️"}
                emoji = severity_emoji.get(issue["severity"], "⚠️")
                lines.append(f"- {emoji} **{issue['severity']}**: {issue['message']}")
            lines.append("")
        else:
            lines.append("✅ **No confidence issues detected**")
            lines.append("")

        return lines

    def _generate_detailed_fallback_explanation(
        self, tech_stack: List[str], session: SessionState
    ) -> str:
        """Generate detailed fallback architecture explanation with specific technology roles."""
        if not tech_stack:
            return "No technology stack specified for this recommendation."

        # Categorize technologies to understand the architecture
        categorized = self._categorize_tech_stack_with_descriptions(tech_stack)

        explanation_parts = []

        # Analyze the requirements to provide context
        requirements = session.requirements
        domain = requirements.get("domain", "").lower()
        description = requirements.get("description", "")

        # Introduction based on domain
        if (
            "communication" in domain
            or "messaging" in domain
            or "sms" in description.lower()
        ):
            explanation_parts.append(
                "This communication automation solution is architected to handle message processing, delivery, and analysis at scale."
            )
        elif "data" in domain or "analytics" in domain:
            explanation_parts.append(
                "This data processing solution is designed to handle large-scale data ingestion, analysis, and reporting workflows."
            )
        elif "api" in domain or "integration" in domain:
            explanation_parts.append(
                "This integration solution provides a robust API-first architecture for connecting systems and automating workflows."
            )
        else:
            explanation_parts.append(
                "This automation solution is architected to provide scalable, reliable, and maintainable system integration."
            )

        # Explain each technology category's role
        if categorized.get("Cloud & Infrastructure"):
            cloud_techs = [
                tech["name"] for tech in categorized["Cloud & Infrastructure"]
            ]
            if "AWS Lambda" in cloud_techs or "Lambda" in cloud_techs:
                explanation_parts.append(
                    f"The serverless architecture leverages {', '.join(cloud_techs)} to provide automatic scaling and cost-effective execution without server management overhead."
                )
            else:
                explanation_parts.append(
                    f"The cloud infrastructure utilizes {', '.join(cloud_techs)} to provide scalable, reliable hosting and deployment capabilities."
                )

        if categorized.get("Communication & Integration"):
            comm_techs = [
                tech["name"] for tech in categorized["Communication & Integration"]
            ]
            if "Twilio" in comm_techs:
                explanation_parts.append(
                    f"Communication services are handled by {', '.join(comm_techs)}, enabling reliable SMS, voice, and messaging capabilities with robust delivery tracking and error handling."
                )
            else:
                explanation_parts.append(
                    f"System integration and communication is managed through {', '.join(comm_techs)}, enabling seamless data exchange between components."
                )

        if categorized.get("Data Processing & Analytics"):
            data_techs = [
                tech["name"] for tech in categorized["Data Processing & Analytics"]
            ]
            if "AWS Comprehend" in data_techs:
                explanation_parts.append(
                    f"Natural language processing and sentiment analysis are powered by {', '.join(data_techs)}, providing intelligent text analysis and insights extraction from communication data."
                )
            else:
                explanation_parts.append(
                    f"Data processing and analytics are handled by {', '.join(data_techs)}, enabling intelligent analysis and insights generation."
                )

        if categorized.get("Databases & Storage"):
            db_techs = [tech["name"] for tech in categorized["Databases & Storage"]]
            explanation_parts.append(
                f"Data persistence and retrieval are managed by {', '.join(db_techs)}, ensuring reliable storage, fast access, and data integrity throughout the system."
            )

        if categorized.get("Programming Languages"):
            lang_techs = [tech["name"] for tech in categorized["Programming Languages"]]
            explanation_parts.append(
                f"The core application logic is implemented in {', '.join(lang_techs)}, providing robust, maintainable code with excellent library ecosystem support."
            )

        if categorized.get("Web Frameworks & APIs"):
            api_techs = [tech["name"] for tech in categorized["Web Frameworks & APIs"]]
            explanation_parts.append(
                f"API endpoints and web services are built using {', '.join(api_techs)}, providing fast, secure, and well-documented interfaces for system interaction."
            )

        # Add workflow description
        if "communication" in domain or "sms" in description.lower():
            explanation_parts.append(
                "The typical workflow involves message ingestion, content analysis, processing through business rules, delivery via communication channels, and comprehensive monitoring of delivery status and system performance."
            )
        elif "data" in domain:
            explanation_parts.append(
                "The data flow follows an ETL pattern: extraction from various sources, transformation and validation, intelligent analysis, and loading into storage systems with real-time monitoring and alerting."
            )
        else:
            explanation_parts.append(
                "The system components work together in a coordinated workflow, with each technology handling its specialized function while maintaining high availability, security, and performance standards."
            )

        return " ".join(explanation_parts)
