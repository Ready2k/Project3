#!/usr/bin/env python3
"""
Dependency Update Notification System

This script monitors dependencies for updates, security vulnerabilities,
and compatibility issues, providing notifications and recommendations.
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import argparse
import re

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.dependencies import DependencyValidator, DependencyInfo, ValidationResult, DependencyType


@dataclass
class UpdateInfo:
    """Information about a dependency update."""
    package_name: str
    current_version: str
    latest_version: str
    update_type: str  # major, minor, patch
    security_update: bool = False
    breaking_changes: bool = False
    release_date: Optional[str] = None
    changelog_url: Optional[str] = None
    vulnerability_info: Optional[Dict[str, Any]] = None


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    email_enabled: bool = False
    email_recipients: List[str] = None
    slack_enabled: bool = False
    slack_webhook: Optional[str] = None
    file_output: bool = True
    output_directory: str = "docs/monitoring"
    check_interval_hours: int = 24
    notify_security_updates: bool = True
    notify_major_updates: bool = True
    notify_minor_updates: bool = False
    notify_patch_updates: bool = False


class DependencyNotifier:
    """System for monitoring and notifying about dependency updates."""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        """
        Initialize the dependency notifier.
        
        Args:
            config: Notification configuration
        """
        self.config = config or NotificationConfig()
        self.validator = DependencyValidator()
        
        # Create output directory
        self.output_dir = Path(project_root) / self.config.output_directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load previous check data
        self.state_file = self.output_dir / "dependency_check_state.json"
        self.previous_state = self._load_previous_state()
    
    def check_for_updates(self, force_check: bool = False) -> List[UpdateInfo]:
        """
        Check for dependency updates.
        
        Args:
            force_check: Force check even if recently checked
            
        Returns:
            List of available updates
        """
        # Check if we should skip based on interval
        if not force_check and not self._should_check():
            print("⏭️  Skipping check - too soon since last check")
            return []
        
        print("🔍 Checking for dependency updates...")
        
        updates = []
        deps_config = self._load_dependencies_config()
        
        if not deps_config:
            print("❌ Could not load dependency configuration")
            return updates
        
        # Check all dependencies
        all_deps = []
        all_deps.extend(deps_config.get("dependencies", {}).get("required", []))
        all_deps.extend(deps_config.get("dependencies", {}).get("optional", []))
        
        for dep_config in all_deps:
            try:
                update_info = self._check_package_updates(dep_config)
                if update_info:
                    updates.append(update_info)
            except Exception as e:
                print(f"⚠️  Error checking {dep_config['name']}: {e}")
        
        # Save current state
        self._save_current_state(updates)
        
        print(f"✅ Found {len(updates)} available updates")
        return updates
    
    def generate_update_report(self, updates: List[UpdateInfo], output_file: Optional[str] = None) -> str:
        """
        Generate a comprehensive update report.
        
        Args:
            updates: List of available updates
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"dependency_updates_{timestamp}.md"
        
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = self.output_dir / output_file
        
        # Categorize updates
        security_updates = [u for u in updates if u.security_update]
        major_updates = [u for u in updates if u.update_type == "major"]
        minor_updates = [u for u in updates if u.update_type == "minor"]
        patch_updates = [u for u in updates if u.update_type == "patch"]
        
        content = [
            "# Dependency Update Report",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Total Updates Available:** {len(updates)}",
            "",
            "## Summary",
            "",
            f"- 🔴 **Security Updates:** {len(security_updates)}",
            f"- 🟠 **Major Updates:** {len(major_updates)}",
            f"- 🟡 **Minor Updates:** {len(minor_updates)}",
            f"- 🟢 **Patch Updates:** {len(patch_updates)}",
            ""
        ]
        
        # Security updates section
        if security_updates:
            content.extend([
                "## 🔴 Security Updates (High Priority)",
                "",
                "These updates address security vulnerabilities and should be applied immediately:",
                ""
            ])
            
            for update in security_updates:
                content.extend(self._format_update_entry(update, include_security=True))
        
        # Major updates section
        if major_updates:
            content.extend([
                "## 🟠 Major Updates (Review Required)",
                "",
                "These updates may contain breaking changes and require careful review:",
                ""
            ])
            
            for update in major_updates:
                content.extend(self._format_update_entry(update))
        
        # Minor updates section
        if minor_updates:
            content.extend([
                "## 🟡 Minor Updates (Low Risk)",
                "",
                "These updates add new features but should be backward compatible:",
                ""
            ])
            
            for update in minor_updates:
                content.extend(self._format_update_entry(update))
        
        # Patch updates section
        if patch_updates:
            content.extend([
                "## 🟢 Patch Updates (Safe)",
                "",
                "These updates contain bug fixes and are generally safe to apply:",
                ""
            ])
            
            for update in patch_updates:
                content.extend(self._format_update_entry(update))
        
        # Recommendations section
        content.extend([
            "## 📋 Recommendations",
            "",
            self._generate_recommendations(updates),
            "",
            "## 🔧 Update Commands",
            "",
            "To update specific packages:",
            ""
        ])
        
        for update in updates:
            if update.security_update or update.update_type in ["major", "minor"]:
                content.append(f"```bash")
                content.append(f"pip install {update.package_name}=={update.latest_version}")
                content.append(f"```")
                content.append("")
        
        # Write report
        with open(output_path, 'w') as f:
            f.write('\n'.join(content))
        
        return str(output_path)
    
    def send_notifications(self, updates: List[UpdateInfo]) -> None:
        """
        Send notifications about available updates.
        
        Args:
            updates: List of available updates
        """
        if not updates:
            print("📭 No updates to notify about")
            return
        
        # Filter updates based on notification preferences
        filtered_updates = self._filter_updates_for_notification(updates)
        
        if not filtered_updates:
            print("📭 No updates match notification criteria")
            return
        
        print(f"📢 Sending notifications for {len(filtered_updates)} updates...")
        
        # Generate notification content
        notification_content = self._generate_notification_content(filtered_updates)
        
        # Send notifications
        if self.config.file_output:
            self._send_file_notification(notification_content, filtered_updates)
        
        if self.config.email_enabled:
            self._send_email_notification(notification_content, filtered_updates)
        
        if self.config.slack_enabled:
            self._send_slack_notification(notification_content, filtered_updates)
    
    def monitor_continuously(self, check_interval_hours: Optional[int] = None) -> None:
        """
        Monitor dependencies continuously.
        
        Args:
            check_interval_hours: Override default check interval
        """
        interval = check_interval_hours or self.config.check_interval_hours
        print(f"🔄 Starting continuous monitoring (interval: {interval} hours)")
        
        try:
            while True:
                updates = self.check_for_updates()
                if updates:
                    self.send_notifications(updates)
                    report_path = self.generate_update_report(updates)
                    print(f"📄 Report generated: {report_path}")
                
                print(f"⏰ Sleeping for {interval} hours...")
                time.sleep(interval * 3600)  # Convert hours to seconds
        
        except KeyboardInterrupt:
            print("\n⚠️  Monitoring stopped by user")
    
    def _check_package_updates(self, dep_config: Dict[str, Any]) -> Optional[UpdateInfo]:
        """Check for updates for a specific package."""
        package_name = dep_config["installation_name"]
        
        # Get current version
        current_version = self._get_installed_version(package_name)
        if not current_version:
            return None  # Package not installed
        
        # Get latest version from PyPI
        latest_version = self._get_latest_version(package_name)
        if not latest_version or latest_version == current_version:
            return None  # No update available
        
        # Determine update type
        update_type = self._determine_update_type(current_version, latest_version)
        
        # Check for security vulnerabilities
        security_info = self._check_security_vulnerabilities(package_name, current_version)
        
        # Get release information
        release_info = self._get_release_info(package_name, latest_version)
        
        return UpdateInfo(
            package_name=package_name,
            current_version=current_version,
            latest_version=latest_version,
            update_type=update_type,
            security_update=bool(security_info),
            breaking_changes=update_type == "major",
            release_date=release_info.get("release_date"),
            changelog_url=release_info.get("changelog_url"),
            vulnerability_info=security_info
        )
    
    def _get_installed_version(self, package_name: str) -> Optional[str]:
        """Get the currently installed version of a package."""
        try:
            result = subprocess.run(
                ["pip", "show", package_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()
        
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def _get_latest_version(self, package_name: str) -> Optional[str]:
        """Get the latest version of a package from PyPI."""
        try:
            result = subprocess.run(
                ["pip", "index", "versions", package_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse output to find latest version
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Available versions:' in line:
                    versions = line.split(':', 1)[1].strip().split(', ')
                    if versions and versions[0]:
                        return versions[0]
        
        except subprocess.CalledProcessError:
            # Fallback: try using pip search (if available)
            try:
                import requests
                response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data["info"]["version"]
            except Exception:
                pass
        
        return None
    
    def _determine_update_type(self, current: str, latest: str) -> str:
        """Determine the type of update (major, minor, patch)."""
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            if latest_parts[0] > current_parts[0]:
                return "major"
            elif latest_parts[1] > current_parts[1]:
                return "minor"
            else:
                return "patch"
        
        except (ValueError, IndexError):
            return "unknown"
    
    def _check_security_vulnerabilities(self, package_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Check for known security vulnerabilities."""
        try:
            # Use safety package if available
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                safety_data = json.loads(result.stdout)
                for vuln in safety_data:
                    if vuln.get("package_name") == package_name:
                        return {
                            "vulnerability_id": vuln.get("vulnerability_id"),
                            "advisory": vuln.get("advisory"),
                            "cve": vuln.get("cve"),
                            "affected_versions": vuln.get("affected_versions")
                        }
        
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            pass
        
        return None
    
    def _get_release_info(self, package_name: str, version: str) -> Dict[str, Any]:
        """Get release information for a package version."""
        try:
            import requests
            response = requests.get(f"https://pypi.org/pypi/{package_name}/{version}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                info = data.get("info", {})
                
                return {
                    "release_date": data.get("releases", {}).get(version, [{}])[0].get("upload_time"),
                    "changelog_url": info.get("project_urls", {}).get("Changelog") or info.get("home_page")
                }
        
        except Exception:
            pass
        
        return {}
    
    def _load_dependencies_config(self) -> Optional[Dict[str, Any]]:
        """Load dependencies configuration."""
        config_file = project_root / "config" / "dependencies.yaml"
        try:
            import yaml
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return None
    
    def _should_check(self) -> bool:
        """Check if we should perform a dependency check based on interval."""
        if not self.previous_state:
            return True
        
        last_check = self.previous_state.get("last_check")
        if not last_check:
            return True
        
        last_check_time = datetime.fromisoformat(last_check)
        interval_delta = timedelta(hours=self.config.check_interval_hours)
        
        return datetime.now() - last_check_time >= interval_delta
    
    def _load_previous_state(self) -> Dict[str, Any]:
        """Load previous check state."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return {}
    
    def _save_current_state(self, updates: List[UpdateInfo]) -> None:
        """Save current check state."""
        state = {
            "last_check": datetime.now().isoformat(),
            "updates_found": len(updates),
            "updates": [asdict(update) for update in updates]
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save state: {e}")
    
    def _filter_updates_for_notification(self, updates: List[UpdateInfo]) -> List[UpdateInfo]:
        """Filter updates based on notification preferences."""
        filtered = []
        
        for update in updates:
            should_notify = False
            
            if update.security_update and self.config.notify_security_updates:
                should_notify = True
            elif update.update_type == "major" and self.config.notify_major_updates:
                should_notify = True
            elif update.update_type == "minor" and self.config.notify_minor_updates:
                should_notify = True
            elif update.update_type == "patch" and self.config.notify_patch_updates:
                should_notify = True
            
            if should_notify:
                filtered.append(update)
        
        return filtered
    
    def _generate_notification_content(self, updates: List[UpdateInfo]) -> str:
        """Generate notification content."""
        security_count = sum(1 for u in updates if u.security_update)
        major_count = sum(1 for u in updates if u.update_type == "major")
        
        title = f"Dependency Updates Available ({len(updates)} total)"
        
        if security_count > 0:
            title += f" - {security_count} SECURITY UPDATES"
        
        content = [title, ""]
        
        # High priority updates first
        high_priority = [u for u in updates if u.security_update or u.update_type == "major"]
        if high_priority:
            content.append("🚨 HIGH PRIORITY UPDATES:")
            for update in high_priority:
                priority = "SECURITY" if update.security_update else "MAJOR"
                content.append(f"  • {update.package_name}: {update.current_version} → {update.latest_version} ({priority})")
            content.append("")
        
        # Other updates
        other_updates = [u for u in updates if not (u.security_update or u.update_type == "major")]
        if other_updates:
            content.append("📦 Other Updates:")
            for update in other_updates:
                content.append(f"  • {update.package_name}: {update.current_version} → {update.latest_version} ({update.update_type})")
        
        return '\n'.join(content)
    
    def _send_file_notification(self, content: str, updates: List[UpdateInfo]) -> None:
        """Send file-based notification."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        notification_file = self.output_dir / f"update_notification_{timestamp}.txt"
        
        with open(notification_file, 'w') as f:
            f.write(content)
        
        print(f"📄 Notification saved: {notification_file}")
    
    def _send_email_notification(self, content: str, updates: List[UpdateInfo]) -> None:
        """Send email notification."""
        if not self.config.email_recipients:
            print("⚠️  Email notification enabled but no recipients configured")
            return
        
        try:
            import smtplib
            from email.mime.text import MimeText
            from email.mime.multipart import MimeMultipart
            
            # This is a basic implementation - in production, you'd want proper SMTP configuration
            print("📧 Email notification would be sent to:", ', '.join(self.config.email_recipients))
            print("📧 Email content preview:")
            print(content[:200] + "..." if len(content) > 200 else content)
        
        except ImportError:
            print("⚠️  Email notification requires additional packages (smtplib)")
    
    def _send_slack_notification(self, content: str, updates: List[UpdateInfo]) -> None:
        """Send Slack notification."""
        if not self.config.slack_webhook:
            print("⚠️  Slack notification enabled but no webhook configured")
            return
        
        try:
            import requests
            
            payload = {
                "text": content,
                "username": "Dependency Monitor",
                "icon_emoji": ":package:"
            }
            
            response = requests.post(self.config.slack_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                print("📱 Slack notification sent successfully")
            else:
                print(f"⚠️  Slack notification failed: {response.status_code}")
        
        except Exception as e:
            print(f"⚠️  Slack notification error: {e}")
    
    def _format_update_entry(self, update: UpdateInfo, include_security: bool = False) -> List[str]:
        """Format an update entry for the report."""
        entry = [
            f"### {update.package_name}",
            "",
            f"- **Current Version:** {update.current_version}",
            f"- **Latest Version:** {update.latest_version}",
            f"- **Update Type:** {update.update_type.title()}",
        ]
        
        if update.release_date:
            entry.append(f"- **Release Date:** {update.release_date}")
        
        if update.changelog_url:
            entry.append(f"- **Changelog:** {update.changelog_url}")
        
        if include_security and update.vulnerability_info:
            vuln = update.vulnerability_info
            entry.extend([
                "",
                "**🔴 Security Vulnerability:**",
                f"- **Advisory:** {vuln.get('advisory', 'N/A')}",
                f"- **CVE:** {vuln.get('cve', 'N/A')}",
                f"- **Affected Versions:** {vuln.get('affected_versions', 'N/A')}"
            ])
        
        entry.extend(["", "---", ""])
        return entry
    
    def _generate_recommendations(self, updates: List[UpdateInfo]) -> str:
        """Generate recommendations based on available updates."""
        recommendations = []
        
        security_updates = [u for u in updates if u.security_update]
        major_updates = [u for u in updates if u.update_type == "major"]
        
        if security_updates:
            recommendations.append("🔴 **IMMEDIATE ACTION REQUIRED:** Apply security updates immediately")
            recommendations.append("   Test in staging environment first, then deploy to production")
        
        if major_updates:
            recommendations.append("🟠 **REVIEW REQUIRED:** Major updates may contain breaking changes")
            recommendations.append("   Review changelogs and test thoroughly before updating")
        
        if not security_updates and not major_updates:
            recommendations.append("🟢 **LOW RISK:** All available updates are minor or patch releases")
            recommendations.append("   These can generally be applied safely after basic testing")
        
        recommendations.extend([
            "",
            "**General Guidelines:**",
            "1. Always test updates in a development environment first",
            "2. Review changelogs for breaking changes",
            "3. Update dependencies one at a time when possible",
            "4. Keep backups and have a rollback plan",
            "5. Monitor application behavior after updates"
        ])
        
        return '\n'.join(recommendations)


def main():
    """Main entry point for the dependency notifier CLI."""
    parser = argparse.ArgumentParser(description="Dependency update notification system")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check for dependency updates")
    check_parser.add_argument("--force", "-f", action="store_true", help="Force check even if recently checked")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate update report")
    report_parser.add_argument("--output", "-o", help="Output file path")
    
    # Notify command
    notify_parser = subparsers.add_parser("notify", help="Send notifications about updates")
    notify_parser.add_argument("--email", action="store_true", help="Enable email notifications")
    notify_parser.add_argument("--slack", action="store_true", help="Enable Slack notifications")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start continuous monitoring")
    monitor_parser.add_argument("--interval", "-i", type=int, default=24, help="Check interval in hours")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Show current configuration")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create configuration
    config = NotificationConfig()
    if hasattr(args, 'email') and args.email:
        config.email_enabled = True
    if hasattr(args, 'slack') and args.slack:
        config.slack_enabled = True
    
    notifier = DependencyNotifier(config)
    
    try:
        if args.command == "check":
            updates = notifier.check_for_updates(force_check=args.force)
            
            if updates:
                print(f"\n📦 Found {len(updates)} available updates:")
                for update in updates:
                    priority = "🔴 SECURITY" if update.security_update else f"🔵 {update.update_type.upper()}"
                    print(f"   {priority} {update.package_name}: {update.current_version} → {update.latest_version}")
            else:
                print("✅ All dependencies are up to date")
        
        elif args.command == "report":
            updates = notifier.check_for_updates(force_check=True)
            report_path = notifier.generate_update_report(updates, args.output)
            print(f"📄 Report generated: {report_path}")
        
        elif args.command == "notify":
            updates = notifier.check_for_updates(force_check=True)
            notifier.send_notifications(updates)
        
        elif args.command == "monitor":
            notifier.config.check_interval_hours = args.interval
            notifier.monitor_continuously()
        
        elif args.command == "config":
            print("📋 Current Configuration:")
            print(f"   Check Interval: {config.check_interval_hours} hours")
            print(f"   Email Notifications: {'✅' if config.email_enabled else '❌'}")
            print(f"   Slack Notifications: {'✅' if config.slack_enabled else '❌'}")
            print(f"   File Output: {'✅' if config.file_output else '❌'}")
            print(f"   Output Directory: {config.output_directory}")
            print(f"   Notify Security Updates: {'✅' if config.notify_security_updates else '❌'}")
            print(f"   Notify Major Updates: {'✅' if config.notify_major_updates else '❌'}")
            print(f"   Notify Minor Updates: {'✅' if config.notify_minor_updates else '❌'}")
            print(f"   Notify Patch Updates: {'✅' if config.notify_patch_updates else '❌'}")
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()