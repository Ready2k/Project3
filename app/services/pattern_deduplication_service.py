"""Pattern deduplication service to prevent storing identical patterns."""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass
from app.utils.imports import require_service


@dataclass
class PatternSimilarity:
    """Represents similarity between two patterns."""
    pattern_id_1: str
    pattern_id_2: str
    tech_stack_similarity: float
    pattern_type_similarity: float
    overall_similarity: float
    is_duplicate: bool
    recommended_action: str


class PatternDeduplicationService:
    """Service to detect and handle duplicate patterns."""
    
    def __init__(self, pattern_library_path: Path):
        """Initialize the deduplication service.
        
        Args:
            pattern_library_path: Path to pattern library directory
        """
        self.pattern_library_path = pattern_library_path
        try:
            self.logger = require_service("logger", context="PatternDeduplicationService")
        except Exception:
            # Fallback to basic logging if service registry not available
            import logging
            self.logger = logging.getLogger(__name__)
        
        # Similarity thresholds
        self.duplicate_threshold = 0.95  # 95% similarity = duplicate
        self.high_similarity_threshold = 0.85  # 85% similarity = high similarity
        
    def calculate_tech_stack_similarity(self, stack1: List[str], stack2: List[str]) -> float:
        """Calculate similarity between two tech stacks.
        
        Args:
            stack1: First tech stack
            stack2: Second tech stack
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not stack1 and not stack2:
            return 1.0
        
        if not stack1 or not stack2:
            return 0.0
            
        # Normalize tech stack items (lowercase, strip whitespace)
        set1 = {tech.lower().strip() for tech in stack1}
        set2 = {tech.lower().strip() for tech in stack2}
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_pattern_type_similarity(self, types1: List[str], types2: List[str]) -> float:
        """Calculate similarity between two pattern type lists.
        
        Args:
            types1: First pattern types
            types2: Second pattern types
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not types1 and not types2:
            return 1.0
            
        if not types1 or not types2:
            return 0.0
            
        # Normalize pattern types
        set1 = {ptype.lower().strip() for ptype in types1}
        set2 = {ptype.lower().strip() for ptype in types2}
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_overall_similarity(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> PatternSimilarity:
        """Calculate overall similarity between two patterns.
        
        Args:
            pattern1: First pattern
            pattern2: Second pattern
            
        Returns:
            PatternSimilarity object with detailed similarity metrics
        """
        # Get tech stacks
        tech_stack1 = pattern1.get('tech_stack', [])
        tech_stack2 = pattern2.get('tech_stack', [])
        tech_similarity = self.calculate_tech_stack_similarity(tech_stack1, tech_stack2)
        
        # Get pattern types
        types1 = pattern1.get('pattern_type', [])
        types2 = pattern2.get('pattern_type', [])
        type_similarity = self.calculate_pattern_type_similarity(types1, types2)
        
        # Calculate weighted overall similarity
        # Tech stack and pattern types are most important for determining duplicates
        tech_weight = 0.5
        type_weight = 0.5
        
        overall_similarity = (tech_similarity * tech_weight + type_similarity * type_weight)
        
        # Additional factors that could indicate duplicates
        domain1 = pattern1.get('domain', '').lower().strip()
        domain2 = pattern2.get('domain', '').lower().strip()
        same_domain = domain1 == domain2 and domain1 != ''
        
        feasibility1 = pattern1.get('feasibility', '').lower().strip()
        feasibility2 = pattern2.get('feasibility', '').lower().strip()
        same_feasibility = feasibility1 == feasibility2
        
        # Boost similarity if domain and feasibility match
        if same_domain and same_feasibility:
            overall_similarity = min(1.0, overall_similarity * 1.1)
        
        # Determine if it's a duplicate
        is_duplicate = overall_similarity >= self.duplicate_threshold
        
        # Recommend action
        if is_duplicate:
            recommended_action = "merge_patterns"
        elif overall_similarity >= self.high_similarity_threshold:
            recommended_action = "review_similarity"
        else:
            recommended_action = "keep_separate"
        
        return PatternSimilarity(
            pattern_id_1=pattern1.get('pattern_id', ''),
            pattern_id_2=pattern2.get('pattern_id', ''),
            tech_stack_similarity=tech_similarity,
            pattern_type_similarity=type_similarity,
            overall_similarity=overall_similarity,
            is_duplicate=is_duplicate,
            recommended_action=recommended_action
        )
    
    def find_all_duplicates(self) -> List[PatternSimilarity]:
        """Find all duplicate patterns in the library.
        
        Returns:
            List of PatternSimilarity objects for all pattern pairs
        """
        duplicates = []
        
        try:
            # Load all patterns
            patterns = []
            for pattern_file in self.pattern_library_path.glob("*.json"):
                try:
                    with open(pattern_file, 'r', encoding='utf-8') as f:
                        pattern = json.load(f)
                        patterns.append(pattern)
                except Exception as e:
                    self.logger.warning(f"Error reading pattern file {pattern_file}: {e}")
            
            self.logger.info(f"Analyzing {len(patterns)} patterns for duplicates")
            
            # Compare each pattern with every other pattern
            for i in range(len(patterns)):
                for j in range(i + 1, len(patterns)):
                    pattern1 = patterns[i]
                    pattern2 = patterns[j]
                    
                    similarity = self.calculate_overall_similarity(pattern1, pattern2)
                    
                    # Only include high similarity or duplicates
                    if similarity.overall_similarity >= self.high_similarity_threshold:
                        duplicates.append(similarity)
                        
                        if similarity.is_duplicate:
                            self.logger.warning(
                                f"Duplicate found: {similarity.pattern_id_1} <-> {similarity.pattern_id_2} "
                                f"(similarity: {similarity.overall_similarity:.1%})"
                            )
        
        except Exception as e:
            self.logger.error(f"Error finding duplicates: {e}")
        
        # Sort by similarity (highest first)
        duplicates.sort(key=lambda x: x.overall_similarity, reverse=True)
        
        return duplicates
    
    def check_pattern_before_save(self, new_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a new pattern is a duplicate before saving.
        
        Args:
            new_pattern: Pattern to check
            
        Returns:
            Dictionary with check results
        """
        result = {
            'is_duplicate': False,
            'similar_patterns': [],
            'should_save': True,
            'recommended_action': 'save_new_pattern',
            'message': ''
        }
        
        try:
            # Load existing patterns
            existing_patterns = []
            for pattern_file in self.pattern_library_path.glob("*.json"):
                try:
                    with open(pattern_file, 'r', encoding='utf-8') as f:
                        pattern = json.load(f)
                        existing_patterns.append(pattern)
                except Exception as e:
                    self.logger.warning(f"Error reading pattern file {pattern_file}: {e}")
            
            # Check similarity with existing patterns
            high_similarity_patterns = []
            
            for existing_pattern in existing_patterns:
                similarity = self.calculate_overall_similarity(new_pattern, existing_pattern)
                
                if similarity.is_duplicate:
                    result['is_duplicate'] = True
                    result['should_save'] = False
                    result['recommended_action'] = 'use_existing_pattern'
                    result['message'] = (
                        f"Pattern is {similarity.overall_similarity:.1%} similar to existing pattern "
                        f"{similarity.pattern_id_2}. Consider using the existing pattern instead."
                    )
                    high_similarity_patterns.append({
                        'pattern_id': existing_pattern['pattern_id'],
                        'pattern_name': existing_pattern.get('name', 'Unknown'),
                        'similarity': similarity.overall_similarity,
                        'tech_stack_similarity': similarity.tech_stack_similarity,
                        'pattern_type_similarity': similarity.pattern_type_similarity
                    })
                    break  # Found a duplicate, no need to check further
                
                elif similarity.overall_similarity >= self.high_similarity_threshold:
                    high_similarity_patterns.append({
                        'pattern_id': existing_pattern['pattern_id'],
                        'pattern_name': existing_pattern.get('name', 'Unknown'),
                        'similarity': similarity.overall_similarity,
                        'tech_stack_similarity': similarity.tech_stack_similarity,
                        'pattern_type_similarity': similarity.pattern_type_similarity
                    })
            
            result['similar_patterns'] = high_similarity_patterns
            
            if not result['is_duplicate'] and high_similarity_patterns:
                result['recommended_action'] = 'review_before_save'
                result['message'] = (
                    f"Pattern has high similarity to {len(high_similarity_patterns)} existing pattern(s). "
                    "Review for potential consolidation."
                )
        
        except Exception as e:
            self.logger.error(f"Error checking pattern for duplicates: {e}")
            result['message'] = f"Error during duplicate check: {e}"
        
        return result
    
    def merge_duplicate_patterns(self, pattern_id_1: str, pattern_id_2: str, 
                                keep_pattern_id: str) -> Dict[str, Any]:
        """Merge two duplicate patterns, keeping one and removing the other.
        
        Args:
            pattern_id_1: First pattern ID
            pattern_id_2: Second pattern ID
            keep_pattern_id: ID of pattern to keep
            
        Returns:
            Dictionary with merge results
        """
        result = {
            'success': False,
            'kept_pattern': keep_pattern_id,
            'removed_pattern': '',
            'message': ''
        }
        
        try:
            if keep_pattern_id not in [pattern_id_1, pattern_id_2]:
                result['message'] = "keep_pattern_id must be one of the two patterns being merged"
                return result
            
            remove_pattern_id = pattern_id_1 if keep_pattern_id == pattern_id_2 else pattern_id_2
            
            # Load both patterns
            keep_file = self.pattern_library_path / f"{keep_pattern_id}.json"
            remove_file = self.pattern_library_path / f"{remove_pattern_id}.json"
            
            if not keep_file.exists():
                result['message'] = f"Pattern to keep not found: {keep_pattern_id}"
                return result
                
            if not remove_file.exists():
                result['message'] = f"Pattern to remove not found: {remove_pattern_id}"
                return result
            
            # Load the pattern to keep
            with open(keep_file, 'r', encoding='utf-8') as f:
                keep_pattern = json.load(f)
            
            # Load the pattern to remove (for metadata)
            with open(remove_file, 'r', encoding='utf-8') as f:
                remove_pattern = json.load(f)
            
            # Add metadata about the merge
            if 'metadata' not in keep_pattern:
                keep_pattern['metadata'] = {}
            
            keep_pattern['metadata']['merged_from'] = remove_pattern_id
            keep_pattern['metadata']['merge_timestamp'] = str(int(time.time()))
            keep_pattern['metadata']['removed_pattern_name'] = remove_pattern.get('name', 'Unknown')
            
            # Save updated pattern
            with open(keep_file, 'w', encoding='utf-8') as f:
                json.dump(keep_pattern, f, indent=2, ensure_ascii=False)
            
            # Remove duplicate pattern file
            remove_file.unlink()
            
            result['success'] = True
            result['removed_pattern'] = remove_pattern_id
            result['message'] = f"Successfully merged {remove_pattern_id} into {keep_pattern_id}"
            
            self.logger.info(f"Merged duplicate patterns: kept {keep_pattern_id}, removed {remove_pattern_id}")
            
        except Exception as e:
            result['message'] = f"Error merging patterns: {e}"
            self.logger.error(f"Error merging patterns {pattern_id_1} and {pattern_id_2}: {e}")
        
        return result
    
    def generate_deduplication_report(self) -> Dict[str, Any]:
        """Generate a comprehensive deduplication report.
        
        Returns:
            Dictionary with deduplication analysis
        """
        duplicates = self.find_all_duplicates()
        
        # Categorize by similarity level
        exact_duplicates = [d for d in duplicates if d.overall_similarity >= 0.99]
        near_duplicates = [d for d in duplicates if 0.95 <= d.overall_similarity < 0.99]
        high_similarity = [d for d in duplicates if 0.85 <= d.overall_similarity < 0.95]
        
        report = {
            'total_comparisons': len(duplicates),
            'exact_duplicates': len(exact_duplicates),
            'near_duplicates': len(near_duplicates),
            'high_similarity': len(high_similarity),
            'recommendations': [],
            'duplicate_details': []
        }
        
        # Add recommendations
        if exact_duplicates:
            report['recommendations'].append(
                f"Remove {len(exact_duplicates)} exact duplicate patterns immediately"
            )
        
        if near_duplicates:
            report['recommendations'].append(
                f"Review {len(near_duplicates)} near-duplicate patterns for consolidation"
            )
        
        if high_similarity:
            report['recommendations'].append(
                f"Consider consolidating {len(high_similarity)} highly similar patterns"
            )
        
        # Add details for exact duplicates
        for duplicate in exact_duplicates:
            report['duplicate_details'].append({
                'pattern_1': duplicate.pattern_id_1,
                'pattern_2': duplicate.pattern_id_2,
                'similarity': f"{duplicate.overall_similarity:.1%}",
                'tech_stack_similarity': f"{duplicate.tech_stack_similarity:.1%}",
                'pattern_type_similarity': f"{duplicate.pattern_type_similarity:.1%}",
                'action': duplicate.recommended_action
            })
        
        return report