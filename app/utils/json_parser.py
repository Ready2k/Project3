"""Utility functions for parsing JSON from LLM responses."""

import json
import re
from typing import Any, Dict, List, Union, Optional
from app.utils.logger import app_logger


def extract_json_from_response(response: str) -> str:
    """Extract JSON from LLM response that may contain markdown or other text.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Cleaned JSON string ready for parsing
    """
    if not response or not response.strip():
        return ""
    
    response = response.strip()
    
    # Remove markdown code fences if present
    if response.startswith('```json'):
        response = response[7:]  # Remove ```json
    elif response.startswith('```'):
        response = response[3:]   # Remove ```
    
    if response.endswith('```'):
        response = response[:-3]  # Remove trailing ```
    
    response = response.strip()
    
    # If it doesn't start with { or [, try to find JSON within the text
    if not response.startswith('{') and not response.startswith('['):
        # Look for JSON object or array
        json_match = re.search(r'[\{\[].*[\}\]]', response, re.DOTALL)
        if json_match:
            response = json_match.group()
        else:
            # Try to find just the object part
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response = response[start_idx:end_idx+1]
    
    return response


def parse_llm_json_response(response: str, 
                           default_value: Optional[Union[Dict, List]] = None,
                           service_name: str = "unknown") -> Union[Dict, List]:
    """Parse JSON from LLM response with robust error handling.
    
    Args:
        response: Raw LLM response
        default_value: Default value to return if parsing fails
        service_name: Name of the service for logging
        
    Returns:
        Parsed JSON object or default value
    """
    if default_value is None:
        default_value = {}
    
    try:
        if not response or not response.strip():
            app_logger.warning(f"Empty response from LLM in {service_name}")
            return default_value
        
        cleaned_response = extract_json_from_response(response)
        
        if not cleaned_response:
            app_logger.warning(f"No JSON found in response from {service_name}: {response[:100]}...")
            return default_value
        
        parsed = json.loads(cleaned_response)
        app_logger.debug(f"Successfully parsed JSON response in {service_name}")
        return parsed
        
    except json.JSONDecodeError as e:
        app_logger.error(f"JSON decode error in {service_name}: {e}")
        app_logger.debug(f"Raw response was: {response[:200]}...")
        app_logger.debug(f"Cleaned response was: {cleaned_response[:200] if 'cleaned_response' in locals() else 'N/A'}")
        return default_value
        
    except Exception as e:
        app_logger.error(f"Unexpected error parsing JSON in {service_name}: {e}")
        app_logger.debug(f"Raw response was: {response[:200] if response else 'None'}")
        return default_value


def safe_get_float(data: Dict, key: str, default: float = 0.0) -> float:
    """Safely extract float value from parsed JSON.
    
    Args:
        data: Parsed JSON data
        key: Key to extract
        default: Default value if key missing or invalid
        
    Returns:
        Float value or default
    """
    try:
        value = data.get(key, default)
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_get_list(data: Dict, key: str, default: Optional[List] = None) -> List:
    """Safely extract list value from parsed JSON.
    
    Args:
        data: Parsed JSON data
        key: Key to extract
        default: Default value if key missing or invalid
        
    Returns:
        List value or default
    """
    if default is None:
        default = []
    
    try:
        value = data.get(key, default)
        return list(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_get_string(data: Dict, key: str, default: str = "") -> str:
    """Safely extract string value from parsed JSON.
    
    Args:
        data: Parsed JSON data
        key: Key to extract
        default: Default value if key missing or invalid
        
    Returns:
        String value or default
    """
    try:
        value = data.get(key, default)
        return str(value) if value is not None else default
    except (ValueError, TypeError):
        return default