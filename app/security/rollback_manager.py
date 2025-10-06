"""
Rollback mechanisms for security system issues.
Handles automatic and manual rollbacks based on health metrics and triggers.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from app.security.deployment_config import (
    get_deployment_config, RollbackTrigger
)
from app.security.attack_pack_manager import get_attack_pack_manager
from app.utils.logger import app_logger


class RollbackStatus(Enum):
    """Status of rollback operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class HealthMetrics:
    """Health metrics for rollback decision making."""
    timestamp: datetime
    error_rate: float = 0.0
    average_latency_ms: float = 0.0
    false_positive_rate: float = 0.0
    request_count: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocked_requests: int = 0
    flagged_requests: int = 0
    detector_failures: Dict[str, int] = field(default_factory=dict)
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class RollbackEvent:
    """Record of a rollback event."""
    id: str
    trigger: RollbackTrigger
    feature_name: str
    timestamp: datetime
    status: RollbackStatus
    reason: str
    metrics_snapshot: Optional[HealthMetrics] = None
    previous_config: Dict = field(default_factory=dict)
    rollback_config: Dict = field(default_factory=dict)
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class RollbackManager:
    """Manages automatic and manual rollbacks for security system issues."""
    
    def __init__(self):
        self.deployment_config = get_deployment_config()
        self.attack_pack_manager = get_attack_pack_manager()
        self.health_metrics_history: List[HealthMetrics] = []
        self.rollback_history: List[RollbackEvent] = []
        self.active_rollbacks: Dict[str, RollbackEvent] = {}
        self.last_rollback_time: Optional[datetime] = None
        self.rollback_count_today = 0
        self._monitoring_task: Optional[asyncio.Task] = None
    
    def start_monitoring(self) -> None:
        """Start the rollback monitoring task."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            app_logger.info("Started rollback monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop the rollback monitoring task."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            app_logger.info("Stopped rollback monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for automatic rollbacks."""
        try:
            while True:
                if self.deployment_config.rollback_config.enabled:
                    await self._check_rollback_triggers()
                
                # Sleep for the health check interval
                await asyncio.sleep(self.deployment_config.health_check_interval_seconds)
                
        except asyncio.CancelledError:
            app_logger.info("Rollback monitoring cancelled")
        except Exception as e:
            app_logger.error(f"Error in rollback monitoring loop: {e}")
    
    async def _check_rollback_triggers(self) -> None:
        """Check all rollback triggers and initiate rollbacks if needed."""
        try:
            # Get current health metrics
            current_metrics = await self._collect_health_metrics()
            self.health_metrics_history.append(current_metrics)
            
            # Keep only recent metrics (last hour)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            self.health_metrics_history = [
                m for m in self.health_metrics_history if m.timestamp > cutoff_time
            ]
            
            # Check each trigger
            for trigger, config in self.deployment_config.rollback_config.triggers.items():
                if await self._should_trigger_rollback(trigger, config, current_metrics):
                    await self._initiate_automatic_rollback(trigger, current_metrics)
                    
        except Exception as e:
            app_logger.error(f"Error checking rollback triggers: {e}")
    
    async def _collect_health_metrics(self) -> HealthMetrics:
        """Collect current health metrics from the system."""
        # This would integrate with actual monitoring systems
        # For now, return mock metrics
        return HealthMetrics(
            timestamp=datetime.utcnow(),
            error_rate=0.01,  # 1% error rate
            average_latency_ms=25.0,
            false_positive_rate=0.02,  # 2% false positive rate
            request_count=1000,
            successful_requests=990,
            failed_requests=10,
            blocked_requests=50,
            flagged_requests=20,
            detector_failures={},
            memory_usage_mb=256.0,
            cpu_usage_percent=15.0
        )
    
    async def _should_trigger_rollback(self, trigger: RollbackTrigger, 
                                     config: Dict, current_metrics: HealthMetrics) -> bool:
        """Check if a specific trigger should initiate a rollback."""
        try:
            if trigger == RollbackTrigger.HIGH_ERROR_RATE:
                threshold = config.get('threshold', 0.05)
                window_minutes = config.get('window_minutes', 5)
                min_requests = config.get('min_requests', 100)
                
                # Check error rate over the window
                window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
                window_metrics = [m for m in self.health_metrics_history if m.timestamp > window_start]
                
                if len(window_metrics) == 0:
                    return False
                
                total_requests = sum(m.request_count for m in window_metrics)
                total_errors = sum(m.failed_requests for m in window_metrics)
                
                if total_requests < min_requests:
                    return False
                
                error_rate = total_errors / total_requests if total_requests > 0 else 0
                return error_rate > threshold
                
            elif trigger == RollbackTrigger.HIGH_LATENCY:
                threshold_ms = config.get('threshold_ms', 200)
                window_minutes = config.get('window_minutes', 5)
                min_requests = config.get('min_requests', 100)
                
                # Check average latency over the window
                window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
                window_metrics = [m for m in self.health_metrics_history if m.timestamp > window_start]
                
                if len(window_metrics) == 0:
                    return False
                
                total_requests = sum(m.request_count for m in window_metrics)
                if total_requests < min_requests:
                    return False
                
                avg_latency = sum(m.average_latency_ms for m in window_metrics) / len(window_metrics)
                return avg_latency > threshold_ms
                
            elif trigger == RollbackTrigger.HIGH_FALSE_POSITIVE_RATE:
                threshold = config.get('threshold', 0.10)
                window_minutes = config.get('window_minutes', 10)
                min_requests = config.get('min_requests', 50)
                
                # Check false positive rate over the window
                window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
                window_metrics = [m for m in self.health_metrics_history if m.timestamp > window_start]
                
                if len(window_metrics) == 0:
                    return False
                
                total_requests = sum(m.request_count for m in window_metrics)
                if total_requests < min_requests:
                    return False
                
                avg_fp_rate = sum(m.false_positive_rate for m in window_metrics) / len(window_metrics)
                return avg_fp_rate > threshold
                
            elif trigger == RollbackTrigger.HEALTH_CHECK_FAILURE:
                # This would check actual health check endpoints
                # For now, return False (no health check failures)
                return False
                
            return False
            
        except Exception as e:
            app_logger.error(f"Error checking rollback trigger {trigger}: {e}")
            return False
    
    async def _initiate_automatic_rollback(self, trigger: RollbackTrigger, 
                                         metrics: HealthMetrics) -> None:
        """Initiate an automatic rollback based on a trigger."""
        try:
            # Check cooldown period
            if self._is_in_cooldown():
                app_logger.warning(f"Rollback trigger {trigger} fired but in cooldown period")
                return
            
            # Check daily rollback limit
            if self._has_exceeded_daily_limit():
                app_logger.warning(f"Rollback trigger {trigger} fired but daily limit exceeded")
                return
            
            # Determine which feature to rollback
            feature_to_rollback = self._determine_rollback_target(trigger, metrics)
            if not feature_to_rollback:
                app_logger.warning(f"No rollback target determined for trigger {trigger}")
                return
            
            # Create rollback event
            rollback_id = f"auto_{trigger.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            rollback_event = RollbackEvent(
                id=rollback_id,
                trigger=trigger,
                feature_name=feature_to_rollback,
                timestamp=datetime.utcnow(),
                status=RollbackStatus.PENDING,
                reason=f"Automatic rollback triggered by {trigger.value}",
                metrics_snapshot=metrics
            )
            
            # Execute rollback
            await self._execute_rollback(rollback_event)
            
        except Exception as e:
            app_logger.error(f"Failed to initiate automatic rollback for trigger {trigger}: {e}")
    
    def _is_in_cooldown(self) -> bool:
        """Check if we're in the cooldown period after the last rollback."""
        if self.last_rollback_time is None:
            return False
        
        cooldown_minutes = self.deployment_config.rollback_config.cooldown_minutes
        cooldown_end = self.last_rollback_time + timedelta(minutes=cooldown_minutes)
        return datetime.utcnow() < cooldown_end
    
    def _has_exceeded_daily_limit(self) -> bool:
        """Check if we've exceeded the daily rollback limit."""
        max_rollbacks = self.deployment_config.rollback_config.max_rollbacks_per_day
        
        # Count rollbacks today
        today = datetime.utcnow().date()
        today_rollbacks = [
            r for r in self.rollback_history 
            if r.timestamp.date() == today and r.status == RollbackStatus.COMPLETED
        ]
        
        return len(today_rollbacks) >= max_rollbacks
    
    def _determine_rollback_target(self, trigger: RollbackTrigger, 
                                 metrics: HealthMetrics) -> Optional[str]:
        """Determine which feature should be rolled back based on the trigger."""
        # This logic would be more sophisticated in a real implementation
        # For now, rollback the main defense system
        
        if trigger in [RollbackTrigger.HIGH_ERROR_RATE, RollbackTrigger.HIGH_LATENCY]:
            return "advanced_prompt_defense"
        elif trigger == RollbackTrigger.HIGH_FALSE_POSITIVE_RATE:
            # Find the detector with the highest false positive contribution
            # For now, return the main system
            return "advanced_prompt_defense"
        elif trigger == RollbackTrigger.HEALTH_CHECK_FAILURE:
            return "advanced_prompt_defense"
        
        return None
    
    async def _execute_rollback(self, rollback_event: RollbackEvent) -> None:
        """Execute a rollback operation."""
        try:
            rollback_event.status = RollbackStatus.IN_PROGRESS
            self.active_rollbacks[rollback_event.id] = rollback_event
            
            app_logger.warning(f"Starting rollback {rollback_event.id} for feature {rollback_event.feature_name}")
            
            # Save current configuration
            rollback_event.previous_config = self._capture_current_config(rollback_event.feature_name)
            
            # Perform the rollback
            success = await self._perform_rollback(rollback_event)
            
            if success:
                rollback_event.status = RollbackStatus.COMPLETED
                rollback_event.completed_at = datetime.utcnow()
                self.last_rollback_time = datetime.utcnow()
                app_logger.warning(f"Rollback {rollback_event.id} completed successfully")
            else:
                rollback_event.status = RollbackStatus.FAILED
                rollback_event.error_message = "Rollback operation failed"
                app_logger.error(f"Rollback {rollback_event.id} failed")
            
            # Move to history
            self.rollback_history.append(rollback_event)
            del self.active_rollbacks[rollback_event.id]
            
            # Send notifications
            await self._send_rollback_notification(rollback_event)
            
        except Exception as e:
            rollback_event.status = RollbackStatus.FAILED
            rollback_event.error_message = str(e)
            app_logger.error(f"Error executing rollback {rollback_event.id}: {e}")
    
    def _capture_current_config(self, feature_name: str) -> Dict:
        """Capture the current configuration for a feature."""
        if feature_name in self.deployment_config.feature_flags:
            flag = self.deployment_config.feature_flags[feature_name]
            return {
                'enabled': flag.enabled,
                'stage': flag.stage.value,
                'rollout_percentage': flag.rollout_percentage,
                'target_groups': list(flag.target_groups),
                'metadata': flag.metadata.copy()
            }
        return {}
    
    async def _perform_rollback(self, rollback_event: RollbackEvent) -> bool:
        """Perform the actual rollback operation."""
        try:
            feature_name = rollback_event.feature_name
            
            if feature_name == "advanced_prompt_defense":
                # Rollback the main defense system
                self.deployment_config.disable_feature(feature_name)
                
                # Also consider rolling back to a previous attack pack version
                if rollback_event.trigger in [RollbackTrigger.HIGH_FALSE_POSITIVE_RATE]:
                    success, message = self.attack_pack_manager.rollback_attack_pack()
                    if not success:
                        app_logger.warning(f"Attack pack rollback failed: {message}")
                
            elif feature_name in self.deployment_config.feature_flags:
                # Rollback specific detector
                self.deployment_config.disable_feature(feature_name)
            
            # Save configuration
            self.deployment_config.save_to_file("config.yaml")
            
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to perform rollback for {rollback_event.feature_name}: {e}")
            return False
    
    async def _send_rollback_notification(self, rollback_event: RollbackEvent) -> None:
        """Send notifications about the rollback event."""
        try:
            
            message = (
                f"Security System Rollback Alert\n"
                f"Feature: {rollback_event.feature_name}\n"
                f"Trigger: {rollback_event.trigger.value}\n"
                f"Status: {rollback_event.status.value}\n"
                f"Time: {rollback_event.timestamp.isoformat()}\n"
                f"Reason: {rollback_event.reason}"
            )
            
            if rollback_event.error_message:
                message += f"\nError: {rollback_event.error_message}"
            
            # In a real implementation, this would send to actual notification channels
            app_logger.warning(f"Rollback notification: {message}")
            
        except Exception as e:
            app_logger.error(f"Failed to send rollback notification: {e}")
    
    async def manual_rollback(self, feature_name: str, reason: str = "Manual rollback") -> str:
        """Initiate a manual rollback."""
        try:
            # Check if feature exists
            if feature_name not in self.deployment_config.feature_flags:
                return f"Feature {feature_name} not found"
            
            # Check cooldown period
            if self._is_in_cooldown():
                return "Cannot perform rollback: still in cooldown period"
            
            # Check daily limit
            if self._has_exceeded_daily_limit():
                return "Cannot perform rollback: daily limit exceeded"
            
            # Create rollback event
            rollback_id = f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            rollback_event = RollbackEvent(
                id=rollback_id,
                trigger=RollbackTrigger.MANUAL,
                feature_name=feature_name,
                timestamp=datetime.utcnow(),
                status=RollbackStatus.PENDING,
                reason=reason
            )
            
            # Execute rollback
            await self._execute_rollback(rollback_event)
            
            if rollback_event.status == RollbackStatus.COMPLETED:
                return f"Manual rollback completed successfully for {feature_name}"
            else:
                return f"Manual rollback failed: {rollback_event.error_message}"
                
        except Exception as e:
            error_msg = f"Failed to perform manual rollback: {str(e)}"
            app_logger.error(error_msg)
            return error_msg
    
    def get_rollback_history(self, limit: int = 50) -> List[Dict]:
        """Get the rollback history."""
        history = sorted(self.rollback_history, key=lambda x: x.timestamp, reverse=True)
        
        result = []
        for event in history[:limit]:
            result.append({
                'id': event.id,
                'trigger': event.trigger.value,
                'feature_name': event.feature_name,
                'timestamp': event.timestamp.isoformat(),
                'status': event.status.value,
                'reason': event.reason,
                'error_message': event.error_message,
                'completed_at': event.completed_at.isoformat() if event.completed_at else None
            })
        
        return result
    
    def get_active_rollbacks(self) -> List[Dict]:
        """Get currently active rollbacks."""
        result = []
        for event in self.active_rollbacks.values():
            result.append({
                'id': event.id,
                'trigger': event.trigger.value,
                'feature_name': event.feature_name,
                'timestamp': event.timestamp.isoformat(),
                'status': event.status.value,
                'reason': event.reason
            })
        
        return result
    
    def cancel_rollback(self, rollback_id: str) -> bool:
        """Cancel an active rollback."""
        if rollback_id in self.active_rollbacks:
            rollback_event = self.active_rollbacks[rollback_id]
            if rollback_event.status == RollbackStatus.PENDING:
                rollback_event.status = RollbackStatus.CANCELLED
                self.rollback_history.append(rollback_event)
                del self.active_rollbacks[rollback_id]
                app_logger.info(f"Cancelled rollback {rollback_id}")
                return True
        
        return False


# Global rollback manager instance
_rollback_manager: Optional[RollbackManager] = None


def get_rollback_manager() -> RollbackManager:
    """Get the global rollback manager instance."""
    global _rollback_manager
    if _rollback_manager is None:
        _rollback_manager = RollbackManager()
    return _rollback_manager