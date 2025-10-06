"""
Enhanced Pattern Loader Service

Provides advanced pattern loading capabilities with analytics, caching,
and enhanced pattern matching features.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service


class EnhancedPatternLoader(ConfigurableService):
    """
    Enhanced pattern loader with analytics and advanced features.
    
    Extends the basic pattern loader with:
    - Pattern usage analytics
    - Performance metrics
    - Enhanced caching
    - Pattern validation
    - Dynamic pattern updates
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'EnhancedPatternLoader')
        
        # Initialize logger
        try:
            self.logger = require_service('logger', context='EnhancedPatternLoader')
        except Exception:
            import logging
            self.logger = logging.getLogger('EnhancedPatternLoader')
        
        # Configuration
        self.config = {
            'pattern_library_path': './data/patterns',
            'enable_analytics': True,
            'enable_caching': True,
            'cache_ttl_seconds': 3600,
            'enable_validation': True,
            'auto_reload': False,
            'performance_tracking': True,
            **(config or {})
        }
        
        # Pattern storage
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.pattern_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Analytics data
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        
        # Cache service
        self.cache_service = None
        
        # Basic pattern loader
        self.basic_loader = None
    
    def _do_initialize(self) -> None:
        """Initialize the enhanced pattern loader."""
        try:
            # Get cache service if available
            self.cache_service = optional_service('cache', context='EnhancedPatternLoader')
            
            # Get basic pattern loader
            self.basic_loader = optional_service('pattern_loader', context='EnhancedPatternLoader')
            
            # Load patterns synchronously
            self._load_patterns_sync()
            
            self.logger.info("Enhanced pattern loader initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced pattern loader: {e}")
            raise
    
    def _do_shutdown(self) -> None:
        """Shutdown the enhanced pattern loader."""
        try:
            self.logger.info("Shutting down enhanced pattern loader")
            
            # Clear pattern data
            self.patterns.clear()
            self.pattern_metadata.clear()
            self.usage_stats.clear()
            self.performance_metrics.clear()
            
            # Clear service references
            self.cache_service = None
            self.basic_loader = None
            
            self.logger.info("Enhanced pattern loader shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during enhanced pattern loader shutdown: {e}")
    
    def _load_patterns_sync(self) -> None:
        """Load patterns from the pattern library (synchronous version)."""
        try:
            pattern_path = Path(self.config['pattern_library_path'])
            
            if not pattern_path.exists():
                self.logger.warning(f"Pattern library path does not exist: {pattern_path}")
                return
            
            # Load patterns from JSON files
            pattern_files = list(pattern_path.glob("*.json"))
            
            for pattern_file in pattern_files:
                # Skip deleted patterns (files that start with .deleted_)
                if pattern_file.name.startswith('.deleted_'):
                    self.logger.debug(f"Skipping deleted pattern file: {pattern_file.name}")
                    continue
                
                # Only load files that match the PAT-*, APAT-*, or TRAD-* pattern
                if not (pattern_file.name.startswith('PAT-') or 
                       pattern_file.name.startswith('APAT-') or
                       pattern_file.name.startswith('TRAD-')):
                    self.logger.debug(f"Skipping non-pattern file: {pattern_file.name}")
                    continue
                
                try:
                    with open(pattern_file, 'r', encoding='utf-8') as f:
                        pattern_data = json.load(f)
                    
                    pattern_id = pattern_data.get('pattern_id', pattern_data.get('id', pattern_file.stem))
                    
                    # Add capabilities analysis to each pattern
                    pattern_data['_capabilities'] = self._analyze_pattern_capabilities(pattern_data)
                    
                    self.patterns[pattern_id] = pattern_data
                    
                    # Initialize metadata
                    self.pattern_metadata[pattern_id] = {
                        'file_path': str(pattern_file),
                        'loaded_at': datetime.now().isoformat(),
                        'file_size': pattern_file.stat().st_size,
                        'last_modified': datetime.fromtimestamp(pattern_file.stat().st_mtime).isoformat()
                    }
                    
                    # Initialize usage stats
                    self.usage_stats[pattern_id] = {
                        'access_count': 0,
                        'last_accessed': None,
                        'match_count': 0,
                        'success_rate': 0.0
                    }
                    
                except Exception as e:
                    self.logger.error(f"Failed to load pattern from {pattern_file}: {e}")
            
            self.logger.info(f"Loaded {len(self.patterns)} patterns from {len(pattern_files)} files")
            
        except Exception as e:
            self.logger.error(f"Failed to load patterns: {e}")
            raise
    
    async def _load_patterns(self) -> None:
        """Load patterns from the pattern library (async version)."""
        self._load_patterns_sync()
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a pattern by ID with analytics tracking.
        
        Args:
            pattern_id: Pattern identifier
            
        Returns:
            Pattern data if found, None otherwise
        """
        start_time = time.time()
        
        try:
            # Check cache first if enabled
            if self.config['enable_caching'] and self.cache_service:
                cache_key = f"pattern:{pattern_id}"
                cached_pattern = self.cache_service.get(cache_key)
                if cached_pattern:
                    self._track_pattern_access(pattern_id, time.time() - start_time, True)
                    return cached_pattern
            
            # Get from memory
            pattern = self.patterns.get(pattern_id)
            
            if pattern:
                # Cache if enabled
                if self.config['enable_caching'] and self.cache_service:
                    cache_key = f"pattern:{pattern_id}"
                    self.cache_service.set(cache_key, pattern, ttl=self.config['cache_ttl_seconds'])
                
                # Track access
                self._track_pattern_access(pattern_id, time.time() - start_time, True)
                
                return pattern
            else:
                self._track_pattern_access(pattern_id, time.time() - start_time, False)
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting pattern {pattern_id}: {e}")
            self._track_pattern_access(pattern_id, time.time() - start_time, False)
            return None
    
    def load_patterns(self) -> List[Dict[str, Any]]:
        """
        Load and return all patterns (compatibility method).
        
        Returns:
            List of all pattern data
        """
        return list(self.patterns.values())
    
    def list_patterns(self) -> List[str]:
        """
        Get list of all available pattern IDs.
        
        Returns:
            List of pattern identifiers
        """
        return list(self.patterns.keys())
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a pattern by ID (compatibility method).
        
        Args:
            pattern_id: Pattern identifier
            
        Returns:
            Pattern data if found, None otherwise
        """
        return self.get_pattern(pattern_id)
    
    def get_pattern_metadata(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a pattern.
        
        Args:
            pattern_id: Pattern identifier
            
        Returns:
            Pattern metadata if found, None otherwise
        """
        return self.pattern_metadata.get(pattern_id)
    
    def get_patterns_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get all patterns for a specific domain (compatibility method).
        
        Args:
            domain: Domain to filter by
            
        Returns:
            List of patterns in the specified domain
        """
        return [pattern for pattern in self.patterns.values() 
                if pattern.get('domain') == domain]
    
    def get_patterns_by_type(self, pattern_type: str) -> List[Dict[str, Any]]:
        """
        Get all patterns that include a specific type (compatibility method).
        
        Args:
            pattern_type: Pattern type to filter by
            
        Returns:
            List of patterns of the specified type
        """
        return [pattern for pattern in self.patterns.values() 
                if pattern_type in pattern.get('pattern_type', [])]
    
    def get_patterns_by_feasibility(self, feasibility: str) -> List[Dict[str, Any]]:
        """
        Get all patterns with a specific feasibility level (compatibility method).
        
        Args:
            feasibility: Feasibility level to filter by
            
        Returns:
            List of patterns with the specified feasibility level
        """
        return [pattern for pattern in self.patterns.values() 
                if pattern.get('feasibility') == feasibility]
    
    def save_pattern(self, pattern: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Save a pattern to the library (compatibility method).
        
        Args:
            pattern: Pattern data to save
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate pattern first
            is_valid, errors = self.validate_pattern(pattern)
            if not is_valid:
                error_msg = f"Pattern validation failed: {'; '.join(errors)}"
                self.logger.error(error_msg)
                return False, error_msg
            
            # Get pattern ID
            pattern_id = pattern.get('pattern_id', pattern.get('id', 'unknown'))
            
            # Save to file
            pattern_path = Path(self.config['pattern_library_path'])
            pattern_path.mkdir(parents=True, exist_ok=True)
            
            file_path = pattern_path / f"{pattern_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(pattern, f, indent=2)
            
            # Add to internal storage
            self.patterns[pattern_id] = pattern
            
            # Initialize metadata
            self.pattern_metadata[pattern_id] = {
                'file_path': str(file_path),
                'loaded_at': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size,
                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
            # Initialize usage stats
            self.usage_stats[pattern_id] = {
                'access_count': 0,
                'last_accessed': None,
                'match_count': 0,
                'success_rate': 0.0
            }
            
            success_msg = f"Pattern {pattern_id} saved successfully"
            self.logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Failed to save pattern: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def refresh_cache(self) -> None:
        """
        Clear the pattern cache to force reload (compatibility method).
        """
        try:
            # Store current pattern IDs for cache clearing
            current_pattern_ids = list(self.patterns.keys())
            
            # Clear internal caches
            self.patterns.clear()
            self.pattern_metadata.clear()
            self.usage_stats.clear()
            
            # Clear external cache if available
            if self.cache_service:
                # Clear all pattern-related cache entries
                for pattern_id in current_pattern_ids:
                    cache_key = f"pattern:{pattern_id}"
                    try:
                        self.cache_service.delete(cache_key)
                    except Exception:
                        pass  # Ignore cache deletion errors
            
            # Reload patterns synchronously
            try:
                self._load_patterns_sync()
            except Exception as e:
                self.logger.error(f"Error reloading patterns: {e}")
            
            self.logger.info("Pattern cache cleared and reloaded")
            
        except Exception as e:
            self.logger.error(f"Error clearing pattern cache: {e}")
    
    def get_usage_stats(self, pattern_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for patterns.
        
        Args:
            pattern_id: Specific pattern ID, or None for all patterns
            
        Returns:
            Usage statistics
        """
        if pattern_id:
            return self.usage_stats.get(pattern_id, {})
        else:
            return dict(self.usage_stats)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the pattern loader.
        
        Returns:
            Performance metrics including response times and cache hit rates
        """
        metrics = {}
        
        # Calculate average response times
        for pattern_id, times in self.performance_metrics.items():
            if times:
                metrics[pattern_id] = {
                    'avg_response_time_ms': sum(times) / len(times) * 1000,
                    'min_response_time_ms': min(times) * 1000,
                    'max_response_time_ms': max(times) * 1000,
                    'total_requests': len(times)
                }
        
        # Overall statistics
        all_times = [time for times in self.performance_metrics.values() for time in times]
        if all_times:
            metrics['overall'] = {
                'avg_response_time_ms': sum(all_times) / len(all_times) * 1000,
                'total_requests': len(all_times),
                'patterns_loaded': len(self.patterns)
            }
        
        return metrics
    
    def search_patterns(self, query: str, pattern_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search patterns by query and optional type filter.
        
        Args:
            query: Search query
            pattern_type: Optional pattern type filter
            
        Returns:
            List of matching patterns with relevance scores
        """
        results = []
        query_lower = query.lower()
        
        for pattern_id, pattern in self.patterns.items():
            score = 0.0
            
            # Check title match
            title = pattern.get('title', '').lower()
            if query_lower in title:
                score += 2.0
            
            # Check description match
            description = pattern.get('description', '').lower()
            if query_lower in description:
                score += 1.0
            
            # Check tags match
            tags = pattern.get('tags', [])
            for tag in tags:
                if query_lower in tag.lower():
                    score += 1.5
            
            # Check pattern type filter
            if pattern_type and pattern.get('type') != pattern_type:
                continue
            
            if score > 0:
                results.append({
                    'pattern_id': pattern_id,
                    'pattern': pattern,
                    'relevance_score': score
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results
    
    def validate_pattern(self, pattern_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate pattern data structure.
        
        Args:
            pattern_data: Pattern data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Required fields
        required_fields = ['id', 'title', 'description', 'type']
        for field in required_fields:
            if field not in pattern_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate pattern type
        valid_types = ['APAT', 'PAT', 'TRAD-AUTO']
        pattern_type = pattern_data.get('type')
        if pattern_type and pattern_type not in valid_types:
            errors.append(f"Invalid pattern type: {pattern_type}. Must be one of: {valid_types}")
        
        # Validate autonomy level for APAT patterns
        if pattern_type == 'APAT':
            autonomy_level = pattern_data.get('autonomy_level')
            if autonomy_level is None:
                errors.append("APAT patterns must have autonomy_level")
            elif not isinstance(autonomy_level, (int, float)) or not (0.0 <= autonomy_level <= 1.0):
                errors.append("autonomy_level must be a number between 0.0 and 1.0")
        
        return len(errors) == 0, errors
    
    def _track_pattern_access(self, pattern_id: str, response_time: float, success: bool) -> None:
        """Track pattern access for analytics."""
        if not self.config['enable_analytics']:
            return
        
        try:
            # Update usage stats
            if pattern_id not in self.usage_stats:
                self.usage_stats[pattern_id] = {
                    'access_count': 0,
                    'last_accessed': None,
                    'match_count': 0,
                    'success_rate': 0.0
                }
            
            stats = self.usage_stats[pattern_id]
            stats['access_count'] += 1
            stats['last_accessed'] = datetime.now().isoformat()
            
            if success:
                stats['match_count'] += 1
            
            stats['success_rate'] = stats['match_count'] / stats['access_count']
            
            # Track performance metrics
            if self.config['performance_tracking']:
                if pattern_id not in self.performance_metrics:
                    self.performance_metrics[pattern_id] = []
                
                self.performance_metrics[pattern_id].append(response_time)
                
                # Keep only last 100 measurements
                if len(self.performance_metrics[pattern_id]) > 100:
                    self.performance_metrics[pattern_id] = self.performance_metrics[pattern_id][-100:]
        
        except Exception as e:
            self.logger.error(f"Error tracking pattern access: {e}")
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        Get pattern statistics for UI display (compatibility method).
        
        Returns:
            Pattern statistics including counts, types, and complexity data
        """
        try:
            patterns = list(self.patterns.values())
            
            if not patterns:
                return {
                    'total_patterns': 0,
                    'pattern_types': {},
                    'by_type': {},
                    'domains': {},
                    'complexity_scores': [],
                    'feasibility_levels': {},
                    'autonomy_levels': [],
                    'avg_complexity': 0.0,
                    'avg_autonomy': 0.0,
                    'capabilities': {
                        'has_agentic_features': 0,
                        'has_detailed_tech_stack': 0,
                        'has_implementation_guidance': 0
                    }
                }
            
            # Count patterns by type
            pattern_types = {}
            for pattern in patterns:
                # Handle both 'type' (string) and 'pattern_type' (array) fields
                pattern_type = pattern.get('type')
                if not pattern_type:
                    # Check for pattern_type array
                    pattern_type_array = pattern.get('pattern_type', [])
                    if isinstance(pattern_type_array, list) and pattern_type_array:
                        pattern_type = pattern_type_array[0]  # Use first type
                    else:
                        pattern_type = 'Unknown'
                
                # Determine pattern category based on pattern_id prefix
                pattern_id = pattern.get('pattern_id', '')
                if pattern_id.startswith('APAT-'):
                    pattern_category = 'APAT'
                elif pattern_id.startswith('PAT-'):
                    pattern_category = 'PAT'
                elif pattern_id.startswith('TRAD-'):
                    pattern_category = 'TRAD-AUTO'
                else:
                    pattern_category = pattern_type
                
                pattern_types[pattern_category] = pattern_types.get(pattern_category, 0) + 1
            
            # Count patterns by domain
            domains = {}
            for pattern in patterns:
                domain = pattern.get('domain', 'Unknown')
                domains[domain] = domains.get(domain, 0) + 1
            
            # Count patterns by feasibility
            feasibility_levels = {}
            for pattern in patterns:
                feasibility = pattern.get('feasibility', 'Unknown')
                feasibility_levels[feasibility] = feasibility_levels.get(feasibility, 0) + 1
            
            # Extract complexity scores
            complexity_scores = []
            for pattern in patterns:
                complexity = pattern.get('_complexity_score', pattern.get('complexity_score', 0.5))
                if isinstance(complexity, (int, float)):
                    complexity_scores.append(float(complexity))
                else:
                    complexity_scores.append(0.5)  # Default complexity
            
            # Extract autonomy levels (for APAT patterns)
            autonomy_levels = []
            for pattern in patterns:
                pattern_id = pattern.get('pattern_id', '')
                # Check if this is an APAT pattern by ID or type
                is_apat = (pattern_id.startswith('APAT-') or 
                          pattern.get('type') == 'APAT' or
                          'APAT' in pattern.get('pattern_type', []))
                
                if is_apat:
                    autonomy = pattern.get('autonomy_level')
                    if isinstance(autonomy, (int, float)):
                        autonomy_levels.append(float(autonomy))
            
            # Calculate averages
            avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.0
            avg_autonomy = sum(autonomy_levels) / len(autonomy_levels) if autonomy_levels else 0.0
            
            # Calculate capabilities
            capabilities = {
                'has_agentic_features': 0,
                'has_detailed_tech_stack': 0,
                'has_implementation_guidance': 0
            }
            
            for pattern in patterns:
                # Check for agentic features
                pattern_id = pattern.get('pattern_id', '')
                if (pattern_id.startswith('APAT-') or 
                    pattern.get('autonomy_level') is not None or
                    pattern.get('reasoning_types') or
                    pattern.get('decision_boundaries')):
                    capabilities['has_agentic_features'] += 1
                
                # Check for detailed tech stack
                tech_stack = pattern.get('tech_stack', {})
                if (isinstance(tech_stack, dict) and tech_stack.get('core_technologies') or
                    isinstance(tech_stack, list) and len(tech_stack) > 0):
                    capabilities['has_detailed_tech_stack'] += 1
                
                # Check for implementation guidance
                if (pattern.get('implementation_guidance') or
                    pattern.get('llm_recommended_approach') or
                    pattern.get('estimated_effort')):
                    capabilities['has_implementation_guidance'] += 1
            
            return {
                'total_patterns': len(patterns),
                'pattern_types': pattern_types,
                'by_type': pattern_types,  # Alias for UI compatibility
                'domains': domains,
                'complexity_scores': complexity_scores,
                'feasibility_levels': feasibility_levels,
                'autonomy_levels': autonomy_levels,
                'avg_complexity': avg_complexity,
                'avg_autonomy': avg_autonomy,
                'capabilities': capabilities
            }
            
        except Exception as e:
            self.logger.error(f"Error generating pattern statistics: {e}")
            return {
                'total_patterns': 0,
                'pattern_types': {},
                'by_type': {},
                'domains': {},
                'complexity_scores': [],
                'feasibility_levels': {},
                'autonomy_levels': [],
                'avg_complexity': 0.0,
                'avg_autonomy': 0.0,
                'capabilities': {
                    'has_agentic_features': 0,
                    'has_detailed_tech_stack': 0,
                    'has_implementation_guidance': 0
                }
            }
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics summary.
        
        Returns:
            Analytics summary with usage patterns and performance data
        """
        try:
            total_patterns = len(self.patterns)
            total_accesses = sum(stats['access_count'] for stats in self.usage_stats.values())
            
            # Most accessed patterns
            most_accessed = sorted(
                [(pid, stats['access_count']) for pid, stats in self.usage_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Performance summary
            performance_summary = self.get_performance_metrics()
            
            return {
                'total_patterns': total_patterns,
                'total_accesses': total_accesses,
                'most_accessed_patterns': most_accessed,
                'performance_metrics': performance_summary,
                'cache_enabled': self.config['enable_caching'],
                'analytics_enabled': self.config['enable_analytics']
            }
            
        except Exception as e:
            self.logger.error(f"Error generating analytics summary: {e}")
            return {}
    
    def _analyze_pattern_capabilities(self, pattern: Dict[str, Any]) -> Dict[str, bool]:
        """
        Analyze individual pattern capabilities with proper differentiation.
        
        Args:
            pattern: Pattern data to analyze
            
        Returns:
            Dictionary of capability flags
        """
        try:
            capabilities = {}
            pattern_id = pattern.get('pattern_id', '')
            
            # Check for agentic features (more sophisticated analysis)
            agentic_score = 0
            
            # Strong indicators of agentic capabilities
            if pattern_id.startswith('APAT-'):
                agentic_score += 4  # Strong indicator
            
            # Autonomy level indicates agentic capability (stricter thresholds)
            autonomy_level = pattern.get('autonomy_level')
            if autonomy_level is not None and autonomy_level > 0.8:
                agentic_score += 3
            elif autonomy_level is not None and autonomy_level > 0.6:
                agentic_score += 2
            elif autonomy_level is not None and autonomy_level > 0.4:
                agentic_score += 1
            
            # Advanced reasoning capabilities (stricter requirements)
            reasoning_types = pattern.get('reasoning_types', [])
            if reasoning_types and len(reasoning_types) > 2 and autonomy_level and autonomy_level > 0.6:
                agentic_score += 2
            elif reasoning_types and autonomy_level and autonomy_level > 0.4:
                agentic_score += 1
            
            # Decision boundaries indicate autonomous decision making (with autonomy check)
            decision_boundaries = pattern.get('decision_boundaries', {})
            if (decision_boundaries and 
                decision_boundaries.get('decision_authority_level') in ['high', 'medium'] and
                autonomy_level and autonomy_level > 0.6):
                agentic_score += 2
            elif decision_boundaries and autonomy_level and autonomy_level > 0.4:
                agentic_score += 1
            
            # Exception handling strategy indicates sophisticated reasoning
            exception_handling = pattern.get('exception_handling_strategy', {})
            if (exception_handling and 
                len(exception_handling.get('autonomous_resolution_approaches', [])) > 2 and
                autonomy_level and autonomy_level > 0.6):
                agentic_score += 1
            
            # Learning mechanisms indicate adaptive behavior (requires high autonomy)
            learning_mechanisms = pattern.get('learning_mechanisms', [])
            if (learning_mechanisms and 
                len(learning_mechanisms) > 2 and
                autonomy_level and autonomy_level > 0.7):
                agentic_score += 1
            
            # Agentic frameworks (requires decent autonomy)
            agentic_frameworks = pattern.get('agentic_frameworks', [])
            if agentic_frameworks and autonomy_level and autonomy_level > 0.5:
                agentic_score += 1
            
            # Set agentic features based on score (higher threshold for true agentic capability)
            capabilities['has_agentic_features'] = agentic_score >= 4
            
            # Check for detailed tech stack (more nuanced analysis)
            tech_stack = pattern.get('tech_stack', {})
            tech_stack_score = 0
            
            if isinstance(tech_stack, dict):
                # Structured tech stack with categories
                core_techs = tech_stack.get('core_technologies', [])
                data_processing = tech_stack.get('data_processing', [])
                infrastructure = tech_stack.get('infrastructure', [])
                integration_apis = tech_stack.get('integration_apis', [])
                
                total_techs = len(core_techs) + len(data_processing) + len(infrastructure) + len(integration_apis)
                if total_techs > 5:
                    tech_stack_score = 3
                elif total_techs > 2:
                    tech_stack_score = 2
                elif total_techs > 0:
                    tech_stack_score = 1
                    
            elif isinstance(tech_stack, list):
                # Simple list of technologies
                if len(tech_stack) > 8:
                    tech_stack_score = 3
                elif len(tech_stack) > 4:
                    tech_stack_score = 2
                elif len(tech_stack) > 0:
                    tech_stack_score = 1
            
            capabilities['has_detailed_tech_stack'] = tech_stack_score >= 2
            
            # Check for implementation guidance (more specific)
            guidance_score = 0
            
            if pattern.get('implementation_guidance'):
                guidance_score += 2
            
            if pattern.get('llm_recommended_approach'):
                guidance_score += 2
            
            if pattern.get('llm_insights'):
                guidance_score += 1
            
            if pattern.get('llm_challenges'):
                guidance_score += 1
            
            if pattern.get('architecture_decisions'):
                guidance_score += 1
            
            capabilities['has_implementation_guidance'] = guidance_score >= 2
            
            # Check for detailed effort breakdown (more comprehensive)
            effort_score = 0
            
            if pattern.get('estimated_effort'):
                effort_score += 2
            
            if pattern.get('complexity') and pattern.get('complexity') != 'Unknown':
                effort_score += 1
            
            if pattern.get('confidence_score') is not None:
                effort_score += 1
            
            # Check for detailed constraints and requirements
            constraints = pattern.get('constraints', {})
            if constraints and (constraints.get('banned_tools') or constraints.get('required_integrations')):
                effort_score += 1
            
            # Check for detailed pattern types
            pattern_types = pattern.get('pattern_type', [])
            if isinstance(pattern_types, list) and len(pattern_types) > 2:
                effort_score += 1
            
            capabilities['has_detailed_effort_breakdown'] = effort_score >= 2
            
            # Add complexity score for UI display
            if pattern_id.startswith('APAT-'):
                complexity_base = 0.7
            elif pattern_id.startswith('PAT-'):
                complexity_base = 0.5
            elif pattern_id.startswith('TRAD-'):
                complexity_base = 0.3
            else:
                complexity_base = 0.5
            
            # Adjust based on actual complexity indicators
            complexity_adjustments = 0
            if autonomy_level and autonomy_level > 0.8:
                complexity_adjustments += 0.2
            if tech_stack_score >= 3:
                complexity_adjustments += 0.1
            if guidance_score >= 3:
                complexity_adjustments += 0.1
            
            pattern['_complexity_score'] = min(1.0, complexity_base + complexity_adjustments)
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"Error analyzing pattern capabilities: {e}")
            return {
                'has_agentic_features': False,
                'has_detailed_tech_stack': False,
                'has_implementation_guidance': False,
                'has_detailed_effort_breakdown': False
            }
    
    def health_check(self) -> bool:
        """Check service health."""
        try:
            # Check if patterns are loaded
            if not self.patterns:
                return False
            
            # Check if pattern files are accessible
            pattern_path = Path(self.config['pattern_library_path'])
            if not pattern_path.exists():
                return False
            
            return True
            
        except Exception:
            return False