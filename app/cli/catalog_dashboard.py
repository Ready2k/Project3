#!/usr/bin/env python3
"""
Catalog statistics and health monitoring dashboard.

This tool provides a comprehensive dashboard for monitoring catalog health,
statistics, and trends over time.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import TechEntry, EcosystemType, MaturityLevel, ReviewStatus
from app.utils.imports import require_service


class CatalogDashboard:
    """Catalog statistics and health monitoring dashboard."""
    
    def __init__(self):
        self.manager = IntelligentCatalogManager()
        
    def show_overview(self, args) -> None:
        """Show catalog overview dashboard."""
        try:
            stats = self.manager.get_catalog_statistics()
            technologies = list(self.manager.technologies.values())
            
            print("=" * 80)
            print("TECHNOLOGY CATALOG DASHBOARD")
            print("=" * 80)
            
            # Basic statistics
            print(f"\n📊 OVERVIEW")
            print(f"Total Technologies: {stats.total_entries}")
            print(f"Pending Review: {stats.pending_review}")
            print(f"Auto-Generated: {stats.auto_generated}")
            print(f"Validation Errors: {stats.validation_errors}")
            
            # Health indicators
            health_score = self._calculate_health_score(technologies)
            health_status = self._get_health_status(health_score)
            print(f"Catalog Health: {health_status} ({health_score:.1f}/100)")
            
            # Distribution by ecosystem
            if stats.by_ecosystem:
                print(f"\n🌐 BY ECOSYSTEM")
                for ecosystem, count in sorted(stats.by_ecosystem.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / stats.total_entries) * 100
                    bar = self._create_bar(percentage, 30)
                    print(f"{ecosystem:<15} {count:>4} {bar} {percentage:>5.1f}%")
            
            # Distribution by category
            if stats.by_category:
                print(f"\n📂 BY CATEGORY")
                for category, count in sorted(stats.by_category.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / stats.total_entries) * 100
                    bar = self._create_bar(percentage, 30)
                    print(f"{category:<15} {count:>4} {bar} {percentage:>5.1f}%")
            
            # Distribution by maturity
            if stats.by_maturity:
                print(f"\n🔄 BY MATURITY")
                for maturity, count in sorted(stats.by_maturity.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / stats.total_entries) * 100
                    bar = self._create_bar(percentage, 30)
                    print(f"{maturity:<15} {count:>4} {bar} {percentage:>5.1f}%")
            
            # Recent activity
            self._show_recent_activity(technologies)
            
            # Quality metrics
            self._show_quality_metrics(technologies)
            
            # Recommendations
            self._show_recommendations(technologies, stats)
            
        except Exception as e:
            print(f"✗ Error showing overview: {e}")
            sys.exit(1)
    
    def show_health_report(self, args) -> None:
        """Show detailed health report."""
        try:
            technologies = list(self.manager.technologies.values())
            
            print("=" * 80)
            print("CATALOG HEALTH REPORT")
            print("=" * 80)
            
            # Overall health score
            health_score = self._calculate_health_score(technologies)
            health_status = self._get_health_status(health_score)
            
            print(f"\n🏥 OVERALL HEALTH: {health_status} ({health_score:.1f}/100)")
            
            # Health components
            completeness_score = self._calculate_completeness_score(technologies)
            consistency_score = self._calculate_consistency_score(technologies)
            freshness_score = self._calculate_freshness_score(technologies)
            quality_score = self._calculate_quality_score(technologies)
            
            print(f"\n📋 HEALTH COMPONENTS:")
            print(f"Completeness: {completeness_score:.1f}/100 {self._get_score_indicator(completeness_score)}")
            print(f"Consistency:  {consistency_score:.1f}/100 {self._get_score_indicator(consistency_score)}")
            print(f"Freshness:    {freshness_score:.1f}/100 {self._get_score_indicator(freshness_score)}")
            print(f"Quality:      {quality_score:.1f}/100 {self._get_score_indicator(quality_score)}")
            
            # Detailed issues
            issues = self._identify_health_issues(technologies)
            
            if issues['critical']:
                print(f"\n🚨 CRITICAL ISSUES ({len(issues['critical'])})")
                for issue in issues['critical'][:5]:  # Show top 5
                    print(f"  • {issue}")
                if len(issues['critical']) > 5:
                    print(f"  ... and {len(issues['critical']) - 5} more")
            
            if issues['warnings']:
                print(f"\n⚠️  WARNINGS ({len(issues['warnings'])})")
                for warning in issues['warnings'][:5]:  # Show top 5
                    print(f"  • {warning}")
                if len(issues['warnings']) > 5:
                    print(f"  ... and {len(issues['warnings']) - 5} more")
            
            if issues['suggestions']:
                print(f"\n💡 SUGGESTIONS ({len(issues['suggestions'])})")
                for suggestion in issues['suggestions'][:5]:  # Show top 5
                    print(f"  • {suggestion}")
                if len(issues['suggestions']) > 5:
                    print(f"  ... and {len(issues['suggestions']) - 5} more")
            
            # Validation summary
            validation_result = self.manager.validate_catalog_consistency()
            
            print(f"\n🔍 VALIDATION SUMMARY:")
            print(f"Errors:      {len(validation_result.errors)}")
            print(f"Warnings:    {len(validation_result.warnings)}")
            print(f"Suggestions: {len(validation_result.suggestions)}")
            
        except Exception as e:
            print(f"✗ Error showing health report: {e}")
            sys.exit(1)
    
    def show_trends(self, args) -> None:
        """Show catalog trends and analytics."""
        try:
            technologies = list(self.manager.technologies.values())
            
            print("=" * 80)
            print("CATALOG TRENDS & ANALYTICS")
            print("=" * 80)
            
            # Growth trends
            self._show_growth_trends(technologies)
            
            # Usage patterns
            self._show_usage_patterns(technologies)
            
            # Review queue trends
            self._show_review_trends(technologies)
            
            # Technology popularity
            self._show_popularity_metrics(technologies)
            
        except Exception as e:
            print(f"✗ Error showing trends: {e}")
            sys.exit(1)
    
    def show_quality_report(self, args) -> None:
        """Show detailed quality report."""
        try:
            technologies = list(self.manager.technologies.values())
            
            print("=" * 80)
            print("CATALOG QUALITY REPORT")
            print("=" * 80)
            
            # Quality metrics
            total_techs = len(technologies)
            
            # Completeness metrics
            complete_descriptions = len([t for t in technologies if t.description and len(t.description.strip()) > 20])
            has_integrations = len([t for t in technologies if t.integrates_with])
            has_alternatives = len([t for t in technologies if t.alternatives])
            has_use_cases = len([t for t in technologies if t.use_cases])
            has_tags = len([t for t in technologies if t.tags])
            
            print(f"\n📝 COMPLETENESS METRICS:")
            print(f"Complete descriptions: {complete_descriptions}/{total_techs} ({(complete_descriptions/total_techs)*100:.1f}%)")
            print(f"Has integrations:      {has_integrations}/{total_techs} ({(has_integrations/total_techs)*100:.1f}%)")
            print(f"Has alternatives:      {has_alternatives}/{total_techs} ({(has_alternatives/total_techs)*100:.1f}%)")
            print(f"Has use cases:         {has_use_cases}/{total_techs} ({(has_use_cases/total_techs)*100:.1f}%)")
            print(f"Has tags:              {has_tags}/{total_techs} ({(has_tags/total_techs)*100:.1f}%)")
            
            # Validation metrics
            validation_errors = 0
            validation_warnings = 0
            
            for tech in technologies:
                result = self.manager.validate_catalog_entry(tech)
                if not result.is_valid:
                    validation_errors += 1
                if result.warnings:
                    validation_warnings += 1
            
            print(f"\n✅ VALIDATION METRICS:")
            print(f"Validation errors:     {validation_errors}/{total_techs} ({(validation_errors/total_techs)*100:.1f}%)")
            print(f"Validation warnings:   {validation_warnings}/{total_techs} ({(validation_warnings/total_techs)*100:.1f}%)")
            
            # Review metrics
            pending_review = len([t for t in technologies if t.pending_review])
            auto_generated = len([t for t in technologies if t.auto_generated])
            low_confidence = len([t for t in technologies if t.confidence_score < 0.7])
            
            print(f"\n👥 REVIEW METRICS:")
            print(f"Pending review:        {pending_review}/{total_techs} ({(pending_review/total_techs)*100:.1f}%)")
            print(f"Auto-generated:        {auto_generated}/{total_techs} ({(auto_generated/total_techs)*100:.1f}%)")
            print(f"Low confidence (<0.7): {low_confidence}/{total_techs} ({(low_confidence/total_techs)*100:.1f}%)")
            
            # Top quality issues
            quality_issues = []
            
            for tech in technologies:
                issues = []
                
                if not tech.description or len(tech.description.strip()) < 20:
                    issues.append("Short/missing description")
                
                if not tech.integrates_with:
                    issues.append("No integrations specified")
                
                if not tech.use_cases:
                    issues.append("No use cases specified")
                
                if tech.confidence_score < 0.7:
                    issues.append("Low confidence score")
                
                if tech.pending_review:
                    issues.append("Pending review")
                
                if issues:
                    quality_issues.append((tech.name, issues))
            
            if quality_issues:
                print(f"\n🔍 TOP QUALITY ISSUES:")
                for tech_name, issues in sorted(quality_issues, key=lambda x: len(x[1]), reverse=True)[:10]:
                    print(f"{tech_name}: {', '.join(issues)}")
            
        except Exception as e:
            print(f"✗ Error showing quality report: {e}")
            sys.exit(1)
    
    def _calculate_health_score(self, technologies: List[TechEntry]) -> float:
        """Calculate overall catalog health score (0-100)."""
        if not technologies:
            return 0.0
        
        completeness = self._calculate_completeness_score(technologies)
        consistency = self._calculate_consistency_score(technologies)
        freshness = self._calculate_freshness_score(technologies)
        quality = self._calculate_quality_score(technologies)
        
        # Weighted average
        return (completeness * 0.3 + consistency * 0.25 + freshness * 0.2 + quality * 0.25)
    
    def _calculate_completeness_score(self, technologies: List[TechEntry]) -> float:
        """Calculate completeness score based on filled fields."""
        if not technologies:
            return 0.0
        
        total_score = 0
        
        for tech in technologies:
            score = 0
            
            # Required fields (40 points)
            if tech.name and tech.category and tech.description:
                score += 40
            
            # Important fields (30 points)
            if tech.integrates_with:
                score += 10
            if tech.alternatives:
                score += 10
            if tech.use_cases:
                score += 10
            
            # Nice-to-have fields (30 points)
            if tech.tags:
                score += 10
            if tech.ecosystem:
                score += 10
            if len(tech.description) > 50:  # Detailed description
                score += 10
            
            total_score += score
        
        return total_score / len(technologies)
    
    def _calculate_consistency_score(self, technologies: List[TechEntry]) -> float:
        """Calculate consistency score based on validation results."""
        validation_result = self.manager.validate_catalog_consistency()
        
        if validation_result.is_valid:
            return 100.0
        
        # Deduct points for issues
        score = 100.0
        score -= len(validation_result.errors) * 10  # 10 points per error
        score -= len(validation_result.warnings) * 5  # 5 points per warning
        
        return max(0.0, score)
    
    def _calculate_freshness_score(self, technologies: List[TechEntry]) -> float:
        """Calculate freshness score based on recent updates."""
        if not technologies:
            return 0.0
        
        now = datetime.now()
        total_score = 0
        
        for tech in technologies:
            last_update = tech.last_updated or tech.added_date
            
            if not last_update:
                score = 50  # Neutral score for unknown dates
            else:
                days_old = (now - last_update).days
                
                if days_old <= 30:
                    score = 100  # Very fresh
                elif days_old <= 90:
                    score = 80   # Fresh
                elif days_old <= 180:
                    score = 60   # Moderate
                elif days_old <= 365:
                    score = 40   # Old
                else:
                    score = 20   # Very old
            
            total_score += score
        
        return total_score / len(technologies)
    
    def _calculate_quality_score(self, technologies: List[TechEntry]) -> float:
        """Calculate quality score based on validation and confidence."""
        if not technologies:
            return 0.0
        
        total_score = 0
        
        for tech in technologies:
            score = 100
            
            # Validation issues
            validation_result = self.manager.validate_catalog_entry(tech)
            if not validation_result.is_valid:
                score -= len(validation_result.errors) * 20
            score -= len(validation_result.warnings) * 10
            
            # Confidence score
            if tech.auto_generated:
                score = score * tech.confidence_score
            
            # Pending review penalty
            if tech.pending_review:
                score *= 0.8
            
            total_score += max(0, score)
        
        return total_score / len(technologies)
    
    def _get_health_status(self, score: float) -> str:
        """Get health status string based on score."""
        if score >= 90:
            return "🟢 EXCELLENT"
        elif score >= 75:
            return "🟡 GOOD"
        elif score >= 60:
            return "🟠 FAIR"
        elif score >= 40:
            return "🔴 POOR"
        else:
            return "💀 CRITICAL"
    
    def _get_score_indicator(self, score: float) -> str:
        """Get score indicator emoji."""
        if score >= 90:
            return "🟢"
        elif score >= 75:
            return "🟡"
        elif score >= 60:
            return "🟠"
        else:
            return "🔴"
    
    def _create_bar(self, percentage: float, width: int = 20) -> str:
        """Create a text-based progress bar."""
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def _identify_health_issues(self, technologies: List[TechEntry]) -> Dict[str, List[str]]:
        """Identify health issues in the catalog."""
        issues = {
            'critical': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Critical issues
        pending_count = len([t for t in technologies if t.pending_review])
        if pending_count > 10:
            issues['critical'].append(f"{pending_count} technologies pending review")
        
        validation_errors = 0
        for tech in technologies:
            result = self.manager.validate_catalog_entry(tech)
            if not result.is_valid:
                validation_errors += 1
        
        if validation_errors > 5:
            issues['critical'].append(f"{validation_errors} technologies with validation errors")
        
        # Warnings
        low_confidence = len([t for t in technologies if t.confidence_score < 0.7])
        if low_confidence > 0:
            issues['warnings'].append(f"{low_confidence} technologies with low confidence scores")
        
        missing_descriptions = len([t for t in technologies if not t.description or len(t.description.strip()) < 20])
        if missing_descriptions > 0:
            issues['warnings'].append(f"{missing_descriptions} technologies with poor descriptions")
        
        # Suggestions
        missing_integrations = len([t for t in technologies if not t.integrates_with])
        if missing_integrations > 0:
            issues['suggestions'].append(f"{missing_integrations} technologies missing integration info")
        
        missing_use_cases = len([t for t in technologies if not t.use_cases])
        if missing_use_cases > 0:
            issues['suggestions'].append(f"{missing_use_cases} technologies missing use cases")
        
        return issues
    
    def _show_recent_activity(self, technologies: List[TechEntry]) -> None:
        """Show recent catalog activity."""
        now = datetime.now()
        
        # Recent additions (last 30 days)
        recent_additions = [
            t for t in technologies 
            if t.added_date and (now - t.added_date).days <= 30
        ]
        
        # Recent updates (last 30 days)
        recent_updates = [
            t for t in technologies 
            if t.last_updated and (now - t.last_updated).days <= 30
        ]
        
        print(f"\n📅 RECENT ACTIVITY (Last 30 days)")
        print(f"New additions: {len(recent_additions)}")
        print(f"Updates: {len(recent_updates)}")
        
        if recent_additions:
            print("Recent additions:")
            for tech in sorted(recent_additions, key=lambda t: t.added_date, reverse=True)[:5]:
                days_ago = (now - tech.added_date).days
                print(f"  • {tech.name} ({days_ago} days ago)")
    
    def _show_quality_metrics(self, technologies: List[TechEntry]) -> None:
        """Show quality metrics summary."""
        total = len(technologies)
        
        # Quality indicators
        complete_entries = len([
            t for t in technologies 
            if t.description and t.integrates_with and t.use_cases
        ])
        
        high_confidence = len([t for t in technologies if t.confidence_score >= 0.8])
        validated_entries = len([
            t for t in technologies 
            if self.manager.validate_catalog_entry(t).is_valid
        ])
        
        print(f"\n⭐ QUALITY METRICS")
        print(f"Complete entries: {complete_entries}/{total} ({(complete_entries/total)*100:.1f}%)")
        print(f"High confidence: {high_confidence}/{total} ({(high_confidence/total)*100:.1f}%)")
        print(f"Validated: {validated_entries}/{total} ({(validated_entries/total)*100:.1f}%)")
    
    def _show_recommendations(self, technologies: List[TechEntry], stats) -> None:
        """Show actionable recommendations."""
        recommendations = []
        
        if stats.pending_review > 0:
            recommendations.append(f"Review {stats.pending_review} pending technologies")
        
        if stats.validation_errors > 0:
            recommendations.append(f"Fix {stats.validation_errors} validation errors")
        
        missing_descriptions = len([t for t in technologies if not t.description or len(t.description.strip()) < 20])
        if missing_descriptions > 0:
            recommendations.append(f"Improve descriptions for {missing_descriptions} technologies")
        
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"{i}. {rec}")
    
    def _show_growth_trends(self, technologies: List[TechEntry]) -> None:
        """Show catalog growth trends."""
        # Group by month
        monthly_additions = defaultdict(int)
        
        for tech in technologies:
            if tech.added_date:
                month_key = tech.added_date.strftime("%Y-%m")
                monthly_additions[month_key] += 1
        
        print(f"\n📈 GROWTH TRENDS")
        
        if monthly_additions:
            recent_months = sorted(monthly_additions.keys())[-6:]  # Last 6 months
            
            for month in recent_months:
                count = monthly_additions[month]
                bar = self._create_bar((count / max(monthly_additions.values())) * 100, 20)
                print(f"{month}: {count:>3} {bar}")
    
    def _show_usage_patterns(self, technologies: List[TechEntry]) -> None:
        """Show technology usage patterns."""
        # Most mentioned technologies
        mentioned_techs = [(t.name, t.mention_count) for t in technologies if t.mention_count > 0]
        mentioned_techs.sort(key=lambda x: x[1], reverse=True)
        
        # Most selected technologies
        selected_techs = [(t.name, t.selection_count) for t in technologies if t.selection_count > 0]
        selected_techs.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n📊 USAGE PATTERNS")
        
        if mentioned_techs:
            print("Most mentioned:")
            for name, count in mentioned_techs[:5]:
                print(f"  {name}: {count} mentions")
        
        if selected_techs:
            print("Most selected:")
            for name, count in selected_techs[:5]:
                print(f"  {name}: {count} selections")
    
    def _show_review_trends(self, technologies: List[TechEntry]) -> None:
        """Show review queue trends."""
        pending_by_status = Counter(t.review_status.value for t in technologies if t.pending_review)
        
        print(f"\n👥 REVIEW QUEUE")
        
        for status, count in pending_by_status.most_common():
            print(f"{status}: {count}")
    
    def _show_popularity_metrics(self, technologies: List[TechEntry]) -> None:
        """Show technology popularity metrics."""
        # Calculate popularity score (mentions + selections)
        popularity_scores = []
        
        for tech in technologies:
            score = tech.mention_count + (tech.selection_count * 2)  # Weight selections more
            if score > 0:
                popularity_scores.append((tech.name, score))
        
        popularity_scores.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n🌟 POPULARITY RANKINGS")
        
        for i, (name, score) in enumerate(popularity_scores[:10], 1):
            print(f"{i:>2}. {name:<25} (score: {score})")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Catalog Statistics and Health Monitoring Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show overview dashboard
  python -m app.cli.catalog_dashboard overview
  
  # Show detailed health report
  python -m app.cli.catalog_dashboard health
  
  # Show trends and analytics
  python -m app.cli.catalog_dashboard trends
  
  # Show quality report
  python -m app.cli.catalog_dashboard quality
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Overview command
    overview_parser = subparsers.add_parser('overview', help='Show catalog overview dashboard')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Show detailed health report')
    
    # Trends command
    trends_parser = subparsers.add_parser('trends', help='Show trends and analytics')
    
    # Quality command
    quality_parser = subparsers.add_parser('quality', help='Show detailed quality report')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    dashboard = CatalogDashboard()
    
    # Route to appropriate command handler
    if args.command == 'overview':
        dashboard.show_overview(args)
    elif args.command == 'health':
        dashboard.show_health_report(args)
    elif args.command == 'trends':
        dashboard.show_trends(args)
    elif args.command == 'quality':
        dashboard.show_quality_report(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()