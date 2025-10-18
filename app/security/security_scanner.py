"""Automated security scanning system for continuous security monitoring."""

import re
import json
import hashlib
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

import yaml

from app.utils.logger import app_logger
from app.config import Settings


class SeverityLevel(Enum):
    """Security issue severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityIssue:
    """Represents a security issue found during scanning."""

    id: str
    title: str
    description: str
    severity: SeverityLevel
    category: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
            "cwe_id": self.cwe_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ScanResult:
    """Results of a security scan."""

    scan_id: str
    scan_type: str
    start_time: datetime
    end_time: datetime
    issues: List[SecurityIssue]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "scan_id": self.scan_id,
            "scan_type": self.scan_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": self.summary,
        }


class SecurityScanner:
    """Comprehensive security scanner for the AAA application."""

    def __init__(self, settings: Settings) -> None:
        """Initialize security scanner.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.scan_results_dir = Path("security_scans")
        self.scan_results_dir.mkdir(exist_ok=True)

        # Security patterns to detect
        self._init_security_patterns()

        app_logger.info("Security scanner initialized")

    def _init_security_patterns(self) -> None:
        """Initialize security vulnerability patterns."""
        self.security_patterns = {
            # Hardcoded secrets
            "hardcoded_secrets": [
                (
                    r'(?i)(password|pwd|pass)\s*=\s*["\'][^"\']{8,}["\']',
                    "Hardcoded password detected",
                ),
                (
                    r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][^"\']{20,}["\']',
                    "Hardcoded API key detected",
                ),
                (
                    r'(?i)(secret|token)\s*=\s*["\'][^"\']{16,}["\']',
                    "Hardcoded secret/token detected",
                ),
                (
                    r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*=\s*["\'][A-Z0-9]{20}["\']',
                    "AWS access key detected",
                ),
                (
                    r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*=\s*["\'][A-Za-z0-9/+=]{40}["\']',
                    "AWS secret key detected",
                ),
            ],
            # SQL injection vulnerabilities
            "sql_injection": [
                (
                    r'execute\s*\(\s*["\'].*%s.*["\']',
                    "Potential SQL injection via string formatting",
                ),
                (
                    r'query\s*\(\s*["\'].*\+.*["\']',
                    "Potential SQL injection via string concatenation",
                ),
                (
                    r"cursor\.execute\s*\([^)]*%[^)]*\)",
                    "Potential SQL injection in cursor.execute",
                ),
            ],
            # Command injection
            "command_injection": [
                (r"os\.system\s*\([^)]*\+[^)]*\)", "Command injection via os.system"),
                (
                    r"subprocess\.(call|run|Popen)\s*\([^)]*\+[^)]*\)",
                    "Command injection via subprocess",
                ),
                (
                    r"eval\s*\([^)]*input[^)]*\)",
                    "Code injection via eval with user input",
                ),
                (
                    r"exec\s*\([^)]*input[^)]*\)",
                    "Code injection via exec with user input",
                ),
            ],
            # Path traversal
            "path_traversal": [
                (
                    r"open\s*\([^)]*\+[^)]*\)",
                    "Potential path traversal in file operations",
                ),
                (
                    r"Path\s*\([^)]*\+[^)]*\)",
                    "Potential path traversal in Path operations",
                ),
            ],
            # Insecure random
            "weak_crypto": [
                (r"random\.random\(\)", "Weak random number generation"),
                (r"random\.randint\(", "Weak random number generation"),
                (r"hashlib\.md5\(", "Weak hash algorithm (MD5)"),
                (r"hashlib\.sha1\(", "Weak hash algorithm (SHA1)"),
            ],
            # Debug/development code
            "debug_code": [
                (r"print\s*\([^)]*password[^)]*\)", "Password in print statement"),
                (r"print\s*\([^)]*secret[^)]*\)", "Secret in print statement"),
                (r"debug\s*=\s*True", "Debug mode enabled"),
                (r"DEBUG\s*=\s*True", "Debug mode enabled"),
            ],
            # Insecure configurations
            "insecure_config": [
                (r"ssl_verify\s*=\s*False", "SSL verification disabled"),
                (r"verify\s*=\s*False", "SSL verification disabled"),
                (r"ALLOWED_HOSTS\s*=\s*\[\s*\*\s*\]", "Wildcard in ALLOWED_HOSTS"),
            ],
        }

    def _generate_scan_id(self) -> str:
        """Generate unique scan ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:8]
        return f"scan_{timestamp}_{random_suffix}"

    async def scan_code_vulnerabilities(self) -> ScanResult:
        """Scan code for security vulnerabilities."""
        scan_id = self._generate_scan_id()
        start_time = datetime.utcnow()

        app_logger.info(f"Starting code vulnerability scan: {scan_id}")

        issues = []

        # Scan Python files
        python_files = list(Path(".").rglob("*.py"))
        for file_path in python_files:
            # Skip virtual environment and cache directories
            if any(
                part in str(file_path)
                for part in [".venv", "__pycache__", ".git", "node_modules"]
            ):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                file_issues = self._scan_file_content(str(file_path), content)
                issues.extend(file_issues)

            except Exception as e:
                app_logger.warning(f"Could not scan file {file_path}: {e}")

        # Scan configuration files
        config_files = []
        config_files.extend(Path(".").rglob("*.yaml"))
        config_files.extend(Path(".").rglob("*.yml"))
        config_files.extend(Path(".").rglob("*.json"))
        config_files.extend(Path(".").rglob("*.env*"))

        for file_path in config_files:
            if any(
                part in str(file_path)
                for part in [".git", "node_modules", "__pycache__"]
            ):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                file_issues = self._scan_config_file(str(file_path), content)
                issues.extend(file_issues)

            except Exception as e:
                app_logger.warning(f"Could not scan config file {file_path}: {e}")

        end_time = datetime.utcnow()

        # Generate summary
        summary = self._generate_scan_summary(issues)

        scan_result = ScanResult(
            scan_id=scan_id,
            scan_type="code_vulnerabilities",
            start_time=start_time,
            end_time=end_time,
            issues=issues,
            summary=summary,
        )

        # Save scan results
        await self._save_scan_results(scan_result)

        app_logger.info(
            f"Code vulnerability scan completed: {len(issues)} issues found"
        )
        return scan_result

    def _scan_file_content(self, file_path: str, content: str) -> List[SecurityIssue]:
        """Scan file content for security issues."""
        issues = []
        lines = content.split("\n")

        for category, patterns in self.security_patterns.items():
            for pattern, description in patterns:
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        issue_id = hashlib.sha256(
                            f"{file_path}:{line_num}:{pattern}".encode()
                        ).hexdigest()[:16]

                        # Determine severity based on category
                        severity = self._get_severity_for_category(category)

                        # Get CWE ID if available
                        cwe_id = self._get_cwe_for_pattern(pattern)

                        # Generate recommendation
                        recommendation = self._get_recommendation_for_category(category)

                        issue = SecurityIssue(
                            id=issue_id,
                            title=description,
                            description=f"{description} in {file_path}",
                            severity=severity,
                            category=category,
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=line.strip(),
                            recommendation=recommendation,
                            cwe_id=cwe_id,
                        )
                        issues.append(issue)

        return issues

    def _scan_config_file(self, file_path: str, content: str) -> List[SecurityIssue]:
        """Scan configuration files for security issues."""
        issues = []

        # Check for secrets in config files
        secret_patterns = [
            (
                r'(?i)(password|pwd|pass|secret|token|key)\s*[:=]\s*["\']?[a-zA-Z0-9]{8,}["\']?',
                "Potential secret in config file",
            ),
            (
                r'(?i)api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
                "API key in config file",
            ),
        ]

        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            for pattern, description in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip obvious placeholders
                    if any(
                        placeholder in line.lower()
                        for placeholder in [
                            "placeholder",
                            "example",
                            "your_",
                            "xxx",
                            "***",
                        ]
                    ):
                        continue

                    issue_id = hashlib.sha256(
                        f"{file_path}:{line_num}:{pattern}".encode()
                    ).hexdigest()[:16]

                    issue = SecurityIssue(
                        id=issue_id,
                        title=description,
                        description=f"{description}: {file_path}",
                        severity=SeverityLevel.HIGH,
                        category="config_secrets",
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        recommendation="Remove secrets from config files and use environment variables or secure vaults",
                        cwe_id="CWE-798",
                    )
                    issues.append(issue)

        return issues

    def _get_severity_for_category(self, category: str) -> SeverityLevel:
        """Get severity level for a vulnerability category."""
        severity_map = {
            "hardcoded_secrets": SeverityLevel.CRITICAL,
            "sql_injection": SeverityLevel.HIGH,
            "command_injection": SeverityLevel.HIGH,
            "path_traversal": SeverityLevel.HIGH,
            "weak_crypto": SeverityLevel.MEDIUM,
            "debug_code": SeverityLevel.LOW,
            "insecure_config": SeverityLevel.MEDIUM,
            "config_secrets": SeverityLevel.HIGH,
        }
        return severity_map.get(category, SeverityLevel.MEDIUM)

    def _get_cwe_for_pattern(self, pattern: str) -> Optional[str]:
        """Get CWE ID for a vulnerability pattern."""
        cwe_map = {
            "password": "CWE-798",  # Use of Hard-coded Credentials
            "api_key": "CWE-798",
            "secret": "CWE-798",
            "sql": "CWE-89",  # SQL Injection
            "command": "CWE-78",  # OS Command Injection
            "eval": "CWE-94",  # Code Injection
            "exec": "CWE-94",
            "path": "CWE-22",  # Path Traversal
            "random": "CWE-330",  # Use of Insufficiently Random Values
            "md5": "CWE-327",  # Use of a Broken Cryptographic Algorithm
            "sha1": "CWE-327",
            "ssl_verify": "CWE-295",  # Improper Certificate Validation
        }

        for keyword, cwe in cwe_map.items():
            if keyword in pattern.lower():
                return cwe

        return None

    def _get_recommendation_for_category(self, category: str) -> str:
        """Get security recommendation for a vulnerability category."""
        recommendations = {
            "hardcoded_secrets": "Use environment variables or secure credential management systems",
            "sql_injection": "Use parameterized queries or ORM methods to prevent SQL injection",
            "command_injection": "Validate and sanitize all user inputs before using in system commands",
            "path_traversal": "Validate file paths and use safe path manipulation functions",
            "weak_crypto": "Use cryptographically secure random number generators and strong hash algorithms",
            "debug_code": "Remove debug code and sensitive information from production code",
            "insecure_config": "Enable security features and avoid insecure configurations",
            "config_secrets": "Move secrets to environment variables or secure vaults",
        }
        return recommendations.get(category, "Review and fix the security issue")

    async def scan_dependencies(self) -> ScanResult:
        """Scan dependencies for known vulnerabilities."""
        scan_id = self._generate_scan_id()
        start_time = datetime.utcnow()

        app_logger.info(f"Starting dependency vulnerability scan: {scan_id}")

        issues = []

        try:
            # Use safety to check Python dependencies
            result = subprocess.run(
                ["python", "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)

                # Check for known vulnerable packages (simplified check)
                vulnerable_packages = {
                    "requests": {"version": "2.25.0", "issue": "CVE-2021-33503"},
                    "urllib3": {"version": "1.26.4", "issue": "CVE-2021-33503"},
                    "pyyaml": {"version": "5.4.0", "issue": "CVE-2020-14343"},
                }

                for package in packages:
                    name = package["name"].lower()
                    version = package["version"]

                    if name in vulnerable_packages:
                        vulnerable_packages[name]

                        issue = SecurityIssue(
                            id=f"dep_{name}_{version}",
                            title=f"Vulnerable dependency: {name}",
                            description=f"Package {name} version {version} has known vulnerabilities",
                            severity=SeverityLevel.HIGH,
                            category="vulnerable_dependency",
                            recommendation=f"Update {name} to a secure version",
                            cwe_id="CWE-1104",
                        )
                        issues.append(issue)

        except Exception as e:
            app_logger.warning(f"Could not scan dependencies: {e}")

        end_time = datetime.utcnow()

        summary = self._generate_scan_summary(issues)

        scan_result = ScanResult(
            scan_id=scan_id,
            scan_type="dependency_vulnerabilities",
            start_time=start_time,
            end_time=end_time,
            issues=issues,
            summary=summary,
        )

        await self._save_scan_results(scan_result)

        app_logger.info(
            f"Dependency vulnerability scan completed: {len(issues)} issues found"
        )
        return scan_result

    async def scan_configuration_security(self) -> ScanResult:
        """Scan system configuration for security issues."""
        scan_id = self._generate_scan_id()
        start_time = datetime.utcnow()

        app_logger.info(f"Starting configuration security scan: {scan_id}")

        issues = []

        # Check file permissions
        sensitive_files = [
            "config.yaml",
            ".env",
            "requirements.txt",
            "docker-compose.yml",
        ]

        for file_name in sensitive_files:
            file_path = Path(file_name)
            if file_path.exists():
                try:
                    stat_info = file_path.stat()
                    permissions = oct(stat_info.st_mode)[-3:]

                    # Check if file is world-readable
                    if permissions[2] in ["4", "5", "6", "7"]:
                        issue = SecurityIssue(
                            id=f"perm_{file_name}",
                            title=f"Insecure file permissions: {file_name}",
                            description=f"File {file_name} is world-readable (permissions: {permissions})",
                            severity=SeverityLevel.MEDIUM,
                            category="file_permissions",
                            file_path=str(file_path),
                            recommendation="Restrict file permissions to owner only",
                            cwe_id="CWE-732",
                        )
                        issues.append(issue)

                except Exception as e:
                    app_logger.warning(
                        f"Could not check permissions for {file_name}: {e}"
                    )

        # Check Docker configuration if present
        docker_compose_path = Path("docker-compose.yml")
        if docker_compose_path.exists():
            try:
                with open(docker_compose_path, "r") as f:
                    docker_config = yaml.safe_load(f)

                # Check for privileged containers
                services = docker_config.get("services", {})
                for service_name, service_config in services.items():
                    if service_config.get("privileged", False):
                        issue = SecurityIssue(
                            id=f"docker_priv_{service_name}",
                            title=f"Privileged Docker container: {service_name}",
                            description=f"Service {service_name} runs in privileged mode",
                            severity=SeverityLevel.HIGH,
                            category="docker_security",
                            file_path="docker-compose.yml",
                            recommendation="Remove privileged mode unless absolutely necessary",
                            cwe_id="CWE-250",
                        )
                        issues.append(issue)

            except Exception as e:
                app_logger.warning(f"Could not scan Docker configuration: {e}")

        end_time = datetime.utcnow()

        summary = self._generate_scan_summary(issues)

        scan_result = ScanResult(
            scan_id=scan_id,
            scan_type="configuration_security",
            start_time=start_time,
            end_time=end_time,
            issues=issues,
            summary=summary,
        )

        await self._save_scan_results(scan_result)

        app_logger.info(
            f"Configuration security scan completed: {len(issues)} issues found"
        )
        return scan_result

    def _generate_scan_summary(self, issues: List[SecurityIssue]) -> Dict[str, Any]:
        """Generate summary statistics for scan results."""
        severity_counts = {severity.value: 0 for severity in SeverityLevel}
        category_counts = {}

        for issue in issues:
            severity_counts[issue.severity.value] += 1
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1

        return {
            "total_issues": len(issues),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "risk_score": self._calculate_risk_score(issues),
        }

    def _calculate_risk_score(self, issues: List[SecurityIssue]) -> float:
        """Calculate overall risk score based on issues found."""
        severity_weights = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.HIGH: 7,
            SeverityLevel.CRITICAL: 10,
        }

        total_score = sum(severity_weights[issue.severity] for issue in issues)

        # Normalize to 0-100 scale
        max_possible_score = len(issues) * 10 if issues else 1
        return min(100, (total_score / max_possible_score) * 100)

    async def _save_scan_results(self, scan_result: ScanResult) -> None:
        """Save scan results to file."""
        try:
            results_file = self.scan_results_dir / f"{scan_result.scan_id}.json"

            with open(results_file, "w") as f:
                json.dump(scan_result.to_dict(), f, indent=2)

            app_logger.info(f"Scan results saved to {results_file}")

        except Exception as e:
            app_logger.error(f"Failed to save scan results: {e}")

    async def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scan history."""
        try:
            scan_files = sorted(
                self.scan_results_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            history = []
            for scan_file in scan_files[:limit]:
                try:
                    with open(scan_file, "r") as f:
                        scan_data = json.load(f)
                    history.append(scan_data)
                except Exception as e:
                    app_logger.warning(f"Could not load scan file {scan_file}: {e}")

            return history

        except Exception as e:
            app_logger.error(f"Failed to get scan history: {e}")
            return []

    async def run_full_security_scan(self) -> Dict[str, ScanResult]:
        """Run all security scans."""
        app_logger.info("Starting full security scan")

        results = {}

        # Run all scan types
        scan_types = [
            ("code_vulnerabilities", self.scan_code_vulnerabilities),
            ("dependencies", self.scan_dependencies),
            ("configuration", self.scan_configuration_security),
        ]

        for scan_name, scan_func in scan_types:
            try:
                result = await scan_func()
                results[scan_name] = result
            except Exception as e:
                app_logger.error(f"Failed to run {scan_name} scan: {e}")

        app_logger.info(f"Full security scan completed: {len(results)} scans run")
        return results


# Global security scanner instance
_security_scanner: Optional[SecurityScanner] = None


def get_security_scanner(settings: Optional[Settings] = None) -> SecurityScanner:
    """Get global security scanner instance.

    Args:
        settings: Application settings

    Returns:
        Security scanner instance
    """
    global _security_scanner

    if _security_scanner is None:
        if settings is None:
            from app.config import load_settings

            settings = load_settings()

        _security_scanner = SecurityScanner(settings)

    return _security_scanner
