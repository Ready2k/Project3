#!/usr/bin/env python3
"""
Service Health Monitoring Dashboard

This script provides a web-based dashboard for monitoring service health,
dependency status, and system metrics in real-time.
"""

import os
import sys
import json
import time
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import argparse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.registry import get_registry, ServiceRegistry
from app.core.dependencies import DependencyValidator, DependencyInfo, ValidationResult, DependencyType


@dataclass
class HealthMetric:
    """Health metric data point."""
    timestamp: str
    service_name: str
    is_healthy: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    """System-wide metrics."""
    timestamp: str
    total_services: int
    healthy_services: int
    unhealthy_services: int
    total_dependencies: int
    satisfied_dependencies: int
    missing_dependencies: int
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None


class HealthMonitor:
    """Service health monitoring system."""
    
    def __init__(self, check_interval: int = 30):
        """
        Initialize the health monitor.
        
        Args:
            check_interval: Health check interval in seconds
        """
        self.registry = get_registry()
        self.validator = DependencyValidator()
        self.check_interval = check_interval
        self.metrics_history: List[HealthMetric] = []
        self.system_metrics_history: List[SystemMetrics] = []
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Create output directory
        self.output_dir = project_root / "docs" / "monitoring"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self.is_monitoring:
            print("⚠️  Monitoring is already running")
            return
        
        print(f"🚀 Starting health monitoring (interval: {self.check_interval}s)")
        self.is_monitoring = True
        
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        if not self.is_monitoring:
            print("⚠️  Monitoring is not running")
            return
        
        print("🛑 Stopping health monitoring...")
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def check_all_services(self) -> Dict[str, HealthMetric]:
        """
        Check health of all services.
        
        Returns:
            Dictionary mapping service names to health metrics
        """
        timestamp = datetime.now().isoformat()
        health_metrics = {}
        
        try:
            # Get service health from registry
            health_status = self.registry.health_check()
            
            for service_name, is_healthy in health_status.items():
                start_time = time.time()
                
                # Get additional service information
                service_info = self.registry.get_service_info(service_name)
                error_message = None
                metadata = {}
                
                if service_info:
                    error_message = service_info.error_message
                    metadata = {
                        "lifecycle": service_info.lifecycle.value,
                        "service_type": service_info.service_type,
                        "dependencies": service_info.dependencies
                    }
                
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                metric = HealthMetric(
                    timestamp=timestamp,
                    service_name=service_name,
                    is_healthy=is_healthy,
                    response_time_ms=response_time,
                    error_message=error_message,
                    metadata=metadata
                )
                
                health_metrics[service_name] = metric
                self.metrics_history.append(metric)
        
        except Exception as e:
            print(f"❌ Error checking service health: {e}")
        
        # Trim history to last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return health_metrics
    
    def check_system_metrics(self) -> SystemMetrics:
        """
        Check overall system metrics.
        
        Returns:
            System metrics snapshot
        """
        timestamp = datetime.now().isoformat()
        
        # Service metrics
        services = self.registry.list_services()
        health_status = self.registry.health_check()
        
        total_services = len(services)
        healthy_services = sum(1 for status in health_status.values() if status)
        unhealthy_services = total_services - healthy_services
        
        # Dependency metrics
        deps_config = self._load_dependencies_config()
        total_dependencies = 0
        satisfied_dependencies = 0
        missing_dependencies = 0
        
        if deps_config:
            required_deps = deps_config.get("dependencies", {}).get("required", [])
            optional_deps = deps_config.get("dependencies", {}).get("optional", [])
            
            total_dependencies = len(required_deps) + len(optional_deps)
            
            for dep_config in required_deps + optional_deps:
                dep_info = DependencyInfo(
                    name=dep_config["name"],
                    version_constraint=dep_config.get("version_constraint", ""),
                    dependency_type=DependencyType.REQUIRED if dep_config in required_deps else DependencyType.OPTIONAL,
                    purpose=dep_config.get("purpose", ""),
                    alternatives=dep_config.get("alternatives", []),
                    import_name=dep_config["import_name"],
                    installation_name=dep_config["installation_name"]
                )
                
                result = self.validator.validate_dependency(dep_info)
                if result.is_available:
                    satisfied_dependencies += 1
                else:
                    missing_dependencies += 1
        
        # System resource metrics (optional)
        cpu_usage = None
        memory_usage = None
        
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
        except ImportError:
            pass  # psutil not available
        
        metrics = SystemMetrics(
            timestamp=timestamp,
            total_services=total_services,
            healthy_services=healthy_services,
            unhealthy_services=unhealthy_services,
            total_dependencies=total_dependencies,
            satisfied_dependencies=satisfied_dependencies,
            missing_dependencies=missing_dependencies,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage
        )
        
        self.system_metrics_history.append(metrics)
        
        # Trim history to last 1000 entries
        if len(self.system_metrics_history) > 1000:
            self.system_metrics_history = self.system_metrics_history[-1000:]
        
        return metrics
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """
        Generate dashboard data for web interface.
        
        Returns:
            Dashboard data structure
        """
        current_health = self.check_all_services()
        current_system = self.check_system_metrics()
        
        # Get recent history (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > one_hour_ago
        ]
        
        recent_system_metrics = [
            m for m in self.system_metrics_history
            if datetime.fromisoformat(m.timestamp) > one_hour_ago
        ]
        
        # Calculate uptime percentages
        service_uptime = {}
        for service_name in current_health.keys():
            service_metrics = [m for m in recent_metrics if m.service_name == service_name]
            if service_metrics:
                healthy_count = sum(1 for m in service_metrics if m.is_healthy)
                uptime_percentage = (healthy_count / len(service_metrics)) * 100
                service_uptime[service_name] = uptime_percentage
            else:
                service_uptime[service_name] = 100.0 if current_health[service_name].is_healthy else 0.0
        
        return {
            "generated_at": datetime.now().isoformat(),
            "current_health": {name: asdict(metric) for name, metric in current_health.items()},
            "current_system": asdict(current_system),
            "service_uptime": service_uptime,
            "recent_metrics": [asdict(m) for m in recent_metrics[-100:]],  # Last 100 entries
            "recent_system_metrics": [asdict(m) for m in recent_system_metrics[-100:]],
            "alerts": self._generate_alerts(current_health, current_system)
        }
    
    def generate_html_dashboard(self, output_file: Optional[str] = None) -> str:
        """
        Generate HTML dashboard.
        
        Args:
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Path to generated HTML file
        """
        dashboard_data = self.generate_dashboard_data()
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"health_dashboard_{timestamp}.html"
        
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = self.output_dir / output_file
        
        html_content = self._generate_html_content(dashboard_data)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def export_metrics(self, output_file: Optional[str] = None, format: str = "json") -> str:
        """
        Export metrics data.
        
        Args:
            output_file: Output file path (auto-generated if None)
            format: Export format (json, csv)
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"health_metrics_{timestamp}.{format}"
        
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = self.output_dir / output_file
        
        if format.lower() == "json":
            data = {
                "exported_at": datetime.now().isoformat(),
                "metrics_history": [asdict(m) for m in self.metrics_history],
                "system_metrics_history": [asdict(m) for m in self.system_metrics_history]
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write service metrics
                writer.writerow(["Type", "Timestamp", "Service", "Healthy", "ResponseTime", "Error"])
                for metric in self.metrics_history:
                    writer.writerow([
                        "service",
                        metric.timestamp,
                        metric.service_name,
                        metric.is_healthy,
                        metric.response_time_ms,
                        metric.error_message or ""
                    ])
                
                # Write system metrics
                writer.writerow([])  # Empty row separator
                writer.writerow(["Type", "Timestamp", "TotalServices", "HealthyServices", "TotalDeps", "SatisfiedDeps"])
                for metric in self.system_metrics_history:
                    writer.writerow([
                        "system",
                        metric.timestamp,
                        metric.total_services,
                        metric.healthy_services,
                        metric.total_dependencies,
                        metric.satisfied_dependencies
                    ])
        
        return str(output_path)
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                self.check_all_services()
                self.check_system_metrics()
                
                # Generate updated dashboard
                dashboard_path = self.generate_html_dashboard("current_dashboard.html")
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _load_dependencies_config(self) -> Optional[Dict[str, Any]]:
        """Load dependencies configuration."""
        config_file = project_root / "config" / "dependencies.yaml"
        try:
            import yaml
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return None
    
    def _generate_alerts(self, current_health: Dict[str, HealthMetric], current_system: SystemMetrics) -> List[Dict[str, Any]]:
        """Generate alerts based on current status."""
        alerts = []
        
        # Service health alerts
        for service_name, metric in current_health.items():
            if not metric.is_healthy:
                alerts.append({
                    "type": "error",
                    "title": f"Service Unhealthy: {service_name}",
                    "message": metric.error_message or "Service health check failed",
                    "timestamp": metric.timestamp
                })
            elif metric.response_time_ms and metric.response_time_ms > 1000:  # > 1 second
                alerts.append({
                    "type": "warning",
                    "title": f"Slow Response: {service_name}",
                    "message": f"Response time: {metric.response_time_ms:.1f}ms",
                    "timestamp": metric.timestamp
                })
        
        # System alerts
        if current_system.missing_dependencies > 0:
            alerts.append({
                "type": "error",
                "title": "Missing Dependencies",
                "message": f"{current_system.missing_dependencies} dependencies are missing",
                "timestamp": current_system.timestamp
            })
        
        if current_system.unhealthy_services > 0:
            alerts.append({
                "type": "warning",
                "title": "Unhealthy Services",
                "message": f"{current_system.unhealthy_services} services are unhealthy",
                "timestamp": current_system.timestamp
            })
        
        # Resource alerts (if available)
        if current_system.cpu_usage and current_system.cpu_usage > 80:
            alerts.append({
                "type": "warning",
                "title": "High CPU Usage",
                "message": f"CPU usage: {current_system.cpu_usage:.1f}%",
                "timestamp": current_system.timestamp
            })
        
        if current_system.memory_usage and current_system.memory_usage > 80:
            alerts.append({
                "type": "warning",
                "title": "High Memory Usage",
                "message": f"Memory usage: {current_system.memory_usage:.1f}%",
                "timestamp": current_system.timestamp
            })
        
        return alerts
    
    def _generate_html_content(self, dashboard_data: Dict[str, Any]) -> str:
        """Generate HTML content for dashboard."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Service Health Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .services-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .service-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .service-status {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .status-healthy {{ background-color: #4CAF50; }}
        .status-unhealthy {{ background-color: #F44336; }}
        .alerts {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .alert {{
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 4px solid;
        }}
        .alert-error {{
            background-color: #ffebee;
            border-left-color: #f44336;
        }}
        .alert-warning {{
            background-color: #fff3e0;
            border-left-color: #ff9800;
        }}
        .uptime-bar {{
            width: 100%;
            height: 8px;
            background-color: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }}
        .uptime-fill {{
            height: 100%;
            background-color: #4CAF50;
            transition: width 0.3s ease;
        }}
        .refresh-info {{
            color: #666;
            font-size: 0.9em;
            text-align: center;
            margin-top: 20px;
        }}
    </style>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {{
            window.location.reload();
        }}, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Service Health Dashboard</h1>
            <p>Generated at: {dashboard_data['generated_at']}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" style="color: #4CAF50;">
                    {dashboard_data['current_system']['healthy_services']}
                </div>
                <div class="metric-label">Healthy Services</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #F44336;">
                    {dashboard_data['current_system']['unhealthy_services']}
                </div>
                <div class="metric-label">Unhealthy Services</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #2196F3;">
                    {dashboard_data['current_system']['satisfied_dependencies']}
                </div>
                <div class="metric-label">Satisfied Dependencies</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #FF9800;">
                    {dashboard_data['current_system']['missing_dependencies']}
                </div>
                <div class="metric-label">Missing Dependencies</div>
            </div>
        </div>
        
        <div class="services-grid">
            {self._generate_service_cards_html(dashboard_data)}
        </div>
        
        {self._generate_alerts_html(dashboard_data['alerts'])}
        
        <div class="refresh-info">
            Dashboard auto-refreshes every 30 seconds
        </div>
    </div>
</body>
</html>"""
    
    def _generate_service_cards_html(self, dashboard_data: Dict[str, Any]) -> str:
        """Generate HTML for service cards."""
        cards_html = []
        
        for service_name, health_data in dashboard_data['current_health'].items():
            is_healthy = health_data['is_healthy']
            status_class = "status-healthy" if is_healthy else "status-unhealthy"
            status_text = "Healthy" if is_healthy else "Unhealthy"
            
            uptime = dashboard_data['service_uptime'].get(service_name, 0)
            uptime_color = "#4CAF50" if uptime >= 95 else "#FF9800" if uptime >= 80 else "#F44336"
            
            response_time = health_data.get('response_time_ms', 0)
            response_time_text = f"{response_time:.1f}ms" if response_time else "N/A"
            
            error_message = health_data.get('error_message', '')
            error_html = f"<div style='color: #F44336; font-size: 0.9em; margin-top: 5px;'>{error_message}</div>" if error_message else ""
            
            cards_html.append(f"""
            <div class="service-card">
                <div class="service-status">
                    <div class="status-indicator {status_class}"></div>
                    <strong>{service_name}</strong>
                </div>
                <div>Status: {status_text}</div>
                <div>Response Time: {response_time_text}</div>
                <div>Uptime: {uptime:.1f}%</div>
                <div class="uptime-bar">
                    <div class="uptime-fill" style="width: {uptime}%; background-color: {uptime_color};"></div>
                </div>
                {error_html}
            </div>
            """)
        
        return ''.join(cards_html)
    
    def _generate_alerts_html(self, alerts: List[Dict[str, Any]]) -> str:
        """Generate HTML for alerts section."""
        if not alerts:
            return """
            <div class="alerts">
                <h2>🟢 Alerts</h2>
                <p>No alerts - all systems are operating normally.</p>
            </div>
            """
        
        alerts_html = []
        for alert in alerts:
            alert_class = f"alert-{alert['type']}"
            icon = "🔴" if alert['type'] == 'error' else "⚠️"
            
            alerts_html.append(f"""
            <div class="alert {alert_class}">
                <strong>{icon} {alert['title']}</strong><br>
                {alert['message']}
                <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
                    {alert['timestamp']}
                </div>
            </div>
            """)
        
        return f"""
        <div class="alerts">
            <h2>🚨 Alerts ({len(alerts)})</h2>
            {''.join(alerts_html)}
        </div>
        """


def main():
    """Main entry point for the health dashboard CLI."""
    parser = argparse.ArgumentParser(description="Service health monitoring dashboard")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check current health status")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start continuous monitoring")
    monitor_parser.add_argument("--interval", "-i", type=int, default=30, help="Check interval in seconds")
    monitor_parser.add_argument("--duration", "-d", type=int, help="Monitoring duration in seconds")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Generate HTML dashboard")
    dashboard_parser.add_argument("--output", "-o", help="Output file path")
    dashboard_parser.add_argument("--open", action="store_true", help="Open dashboard in browser")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export metrics data")
    export_parser.add_argument("--output", "-o", help="Output file path")
    export_parser.add_argument("--format", "-f", choices=["json", "csv"], default="json", help="Export format")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    monitor = HealthMonitor()
    
    try:
        if args.command == "check":
            print("🏥 Checking service health...")
            health_metrics = monitor.check_all_services()
            system_metrics = monitor.check_system_metrics()
            
            print(f"\n📊 System Status:")
            print(f"   Services: {system_metrics.healthy_services}/{system_metrics.total_services} healthy")
            print(f"   Dependencies: {system_metrics.satisfied_dependencies}/{system_metrics.total_dependencies} satisfied")
            
            print(f"\n🔍 Service Details:")
            for service_name, metric in sorted(health_metrics.items()):
                status = "✅" if metric.is_healthy else "❌"
                response_time = f" ({metric.response_time_ms:.1f}ms)" if metric.response_time_ms else ""
                print(f"   {status} {service_name}{response_time}")
                if metric.error_message:
                    print(f"      Error: {metric.error_message}")
        
        elif args.command == "monitor":
            monitor.check_interval = args.interval
            monitor.start_monitoring()
            
            try:
                if args.duration:
                    print(f"⏱️  Monitoring for {args.duration} seconds...")
                    time.sleep(args.duration)
                else:
                    print("⏱️  Monitoring continuously (Press Ctrl+C to stop)...")
                    while True:
                        time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                monitor.stop_monitoring()
        
        elif args.command == "dashboard":
            print("📊 Generating health dashboard...")
            dashboard_path = monitor.generate_html_dashboard(args.output)
            print(f"✅ Dashboard generated: {dashboard_path}")
            
            if args.open:
                import webbrowser
                webbrowser.open(f"file://{Path(dashboard_path).absolute()}")
                print("🌐 Dashboard opened in browser")
        
        elif args.command == "export":
            print(f"📤 Exporting metrics in {args.format} format...")
            export_path = monitor.export_metrics(args.output, args.format)
            print(f"✅ Metrics exported: {export_path}")
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()