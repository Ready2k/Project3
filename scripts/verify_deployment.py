#!/usr/bin/env python3
"""
Deployment verification script for Automated AI Assessment (AAA)
Checks that all deployment files are properly configured
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (missing)")
        return False


def check_dockerfile() -> bool:
    """Verify Dockerfile configuration"""
    print("\n🐳 Checking Dockerfile...")
    
    if not check_file_exists("Dockerfile", "Dockerfile"):
        return False
    
    with open("Dockerfile", "r") as f:
        content = f.read()
    
    checks = [
        ("Multi-stage build", "FROM python:3.10-slim as builder" in content),
        ("Health check", "HEALTHCHECK" in content),
        ("Non-root user", "useradd" in content and "USER agentic" in content),
        ("Proper WORKDIR", "WORKDIR /app" in content),
        ("Port exposure", "EXPOSE 8000 8500" in content),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed


def check_docker_compose() -> bool:
    """Verify docker-compose files"""
    print("\n🐳 Checking Docker Compose files...")
    
    files = [
        ("docker-compose.yml", "Main compose file"),
        ("docker-compose.dev.yml", "Development override"),
        ("docker-compose.prod.yml", "Production override"),
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    if not all_exist:
        return False
    
    # Check main compose file structure
    try:
        with open("docker-compose.yml", "r") as f:
            compose_data = yaml.safe_load(f)
        
        required_services = ["api", "ui", "redis"]
        for service in required_services:
            if service in compose_data.get("services", {}):
                print(f"  ✅ Service: {service}")
            else:
                print(f"  ❌ Service: {service} (missing)")
                return False
        
        # Check for health checks
        api_service = compose_data["services"].get("api", {})
        if "healthcheck" in api_service:
            print("  ✅ API health check configured")
        else:
            print("  ❌ API health check missing")
            return False
        
        return True
        
    except yaml.YAMLError as e:
        print(f"  ❌ Invalid YAML in docker-compose.yml: {e}")
        return False


def check_makefile() -> bool:
    """Verify Makefile has required targets"""
    print("\n🔧 Checking Makefile...")
    
    if not check_file_exists("Makefile", "Makefile"):
        return False
    
    with open("Makefile", "r") as f:
        content = f.read()
    
    required_targets = [
        "fmt", "lint", "test", "up", "docker-build", 
        "docker-up", "docker-dev", "docker-down"
    ]
    
    all_passed = True
    for target in required_targets:
        if f"{target}:" in content:
            print(f"  ✅ Target: {target}")
        else:
            print(f"  ❌ Target: {target} (missing)")
            all_passed = False
    
    return all_passed


def check_requirements() -> bool:
    """Verify requirements.txt has all dependencies"""
    print("\n📦 Checking requirements.txt...")
    
    if not check_file_exists("requirements.txt", "Requirements file"):
        return False
    
    with open("requirements.txt", "r") as f:
        requirements = f.read()
    
    critical_deps = [
        "fastapi", "uvicorn", "streamlit", "pydantic", 
        "redis", "faiss-cpu", "sentence-transformers",
        "pytest", "black", "ruff"
    ]
    
    all_passed = True
    for dep in critical_deps:
        if dep in requirements:
            print(f"  ✅ Dependency: {dep}")
        else:
            print(f"  ❌ Dependency: {dep} (missing)")
            all_passed = False
    
    return all_passed


def check_env_example() -> bool:
    """Verify .env.example has required variables"""
    print("\n🔐 Checking .env.example...")
    
    if not check_file_exists(".env.example", "Environment example"):
        return False
    
    with open(".env.example", "r") as f:
        content = f.read()
    
    required_vars = [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", 
        "AWS_ACCESS_KEY_ID", "PROVIDER", "MODEL"
    ]
    
    all_passed = True
    for var in required_vars:
        if var in content:
            print(f"  ✅ Variable: {var}")
        else:
            print(f"  ❌ Variable: {var} (missing)")
            all_passed = False
    
    return all_passed


def check_deployment_docs() -> bool:
    """Verify deployment documentation exists"""
    print("\n📚 Checking deployment documentation...")
    
    files = [
        ("DEPLOYMENT.md", "Deployment guide"),
        ("nginx.conf", "Nginx configuration"),
        (".dockerignore", "Docker ignore file"),
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist


def check_scripts() -> bool:
    """Verify deployment scripts exist and are executable"""
    print("\n🔧 Checking deployment scripts...")
    
    scripts = [
        ("scripts/health_check.py", "Health check script"),
        ("scripts/monitor.sh", "Monitoring script"),
        ("scripts/verify_deployment.py", "This verification script"),
    ]
    
    all_passed = True
    for script_path, description in scripts:
        if check_file_exists(script_path, description):
            # Check if executable
            if os.access(script_path, os.X_OK):
                print(f"    ✅ Executable")
            else:
                print(f"    ⚠️  Not executable (run: chmod +x {script_path})")
        else:
            all_passed = False
    
    return all_passed


def main():
    """Run all deployment verification checks"""
    print("🚀 Automated AI Assessment (AAA) - Deployment Verification")
    print("=" * 60)
    
    checks = [
        ("Dockerfile", check_dockerfile),
        ("Docker Compose", check_docker_compose),
        ("Makefile", check_makefile),
        ("Requirements", check_requirements),
        ("Environment", check_env_example),
        ("Documentation", check_deployment_docs),
        ("Scripts", check_scripts),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error checking {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All deployment checks passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()