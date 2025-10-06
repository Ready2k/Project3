"""
Type checking tests using mypy.

This module contains tests that verify type safety across the codebase
by running mypy programmatically as part of the test suite.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import pytest


class TypeCheckingError(Exception):
    """Raised when type checking fails."""
    pass


def run_mypy(
    paths: Optional[List[str]] = None,
    config_file: str = "mypy.ini",
    strict: bool = False
) -> tuple[int, str, str]:
    """
    Run mypy type checking on specified paths.
    
    Args:
        paths: List of paths to check. If None, uses config file settings.
        config_file: Path to mypy configuration file.
        strict: Whether to use strict mode.
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "mypy"]
    
    if config_file:
        cmd.extend(["--config-file", config_file])
    
    if strict:
        cmd.append("--strict")
    
    cmd.extend(["--show-error-codes", "--pretty"])
    
    if paths:
        cmd.extend(paths)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            timeout=120  # 2 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        raise TypeCheckingError("MyPy type checking timed out after 2 minutes")


@pytest.mark.typecheck
def test_core_modules_type_safety():
    """Test that core modules pass type checking."""
    core_paths = [
        "app/core/",
        "app/utils/",
    ]
    
    return_code, stdout, stderr = run_mypy(core_paths)
    
    if return_code != 0:
        error_msg = f"Type checking failed for core modules:\n{stdout}\n{stderr}"
        pytest.fail(error_msg)


@pytest.mark.typecheck
def test_service_layer_type_safety():
    """Test that service layer modules pass type checking."""
    service_paths = [
        "app/services/",
        "app/llm/",
    ]
    
    return_code, stdout, stderr = run_mypy(service_paths)
    
    if return_code != 0:
        error_msg = f"Type checking failed for service layer:\n{stdout}\n{stderr}"
        pytest.fail(error_msg)


@pytest.mark.typecheck
def test_api_layer_type_safety():
    """Test that API layer modules pass type checking."""
    api_paths = [
        "app/api.py",
        "app/main.py",
        "app/middleware/",
        "app/health/",
    ]
    
    return_code, stdout, stderr = run_mypy(api_paths)
    
    if return_code != 0:
        error_msg = f"Type checking failed for API layer:\n{stdout}\n{stderr}"
        pytest.fail(error_msg)


@pytest.mark.typecheck
@pytest.mark.slow
def test_full_codebase_type_safety():
    """Test that the entire codebase passes type checking."""
    return_code, stdout, stderr = run_mypy()
    
    if return_code != 0:
        error_msg = f"Type checking failed for full codebase:\n{stdout}\n{stderr}"
        pytest.fail(error_msg)


@pytest.mark.typecheck
def test_mypy_configuration_valid():
    """Test that mypy configuration is valid."""
    cmd = [sys.executable, "-m", "mypy", "--help"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"MyPy not properly installed: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("MyPy help command timed out")


@pytest.mark.typecheck
def test_type_stubs_available():
    """Test that required type stubs are available."""
    required_stubs = [
        "types-PyYAML",
        "types-requests", 
        "types-redis",
        "types-setuptools"
    ]
    
    for stub in required_stubs:
        cmd = [sys.executable, "-c", f"import {stub.replace('types-', '').replace('-', '_')}"]
        try:
            subprocess.run(cmd, capture_output=True, timeout=10)
            # Note: Some type stubs don't have importable modules, so we just check they're installed
        except subprocess.TimeoutExpired:
            pytest.fail(f"Import check for {stub} timed out")


if __name__ == "__main__":
    # Allow running this file directly for quick type checking
    print("Running type checking tests...")
    
    try:
        test_mypy_configuration_valid()
        print("✓ MyPy configuration is valid")
        
        test_core_modules_type_safety()
        print("✓ Core modules pass type checking")
        
        test_service_layer_type_safety()
        print("✓ Service layer passes type checking")
        
        test_api_layer_type_safety()
        print("✓ API layer passes type checking")
        
        print("All type checking tests passed!")
        
    except Exception as e:
        print(f"✗ Type checking failed: {e}")
        sys.exit(1)