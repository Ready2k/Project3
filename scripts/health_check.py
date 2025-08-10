#!/usr/bin/env python3
"""
Health check script for Automated AI Assessment (AAA)
Can be used for monitoring, load balancer health checks, etc.
"""

import asyncio
import sys
import time
from typing import Dict, Any
import httpx
import argparse


async def check_api_health(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Check API health endpoint"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            start_time = time.time()
            response = await client.get(f"{base_url}/health")
            latency = (time.time() - start_time) * 1000
            
            return {
                "service": "api",
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "latency_ms": round(latency, 2),
                "response": response.json() if response.status_code == 200 else None
            }
    except Exception as e:
        return {
            "service": "api",
            "status": "unhealthy",
            "error": str(e)
        }


async def check_ui_health(base_url: str = "http://localhost:8501") -> Dict[str, Any]:
    """Check Streamlit UI health"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            start_time = time.time()
            response = await client.get(f"{base_url}/_stcore/health")
            latency = (time.time() - start_time) * 1000
            
            return {
                "service": "ui",
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "latency_ms": round(latency, 2)
            }
    except Exception as e:
        return {
            "service": "ui",
            "status": "unhealthy",
            "error": str(e)
        }


async def check_redis_health(host: str = "localhost", port: int = 6379) -> Dict[str, Any]:
    """Check Redis health"""
    try:
        import redis.asyncio as redis
        
        start_time = time.time()
        r = redis.Redis(host=host, port=port, decode_responses=True)
        await r.ping()
        latency = (time.time() - start_time) * 1000
        
        info = await r.info()
        await r.close()
        
        return {
            "service": "redis",
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "version": info.get("redis_version"),
            "memory_used": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients")
        }
    except Exception as e:
        return {
            "service": "redis",
            "status": "unhealthy",
            "error": str(e)
        }


async def run_health_checks(api_url: str, ui_url: str, redis_host: str, redis_port: int) -> Dict[str, Any]:
    """Run all health checks concurrently"""
    tasks = [
        check_api_health(api_url),
        check_ui_health(ui_url),
        check_redis_health(redis_host, redis_port)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    health_status = {
        "timestamp": time.time(),
        "overall_status": "healthy",
        "services": {}
    }
    
    for result in results:
        if isinstance(result, Exception):
            health_status["overall_status"] = "unhealthy"
            continue
            
        service_name = result["service"]
        health_status["services"][service_name] = result
        
        if result["status"] != "healthy":
            health_status["overall_status"] = "unhealthy"
    
    return health_status


def main():
    parser = argparse.ArgumentParser(description="Health check for Automated AI Assessment (AAA) services")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--ui-url", default="http://localhost:8501", help="UI base URL")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--quiet", action="store_true", help="Only output status code")
    
    args = parser.parse_args()
    
    # Run health checks
    health_status = asyncio.run(run_health_checks(
        args.api_url, args.ui_url, args.redis_host, args.redis_port
    ))
    
    if args.quiet:
        # Exit with 0 if healthy, 1 if unhealthy
        sys.exit(0 if health_status["overall_status"] == "healthy" else 1)
    
    if args.json:
        import json
        print(json.dumps(health_status, indent=2))
    else:
        # Human-readable output
        print(f"Overall Status: {health_status['overall_status'].upper()}")
        print("-" * 50)
        
        for service_name, service_data in health_status["services"].items():
            status = service_data["status"].upper()
            print(f"{service_name.upper()}: {status}")
            
            if "latency_ms" in service_data:
                print(f"  Latency: {service_data['latency_ms']}ms")
            
            if "error" in service_data:
                print(f"  Error: {service_data['error']}")
            
            if service_name == "redis" and service_data["status"] == "healthy":
                print(f"  Version: {service_data.get('version', 'unknown')}")
                print(f"  Memory: {service_data.get('memory_used', 'unknown')}")
                print(f"  Clients: {service_data.get('connected_clients', 'unknown')}")
            
            print()
    
    # Exit with appropriate code
    sys.exit(0 if health_status["overall_status"] == "healthy" else 1)


if __name__ == "__main__":
    main()