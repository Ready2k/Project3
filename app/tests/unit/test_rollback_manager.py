"""
Unit tests for rollback manager.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from app.security.rollback_manager import (
    RollbackManager, HealthMetrics, RollbackEvent, RollbackStatus,
    get_rollback_manager
)
from app.security.deployment_config import RollbackTrigger, FeatureFlag, DeploymentStage


class TestHealthMetrics:
    """Test HealthMetrics functionality."""
    
    def test_health_metrics_creation(self):
        """Test creating health metrics."""
        timestamp = datetime.utcnow()
        metrics = HealthMetrics(
            timestamp=timestamp,
            error_rate=0.05,
            average_latency_ms=150.0,
            false_positive_rate=0.02,
            request_count=1000,
            successful_requests=950,
            failed_requests=50,
            blocked_requests=100,
            flagged_requests=25,
            detector_failures={"overt_injection": 2},
            memory_usage_mb=512.0,
            cpu_usage_percent=25.0
        )
        
        assert metrics.timestamp == timestamp
        assert metrics.error_rate == 0.05
        assert metrics.average_latency_ms == 150.0
        assert metrics.false_positive_rate == 0.02
        assert metrics.request_count == 1000
        assert metrics.successful_requests == 950
        assert metrics.failed_requests == 50
        assert metrics.blocked_requests == 100
        assert metrics.flagged_requests == 25
        assert metrics.detector_failures["overt_injection"] == 2
        assert metrics.memory_usage_mb == 512.0
        assert metrics.cpu_usage_percent == 25.0
    
    def test_health_metrics_defaults(self):
        """Test health metrics default values."""
        timestamp = datetime.utcnow()
        metrics = HealthMetrics(timestamp=timestamp)
        
        assert metrics.timestamp == timestamp
        assert metrics.error_rate == 0.0
        assert metrics.average_latency_ms == 0.0
        assert metrics.false_positive_rate == 0.0
        assert metrics.request_count == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.blocked_requests == 0
        assert metrics.flagged_requests == 0
        assert len(metrics.detector_failures) == 0
        assert metrics.memory_usage_mb == 0.0
        assert metrics.cpu_usage_percent == 0.0


class TestRollbackEvent:
    """Test RollbackEvent functionality."""
    
    def test_rollback_event_creation(self):
        """Test creating rollback event."""
        timestamp = datetime.utcnow()
        metrics = HealthMetrics(timestamp=timestamp, error_rate=0.1)
        
        event = RollbackEvent(
            id="test_rollback_001",
            trigger=RollbackTrigger.HIGH_ERROR_RATE,
            feature_name="advanced_prompt_defense",
            timestamp=timestamp,
            status=RollbackStatus.PENDING,
            reason="High error rate detected",
            metrics_snapshot=metrics,
            previous_config={"enabled": True},
            rollback_config={"enabled": False}
        )
        
        assert event.id == "test_rollback_001"
        assert event.trigger == RollbackTrigger.HIGH_ERROR_RATE
        assert event.feature_name == "advanced_prompt_defense"
        assert event.timestamp == timestamp
        assert event.status == RollbackStatus.PENDING
        assert event.reason == "High error rate detected"
        assert event.metrics_snapshot == metrics
        assert event.previous_config["enabled"] is True
        assert event.rollback_config["enabled"] is False


class TestRollbackManager:
    """Test RollbackManager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        with patch('app.security.deployment_config.get_deployment_config'), \
             patch('app.security.attack_pack_manager.get_attack_pack_manager'):
            self.manager = RollbackManager()
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        assert isinstance(self.manager.health_metrics_history, list)
        assert isinstance(self.manager.rollback_history, list)
        assert isinstance(self.manager.active_rollbacks, dict)
        assert self.manager.last_rollback_time is None
        assert self.manager.rollback_count_today == 0
        assert self.manager._monitoring_task is None
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        # Mock the monitoring loop
        with patch.object(self.manager, '_monitoring_loop', new_callable=AsyncMock) as mock_loop:
            mock_task = MagicMock()
            mock_task.done.return_value = True
            
            with patch('asyncio.create_task', return_value=mock_task) as mock_create_task:
                self.manager.start_monitoring()
                
                mock_create_task.assert_called_once()
                assert self.manager._monitoring_task == mock_task
        
        # Test stopping
        mock_task = MagicMock()
        mock_task.done.return_value = False
        self.manager._monitoring_task = mock_task
        
        self.manager.stop_monitoring()
        mock_task.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_health_metrics(self):
        """Test collecting health metrics."""
        metrics = await self.manager._collect_health_metrics()
        
        assert isinstance(metrics, HealthMetrics)
        assert metrics.timestamp is not None
        assert isinstance(metrics.error_rate, float)
        assert isinstance(metrics.average_latency_ms, float)
        assert isinstance(metrics.false_positive_rate, float)
        assert isinstance(metrics.request_count, int)
    
    @pytest.mark.asyncio
    async def test_should_trigger_rollback_high_error_rate(self):
        """Test rollback trigger for high error rate."""
        # Add metrics history with high error rate
        base_time = datetime.utcnow()
        for i in range(3):
            metrics = HealthMetrics(
                timestamp=base_time - timedelta(minutes=i),
                request_count=100,
                failed_requests=10,  # 10% error rate
                successful_requests=90
            )
            self.manager.health_metrics_history.append(metrics)
        
        current_metrics = HealthMetrics(
            timestamp=base_time,
            request_count=100,
            failed_requests=10,
            successful_requests=90
        )
        
        trigger_config = {
            'threshold': 0.05,  # 5% threshold
            'window_minutes': 5,
            'min_requests': 100
        }
        
        should_trigger = await self.manager._should_trigger_rollback(
            RollbackTrigger.HIGH_ERROR_RATE, trigger_config, current_metrics
        )
        
        assert should_trigger is True
    
    @pytest.mark.asyncio
    async def test_should_trigger_rollback_low_error_rate(self):
        """Test rollback trigger with low error rate."""
        # Add metrics history with low error rate
        base_time = datetime.utcnow()
        for i in range(3):
            metrics = HealthMetrics(
                timestamp=base_time - timedelta(minutes=i),
                request_count=100,
                failed_requests=2,  # 2% error rate
                successful_requests=98
            )
            self.manager.health_metrics_history.append(metrics)
        
        current_metrics = HealthMetrics(
            timestamp=base_time,
            request_count=100,
            failed_requests=2,
            successful_requests=98
        )
        
        trigger_config = {
            'threshold': 0.05,  # 5% threshold
            'window_minutes': 5,
            'min_requests': 100
        }
        
        should_trigger = await self.manager._should_trigger_rollback(
            RollbackTrigger.HIGH_ERROR_RATE, trigger_config, current_metrics
        )
        
        assert should_trigger is False
    
    @pytest.mark.asyncio
    async def test_should_trigger_rollback_insufficient_requests(self):
        """Test rollback trigger with insufficient requests."""
        # Add metrics history with high error rate but low request count
        base_time = datetime.utcnow()
        metrics = HealthMetrics(
            timestamp=base_time,
            request_count=10,  # Below min_requests threshold
            failed_requests=5,  # 50% error rate
            successful_requests=5
        )
        self.manager.health_metrics_history.append(metrics)
        
        trigger_config = {
            'threshold': 0.05,
            'window_minutes': 5,
            'min_requests': 100
        }
        
        should_trigger = await self.manager._should_trigger_rollback(
            RollbackTrigger.HIGH_ERROR_RATE, trigger_config, metrics
        )
        
        assert should_trigger is False
    
    @pytest.mark.asyncio
    async def test_should_trigger_rollback_high_latency(self):
        """Test rollback trigger for high latency."""
        # Add metrics history with high latency
        base_time = datetime.utcnow()
        for i in range(3):
            metrics = HealthMetrics(
                timestamp=base_time - timedelta(minutes=i),
                request_count=100,
                average_latency_ms=250.0  # Above 200ms threshold
            )
            self.manager.health_metrics_history.append(metrics)
        
        current_metrics = HealthMetrics(
            timestamp=base_time,
            request_count=100,
            average_latency_ms=250.0
        )
        
        trigger_config = {
            'threshold_ms': 200,
            'window_minutes': 5,
            'min_requests': 100
        }
        
        should_trigger = await self.manager._should_trigger_rollback(
            RollbackTrigger.HIGH_LATENCY, trigger_config, current_metrics
        )
        
        assert should_trigger is True
    
    @pytest.mark.asyncio
    async def test_should_trigger_rollback_high_false_positive_rate(self):
        """Test rollback trigger for high false positive rate."""
        # Add metrics history with high false positive rate
        base_time = datetime.utcnow()
        for i in range(3):
            metrics = HealthMetrics(
                timestamp=base_time - timedelta(minutes=i),
                request_count=100,
                false_positive_rate=0.15  # Above 10% threshold
            )
            self.manager.health_metrics_history.append(metrics)
        
        current_metrics = HealthMetrics(
            timestamp=base_time,
            request_count=100,
            false_positive_rate=0.15
        )
        
        trigger_config = {
            'threshold': 0.10,
            'window_minutes': 10,
            'min_requests': 50
        }
        
        should_trigger = await self.manager._should_trigger_rollback(
            RollbackTrigger.HIGH_FALSE_POSITIVE_RATE, trigger_config, current_metrics
        )
        
        assert should_trigger is True
    
    def test_is_in_cooldown_no_previous_rollback(self):
        """Test cooldown check with no previous rollback."""
        assert self.manager._is_in_cooldown() is False
    
    def test_is_in_cooldown_within_period(self):
        """Test cooldown check within cooldown period."""
        # Set last rollback time to 10 minutes ago
        self.manager.last_rollback_time = datetime.utcnow() - timedelta(minutes=10)
        
        # Mock deployment config with 30-minute cooldown
        self.manager.deployment_config.rollback_config.cooldown_minutes = 30
        
        assert self.manager._is_in_cooldown() is True
    
    def test_is_in_cooldown_after_period(self):
        """Test cooldown check after cooldown period."""
        # Set last rollback time to 40 minutes ago
        self.manager.last_rollback_time = datetime.utcnow() - timedelta(minutes=40)
        
        # Mock deployment config with 30-minute cooldown
        self.manager.deployment_config.rollback_config.cooldown_minutes = 30
        
        assert self.manager._is_in_cooldown() is False
    
    def test_has_exceeded_daily_limit_no_rollbacks(self):
        """Test daily limit check with no rollbacks."""
        self.manager.deployment_config.rollback_config.max_rollbacks_per_day = 5
        
        assert self.manager._has_exceeded_daily_limit() is False
    
    def test_has_exceeded_daily_limit_under_limit(self):
        """Test daily limit check under limit."""
        self.manager.deployment_config.rollback_config.max_rollbacks_per_day = 5
        
        # Add 3 rollbacks today
        today = datetime.utcnow()
        for i in range(3):
            event = RollbackEvent(
                id=f"rollback_{i}",
                trigger=RollbackTrigger.MANUAL,
                feature_name="test_feature",
                timestamp=today,
                status=RollbackStatus.COMPLETED,
                reason="Test rollback"
            )
            self.manager.rollback_history.append(event)
        
        assert self.manager._has_exceeded_daily_limit() is False
    
    def test_has_exceeded_daily_limit_at_limit(self):
        """Test daily limit check at limit."""
        self.manager.deployment_config.rollback_config.max_rollbacks_per_day = 3
        
        # Add 3 rollbacks today
        today = datetime.utcnow()
        for i in range(3):
            event = RollbackEvent(
                id=f"rollback_{i}",
                trigger=RollbackTrigger.MANUAL,
                feature_name="test_feature",
                timestamp=today,
                status=RollbackStatus.COMPLETED,
                reason="Test rollback"
            )
            self.manager.rollback_history.append(event)
        
        assert self.manager._has_exceeded_daily_limit() is True
    
    def test_determine_rollback_target(self):
        """Test determining rollback target."""
        metrics = HealthMetrics(timestamp=datetime.utcnow())
        
        # Test different triggers
        target = self.manager._determine_rollback_target(RollbackTrigger.HIGH_ERROR_RATE, metrics)
        assert target == "advanced_prompt_defense"
        
        target = self.manager._determine_rollback_target(RollbackTrigger.HIGH_LATENCY, metrics)
        assert target == "advanced_prompt_defense"
        
        target = self.manager._determine_rollback_target(RollbackTrigger.HIGH_FALSE_POSITIVE_RATE, metrics)
        assert target == "advanced_prompt_defense"
        
        target = self.manager._determine_rollback_target(RollbackTrigger.HEALTH_CHECK_FAILURE, metrics)
        assert target == "advanced_prompt_defense"
    
    def test_capture_current_config(self):
        """Test capturing current configuration."""
        # Mock feature flag
        flag = FeatureFlag(
            name="test_feature",
            enabled=True,
            stage=DeploymentStage.FULL,
            rollout_percentage=100.0,
            target_groups={"testers"},
            metadata={"test": "data"}
        )
        self.manager.deployment_config.feature_flags = {"test_feature": flag}
        
        config = self.manager._capture_current_config("test_feature")
        
        assert config["enabled"] is True
        assert config["stage"] == "full"
        assert config["rollout_percentage"] == 100.0
        assert "testers" in config["target_groups"]
        assert config["metadata"]["test"] == "data"
    
    def test_capture_current_config_not_found(self):
        """Test capturing config for non-existent feature."""
        self.manager.deployment_config.feature_flags = {}
        
        config = self.manager._capture_current_config("nonexistent")
        
        assert config == {}
    
    @pytest.mark.asyncio
    async def test_perform_rollback_main_defense(self):
        """Test performing rollback for main defense system."""
        event = RollbackEvent(
            id="test_rollback",
            trigger=RollbackTrigger.HIGH_ERROR_RATE,
            feature_name="advanced_prompt_defense",
            timestamp=datetime.utcnow(),
            status=RollbackStatus.IN_PROGRESS,
            reason="Test rollback"
        )
        
        # Mock deployment config methods
        self.manager.deployment_config.disable_feature = MagicMock()
        self.manager.deployment_config.save_to_file = MagicMock()
        
        success = await self.manager._perform_rollback(event)
        
        assert success is True
        self.manager.deployment_config.disable_feature.assert_called_once_with("advanced_prompt_defense")
        self.manager.deployment_config.save_to_file.assert_called_once_with("config.yaml")
    
    @pytest.mark.asyncio
    async def test_perform_rollback_specific_detector(self):
        """Test performing rollback for specific detector."""
        event = RollbackEvent(
            id="test_rollback",
            trigger=RollbackTrigger.MANUAL,
            feature_name="overt_injection_detector",
            timestamp=datetime.utcnow(),
            status=RollbackStatus.IN_PROGRESS,
            reason="Test rollback"
        )
        
        # Mock deployment config
        self.manager.deployment_config.feature_flags = {"overt_injection_detector": MagicMock()}
        self.manager.deployment_config.disable_feature = MagicMock()
        self.manager.deployment_config.save_to_file = MagicMock()
        
        success = await self.manager._perform_rollback(event)
        
        assert success is True
        self.manager.deployment_config.disable_feature.assert_called_once_with("overt_injection_detector")
    
    @pytest.mark.asyncio
    async def test_manual_rollback_success(self):
        """Test successful manual rollback."""
        # Mock deployment config
        self.manager.deployment_config.feature_flags = {"test_feature": MagicMock()}
        
        # Mock methods to avoid cooldown and limit checks
        self.manager._is_in_cooldown = MagicMock(return_value=False)
        self.manager._has_exceeded_daily_limit = MagicMock(return_value=False)
        
        # Mock execute_rollback to succeed
        async def mock_execute_rollback(event):
            event.status = RollbackStatus.COMPLETED
        
        self.manager._execute_rollback = AsyncMock(side_effect=mock_execute_rollback)
        
        result = await self.manager.manual_rollback("test_feature", "Manual test")
        
        assert "completed successfully" in result
        self.manager._execute_rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_manual_rollback_feature_not_found(self):
        """Test manual rollback for non-existent feature."""
        self.manager.deployment_config.feature_flags = {}
        
        result = await self.manager.manual_rollback("nonexistent", "Test")
        
        assert "not found" in result
    
    @pytest.mark.asyncio
    async def test_manual_rollback_in_cooldown(self):
        """Test manual rollback during cooldown period."""
        self.manager.deployment_config.feature_flags = {"test_feature": MagicMock()}
        self.manager._is_in_cooldown = MagicMock(return_value=True)
        
        result = await self.manager.manual_rollback("test_feature", "Test")
        
        assert "cooldown period" in result
    
    @pytest.mark.asyncio
    async def test_manual_rollback_daily_limit_exceeded(self):
        """Test manual rollback when daily limit exceeded."""
        self.manager.deployment_config.feature_flags = {"test_feature": MagicMock()}
        self.manager._is_in_cooldown = MagicMock(return_value=False)
        self.manager._has_exceeded_daily_limit = MagicMock(return_value=True)
        
        result = await self.manager.manual_rollback("test_feature", "Test")
        
        assert "daily limit exceeded" in result
    
    def test_get_rollback_history(self):
        """Test getting rollback history."""
        # Add some rollback events
        base_time = datetime.utcnow()
        for i in range(3):
            event = RollbackEvent(
                id=f"rollback_{i}",
                trigger=RollbackTrigger.MANUAL,
                feature_name=f"feature_{i}",
                timestamp=base_time - timedelta(minutes=i),
                status=RollbackStatus.COMPLETED,
                reason=f"Test rollback {i}",
                completed_at=base_time - timedelta(minutes=i) + timedelta(seconds=30)
            )
            self.manager.rollback_history.append(event)
        
        history = self.manager.get_rollback_history(limit=2)
        
        assert len(history) == 2
        # Should be sorted by timestamp (newest first)
        assert history[0]['id'] == 'rollback_0'
        assert history[1]['id'] == 'rollback_1'
        
        # Check structure
        for entry in history:
            assert 'id' in entry
            assert 'trigger' in entry
            assert 'feature_name' in entry
            assert 'timestamp' in entry
            assert 'status' in entry
            assert 'reason' in entry
            assert 'completed_at' in entry
    
    def test_get_active_rollbacks(self):
        """Test getting active rollbacks."""
        # Add active rollback
        event = RollbackEvent(
            id="active_rollback",
            trigger=RollbackTrigger.HIGH_ERROR_RATE,
            feature_name="test_feature",
            timestamp=datetime.utcnow(),
            status=RollbackStatus.IN_PROGRESS,
            reason="Test active rollback"
        )
        self.manager.active_rollbacks["active_rollback"] = event
        
        active = self.manager.get_active_rollbacks()
        
        assert len(active) == 1
        assert active[0]['id'] == 'active_rollback'
        assert active[0]['status'] == 'in_progress'
        assert active[0]['trigger'] == 'high_error_rate'
    
    def test_cancel_rollback_success(self):
        """Test successful rollback cancellation."""
        # Add pending rollback
        event = RollbackEvent(
            id="pending_rollback",
            trigger=RollbackTrigger.MANUAL,
            feature_name="test_feature",
            timestamp=datetime.utcnow(),
            status=RollbackStatus.PENDING,
            reason="Test pending rollback"
        )
        self.manager.active_rollbacks["pending_rollback"] = event
        
        success = self.manager.cancel_rollback("pending_rollback")
        
        assert success is True
        assert "pending_rollback" not in self.manager.active_rollbacks
        assert len(self.manager.rollback_history) == 1
        assert self.manager.rollback_history[0].status == RollbackStatus.CANCELLED
    
    def test_cancel_rollback_not_found(self):
        """Test cancelling non-existent rollback."""
        success = self.manager.cancel_rollback("nonexistent")
        
        assert success is False
    
    def test_cancel_rollback_not_pending(self):
        """Test cancelling non-pending rollback."""
        # Add in-progress rollback
        event = RollbackEvent(
            id="in_progress_rollback",
            trigger=RollbackTrigger.MANUAL,
            feature_name="test_feature",
            timestamp=datetime.utcnow(),
            status=RollbackStatus.IN_PROGRESS,
            reason="Test in-progress rollback"
        )
        self.manager.active_rollbacks["in_progress_rollback"] = event
        
        success = self.manager.cancel_rollback("in_progress_rollback")
        
        assert success is False
        assert "in_progress_rollback" in self.manager.active_rollbacks


class TestGlobalRollbackManager:
    """Test global rollback manager functions."""
    
    @patch('app.security.rollback_manager._rollback_manager', None)
    def test_get_rollback_manager(self):
        """Test getting global rollback manager."""
        with patch('app.security.deployment_config.get_deployment_config'), \
             patch('app.security.attack_pack_manager.get_attack_pack_manager'):
            manager = get_rollback_manager()
            
            assert isinstance(manager, RollbackManager)
            
            # Should return same instance on subsequent calls
            manager2 = get_rollback_manager()
            assert manager is manager2


if __name__ == "__main__":
    pytest.main([__file__])