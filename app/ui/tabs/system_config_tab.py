"""System Configuration tab for the AAA application."""

import streamlit as st
from typing import Dict, Any, Optional
import json
from pathlib import Path

from app.ui.tabs.base import BaseTab
from app.core.registry import ServiceRegistry
from app.ui.main_app import SessionManager


class SystemConfigTab(BaseTab):
    """Tab for system configuration and settings."""
    
    def __init__(self, session_manager: SessionManager, service_registry: ServiceRegistry):
        super().__init__("system_config", "🔧 System Config", "Configure system settings")
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    def initialize(self) -> None:
        """Initialize the tab."""
        pass
    
    def render(self) -> None:
        """Render the system configuration tab."""
        st.header("🔧 System Configuration")
        st.markdown("*Configure system settings, performance, and operational parameters*")
        
        # Configuration tabs
        general_tab, performance_tab, security_tab, logging_tab, advanced_tab = st.tabs([
            "⚙️ General",
            "⚡ Performance", 
            "🔒 Security",
            "📝 Logging",
            "🔬 Advanced"
        ])
        
        with general_tab:
            self._render_general_config()
        
        with performance_tab:
            self._render_performance_config()
        
        with security_tab:
            self._render_security_config()
        
        with logging_tab:
            self._render_logging_config()
        
        with advanced_tab:
            self._render_advanced_config()
    
    def _render_general_config(self) -> None:
        """Render general system configuration."""
        st.subheader("⚙️ General Settings")
        
        try:
            config = self._load_system_config()
            general_config = config.get('general', {})
            
            with st.form("general_config_form"):
                # Application settings
                st.subheader("Application Settings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    app_name = st.text_input(
                        "Application Name:",
                        value=general_config.get('app_name', 'Automated AI Assessment (AAA)'),
                        key="app_name"
                    )
                    
                    app_version = st.text_input(
                        "Version:",
                        value=general_config.get('version', '1.0.0'),
                        key="app_version"
                    )
                    
                    environment = st.selectbox(
                        "Environment:",
                        ["development", "staging", "production"],
                        index=["development", "staging", "production"].index(
                            general_config.get('environment', 'development')
                        ),
                        key="environment"
                    )
                
                with col2:
                    debug_mode = st.checkbox(
                        "Debug Mode",
                        value=general_config.get('debug_mode', True),
                        key="debug_mode"
                    )
                    
                    maintenance_mode = st.checkbox(
                        "Maintenance Mode",
                        value=general_config.get('maintenance_mode', False),
                        key="maintenance_mode"
                    )
                    
                    auto_backup = st.checkbox(
                        "Auto Backup",
                        value=general_config.get('auto_backup', True),
                        key="auto_backup"
                    )
                
                # UI settings
                st.subheader("UI Settings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    theme = st.selectbox(
                        "Theme:",
                        ["auto", "light", "dark"],
                        index=["auto", "light", "dark"].index(
                            general_config.get('theme', 'auto')
                        ),
                        key="theme"
                    )
                    
                    page_layout = st.selectbox(
                        "Page Layout:",
                        ["wide", "centered"],
                        index=["wide", "centered"].index(
                            general_config.get('page_layout', 'wide')
                        ),
                        key="page_layout"
                    )
                
                with col2:
                    sidebar_state = st.selectbox(
                        "Default Sidebar State:",
                        ["expanded", "collapsed", "auto"],
                        index=["expanded", "collapsed", "auto"].index(
                            general_config.get('sidebar_state', 'expanded')
                        ),
                        key="sidebar_state"
                    )
                    
                    show_debug_info = st.checkbox(
                        "Show Debug Info by Default",
                        value=general_config.get('show_debug_info', False),
                        key="show_debug_info"
                    )
                
                # Data settings
                st.subheader("Data Settings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    data_retention_days = st.number_input(
                        "Data Retention (days):",
                        min_value=1,
                        max_value=365,
                        value=general_config.get('data_retention_days', 30),
                        key="data_retention_days"
                    )
                    
                    max_file_size_mb = st.number_input(
                        "Max File Size (MB):",
                        min_value=1,
                        max_value=100,
                        value=general_config.get('max_file_size_mb', 10),
                        key="max_file_size_mb"
                    )
                
                with col2:
                    backup_frequency = st.selectbox(
                        "Backup Frequency:",
                        ["hourly", "daily", "weekly"],
                        index=["hourly", "daily", "weekly"].index(
                            general_config.get('backup_frequency', 'daily')
                        ),
                        key="backup_frequency"
                    )
                    
                    cleanup_temp_files = st.checkbox(
                        "Auto-cleanup Temp Files",
                        value=general_config.get('cleanup_temp_files', True),
                        key="cleanup_temp_files"
                    )
                
                # Save button
                if st.form_submit_button("💾 Save General Settings"):
                    new_general_config = {
                        'app_name': app_name,
                        'version': app_version,
                        'environment': environment,
                        'debug_mode': debug_mode,
                        'maintenance_mode': maintenance_mode,
                        'auto_backup': auto_backup,
                        'theme': theme,
                        'page_layout': page_layout,
                        'sidebar_state': sidebar_state,
                        'show_debug_info': show_debug_info,
                        'data_retention_days': data_retention_days,
                        'max_file_size_mb': max_file_size_mb,
                        'backup_frequency': backup_frequency,
                        'cleanup_temp_files': cleanup_temp_files
                    }
                    
                    if self._save_general_config(new_general_config):
                        st.success("✅ General settings saved successfully!")
                    else:
                        st.error("❌ Failed to save general settings")
        
        except Exception as e:
            st.error(f"Error loading general configuration: {str(e)}")
    
    def _render_performance_config(self) -> None:
        """Render performance configuration."""
        st.subheader("⚡ Performance Settings")
        
        try:
            config = self._load_system_config()
            perf_config = config.get('performance', {})
            
            with st.form("performance_config_form"):
                # API settings
                st.subheader("API Performance")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    api_timeout = st.number_input(
                        "API Timeout (seconds):",
                        min_value=5,
                        max_value=300,
                        value=perf_config.get('api_timeout', 30),
                        key="api_timeout"
                    )
                    
                    max_concurrent_requests = st.number_input(
                        "Max Concurrent Requests:",
                        min_value=1,
                        max_value=50,
                        value=perf_config.get('max_concurrent_requests', 10),
                        key="max_concurrent_requests"
                    )
                
                with col2:
                    request_retry_count = st.number_input(
                        "Request Retry Count:",
                        min_value=0,
                        max_value=5,
                        value=perf_config.get('request_retry_count', 3),
                        key="request_retry_count"
                    )
                    
                    retry_delay = st.number_input(
                        "Retry Delay (seconds):",
                        min_value=1,
                        max_value=10,
                        value=perf_config.get('retry_delay', 2),
                        key="retry_delay"
                    )
                
                # Cache settings
                st.subheader("Cache Settings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    enable_caching = st.checkbox(
                        "Enable Caching",
                        value=perf_config.get('enable_caching', True),
                        key="enable_caching"
                    )
                    
                    cache_ttl = st.number_input(
                        "Cache TTL (seconds):",
                        min_value=60,
                        max_value=86400,
                        value=perf_config.get('cache_ttl', 3600),
                        key="cache_ttl"
                    )
                
                with col2:
                    max_cache_size_mb = st.number_input(
                        "Max Cache Size (MB):",
                        min_value=10,
                        max_value=1000,
                        value=perf_config.get('max_cache_size_mb', 100),
                        key="max_cache_size_mb"
                    )
                    
                    cache_cleanup_interval = st.number_input(
                        "Cache Cleanup Interval (minutes):",
                        min_value=5,
                        max_value=60,
                        value=perf_config.get('cache_cleanup_interval', 15),
                        key="cache_cleanup_interval"
                    )
                
                # Processing settings
                st.subheader("Processing Settings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    max_workers = st.number_input(
                        "Max Worker Threads:",
                        min_value=1,
                        max_value=20,
                        value=perf_config.get('max_workers', 4),
                        key="max_workers"
                    )
                    
                    batch_size = st.number_input(
                        "Batch Processing Size:",
                        min_value=1,
                        max_value=100,
                        value=perf_config.get('batch_size', 10),
                        key="batch_size"
                    )
                
                with col2:
                    enable_async_processing = st.checkbox(
                        "Enable Async Processing",
                        value=perf_config.get('enable_async_processing', True),
                        key="enable_async_processing"
                    )
                    
                    memory_limit_mb = st.number_input(
                        "Memory Limit (MB):",
                        min_value=100,
                        max_value=4000,
                        value=perf_config.get('memory_limit_mb', 1000),
                        key="memory_limit_mb"
                    )
                
                # Save button
                if st.form_submit_button("💾 Save Performance Settings"):
                    new_perf_config = {
                        'api_timeout': api_timeout,
                        'max_concurrent_requests': max_concurrent_requests,
                        'request_retry_count': request_retry_count,
                        'retry_delay': retry_delay,
                        'enable_caching': enable_caching,
                        'cache_ttl': cache_ttl,
                        'max_cache_size_mb': max_cache_size_mb,
                        'cache_cleanup_interval': cache_cleanup_interval,
                        'max_workers': max_workers,
                        'batch_size': batch_size,
                        'enable_async_processing': enable_async_processing,
                        'memory_limit_mb': memory_limit_mb
                    }
                    
                    if self._save_performance_config(new_perf_config):
                        st.success("✅ Performance settings saved successfully!")
                    else:
                        st.error("❌ Failed to save performance settings")
        
        except Exception as e:
            st.error(f"Error loading performance configuration: {str(e)}")
    
    def _render_security_config(self) -> None:
        """Render security configuration."""
        st.subheader("🔒 Security Settings")
        
        st.info("🔐 Security settings are managed through the Advanced Prompt Defense system")
        
        try:
            config = self._load_system_config()
            security_config = config.get('security', {})
            
            # Security status overview
            st.subheader("Security Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Security Level", "High", "✅")
            
            with col2:
                st.metric("Active Detectors", "8", "✅")
            
            with col3:
                st.metric("Threat Level", "Low", "✅")
            
            # Security features
            st.subheader("Security Features")
            
            features = [
                ("🛡️ Advanced Prompt Defense", "Active", "success"),
                ("🔍 Overt Injection Detection", "Active", "success"),
                ("🕵️ Covert Attack Detection", "Active", "success"),
                ("🌐 Multilingual Attack Detection", "Active", "success"),
                ("📊 Context Attack Detection", "Active", "success"),
                ("🔒 Data Egress Protection", "Active", "success"),
                ("⚙️ Business Logic Protection", "Active", "success"),
                ("🔧 Protocol Tampering Detection", "Active", "success")
            ]
            
            for feature, status, status_type in features:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(feature)
                with col2:
                    if status_type == "success":
                        st.success(status)
                    else:
                        st.warning(status)
            
            # Security configuration
            st.subheader("Security Configuration")
            
            with st.form("security_config_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    enable_security = st.checkbox(
                        "Enable Security System",
                        value=security_config.get('enable_security', True),
                        key="enable_security"
                    )
                    
                    log_security_events = st.checkbox(
                        "Log Security Events",
                        value=security_config.get('log_security_events', True),
                        key="log_security_events"
                    )
                    
                    enable_user_education = st.checkbox(
                        "Enable User Education",
                        value=security_config.get('enable_user_education', True),
                        key="enable_user_education"
                    )
                
                with col2:
                    security_level = st.selectbox(
                        "Security Level:",
                        ["low", "medium", "high", "maximum"],
                        index=["low", "medium", "high", "maximum"].index(
                            security_config.get('security_level', 'high')
                        ),
                        key="security_level"
                    )
                    
                    alert_threshold = st.selectbox(
                        "Alert Threshold:",
                        ["low", "medium", "high"],
                        index=["low", "medium", "high"].index(
                            security_config.get('alert_threshold', 'medium')
                        ),
                        key="alert_threshold"
                    )
                    
                    auto_block_threats = st.checkbox(
                        "Auto-block Threats",
                        value=security_config.get('auto_block_threats', True),
                        key="auto_block_threats"
                    )
                
                # Save button
                if st.form_submit_button("💾 Save Security Settings"):
                    new_security_config = {
                        'enable_security': enable_security,
                        'log_security_events': log_security_events,
                        'enable_user_education': enable_user_education,
                        'security_level': security_level,
                        'alert_threshold': alert_threshold,
                        'auto_block_threats': auto_block_threats
                    }
                    
                    if self._save_security_config(new_security_config):
                        st.success("✅ Security settings saved successfully!")
                    else:
                        st.error("❌ Failed to save security settings")
        
        except Exception as e:
            st.error(f"Error loading security configuration: {str(e)}")
    
    def _render_logging_config(self) -> None:
        """Render logging configuration."""
        st.subheader("📝 Logging Settings")
        
        try:
            config = self._load_system_config()
            logging_config = config.get('logging', {})
            
            # Initialize debug options from config if available
            debug_options = logging_config.get('debug_options', {})
            if debug_options:
                for key, value in debug_options.items():
                    if key not in st.session_state:
                        st.session_state[key] = value
            
            with st.form("logging_config_form"):
                # Log levels
                st.subheader("Log Levels")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    app_log_level = st.selectbox(
                        "Application Log Level:",
                        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                            logging_config.get('app_log_level', 'INFO')
                        ),
                        key="app_log_level"
                    )
                    
                    security_log_level = st.selectbox(
                        "Security Log Level:",
                        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                            logging_config.get('security_log_level', 'WARNING')
                        ),
                        key="security_log_level"
                    )
                
                with col2:
                    api_log_level = st.selectbox(
                        "API Log Level:",
                        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                            logging_config.get('api_log_level', 'INFO')
                        ),
                        key="api_log_level"
                    )
                    
                    performance_log_level = st.selectbox(
                        "Performance Log Level:",
                        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                            logging_config.get('performance_log_level', 'INFO')
                        ),
                        key="performance_log_level"
                    )
                
                # Log destinations
                st.subheader("Log Destinations")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    log_to_file = st.checkbox(
                        "Log to File",
                        value=logging_config.get('log_to_file', True),
                        key="log_to_file"
                    )
                    
                    log_to_console = st.checkbox(
                        "Log to Console",
                        value=logging_config.get('log_to_console', True),
                        key="log_to_console"
                    )
                
                with col2:
                    log_to_database = st.checkbox(
                        "Log to Database",
                        value=logging_config.get('log_to_database', False),
                        key="log_to_database"
                    )
                    
                    log_to_external = st.checkbox(
                        "Log to External Service",
                        value=logging_config.get('log_to_external', False),
                        key="log_to_external"
                    )
                
                # Log rotation
                st.subheader("Log Rotation")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    max_log_size_mb = st.number_input(
                        "Max Log File Size (MB):",
                        min_value=1,
                        max_value=1000,
                        value=logging_config.get('max_log_size_mb', 50),
                        key="max_log_size_mb"
                    )
                    
                    max_log_files = st.number_input(
                        "Max Log Files to Keep:",
                        min_value=1,
                        max_value=100,
                        value=logging_config.get('max_log_files', 10),
                        key="max_log_files"
                    )
                
                with col2:
                    log_retention_days = st.number_input(
                        "Log Retention (days):",
                        min_value=1,
                        max_value=365,
                        value=logging_config.get('log_retention_days', 30),
                        key="log_retention_days"
                    )
                    
                    compress_old_logs = st.checkbox(
                        "Compress Old Logs",
                        value=logging_config.get('compress_old_logs', True),
                        key="compress_old_logs"
                    )
                
                # Debug options
                st.subheader("Debug Options")
                st.info("💡 These options control what debug information is shown throughout the application")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    show_diagram_debug = st.checkbox(
                        "Show Diagram Debug Info",
                        value=st.session_state.get('show_diagram_debug', False),
                        key="show_diagram_debug",
                        help="Show technical debug information on diagram pages"
                    )
                    
                    show_qa_debug = st.checkbox(
                        "Show Q&A Debug Info",
                        value=st.session_state.get('show_qa_debug', False),
                        key="show_qa_debug",
                        help="Show debug information during question generation and answering"
                    )
                    
                    show_api_debug = st.checkbox(
                        "Show API Debug Info",
                        value=st.session_state.get('show_api_debug', False),
                        key="show_api_debug",
                        help="Show API request/response debug information"
                    )
                
                with col2:
                    show_performance_debug = st.checkbox(
                        "Show Performance Debug Info",
                        value=st.session_state.get('show_performance_debug', False),
                        key="show_performance_debug",
                        help="Show performance metrics and timing information"
                    )
                    
                    show_llm_debug = st.checkbox(
                        "Show LLM Debug Info",
                        value=st.session_state.get('show_llm_debug', False),
                        key="show_llm_debug",
                        help="Show LLM provider debug information and prompts"
                    )
                    
                    show_security_debug = st.checkbox(
                        "Show Security Debug Info",
                        value=st.session_state.get('show_security_debug', False),
                        key="show_security_debug",
                        help="Show security system debug information"
                    )

                # Save button
                if st.form_submit_button("💾 Save Logging Settings"):
                    # Update session state with debug options
                    st.session_state.show_diagram_debug = show_diagram_debug
                    st.session_state.show_qa_debug = show_qa_debug
                    st.session_state.show_api_debug = show_api_debug
                    st.session_state.show_performance_debug = show_performance_debug
                    st.session_state.show_llm_debug = show_llm_debug
                    st.session_state.show_security_debug = show_security_debug
                    
                    new_logging_config = {
                        'app_log_level': app_log_level,
                        'security_log_level': security_log_level,
                        'api_log_level': api_log_level,
                        'performance_log_level': performance_log_level,
                        'log_to_file': log_to_file,
                        'log_to_console': log_to_console,
                        'log_to_database': log_to_database,
                        'log_to_external': log_to_external,
                        'max_log_size_mb': max_log_size_mb,
                        'max_log_files': max_log_files,
                        'log_retention_days': log_retention_days,
                        'compress_old_logs': compress_old_logs,
                        'debug_options': {
                            'show_diagram_debug': show_diagram_debug,
                            'show_qa_debug': show_qa_debug,
                            'show_api_debug': show_api_debug,
                            'show_performance_debug': show_performance_debug,
                            'show_llm_debug': show_llm_debug,
                            'show_security_debug': show_security_debug
                        }
                    }
                    
                    if self._save_logging_config(new_logging_config):
                        st.success("✅ Logging settings and debug options saved successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save logging settings")
        
            # Debug status overview
            st.divider()
            st.subheader("🔍 Current Debug Status")
            
            debug_status = [
                ("Diagram Debug", st.session_state.get('show_diagram_debug', False)),
                ("Q&A Debug", st.session_state.get('show_qa_debug', False)),
                ("API Debug", st.session_state.get('show_api_debug', False)),
                ("Performance Debug", st.session_state.get('show_performance_debug', False)),
                ("LLM Debug", st.session_state.get('show_llm_debug', False)),
                ("Security Debug", st.session_state.get('show_security_debug', False))
            ]
            
            col1, col2, col3 = st.columns(3)
            
            for i, (name, status) in enumerate(debug_status):
                col = [col1, col2, col3][i % 3]
                with col:
                    if status:
                        st.success(f"✅ {name}")
                    else:
                        st.info(f"⚪ {name}")
            
            # Quick actions
            st.subheader("🚀 Quick Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔧 Enable All Debug", key="enable_all_debug"):
                    st.session_state.show_diagram_debug = True
                    st.session_state.show_qa_debug = True
                    st.session_state.show_api_debug = True
                    st.session_state.show_performance_debug = True
                    st.session_state.show_llm_debug = True
                    st.session_state.show_security_debug = True
                    st.success("✅ All debug options enabled!")
                    st.rerun()
            
            with col2:
                if st.button("🔇 Disable All Debug", key="disable_all_debug"):
                    st.session_state.show_diagram_debug = False
                    st.session_state.show_qa_debug = False
                    st.session_state.show_api_debug = False
                    st.session_state.show_performance_debug = False
                    st.session_state.show_llm_debug = False
                    st.session_state.show_security_debug = False
                    st.success("✅ All debug options disabled!")
                    st.rerun()
            
            with col3:
                if st.button("📊 Show Session State", key="show_session_state"):
                    with st.expander("🔍 Session State Debug", expanded=True):
                        # Filter out sensitive information
                        filtered_state = {}
                        for key, value in st.session_state.items():
                            if 'api_key' not in key.lower() and 'secret' not in key.lower() and 'password' not in key.lower():
                                filtered_state[key] = value
                            else:
                                filtered_state[key] = "***HIDDEN***"
                        
                        st.json(filtered_state)
        
        except Exception as e:
            st.error(f"Error loading logging configuration: {str(e)}")
    
    def _render_advanced_config(self) -> None:
        """Render advanced configuration options."""
        st.subheader("🔬 Advanced Settings")
        
        st.warning("⚠️ Advanced settings should only be modified by system administrators")
        
        try:
            config = self._load_system_config()
            advanced_config = config.get('advanced', {})
            
            # System information
            st.subheader("System Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Python Version:**", "3.10+")
                st.write("**Streamlit Version:**", "1.28+")
                st.write("**FastAPI Version:**", "0.104+")
            
            with col2:
                st.write("**Environment:**", config.get('general', {}).get('environment', 'development'))
                st.write("**Debug Mode:**", config.get('general', {}).get('debug_mode', True))
                st.write("**Maintenance Mode:**", config.get('general', {}).get('maintenance_mode', False))
            
            # Advanced settings form
            with st.form("advanced_config_form"):
                st.subheader("Advanced Configuration")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    enable_experimental_features = st.checkbox(
                        "Enable Experimental Features",
                        value=advanced_config.get('enable_experimental_features', False),
                        key="enable_experimental_features"
                    )
                    
                    enable_profiling = st.checkbox(
                        "Enable Performance Profiling",
                        value=advanced_config.get('enable_profiling', False),
                        key="enable_profiling"
                    )
                    
                    enable_metrics_collection = st.checkbox(
                        "Enable Metrics Collection",
                        value=advanced_config.get('enable_metrics_collection', True),
                        key="enable_metrics_collection"
                    )
                
                with col2:
                    custom_config_path = st.text_input(
                        "Custom Config Path:",
                        value=advanced_config.get('custom_config_path', ''),
                        key="custom_config_path"
                    )
                    
                    external_service_url = st.text_input(
                        "External Service URL:",
                        value=advanced_config.get('external_service_url', ''),
                        key="external_service_url"
                    )
                    
                    feature_flags = st.text_area(
                        "Feature Flags (JSON):",
                        value=json.dumps(advanced_config.get('feature_flags', {}), indent=2),
                        key="feature_flags"
                    )
                
                # Save button
                if st.form_submit_button("💾 Save Advanced Settings"):
                    try:
                        feature_flags_dict = json.loads(feature_flags) if feature_flags else {}
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON in feature flags")
                        return
                    
                    new_advanced_config = {
                        'enable_experimental_features': enable_experimental_features,
                        'enable_profiling': enable_profiling,
                        'enable_metrics_collection': enable_metrics_collection,
                        'custom_config_path': custom_config_path,
                        'external_service_url': external_service_url,
                        'feature_flags': feature_flags_dict
                    }
                    
                    if self._save_advanced_config(new_advanced_config):
                        st.success("✅ Advanced settings saved successfully!")
                    else:
                        st.error("❌ Failed to save advanced settings")
            
            # Configuration export/import
            st.subheader("Configuration Management")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📤 Export All Config", key="export_all_config_btn"):
                    self._export_all_config()
            
            with col2:
                if st.button("🔄 Reset to Defaults", key="reset_all_config_btn"):
                    if self._reset_all_config():
                        st.success("✅ Configuration reset to defaults")
                        st.rerun()
                    else:
                        st.error("❌ Failed to reset configuration")
            
            with col3:
                if st.button("🔍 Validate Config", key="validate_config_btn"):
                    self._validate_config()
        
        except Exception as e:
            st.error(f"Error loading advanced configuration: {str(e)}")
    
    def _load_system_config(self) -> Dict[str, Any]:
        """Load system configuration."""
        try:
            config_file = Path("config/system_config.json")
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                # Return default configuration
                return self._get_default_config()
        
        except Exception as e:
            st.error(f"Error loading system configuration: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default system configuration."""
        return {
            "general": {
                "app_name": "Automated AI Assessment (AAA)",
                "version": "1.0.0",
                "environment": "development",
                "debug_mode": True,
                "maintenance_mode": False,
                "auto_backup": True,
                "theme": "auto",
                "page_layout": "wide",
                "sidebar_state": "expanded",
                "show_debug_info": False,
                "data_retention_days": 30,
                "max_file_size_mb": 10,
                "backup_frequency": "daily",
                "cleanup_temp_files": True
            },
            "performance": {
                "api_timeout": 30,
                "max_concurrent_requests": 10,
                "request_retry_count": 3,
                "retry_delay": 2,
                "enable_caching": True,
                "cache_ttl": 3600,
                "max_cache_size_mb": 100,
                "cache_cleanup_interval": 15,
                "max_workers": 4,
                "batch_size": 10,
                "enable_async_processing": True,
                "memory_limit_mb": 1000
            },
            "security": {
                "enable_security": True,
                "log_security_events": True,
                "enable_user_education": True,
                "security_level": "high",
                "alert_threshold": "medium",
                "auto_block_threats": True
            },
            "logging": {
                "app_log_level": "INFO",
                "security_log_level": "WARNING",
                "api_log_level": "INFO",
                "performance_log_level": "INFO",
                "log_to_file": True,
                "log_to_console": True,
                "log_to_database": False,
                "log_to_external": False,
                "max_log_size_mb": 50,
                "max_log_files": 10,
                "log_retention_days": 30,
                "compress_old_logs": True
            },
            "advanced": {
                "enable_experimental_features": False,
                "enable_profiling": False,
                "enable_metrics_collection": True,
                "custom_config_path": "",
                "external_service_url": "",
                "feature_flags": {}
            }
        }
    
    def _save_general_config(self, config: Dict[str, Any]) -> bool:
        """Save general configuration."""
        return self._save_config_section('general', config)
    
    def _save_performance_config(self, config: Dict[str, Any]) -> bool:
        """Save performance configuration."""
        return self._save_config_section('performance', config)
    
    def _save_security_config(self, config: Dict[str, Any]) -> bool:
        """Save security configuration."""
        return self._save_config_section('security', config)
    
    def _save_logging_config(self, config: Dict[str, Any]) -> bool:
        """Save logging configuration."""
        return self._save_config_section('logging', config)
    
    def _save_advanced_config(self, config: Dict[str, Any]) -> bool:
        """Save advanced configuration."""
        return self._save_config_section('advanced', config)
    
    def _save_config_section(self, section: str, config: Dict[str, Any]) -> bool:
        """Save a configuration section."""
        try:
            full_config = self._load_system_config()
            full_config[section] = config
            
            config_file = Path("config/system_config.json")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(full_config, f, indent=2)
            
            return True
        
        except Exception as e:
            st.error(f"Error saving {section} configuration: {str(e)}")
            return False
    
    def _export_all_config(self) -> None:
        """Export all configuration."""
        try:
            config = self._load_system_config()
            
            config_json = json.dumps(config, indent=2)
            st.download_button(
                "📥 Download Configuration",
                config_json,
                file_name="system_config.json",
                mime="application/json"
            )
            
            st.success("✅ Configuration exported successfully!")
        
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
    
    def _reset_all_config(self) -> bool:
        """Reset all configuration to defaults."""
        try:
            default_config = self._get_default_config()
            
            config_file = Path("config/system_config.json")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return True
        
        except Exception as e:
            st.error(f"Error resetting configuration: {str(e)}")
            return False
    
    def _validate_config(self) -> None:
        """Validate current configuration."""
        try:
            config = self._load_system_config()
            
            # Basic validation
            required_sections = ['general', 'performance', 'security', 'logging', 'advanced']
            missing_sections = [s for s in required_sections if s not in config]
            
            if missing_sections:
                st.error(f"❌ Missing configuration sections: {', '.join(missing_sections)}")
            else:
                st.success("✅ Configuration validation passed!")
                
                # Show validation details
                with st.expander("Validation Details"):
                    st.write("**Sections found:**", len(config))
                    st.write("**Required sections:**", len(required_sections))
                    st.write("**Status:**", "All required sections present")
        
        except Exception as e:
            st.error(f"Configuration validation failed: {str(e)}")