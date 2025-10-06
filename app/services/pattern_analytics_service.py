"""
Pattern Analytics Service

Provides comprehensive analytics for pattern usage, performance,
and system insights for the pattern matching system.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
import statistics

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service


class PatternAnalyticsService(ConfigurableService):
    """
    Pattern analytics service for comprehensive pattern usage analysis.
    
    Provides:
    - Pattern usage analytics
    - Performance metrics
    - Trend analysis
    - Recommendation insights
    - System health monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'PatternAnalyticsService')
        
        # Initialize logger
        try:
            self.logger = require_service('logger', context='PatternAnalyticsService')
        except Exception:
            import logging
            self.logger = logging.getLogger('PatternAnalyticsService')
        
        # Configuration
        self.config = {
            'enable_real_time_analytics': True,
            'analytics_retention_days': 30,
            'performance_window_minutes': 60,
            'trend_analysis_enabled': True,
            'export_analytics': True,
            'alert_thresholds': {
                'low_success_rate': 0.7,
                'high_response_time_ms': 1000,
                'pattern_usage_spike': 5.0
            },
            **(config or {})
        }
        
        # Analytics data storage
        self.pattern_usage_history: List[Dict[str, Any]] = []
        self.performance_history: List[Dict[str, Any]] = []
        self.recommendation_history: List[Dict[str, Any]] = []
        
        # Real-time metrics
        self.current_metrics: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []
        
        # Services
        self.enhanced_pattern_loader = None
        self.cache_service = None
    
    def _do_initialize(self) -> None:
        """Initialize the pattern analytics service."""
        try:
            # Get enhanced pattern loader
            self.enhanced_pattern_loader = optional_service('enhanced_pattern_loader', context='PatternAnalyticsService')
            
            # Get cache service
            self.cache_service = optional_service('cache', context='PatternAnalyticsService')
            
            # Initialize metrics synchronously
            self._initialize_metrics_sync()
            
            self.logger.info("Pattern analytics service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize pattern analytics service: {e}")
            raise
    
    def _do_shutdown(self) -> None:
        """Shutdown the pattern analytics service."""
        try:
            self.logger.info("Shutting down pattern analytics service")
            
            # Clear analytics data
            self.pattern_usage_history.clear()
            self.performance_history.clear()
            self.recommendation_history.clear()
            self.current_metrics.clear()
            self.alerts.clear()
            
            # Clear service references
            self.enhanced_pattern_loader = None
            self.cache_service = None
            
            self.logger.info("Pattern analytics service shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during pattern analytics service shutdown: {e}")
    
    def _initialize_metrics_sync(self) -> None:
        """Initialize analytics metrics (synchronous version)."""
        try:
            self.current_metrics = {
                'total_patterns_accessed': 0,
                'total_recommendations_generated': 0,
                'average_response_time_ms': 0.0,
                'success_rate': 0.0,
                'most_used_patterns': [],
                'performance_trends': {},
                'last_updated': datetime.now().isoformat()
            }
            
            self.logger.info("Analytics metrics initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics: {e}")
            raise
    
    async def _initialize_metrics(self) -> None:
        """Initialize analytics metrics (async version)."""
        self._initialize_metrics_sync()
    
    def track_pattern_usage(self, pattern_id: str, session_id: str, 
                           success: bool, response_time_ms: float,
                           context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track pattern usage event.
        
        Args:
            pattern_id: Pattern identifier
            session_id: Session identifier
            success: Whether the pattern usage was successful
            response_time_ms: Response time in milliseconds
            context: Additional context data
        """
        try:
            usage_event = {
                'pattern_id': pattern_id,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'response_time_ms': response_time_ms,
                'context': context or {}
            }
            
            self.pattern_usage_history.append(usage_event)
            
            # Update real-time metrics
            self._update_real_time_metrics()
            
            # Check for alerts
            self._check_alerts(usage_event)
            
            # Cleanup old data
            self._cleanup_old_data()
            
        except Exception as e:
            self.logger.error(f"Error tracking pattern usage: {e}")
    
    def track_recommendation_generation(self, session_id: str, 
                                      patterns_matched: List[str],
                                      confidence_scores: Dict[str, float],
                                      generation_time_ms: float,
                                      success: bool,
                                      context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track recommendation generation event.
        
        Args:
            session_id: Session identifier
            patterns_matched: List of matched pattern IDs
            confidence_scores: Confidence scores for each pattern
            generation_time_ms: Time taken to generate recommendations
            success: Whether recommendation generation was successful
            context: Additional context data
        """
        try:
            recommendation_event = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'patterns_matched': patterns_matched,
                'confidence_scores': confidence_scores,
                'generation_time_ms': generation_time_ms,
                'success': success,
                'context': context or {}
            }
            
            self.recommendation_history.append(recommendation_event)
            
            # Update metrics
            self._update_real_time_metrics()
            
        except Exception as e:
            self.logger.error(f"Error tracking recommendation generation: {e}")
    
    def get_usage_analytics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get pattern usage analytics for specified time window.
        
        Args:
            time_window_hours: Time window in hours
            
        Returns:
            Usage analytics data
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            
            # Filter events within time window
            recent_usage = [
                event for event in self.pattern_usage_history
                if datetime.fromisoformat(event['timestamp']) >= cutoff_time
            ]
            
            if not recent_usage:
                return {
                    'time_window_hours': time_window_hours,
                    'total_events': 0,
                    'patterns_used': [],
                    'success_rate': 0.0,
                    'average_response_time_ms': 0.0
                }
            
            # Calculate metrics
            total_events = len(recent_usage)
            successful_events = sum(1 for event in recent_usage if event['success'])
            success_rate = successful_events / total_events if total_events > 0 else 0.0
            
            response_times = [event['response_time_ms'] for event in recent_usage]
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            
            # Pattern usage frequency
            pattern_usage = Counter(event['pattern_id'] for event in recent_usage)
            most_used_patterns = pattern_usage.most_common(10)
            
            # Hourly distribution
            hourly_usage = defaultdict(int)
            for event in recent_usage:
                hour = datetime.fromisoformat(event['timestamp']).hour
                hourly_usage[hour] += 1
            
            return {
                'time_window_hours': time_window_hours,
                'total_events': total_events,
                'success_rate': success_rate,
                'average_response_time_ms': avg_response_time,
                'most_used_patterns': most_used_patterns,
                'hourly_distribution': dict(hourly_usage),
                'performance_percentiles': {
                    'p50': statistics.median(response_times) if response_times else 0.0,
                    'p95': self._percentile(response_times, 0.95) if response_times else 0.0,
                    'p99': self._percentile(response_times, 0.99) if response_times else 0.0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage analytics: {e}")
            return {}
    
    def get_performance_analytics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get performance analytics for specified time window.
        
        Args:
            time_window_hours: Time window in hours
            
        Returns:
            Performance analytics data
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            
            # Filter events within time window
            recent_usage = [
                event for event in self.pattern_usage_history
                if datetime.fromisoformat(event['timestamp']) >= cutoff_time
            ]
            
            recent_recommendations = [
                event for event in self.recommendation_history
                if datetime.fromisoformat(event['timestamp']) >= cutoff_time
            ]
            
            # Pattern performance
            pattern_performance = defaultdict(lambda: {'times': [], 'successes': 0, 'total': 0})
            
            for event in recent_usage:
                pattern_id = event['pattern_id']
                pattern_performance[pattern_id]['times'].append(event['response_time_ms'])
                pattern_performance[pattern_id]['total'] += 1
                if event['success']:
                    pattern_performance[pattern_id]['successes'] += 1
            
            # Calculate performance metrics per pattern
            pattern_metrics = {}
            for pattern_id, data in pattern_performance.items():
                if data['times']:
                    pattern_metrics[pattern_id] = {
                        'avg_response_time_ms': statistics.mean(data['times']),
                        'success_rate': data['successes'] / data['total'],
                        'total_usage': data['total'],
                        'p95_response_time_ms': self._percentile(data['times'], 0.95)
                    }
            
            # Recommendation performance
            rec_times = [event['generation_time_ms'] for event in recent_recommendations]
            rec_success_rate = (
                sum(1 for event in recent_recommendations if event['success']) / 
                len(recent_recommendations) if recent_recommendations else 0.0
            )
            
            return {
                'time_window_hours': time_window_hours,
                'pattern_performance': pattern_metrics,
                'recommendation_performance': {
                    'avg_generation_time_ms': statistics.mean(rec_times) if rec_times else 0.0,
                    'success_rate': rec_success_rate,
                    'total_recommendations': len(recent_recommendations)
                },
                'system_performance': {
                    'total_pattern_accesses': len(recent_usage),
                    'overall_success_rate': (
                        sum(1 for event in recent_usage if event['success']) / 
                        len(recent_usage) if recent_usage else 0.0
                    )
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance analytics: {e}")
            return {}
    
    def get_trend_analysis(self, days: int = 7) -> Dict[str, Any]:
        """
        Get trend analysis for specified number of days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Trend analysis data
        """
        try:
            if not self.config['trend_analysis_enabled']:
                return {'trend_analysis_disabled': True}
            
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # Filter events
            recent_usage = [
                event for event in self.pattern_usage_history
                if datetime.fromisoformat(event['timestamp']) >= cutoff_time
            ]
            
            # Daily usage trends
            daily_usage = defaultdict(int)
            daily_success_rates = defaultdict(list)
            daily_response_times = defaultdict(list)
            
            for event in recent_usage:
                date = datetime.fromisoformat(event['timestamp']).date()
                daily_usage[date] += 1
                daily_success_rates[date].append(1 if event['success'] else 0)
                daily_response_times[date].append(event['response_time_ms'])
            
            # Calculate daily metrics
            daily_metrics = {}
            for date in daily_usage.keys():
                success_rate = statistics.mean(daily_success_rates[date]) if daily_success_rates[date] else 0.0
                avg_response_time = statistics.mean(daily_response_times[date]) if daily_response_times[date] else 0.0
                
                daily_metrics[date.isoformat()] = {
                    'usage_count': daily_usage[date],
                    'success_rate': success_rate,
                    'avg_response_time_ms': avg_response_time
                }
            
            # Pattern popularity trends
            pattern_trends = defaultdict(lambda: defaultdict(int))
            for event in recent_usage:
                date = datetime.fromisoformat(event['timestamp']).date()
                pattern_trends[event['pattern_id']][date] += 1
            
            return {
                'analysis_period_days': days,
                'daily_metrics': daily_metrics,
                'pattern_trends': {
                    pattern_id: dict(dates) 
                    for pattern_id, dates in pattern_trends.items()
                },
                'trend_summary': {
                    'total_usage_trend': self._calculate_trend([daily_usage[date] for date in sorted(daily_usage.keys())]),
                    'success_rate_trend': self._calculate_trend([
                        statistics.mean(daily_success_rates[date]) if daily_success_rates[date] else 0.0
                        for date in sorted(daily_success_rates.keys())
                    ])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trend analysis: {e}")
            return {}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """
        Get current real-time metrics.
        
        Returns:
            Real-time metrics data
        """
        return dict(self.current_metrics)
    
    def get_alerts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get system alerts.
        
        Args:
            active_only: Whether to return only active alerts
            
        Returns:
            List of alerts
        """
        if active_only:
            # Filter alerts from last hour
            cutoff_time = datetime.now() - timedelta(hours=1)
            return [
                alert for alert in self.alerts
                if datetime.fromisoformat(alert['timestamp']) >= cutoff_time
            ]
        else:
            return list(self.alerts)
    
    def export_analytics(self, format: str = 'json') -> str:
        """
        Export analytics data in specified format.
        
        Args:
            format: Export format ('json', 'csv')
            
        Returns:
            Exported data as string
        """
        try:
            if not self.config['export_analytics']:
                return "Analytics export is disabled"
            
            analytics_data = {
                'usage_analytics': self.get_usage_analytics(24),
                'performance_analytics': self.get_performance_analytics(24),
                'trend_analysis': self.get_trend_analysis(7),
                'real_time_metrics': self.get_real_time_metrics(),
                'alerts': self.get_alerts(False),
                'export_timestamp': datetime.now().isoformat()
            }
            
            if format.lower() == 'json':
                return json.dumps(analytics_data, indent=2)
            elif format.lower() == 'csv':
                # Simple CSV export for usage data
                csv_lines = ['pattern_id,timestamp,success,response_time_ms']
                for event in self.pattern_usage_history[-1000:]:  # Last 1000 events
                    csv_lines.append(f"{event['pattern_id']},{event['timestamp']},{event['success']},{event['response_time_ms']}")
                return '\n'.join(csv_lines)
            else:
                return f"Unsupported export format: {format}"
                
        except Exception as e:
            self.logger.error(f"Error exporting analytics: {e}")
            return f"Export failed: {str(e)}"
    
    def _update_real_time_metrics(self) -> None:
        """Update real-time metrics based on recent data."""
        try:
            # Get recent data (last hour)
            recent_analytics = self.get_usage_analytics(1)
            
            self.current_metrics.update({
                'total_patterns_accessed': recent_analytics.get('total_events', 0),
                'average_response_time_ms': recent_analytics.get('average_response_time_ms', 0.0),
                'success_rate': recent_analytics.get('success_rate', 0.0),
                'most_used_patterns': recent_analytics.get('most_used_patterns', [])[:5],
                'last_updated': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error updating real-time metrics: {e}")
    
    def _check_alerts(self, event: Dict[str, Any]) -> None:
        """Check for alert conditions based on event data."""
        try:
            thresholds = self.config['alert_thresholds']
            
            # Check response time alert
            if event['response_time_ms'] > thresholds['high_response_time_ms']:
                self._create_alert(
                    'high_response_time',
                    f"High response time detected: {event['response_time_ms']:.1f}ms for pattern {event['pattern_id']}",
                    'warning',
                    event
                )
            
            # Check success rate (based on recent events for same pattern)
            recent_events = [
                e for e in self.pattern_usage_history[-50:]  # Last 50 events
                if e['pattern_id'] == event['pattern_id']
            ]
            
            if len(recent_events) >= 5:  # Only check if we have enough data
                success_rate = sum(1 for e in recent_events if e['success']) / len(recent_events)
                if success_rate < thresholds['low_success_rate']:
                    self._create_alert(
                        'low_success_rate',
                        f"Low success rate detected: {success_rate:.1%} for pattern {event['pattern_id']}",
                        'error',
                        event
                    )
            
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
    
    def _create_alert(self, alert_type: str, message: str, severity: str, context: Dict[str, Any]) -> None:
        """Create a new alert."""
        alert = {
            'id': f"{alert_type}_{int(time.time())}",
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'context': context
        }
        
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        self.logger.warning(f"Alert created: {message}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up old analytics data based on retention policy."""
        try:
            retention_days = self.config['analytics_retention_days']
            cutoff_time = datetime.now() - timedelta(days=retention_days)
            
            # Clean usage history
            self.pattern_usage_history = [
                event for event in self.pattern_usage_history
                if datetime.fromisoformat(event['timestamp']) >= cutoff_time
            ]
            
            # Clean recommendation history
            self.recommendation_history = [
                event for event in self.recommendation_history
                if datetime.fromisoformat(event['timestamp']) >= cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def health_check(self) -> bool:
        """Check service health."""
        try:
            # Check if we can access metrics
            metrics = self.get_real_time_metrics()
            return isinstance(metrics, dict)
            
        except Exception:
            return False