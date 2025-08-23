"""
Dynamic Schema Loader - Configurable validation enums for pattern schemas.

This module provides a flexible alternative to hard-coded JSON schema enums,
allowing users to configure and extend validation values through configuration files.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from app.utils.logger import app_logger


class DynamicSchemaLoader:
    """Loads and manages configurable schema enums."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent / "schema_config.json"
        self.base_schema_path = Path(__file__).parent / "agentic_schema.json"
        self._config_cache: Optional[Dict[str, Any]] = None
        self._schema_cache: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load the schema configuration."""
        if self._config_cache is not None:
            return self._config_cache
            
        try:
            with open(self.config_path, 'r') as f:
                self._config_cache = json.load(f)
                app_logger.info(f"Loaded schema configuration from {self.config_path}")
                return self._config_cache
        except Exception as e:
            app_logger.warning(f"Failed to load schema config from {self.config_path}: {e}")
            # Return default minimal config
            return {
                "schema_enums": {},
                "validation_settings": {
                    "strict_mode": True,
                    "allow_custom_values": False,
                    "warn_on_unknown_values": True,
                    "auto_add_new_values": False
                }
            }
    
    def get_enum_values(self, enum_name: str) -> List[str]:
        """Get the allowed values for a specific enum."""
        config = self.load_config()
        enum_config = config.get("schema_enums", {}).get(enum_name, {})
        return enum_config.get("values", [])
    
    def is_user_extensible(self, enum_name: str) -> bool:
        """Check if an enum allows user extensions."""
        config = self.load_config()
        enum_config = config.get("schema_enums", {}).get(enum_name, {})
        return enum_config.get("user_extensible", False)
    
    def add_enum_value(self, enum_name: str, new_value: str) -> bool:
        """Add a new value to an enum if it's user extensible."""
        if not self.is_user_extensible(enum_name):
            app_logger.warning(f"Enum '{enum_name}' is not user extensible")
            return False
        
        config = self.load_config()
        enum_config = config.get("schema_enums", {}).get(enum_name, {})
        current_values = enum_config.get("values", [])
        
        if new_value not in current_values:
            current_values.append(new_value)
            enum_config["values"] = current_values
            
            # Save updated config
            try:
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                app_logger.info(f"Added '{new_value}' to enum '{enum_name}'")
                self._config_cache = None  # Clear cache
                self._schema_cache = None  # Clear schema cache
                return True
            except Exception as e:
                app_logger.error(f"Failed to save updated config: {e}")
                return False
        
        return True  # Value already exists
    
    def validate_enum_value(self, enum_name: str, value: str) -> bool:
        """Validate if a value is allowed for an enum."""
        allowed_values = self.get_enum_values(enum_name)
        config = self.load_config()
        settings = config.get("validation_settings", {})
        
        if value in allowed_values:
            return True
        
        # Handle unknown values based on settings
        if settings.get("allow_custom_values", False):
            if settings.get("warn_on_unknown_values", True):
                app_logger.warning(f"Unknown value '{value}' for enum '{enum_name}' (allowed in non-strict mode)")
            
            if settings.get("auto_add_new_values", False) and self.is_user_extensible(enum_name):
                self.add_enum_value(enum_name, value)
            
            return True
        
        return False
    
    def generate_dynamic_schema(self) -> Dict[str, Any]:
        """Generate a JSON schema with dynamic enum values."""
        if self._schema_cache is not None:
            return self._schema_cache
        
        # Load base schema
        try:
            with open(self.base_schema_path, 'r') as f:
                base_schema = json.load(f)
        except Exception as e:
            app_logger.error(f"Failed to load base schema: {e}")
            return {}
        
        # Update enum values from config
        config = self.load_config()
        schema_enums = config.get("schema_enums", {})
        
        # Update specific enum fields
        properties = base_schema.get("properties", {})
        
        for enum_name, enum_config in schema_enums.items():
            if enum_name in properties:
                prop = properties[enum_name]
                values = enum_config.get("values", [])
                
                # Handle array of enums
                if prop.get("type") == "array" and "items" in prop:
                    if "enum" in prop["items"]:
                        prop["items"]["enum"] = values
                        app_logger.debug(f"Updated array enum '{enum_name}' with {len(values)} values")
                
                # Handle direct enums
                elif "enum" in prop:
                    prop["enum"] = values
                    app_logger.debug(f"Updated enum '{enum_name}' with {len(values)} values")
        
        self._schema_cache = base_schema
        app_logger.info(f"Generated dynamic schema with {len(schema_enums)} configurable enums")
        return base_schema
    
    def get_available_enums(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available configurable enums."""
        config = self.load_config()
        return config.get("schema_enums", {})
    
    def clear_cache(self):
        """Clear all caches to force reload."""
        self._config_cache = None
        self._schema_cache = None


# Global instance for easy access
dynamic_schema_loader = DynamicSchemaLoader()