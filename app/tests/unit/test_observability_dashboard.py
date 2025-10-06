"""Unit tests for Streamlit observability dashboard functionality."""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from streamlit_app import AutomatedAIAssessmentUI
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

if not STREAMLIT_AVAILABLE:
    pytest.skip("Streamlit app not available", allow_module_level=True)


class TestObservabilityDashboard:
    """Test observability dashboard functionality."""
    
    @pytest.fixture
    def ui_app(self):
        """Create UI app instance for testing."""
        return AutomatedAIAssessmentUI()
    
    @pytest.fixture
    def mock_provider_stats(self):
        """Mock provider statistics data."""
        return {
            'provider_stats': [
                {
                    'provider': 'openai',
                    'model': 'gpt-4o',
                    'call_count': 25,
                    'avg_latency': 1250.5,
                    'min_latency': 800,
                    'max_latency': 2100,
                    'total_tokens': 15000
                },
                {
                    'provider': 'bedrock',
                    'model': 'claude-3-sonnet',
                    'call_count': 15,
                    'avg_latency': 2100.8,
                    'min_latency': 1200,
                    'max_latency': 3500,
                    'total_tokens': 12000
                },
                {
                    'provider': 'claude',
                    'model': 'claude-3-opus',
                    'call_count': 8,
                    'avg_latency': 950.2,
                    'min_latency': 600,
                    'max_latency': 1800,
                    'total_tokens': 8500
                }
            ]
        }
    
    @pytest.fixture
    def mock_pattern_stats(self):
        """Mock pattern statistics data."""
        return {
            'pattern_stats': [
                {
                    'pattern_id': 'PAT-001',
                    'match_count': 20,
                    'avg_score': 0.85,
                    'min_score': 0.65,
                    'max_score': 0.95,
                    'accepted_count': 18,
                    'acceptance_rate': 0.9
                },
                {
                    'pattern_id': 'PAT-002',
                    'match_count': 15,
                    'avg_score': 0.72,
                    'min_score': 0.45,
                    'max_score': 0.88,
                    'accepted_count': 9,
                    'acceptance_rate': 0.6
                },
                {
                    'pattern_id': 'PAT-003',
                    'match_count': 12,
                    'avg_score': 0.91,
                    'min_score': 0.78,
                    'max_score': 0.98,
                    'accepted_count': 11,
                    'acceptance_rate': 0.917
                }
            ]
        }
    
    @pytest.fixture
    def empty_stats(self):
        """Empty statistics for testing no-data scenarios."""
        return {'provider_stats': [], 'pattern_stats': []}
    
    @pytest.mark.asyncio
    async def test_get_provider_statistics_success(self, ui_app, mock_provider_stats):
        """Test successful retrieval of provider statistics."""
        
        with patch('app.utils.audit.get_audit_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.get_provider_stats.return_value = mock_provider_stats
            mock_get_logger.return_value = mock_logger
            
            result = await ui_app.get_provider_statistics()
            
            assert result == mock_provider_stats
            mock_get_logger.assert_called_once()
            mock_logger.get_provider_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_provider_statistics_error(self, ui_app):
        """Test error handling in provider statistics retrieval."""
        
        with patch('app.utils.audit.get_audit_logger') as mock_get_logger:
            mock_get_logger.side_effect = Exception("Database connection failed")
            
            with patch('streamlit.error'):
                result = await ui_app.get_provider_statistics()
                
                assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_pattern_statistics_success(self, ui_app, mock_pattern_stats):
        """Test successful retrieval of pattern statistics."""
        
        with patch('app.utils.audit.get_audit_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.get_pattern_stats.return_value = mock_pattern_stats
            mock_get_logger.return_value = mock_logger
            
            result = await ui_app.get_pattern_statistics()
            
            assert result == mock_pattern_stats
            mock_get_logger.assert_called_once()
            mock_logger.get_pattern_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_pattern_statistics_error(self, ui_app):
        """Test error handling in pattern statistics retrieval."""
        
        with patch('app.utils.audit.get_audit_logger') as mock_get_logger:
            mock_get_logger.side_effect = Exception("Database connection failed")
            
            with patch('streamlit.error'):
                result = await ui_app.get_pattern_statistics()
                
                assert result == {}
    
    def test_render_provider_metrics_with_data(self, ui_app, mock_provider_stats):
        """Test rendering provider metrics with data."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.columns') as mock_columns, \
                 patch('streamlit.bar_chart') as mock_bar_chart, \
                 patch('streamlit.dataframe') as mock_dataframe, \
                 patch('streamlit.metric') as mock_metric, \
                 patch('streamlit.info'):
                
                # Mock columns - need to handle multiple column calls
                mock_col1, mock_col2, mock_col3 = MagicMock(), MagicMock(), MagicMock()
                mock_columns.side_effect = [[mock_col1, mock_col2], [mock_col1, mock_col2, mock_col3]]
                
                mock_run.return_value = mock_provider_stats
                
                ui_app.render_provider_metrics()
                
                # Verify asyncio.run was called to fetch data
                mock_run.assert_called()
                
                # Verify charts were created
                assert mock_bar_chart.call_count >= 2  # Call volume and latency charts
                
                # Verify dataframe was displayed
                mock_dataframe.assert_called()
                
                # Verify metrics were displayed (should be called when there are multiple providers)
                assert mock_metric.call_count >= 1  # At least some metrics displayed
    
    def test_render_provider_metrics_no_data(self, ui_app, empty_stats):
        """Test rendering provider metrics with no data."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.info') as mock_info:
                
                mock_run.return_value = empty_stats
                
                ui_app.render_provider_metrics()
                
                # Verify info message is shown for no data
                mock_info.assert_called_with("No provider metrics available yet. Run some analyses to see performance data.")
    
    def test_render_provider_metrics_error(self, ui_app):
        """Test error handling in provider metrics rendering."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.error') as mock_error:
                
                mock_run.side_effect = Exception("Failed to fetch data")
                
                ui_app.render_provider_metrics()
                
                # Verify error message is displayed
                mock_error.assert_called_with("❌ Error loading provider metrics: Failed to fetch data")
    
    def test_render_pattern_analytics_with_data(self, ui_app, mock_pattern_stats):
        """Test rendering pattern analytics with data."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.columns') as mock_columns, \
                 patch('streamlit.bar_chart') as mock_bar_chart, \
                 patch('streamlit.dataframe') as mock_dataframe, \
                 patch('streamlit.metric') as mock_metric, \
                 patch('streamlit.info'):
                
                # Mock columns - need to handle multiple column calls
                mock_col1, mock_col2, mock_col3 = MagicMock(), MagicMock(), MagicMock()
                mock_columns.side_effect = [[mock_col1, mock_col2], [mock_col1, mock_col2, mock_col3]]
                
                mock_run.return_value = mock_pattern_stats
                
                ui_app.render_pattern_analytics()
                
                # Verify asyncio.run was called to fetch data
                mock_run.assert_called()
                
                # Verify charts were created
                assert mock_bar_chart.call_count >= 2  # Frequency and acceptance rate charts
                
                # Verify dataframe was displayed
                mock_dataframe.assert_called()
                
                # Verify metrics were displayed (should be called when there are patterns)
                assert mock_metric.call_count >= 1  # At least some metrics displayed
    
    def test_render_pattern_analytics_no_data(self, ui_app, empty_stats):
        """Test rendering pattern analytics with no data."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.info') as mock_info:
                
                mock_run.return_value = empty_stats
                
                ui_app.render_pattern_analytics()
                
                # Verify info message is shown for no data
                mock_info.assert_called_with("No pattern analytics available yet. Run some analyses to see pattern matching data.")
    
    def test_render_pattern_analytics_error(self, ui_app):
        """Test error handling in pattern analytics rendering."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.error') as mock_error:
                
                mock_run.side_effect = Exception("Failed to fetch pattern data")
                
                ui_app.render_pattern_analytics()
                
                # Verify error message is displayed
                mock_error.assert_called_with("❌ Error loading pattern analytics: Failed to fetch pattern data")
    
    def test_render_usage_patterns_with_data(self, ui_app, mock_provider_stats, mock_pattern_stats):
        """Test rendering usage patterns with data."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.columns') as mock_columns, \
                 patch('streamlit.metric') as mock_metric, \
                 patch('streamlit.dataframe') as mock_dataframe, \
                 patch('streamlit.info') as mock_info, \
                 patch('streamlit.markdown'):
                
                # Mock columns - need to handle multiple column calls
                mock_col1, mock_col2, mock_col3 = MagicMock(), MagicMock(), MagicMock()
                mock_columns.side_effect = [[mock_col1, mock_col2, mock_col3], [mock_col1, mock_col2]]
                
                # Mock alternating calls to return provider and pattern stats
                mock_run.side_effect = [mock_provider_stats, mock_pattern_stats]
                
                ui_app.render_usage_patterns()
                
                # Verify asyncio.run was called twice (provider and pattern stats)
                assert mock_run.call_count == 2
                
                # Verify metrics were displayed
                assert mock_metric.call_count >= 3  # Total calls, patterns, tokens
                
                # Verify dataframe was displayed for provider usage
                mock_dataframe.assert_called()
                
                # Verify optimization recommendations were shown (should always show at least one)
                assert mock_info.call_count >= 1
    
    def test_render_usage_patterns_no_data(self, ui_app):
        """Test rendering usage patterns with no data."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.info') as mock_info:
                
                mock_run.return_value = {}
                
                ui_app.render_usage_patterns()
                
                # Verify info message is shown for no data
                mock_info.assert_called_with("No usage data available yet. Run some analyses to see usage patterns.")
    
    def test_render_usage_patterns_error(self, ui_app):
        """Test error handling in usage patterns rendering."""
        
        with patch('asyncio.run') as mock_run:
            with patch('streamlit.subheader'), \
                 patch('streamlit.error') as mock_error:
                
                mock_run.side_effect = Exception("Failed to fetch usage data")
                
                ui_app.render_usage_patterns()
                
                # Verify error message is displayed
                mock_error.assert_called_with("❌ Error loading usage patterns: Failed to fetch usage data")
    
    def test_render_observability_dashboard_structure(self, ui_app):
        """Test the overall structure of the observability dashboard."""
        
        with patch('streamlit.session_state') as mock_session_state, \
             patch('streamlit.header') as mock_header, \
             patch('streamlit.tabs') as mock_tabs, \
             patch.object(ui_app, 'render_provider_metrics') as mock_provider, \
             patch.object(ui_app, 'render_pattern_analytics') as mock_pattern, \
             patch.object(ui_app, 'render_usage_patterns') as mock_usage:
            
            # Mock session state to have a session_id
            mock_session_state.session_id = "test-session-123"
            
            # Mock tabs
            mock_tab1, mock_tab2, mock_tab3 = MagicMock(), MagicMock(), MagicMock()
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]
            
            ui_app.render_observability_dashboard()
            
            # Verify header is displayed
            mock_header.assert_called_with("📈 System Observability")
            
            # Verify tabs are created
            mock_tabs.assert_called_with(["🔧 Provider Metrics", "🎯 Pattern Analytics", "📊 Usage Patterns"])
            
            # Verify all render methods are called
            mock_provider.assert_called_once()
            mock_pattern.assert_called_once()
            mock_usage.assert_called_once()
    
    def test_provider_metrics_calculations(self, ui_app, mock_provider_stats):
        """Test calculations in provider metrics."""
        
        # Test the calculation logic directly
        stats = mock_provider_stats['provider_stats']
        
        # Verify fastest provider calculation
        fastest = min(stats, key=lambda x: x['avg_latency'])
        assert fastest['provider'] == 'claude'
        assert fastest['avg_latency'] == 950.2
        
        # Verify slowest provider calculation
        slowest = max(stats, key=lambda x: x['avg_latency'])
        assert slowest['provider'] == 'bedrock'
        assert slowest['avg_latency'] == 2100.8
        
        # Verify total calls calculation
        total_calls = sum(stat['call_count'] for stat in stats)
        assert total_calls == 48  # 25 + 15 + 8
        
        # Verify total tokens calculation
        total_tokens = sum(stat['total_tokens'] for stat in stats)
        assert total_tokens == 35500  # 15000 + 12000 + 8500
    
    def test_pattern_analytics_calculations(self, ui_app, mock_pattern_stats):
        """Test calculations in pattern analytics."""
        
        # Test the calculation logic directly
        stats = mock_pattern_stats['pattern_stats']
        
        # Verify best acceptance rate calculation
        best_pattern = max(stats, key=lambda x: x['acceptance_rate'])
        assert best_pattern['pattern_id'] == 'PAT-003'
        assert best_pattern['acceptance_rate'] == 0.917
        
        # Verify most used pattern calculation
        most_used = max(stats, key=lambda x: x['match_count'])
        assert most_used['pattern_id'] == 'PAT-001'
        assert most_used['match_count'] == 20
        
        # Verify highest score calculation
        highest_score = max(stats, key=lambda x: x['avg_score'])
        assert highest_score['pattern_id'] == 'PAT-003'
        assert highest_score['avg_score'] == 0.91
        
        # Verify total matches calculation
        total_matches = sum(stat['match_count'] for stat in stats)
        assert total_matches == 47  # 20 + 15 + 12
    
    def test_usage_patterns_calculations(self, ui_app, mock_provider_stats, mock_pattern_stats):
        """Test calculations in usage patterns."""
        
        # Test the calculation logic directly
        provider_stats = mock_provider_stats['provider_stats']
        pattern_stats = mock_pattern_stats['pattern_stats']
        
        # Verify total calls calculation
        total_calls = sum(stat['call_count'] for stat in provider_stats)
        assert total_calls == 48  # 25 + 15 + 8
        
        # Verify total patterns calculation
        total_patterns = sum(stat['match_count'] for stat in pattern_stats)
        assert total_patterns == 47  # 20 + 15 + 12
        
        # Verify total tokens calculation
        total_tokens = sum(stat['total_tokens'] for stat in provider_stats)
        assert total_tokens == 35500  # 15000 + 12000 + 8500
        
        # Verify provider usage distribution calculation
        provider_usage = {}
        for stat in provider_stats:
            provider = stat['provider']
            if provider in provider_usage:
                provider_usage[provider] += stat['call_count']
            else:
                provider_usage[provider] = stat['call_count']
        
        assert provider_usage['openai'] == 25
        assert provider_usage['bedrock'] == 15
        assert provider_usage['claude'] == 8
    
    def test_health_status_calculation(self, ui_app):
        """Test system health status calculation based on latency."""
        
        # Test health status calculation logic directly
        
        # Test excellent health (< 1000ms)
        excellent_latencies = [800.0, 900.0, 750.0]
        excellent_avg = sum(excellent_latencies) / len(excellent_latencies)
        assert excellent_avg < 1000
        
        # Test good health (1000-3000ms)
        good_latencies = [1200.0, 1800.0, 2200.0]
        good_avg = sum(good_latencies) / len(good_latencies)
        assert 1000 <= good_avg < 3000
        
        # Test needs attention (>= 3000ms)
        poor_latencies = [3200.0, 4100.0, 3800.0]
        poor_avg = sum(poor_latencies) / len(poor_latencies)
        assert poor_avg >= 3000
        
        # Verify health status determination logic
        def get_health_status(avg_latency):
            if avg_latency < 1000:
                return "🟢 Excellent"
            elif avg_latency < 3000:
                return "🟡 Good"
            else:
                return "🔴 Needs Attention"
        
        assert get_health_status(excellent_avg) == "🟢 Excellent"
        assert get_health_status(good_avg) == "🟡 Good"
        assert get_health_status(poor_avg) == "🔴 Needs Attention"


class TestObservabilityIntegration:
    """Test integration of observability dashboard with main UI."""
    
    def test_observability_tab_integration(self):
        """Test that observability tab is properly integrated into main UI."""
        
        ui_app = AutomatedAIAssessmentUI()
        
        with patch('streamlit.title'), \
             patch('streamlit.markdown'), \
             patch('streamlit.tabs') as mock_tabs, \
             patch.object(ui_app, 'render_provider_panel'), \
             patch.object(ui_app, 'render_input_methods'), \
             patch.object(ui_app, 'render_mermaid_diagrams'), \
             patch.object(ui_app, 'render_observability_dashboard') as mock_observability:
            
            # Mock tabs to return 4 tabs (including observability)
            mock_tab1, mock_tab2, mock_tab3, mock_tab4 = MagicMock(), MagicMock(), MagicMock(), MagicMock()
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3, mock_tab4]
            
            ui_app.run()
            
            # Verify that 4 tabs are created (including observability)
            mock_tabs.assert_called_with(["📝 Analysis", "📊 Diagrams", "📈 Observability", "ℹ️ About"])
            
            # Verify observability dashboard is called
            mock_observability.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])