# Service Registry Examples

This document provides practical examples of using the service registry in various scenarios.

## Table of Contents

1. [Basic Service Creation](#basic-service-creation)
2. [Service with Dependencies](#service-with-dependencies)
3. [Factory Services](#factory-services)
4. [Optional Services](#optional-services)
5. [Service Lifecycle Management](#service-lifecycle-management)
6. [Testing Examples](#testing-examples)
7. [Real-World Scenarios](#real-world-scenarios)

## Basic Service Creation

### Simple Configuration Service

```python
from app.core.service import ConfigurableService
from typing import Dict, Any
import yaml
import os

class ConfigService(ConfigurableService):
    """Simple configuration service that loads from YAML files."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "config")
        self._dependencies = []  # No dependencies
        self._config_data = {}
    
    def _do_initialize(self) -> None:
        """Load configuration from file."""
        config_file = self.get_config('config_file', 'config.yaml')
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            self._config_data = {}
        
        # Load environment overrides
        env_prefix = self.get_config('environment_prefix', 'APP')
        for key, value in os.environ.items():
            if key.startswith(f"{env_prefix}_"):
                config_key = key[len(env_prefix)+1:].lower().replace('_', '.')
                self._config_data[config_key] = value
    
    def _do_shutdown(self) -> None:
        """Clean up configuration data."""
        self._config_data.clear()
    
    def _do_health_check(self) -> bool:
        """Check if configuration is loaded."""
        return isinstance(self._config_data, dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split('.')
        config = self._config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration data."""
        return self._config_data.copy()

# Registration
from app.core.registry import get_registry

registry = get_registry()
config_service = ConfigService({
    'config_file': 'config.yaml',
    'environment_prefix': 'AAA'
})
registry.register_singleton('config', config_service)
```

### Simple Logger Service

```python
import logging
import sys
from app.core.service import ConfigurableService

class SimpleLoggerService(ConfigurableService):
    """Simple logger service with basic functionality."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "logger")
        self._dependencies = ["config"]
        self._logger = None
    
    def _do_initialize(self) -> None:
        """Initialize the logger."""
        # Get configuration
        config_service = require_service('config', context=self.name)
        
        level = config_service.get('logging.level', 'INFO')
        format_str = config_service.get('logging.format', 
                                       '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Set up logger
        self._logger = logging.getLogger('app')
        self._logger.setLevel(getattr(logging, level.upper()))
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(format_str)
        handler.setFormatter(formatter)
        
        self._logger.handlers.clear()
        self._logger.addHandler(handler)
    
    def _do_shutdown(self) -> None:
        """Clean up logger."""
        if self._logger:
            self._logger.handlers.clear()
    
    def _do_health_check(self) -> bool:
        """Check if logger is working."""
        return self._logger is not None
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        if self._logger:
            self._logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        if self._logger:
            self._logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        if self._logger:
            self._logger.debug(message, **kwargs)

# Registration
logger_service = SimpleLoggerService({})
registry.register_singleton('logger', logger_service, dependencies=['config'])
```

## Service with Dependencies

### Database Service

```python
import sqlite3
from typing import Dict, Any, List, Optional
from app.core.service import ConfigurableService
from app.utils.imports import require_service

class DatabaseService(ConfigurableService):
    """Database service with connection management."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "database")
        self._dependencies = ["config", "logger"]
        self._connection = None
        self._logger = None
    
    def _do_initialize(self) -> None:
        """Initialize database connection."""
        # Get dependencies
        config_service = require_service('config', context=self.name)
        self._logger = require_service('logger', context=self.name)
        
        # Get database configuration
        db_path = config_service.get('database.path', 'app.db')
        
        try:
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Create tables if needed
            self._create_tables()
            
            self._logger.info(f"Database connected: {db_path}")
            
        except Exception as e:
            self._logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _do_shutdown(self) -> None:
        """Close database connection."""
        if self._connection:
            try:
                self._connection.close()
                self._logger.info("Database connection closed")
            except Exception as e:
                self._logger.error(f"Error closing database: {e}")
    
    def _do_health_check(self) -> bool:
        """Check database connection."""
        try:
            if self._connection:
                cursor = self._connection.execute("SELECT 1")
                cursor.fetchone()
                return True
            return False
        except Exception:
            return False
    
    def _create_tables(self) -> None:
        """Create necessary tables."""
        cursor = self._connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self._connection.commit()
    
    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> sqlite3.Cursor:
        """Execute a query."""
        if not self._connection:
            raise RuntimeError("Database not connected")
        
        cursor = self._connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        self._connection.commit()
        return cursor
    
    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single row."""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# Registration
database_service = DatabaseService({})
registry.register_singleton('database', database_service, 
                           dependencies=['config', 'logger'])
```

### User Service (depends on Database)

```python
from app.core.service import ConfigurableService
from app.utils.imports import require_service
from typing import Dict, Any, Optional, List

class UserService(ConfigurableService):
    """User management service."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "user_service")
        self._dependencies = ["database", "logger"]
        self._db = None
        self._logger = None
    
    def _do_initialize(self) -> None:
        """Initialize user service."""
        self._db = require_service('database', context=self.name)
        self._logger = require_service('logger', context=self.name)
        
        self._logger.info("User service initialized")
    
    def _do_shutdown(self) -> None:
        """Shutdown user service."""
        self._logger.info("User service shutdown")
    
    def _do_health_check(self) -> bool:
        """Check if user service is healthy."""
        try:
            # Test database access
            self._db.execute("SELECT COUNT(*) FROM users")
            return True
        except Exception:
            return False
    
    def create_user(self, username: str, email: str) -> Dict[str, Any]:
        """Create a new user."""
        try:
            cursor = self._db.execute(
                "INSERT INTO users (username, email) VALUES (:username, :email)",
                {"username": username, "email": email}
            )
            
            user_id = cursor.lastrowid
            self._logger.info(f"Created user: {username} (ID: {user_id})")
            
            return self.get_user(user_id)
            
        except Exception as e:
            self._logger.error(f"Failed to create user {username}: {e}")
            raise
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return self._db.fetch_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": user_id}
        )
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return self._db.fetch_one(
            "SELECT * FROM users WHERE username = :username",
            {"username": username}
        )
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        return self._db.fetch_all("SELECT * FROM users ORDER BY created_at DESC")
    
    def update_user(self, user_id: int, **updates) -> Optional[Dict[str, Any]]:
        """Update user information."""
        if not updates:
            return self.get_user(user_id)
        
        # Build update query
        set_clauses = []
        params = {"id": user_id}
        
        for field, value in updates.items():
            if field in ['username', 'email']:
                set_clauses.append(f"{field} = :{field}")
                params[field] = value
        
        if not set_clauses:
            return self.get_user(user_id)
        
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = :id"
        self._db.execute(query, params)
        
        self._logger.info(f"Updated user {user_id}: {updates}")
        return self.get_user(user_id)
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        cursor = self._db.execute(
            "DELETE FROM users WHERE id = :id",
            {"id": user_id}
        )
        
        deleted = cursor.rowcount > 0
        if deleted:
            self._logger.info(f"Deleted user {user_id}")
        
        return deleted

# Registration
user_service = UserService({})
registry.register_singleton('user_service', user_service,
                           dependencies=['database', 'logger'])
```

## Factory Services

### LLM Provider Factory

```python
from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service
from typing import Dict, Any, Protocol

class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    def generate(self, prompt: str, **kwargs) -> str: ...
    def health_check(self) -> bool: ...

class OpenAIProvider:
    """OpenAI LLM provider."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'gpt-3.5-turbo')
    
    def generate(self, prompt: str, **kwargs) -> str:
        # Simulate OpenAI API call
        return f"OpenAI response to: {prompt[:50]}..."
    
    def health_check(self) -> bool:
        return bool(self.api_key)

class AnthropicProvider:
    """Anthropic LLM provider."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'claude-3-sonnet')
    
    def generate(self, prompt: str, **kwargs) -> str:
        # Simulate Anthropic API call
        return f"Anthropic response to: {prompt[:50]}..."
    
    def health_check(self) -> bool:
        return bool(self.api_key)

class LLMProviderFactory(ConfigurableService):
    """Factory for creating LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "llm_factory")
        self._dependencies = ["config", "logger"]
        self._providers = {}
        self._logger = None
    
    def _do_initialize(self) -> None:
        """Initialize the factory."""
        config_service = require_service('config', context=self.name)
        self._logger = require_service('logger', context=self.name)
        
        # Register available providers
        self._providers = {
            'openai': OpenAIProvider,
            'anthropic': AnthropicProvider
        }
        
        self._logger.info("LLM provider factory initialized")
    
    def _do_shutdown(self) -> None:
        """Shutdown the factory."""
        self._providers.clear()
    
    def _do_health_check(self) -> bool:
        """Check if factory is healthy."""
        return len(self._providers) > 0
    
    def create_provider(self, provider_type: str) -> LLMProvider:
        """Create an LLM provider instance."""
        if provider_type not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Unknown provider type: {provider_type}. Available: {available}")
        
        # Get provider configuration
        config_service = require_service('config', context=self.name)
        provider_config = config_service.get(f'llm.{provider_type}', {})
        
        # Create provider instance
        provider_class = self._providers[provider_type]
        provider = provider_class(provider_config)
        
        self._logger.info(f"Created {provider_type} provider")
        return provider
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider types."""
        return list(self._providers.keys())

# Register as factory
def create_llm_provider():
    """Factory function for LLM providers."""
    factory = require_service('llm_factory', context='LLMProviderCreator')
    config_service = require_service('config', context='LLMProviderCreator')
    
    # Get default provider type
    provider_type = config_service.get('llm.default_provider', 'openai')
    return factory.create_provider(provider_type)

# Registration
llm_factory = LLMProviderFactory({})
registry.register_singleton('llm_factory', llm_factory, 
                           dependencies=['config', 'logger'])

# Register the factory function
registry.register_factory('llm_provider', create_llm_provider,
                         dependencies=['llm_factory', 'config'])
```

## Optional Services

### Analytics Service with Optional Dependencies

```python
from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service
from typing import Dict, Any, Optional

class AnalyticsService(ConfigurableService):
    """Analytics service with optional cache and metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "analytics")
        self._dependencies = ["logger"]  # Only logger is required
        self._logger = None
        self._cache = None
        self._metrics = None
    
    def _do_initialize(self) -> None:
        """Initialize analytics service."""
        # Required dependencies
        self._logger = require_service('logger', context=self.name)
        
        # Optional dependencies
        self._cache = optional_service('cache', context=self.name)
        self._metrics = optional_service('metrics', context=self.name)
        
        # Log what's available
        features = []
        if self._cache:
            features.append("caching")
        if self._metrics:
            features.append("metrics")
        
        if features:
            self._logger.info(f"Analytics service initialized with: {', '.join(features)}")
        else:
            self._logger.info("Analytics service initialized (basic mode)")
    
    def _do_shutdown(self) -> None:
        """Shutdown analytics service."""
        self._logger.info("Analytics service shutdown")
    
    def _do_health_check(self) -> bool:
        """Check if analytics service is healthy."""
        return True  # Always healthy if initialized
    
    def track_event(self, event_name: str, properties: Dict[str, Any] = None) -> None:
        """Track an analytics event."""
        properties = properties or {}
        
        # Log the event
        self._logger.info(f"Event: {event_name}, Properties: {properties}")
        
        # Send to metrics service if available
        if self._metrics:
            self._metrics.increment_counter(f"events.{event_name}", 
                                          tags=properties)
        
        # Cache recent events if cache is available
        if self._cache:
            cache_key = f"recent_events:{event_name}"
            recent_events = self._cache.get(cache_key) or []
            recent_events.append({
                'timestamp': time.time(),
                'properties': properties
            })
            
            # Keep only last 100 events
            recent_events = recent_events[-100:]
            self._cache.set(cache_key, recent_events, ttl=3600)
    
    def get_recent_events(self, event_name: str) -> List[Dict[str, Any]]:
        """Get recent events (if cache is available)."""
        if not self._cache:
            self._logger.warning("Cache not available, cannot retrieve recent events")
            return []
        
        cache_key = f"recent_events:{event_name}"
        return self._cache.get(cache_key) or []
    
    def get_event_count(self, event_name: str) -> Optional[int]:
        """Get event count (if metrics service is available)."""
        if not self._metrics:
            self._logger.warning("Metrics service not available, cannot get event count")
            return None
        
        return self._metrics.get_counter_value(f"events.{event_name}")

# Registration
analytics_service = AnalyticsService({})
registry.register_singleton('analytics', analytics_service,
                           dependencies=['logger'])  # Only required dependency
```

## Service Lifecycle Management

### Application Startup with Service Coordination

```python
from app.core.service import ServiceLifecycleManager
from app.core.registry import get_registry
import sys

class ApplicationManager:
    """Manages application lifecycle with coordinated service management."""
    
    def __init__(self):
        self.registry = get_registry()
        self.lifecycle_manager = ServiceLifecycleManager()
        self.services_registered = False
        self.services_initialized = False
    
    def register_services(self) -> None:
        """Register all application services."""
        if self.services_registered:
            return
        
        print("Registering services...")
        
        # Register services in dependency order
        services = [
            ('config', ConfigService({})),
            ('logger', SimpleLoggerService({})),
            ('database', DatabaseService({})),
            ('user_service', UserService({})),
            ('analytics', AnalyticsService({}))
        ]
        
        for name, service in services:
            self.registry.register_singleton(name, service)
            self.lifecycle_manager.add_service(service)
            print(f"  ✓ Registered {name}")
        
        self.services_registered = True
        print("Service registration complete")
    
    def initialize_services(self) -> None:
        """Initialize all services in dependency order."""
        if not self.services_registered:
            raise RuntimeError("Services must be registered before initialization")
        
        if self.services_initialized:
            return
        
        print("Initializing services...")
        
        try:
            self.lifecycle_manager.initialize_all()
            self.services_initialized = True
            print("Service initialization complete")
            
            # Validate all services are healthy
            self._validate_service_health()
            
        except Exception as e:
            print(f"Service initialization failed: {e}")
            self.shutdown_services()
            raise
    
    def shutdown_services(self) -> None:
        """Shutdown all services gracefully."""
        if not self.services_initialized:
            return
        
        print("Shutting down services...")
        
        try:
            self.lifecycle_manager.shutdown_all()
            print("Service shutdown complete")
        except Exception as e:
            print(f"Error during service shutdown: {e}")
        finally:
            self.services_initialized = False
    
    def _validate_service_health(self) -> None:
        """Validate that all services are healthy."""
        health_status = self.registry.health_check()
        unhealthy = [name for name, healthy in health_status.items() if not healthy]
        
        if unhealthy:
            print(f"⚠️  Unhealthy services detected: {unhealthy}")
            # Could choose to fail here or continue with warnings
        else:
            print("✓ All services are healthy")
    
    def run_application(self) -> None:
        """Run the main application."""
        try:
            self.register_services()
            self.initialize_services()
            
            print("Application started successfully")
            
            # Main application logic would go here
            self._run_main_loop()
            
        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        except Exception as e:
            print(f"Application error: {e}")
            sys.exit(1)
        finally:
            self.shutdown_services()
    
    def _run_main_loop(self) -> None:
        """Main application loop."""
        # Example usage of services
        user_service = self.registry.get('user_service')
        analytics = self.registry.get('analytics')
        
        # Create a test user
        user = user_service.create_user("testuser", "test@example.com")
        analytics.track_event("user_created", {"user_id": user["id"]})
        
        # List users
        users = user_service.list_users()
        analytics.track_event("users_listed", {"count": len(users)})
        
        print(f"Application running with {len(users)} users")

# Usage
if __name__ == "__main__":
    app = ApplicationManager()
    app.run_application()
```

## Testing Examples

### Unit Test with Service Mocking

```python
import pytest
from unittest.mock import Mock, MagicMock
from app.core.registry import get_registry, reset_registry

class TestUserService:
    """Test user service with mocked dependencies."""
    
    @pytest.fixture(autouse=True)
    def setup_services(self):
        """Set up test services."""
        # Reset registry
        reset_registry()
        registry = get_registry()
        
        # Mock database service
        self.mock_db = Mock()
        self.mock_db.execute.return_value = Mock(lastrowid=123)
        self.mock_db.fetch_one.return_value = {
            'id': 123,
            'username': 'testuser',
            'email': 'test@example.com'
        }
        self.mock_db.fetch_all.return_value = []
        
        # Mock logger service
        self.mock_logger = Mock()
        
        # Register mocks
        registry.register_singleton('database', self.mock_db)
        registry.register_singleton('logger', self.mock_logger)
        
        yield
        
        # Clean up
        reset_registry()
    
    def test_create_user(self):
        """Test user creation."""
        from examples.user_service import UserService
        
        # Create service
        user_service = UserService({})
        user_service.initialize()
        
        # Test user creation
        user = user_service.create_user("testuser", "test@example.com")
        
        # Verify database was called
        self.mock_db.execute.assert_called_once()
        call_args = self.mock_db.execute.call_args
        assert "INSERT INTO users" in call_args[0][0]
        assert call_args[1]["username"] == "testuser"
        assert call_args[1]["email"] == "test@example.com"
        
        # Verify logger was called
        self.mock_logger.info.assert_called()
        
        # Verify return value
        assert user["username"] == "testuser"
    
    def test_get_user_not_found(self):
        """Test getting non-existent user."""
        from examples.user_service import UserService
        
        # Mock database to return None
        self.mock_db.fetch_one.return_value = None
        
        user_service = UserService({})
        user_service.initialize()
        
        user = user_service.get_user(999)
        assert user is None
    
    def test_service_health_check(self):
        """Test service health check."""
        from examples.user_service import UserService
        
        user_service = UserService({})
        user_service.initialize()
        
        # Should be healthy when database works
        assert user_service.health_check() is True
        
        # Should be unhealthy when database fails
        self.mock_db.execute.side_effect = Exception("Database error")
        assert user_service.health_check() is False
```

### Integration Test

```python
import pytest
import tempfile
import os
from app.core.registry import get_registry, reset_registry

class TestServiceIntegration:
    """Integration tests with real services."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def integration_services(self, temp_db):
        """Set up real services for integration testing."""
        reset_registry()
        registry = get_registry()
        
        # Real config service
        config_service = ConfigService({
            'config_file': 'test_config.yaml'
        })
        config_service._config_data = {
            'database': {'path': temp_db},
            'logging': {'level': 'DEBUG'}
        }
        registry.register_singleton('config', config_service)
        
        # Real logger service
        logger_service = SimpleLoggerService({})
        registry.register_singleton('logger', logger_service)
        
        # Real database service
        database_service = DatabaseService({})
        registry.register_singleton('database', database_service)
        
        # Real user service
        user_service = UserService({})
        registry.register_singleton('user_service', user_service)
        
        # Initialize all services
        for service in [config_service, logger_service, database_service, user_service]:
            service.initialize()
        
        yield registry
        
        # Clean up
        for service in [user_service, database_service, logger_service, config_service]:
            service.shutdown()
        reset_registry()
    
    def test_full_user_workflow(self, integration_services):
        """Test complete user management workflow."""
        registry = integration_services
        user_service = registry.get('user_service')
        
        # Create user
        user = user_service.create_user("integrationtest", "integration@test.com")
        assert user is not None
        assert user['username'] == "integrationtest"
        assert user['email'] == "integration@test.com"
        assert 'id' in user
        
        user_id = user['id']
        
        # Get user by ID
        retrieved_user = user_service.get_user(user_id)
        assert retrieved_user == user
        
        # Get user by username
        retrieved_user = user_service.get_user_by_username("integrationtest")
        assert retrieved_user == user
        
        # Update user
        updated_user = user_service.update_user(user_id, email="newemail@test.com")
        assert updated_user['email'] == "newemail@test.com"
        assert updated_user['username'] == "integrationtest"  # Unchanged
        
        # List users
        users = user_service.list_users()
        assert len(users) == 1
        assert users[0]['id'] == user_id
        
        # Delete user
        deleted = user_service.delete_user(user_id)
        assert deleted is True
        
        # Verify user is gone
        retrieved_user = user_service.get_user(user_id)
        assert retrieved_user is None
        
        users = user_service.list_users()
        assert len(users) == 0
    
    def test_service_health_checks(self, integration_services):
        """Test that all services report healthy."""
        registry = integration_services
        
        health_status = registry.health_check()
        
        expected_services = ['config', 'logger', 'database', 'user_service']
        for service_name in expected_services:
            assert service_name in health_status
            assert health_status[service_name] is True, f"Service {service_name} is not healthy"
```

## Real-World Scenarios

### Web Application with Service Registry

```python
from flask import Flask, request, jsonify
from app.core.registry import get_registry
from app.utils.imports import require_service, optional_service

class WebApplication:
    """Web application using service registry."""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.registry = get_registry()
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up Flask routes."""
        
        @self.app.route('/health')
        def health_check():
            """Health check endpoint."""
            health_status = self.registry.health_check()
            all_healthy = all(health_status.values())
            
            return jsonify({
                'status': 'healthy' if all_healthy else 'unhealthy',
                'services': health_status
            }), 200 if all_healthy else 503
        
        @self.app.route('/users', methods=['POST'])
        def create_user():
            """Create a new user."""
            try:
                user_service = require_service('user_service', context='WebAPI')
                analytics = optional_service('analytics', context='WebAPI')
                
                data = request.get_json()
                username = data.get('username')
                email = data.get('email')
                
                if not username or not email:
                    return jsonify({'error': 'Username and email required'}), 400
                
                user = user_service.create_user(username, email)
                
                # Track analytics if available
                if analytics:
                    analytics.track_event('user_created', {
                        'user_id': user['id'],
                        'source': 'web_api'
                    })
                
                return jsonify(user), 201
                
            except Exception as e:
                logger = optional_service('logger', context='WebAPI')
                if logger:
                    logger.error(f"Error creating user: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/users/<int:user_id>')
        def get_user(user_id):
            """Get user by ID."""
            try:
                user_service = require_service('user_service', context='WebAPI')
                
                user = user_service.get_user(user_id)
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                return jsonify(user)
                
            except Exception as e:
                logger = optional_service('logger', context='WebAPI')
                if logger:
                    logger.error(f"Error getting user {user_id}: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/users')
        def list_users():
            """List all users."""
            try:
                user_service = require_service('user_service', context='WebAPI')
                analytics = optional_service('analytics', context='WebAPI')
                
                users = user_service.list_users()
                
                # Track analytics if available
                if analytics:
                    analytics.track_event('users_listed', {
                        'count': len(users),
                        'source': 'web_api'
                    })
                
                return jsonify({'users': users, 'count': len(users)})
                
            except Exception as e:
                logger = optional_service('logger', context='WebAPI')
                if logger:
                    logger.error(f"Error listing users: {e}")
                return jsonify({'error': 'Internal server error'}), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the web application."""
        self.app.run(host=host, port=port, debug=debug)

# Usage
if __name__ == "__main__":
    # Initialize services
    app_manager = ApplicationManager()
    app_manager.register_services()
    app_manager.initialize_services()
    
    try:
        # Start web application
        web_app = WebApplication()
        web_app.run(debug=True)
    finally:
        app_manager.shutdown_services()
```

### Background Task Processor

```python
import time
import threading
from queue import Queue, Empty
from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service

class TaskProcessor(ConfigurableService):
    """Background task processor using services."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "task_processor")
        self._dependencies = ["logger"]
        self._task_queue = Queue()
        self._worker_threads = []
        self._running = False
        self._logger = None
        self._analytics = None
    
    def _do_initialize(self) -> None:
        """Initialize task processor."""
        self._logger = require_service('logger', context=self.name)
        self._analytics = optional_service('analytics', context=self.name)
        
        # Start worker threads
        num_workers = self.get_config('num_workers', 2)
        self._running = True
        
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,))
            worker.daemon = True
            worker.start()
            self._worker_threads.append(worker)
        
        self._logger.info(f"Task processor started with {num_workers} workers")
    
    def _do_shutdown(self) -> None:
        """Shutdown task processor."""
        self._running = False
        
        # Wait for workers to finish
        for worker in self._worker_threads:
            worker.join(timeout=5.0)
        
        self._logger.info("Task processor shutdown")
    
    def _do_health_check(self) -> bool:
        """Check if task processor is healthy."""
        return self._running and any(worker.is_alive() for worker in self._worker_threads)
    
    def submit_task(self, task_type: str, task_data: Dict[str, Any]) -> None:
        """Submit a task for processing."""
        task = {
            'type': task_type,
            'data': task_data,
            'submitted_at': time.time()
        }
        
        self._task_queue.put(task)
        self._logger.debug(f"Submitted task: {task_type}")
        
        if self._analytics:
            self._analytics.track_event('task_submitted', {'type': task_type})
    
    def _worker_loop(self, worker_id: int) -> None:
        """Worker thread main loop."""
        self._logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Get task from queue with timeout
                task = self._task_queue.get(timeout=1.0)
                
                # Process task
                self._process_task(task, worker_id)
                
                # Mark task as done
                self._task_queue.task_done()
                
            except Empty:
                # No tasks available, continue
                continue
            except Exception as e:
                self._logger.error(f"Worker {worker_id} error: {e}")
        
        self._logger.info(f"Worker {worker_id} stopped")
    
    def _process_task(self, task: Dict[str, Any], worker_id: int) -> None:
        """Process a single task."""
        task_type = task['type']
        task_data = task['data']
        
        start_time = time.time()
        
        try:
            self._logger.info(f"Worker {worker_id} processing {task_type}")
            
            # Process different task types
            if task_type == 'send_email':
                self._process_email_task(task_data)
            elif task_type == 'generate_report':
                self._process_report_task(task_data)
            elif task_type == 'cleanup_data':
                self._process_cleanup_task(task_data)
            else:
                self._logger.warning(f"Unknown task type: {task_type}")
                return
            
            # Track success
            duration = time.time() - start_time
            self._logger.info(f"Task {task_type} completed in {duration:.2f}s")
            
            if self._analytics:
                self._analytics.track_event('task_completed', {
                    'type': task_type,
                    'duration': duration,
                    'worker_id': worker_id
                })
        
        except Exception as e:
            duration = time.time() - start_time
            self._logger.error(f"Task {task_type} failed after {duration:.2f}s: {e}")
            
            if self._analytics:
                self._analytics.track_event('task_failed', {
                    'type': task_type,
                    'duration': duration,
                    'error': str(e),
                    'worker_id': worker_id
                })
    
    def _process_email_task(self, data: Dict[str, Any]) -> None:
        """Process email sending task."""
        # Simulate email sending
        time.sleep(0.5)
        self._logger.info(f"Email sent to {data.get('to', 'unknown')}")
    
    def _process_report_task(self, data: Dict[str, Any]) -> None:
        """Process report generation task."""
        # Simulate report generation
        time.sleep(2.0)
        self._logger.info(f"Report generated: {data.get('report_type', 'unknown')}")
    
    def _process_cleanup_task(self, data: Dict[str, Any]) -> None:
        """Process data cleanup task."""
        # Simulate cleanup
        time.sleep(1.0)
        self._logger.info(f"Cleanup completed for {data.get('target', 'unknown')}")
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._task_queue.qsize()

# Usage example
def run_background_processor():
    """Run background task processor."""
    # Initialize services
    app_manager = ApplicationManager()
    app_manager.register_services()
    
    # Register task processor
    task_processor = TaskProcessor({'num_workers': 3})
    app_manager.registry.register_singleton('task_processor', task_processor)
    app_manager.lifecycle_manager.add_service(task_processor)
    
    app_manager.initialize_services()
    
    try:
        # Submit some test tasks
        processor = app_manager.registry.get('task_processor')
        
        processor.submit_task('send_email', {'to': 'user@example.com', 'subject': 'Test'})
        processor.submit_task('generate_report', {'report_type': 'monthly'})
        processor.submit_task('cleanup_data', {'target': 'old_logs'})
        
        # Let tasks process
        print("Processing tasks... Press Ctrl+C to stop")
        while True:
            queue_size = processor.get_queue_size()
            print(f"Queue size: {queue_size}")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("Stopping task processor...")
    finally:
        app_manager.shutdown_services()

if __name__ == "__main__":
    run_background_processor()
```

These examples demonstrate practical usage patterns for the service registry system, from simple services to complex real-world applications. Each example shows proper dependency management, error handling, and service lifecycle management.