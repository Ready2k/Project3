"""
Attack pack version management and update mechanisms.
Handles loading, validation, and deployment of attack pack versions.
"""
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.security.attack_patterns import AttackPattern
from app.security.deployment_config import AttackPackVersion, get_deployment_config
from app.utils.logger import app_logger


@dataclass
class AttackPackValidationResult:
    """Result of attack pack validation."""
    is_valid: bool
    pattern_count: int
    issues: List[str]
    warnings: List[str]
    metadata: Dict


class AttackPackManager:
    """Manages attack pack versions, updates, and validation."""
    
    def __init__(self, attack_packs_dir: str = "data/attack_packs", deployment_config=None):
        self.attack_packs_dir = Path(attack_packs_dir)
        self.attack_packs_dir.mkdir(parents=True, exist_ok=True)
        self.deployment_config = deployment_config or get_deployment_config()
    
    def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            app_logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def validate_attack_pack(self, file_path: Path) -> AttackPackValidationResult:
        """Validate an attack pack file."""
        issues = []
        warnings = []
        pattern_count = 0
        metadata = {}
        
        try:
            if not file_path.exists():
                issues.append(f"Attack pack file not found: {file_path}")
                return AttackPackValidationResult(False, 0, issues, warnings, metadata)
            
            # Read and parse the attack pack file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse as JSON first
            try:
                attack_data = json.loads(content)
                if isinstance(attack_data, dict) and 'patterns' in attack_data:
                    patterns = attack_data['patterns']
                    metadata = attack_data.get('metadata', {})
                elif isinstance(attack_data, list):
                    patterns = attack_data
                else:
                    issues.append("Invalid JSON structure: expected dict with 'patterns' key or list of patterns")
                    return AttackPackValidationResult(False, 0, issues, warnings, metadata)
            except json.JSONDecodeError:
                # Try to parse as text format (like the current attack pack v2)
                patterns = self._parse_text_attack_pack(content)
                if not patterns:
                    issues.append("Failed to parse attack pack as JSON or text format")
                    return AttackPackValidationResult(False, 0, issues, warnings, metadata)
            
            # Validate patterns
            pattern_ids = set()
            for i, pattern_data in enumerate(patterns):
                pattern_issues = self._validate_pattern(pattern_data, i)
                issues.extend(pattern_issues)
                
                # Check for duplicate IDs
                pattern_id = pattern_data.get('id', f'pattern_{i}')
                if pattern_id in pattern_ids:
                    issues.append(f"Duplicate pattern ID: {pattern_id}")
                pattern_ids.add(pattern_id)
            
            pattern_count = len(patterns)
            
            # Check minimum pattern count
            if pattern_count < 10:
                warnings.append(f"Low pattern count: {pattern_count} (expected at least 10)")
            
            # Validate metadata
            if metadata:
                required_metadata = ['version', 'description', 'created_at']
                for field in required_metadata:
                    if field not in metadata:
                        warnings.append(f"Missing metadata field: {field}")
            
            is_valid = len(issues) == 0
            
            app_logger.info(f"Validated attack pack {file_path}: {pattern_count} patterns, "
                          f"{len(issues)} issues, {len(warnings)} warnings")
            
            return AttackPackValidationResult(is_valid, pattern_count, issues, warnings, metadata)
            
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")
            app_logger.error(f"Failed to validate attack pack {file_path}: {e}")
            return AttackPackValidationResult(False, 0, issues, warnings, metadata)
    
    def _parse_text_attack_pack(self, content: str) -> List[Dict]:
        """Parse text-format attack pack (like current v2 format)."""
        patterns = []
        current_pattern = None
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for pattern start (e.g., "## Pattern 1:")
            if line.startswith('## Pattern '):
                if current_pattern:
                    patterns.append(current_pattern)
                
                # Extract pattern number and title
                parts = line[11:].split(':', 1)  # Remove "## Pattern "
                pattern_num = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else f"Pattern {pattern_num}"
                
                current_pattern = {
                    'id': f'PAT-{pattern_num.zfill(3)}',
                    'name': title,
                    'description': '',
                    'category': 'unknown',
                    'severity': 'medium',
                    'examples': [],
                    'indicators': []
                }
            
            elif current_pattern:
                # Add content to current pattern
                if line.startswith('**Category:**'):
                    current_pattern['category'] = line.replace('**Category:**', '').strip()
                elif line.startswith('**Description:**'):
                    current_pattern['description'] = line.replace('**Description:**', '').strip()
                elif line.startswith('**Example:**'):
                    example = line.replace('**Example:**', '').strip()
                    if example:
                        current_pattern['examples'].append(example)
                elif line.startswith('**Indicators:**'):
                    indicators = line.replace('**Indicators:**', '').strip()
                    if indicators:
                        current_pattern['indicators'] = indicators.split(', ')
                elif current_pattern['description'] and not line.startswith('**'):
                    # Continue description
                    current_pattern['description'] += ' ' + line
        
        # Add the last pattern
        if current_pattern:
            patterns.append(current_pattern)
        
        return patterns
    
    def _validate_pattern(self, pattern_data: Dict, index: int) -> List[str]:
        """Validate a single attack pattern."""
        issues = []
        
        # Required fields
        required_fields = ['id', 'name', 'description', 'category']
        for field in required_fields:
            if field not in pattern_data or not pattern_data[field]:
                issues.append(f"Pattern {index}: Missing required field '{field}'")
        
        # Validate ID format
        pattern_id = pattern_data.get('id', '')
        if pattern_id and not pattern_id.startswith('PAT-'):
            issues.append(f"Pattern {index}: ID should start with 'PAT-' (got: {pattern_id})")
        
        # Validate category
        valid_categories = [
            'in_scope_feasibility', 'out_of_scope_tasking', 'overt_prompt_injection',
            'covert_injection', 'tool_abuse', 'data_egress', 'protocol_tampering',
            'long_context_burying', 'multilingual_attacks', 'csv_excel_dangerous',
            'business_logic_toggles', 'stressful_in_scope', 'canary_coverage'
        ]
        category = pattern_data.get('category', '')
        if category and category not in valid_categories:
            issues.append(f"Pattern {index}: Invalid category '{category}'")
        
        # Validate severity
        valid_severities = ['low', 'medium', 'high', 'critical']
        severity = pattern_data.get('severity', 'medium')
        if severity not in valid_severities:
            issues.append(f"Pattern {index}: Invalid severity '{severity}'")
        
        # Validate examples
        examples = pattern_data.get('examples', [])
        if not isinstance(examples, list):
            issues.append(f"Pattern {index}: Examples must be a list")
        elif len(examples) == 0:
            issues.append(f"Pattern {index}: At least one example is required")
        
        return issues
    
    def install_attack_pack(self, source_file: Path, version: str) -> Tuple[bool, str]:
        """Install a new attack pack version."""
        try:
            # Validate the attack pack
            validation_result = self.validate_attack_pack(source_file)
            if not validation_result.is_valid:
                error_msg = f"Attack pack validation failed: {', '.join(validation_result.issues)}"
                app_logger.error(error_msg)
                return False, error_msg
            
            # Calculate checksum
            checksum = self.calculate_file_checksum(source_file)
            if not checksum:
                return False, "Failed to calculate file checksum"
            
            # Create version directory
            version_dir = self.attack_packs_dir / version
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy attack pack file
            dest_file = version_dir / "attack_pack.json"
            shutil.copy2(source_file, dest_file)
            
            # Create metadata file
            metadata = {
                'version': version,
                'installed_at': datetime.utcnow().isoformat(),
                'source_file': str(source_file),
                'checksum': checksum,
                'pattern_count': validation_result.pattern_count,
                'validation_result': {
                    'is_valid': validation_result.is_valid,
                    'issues': validation_result.issues,
                    'warnings': validation_result.warnings
                }
            }
            
            metadata_file = version_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Update deployment config
            attack_pack_version = AttackPackVersion(
                version=version,
                file_path=str(dest_file),
                checksum=checksum,
                deployed_at=datetime.utcnow(),
                is_active=False,
                validation_status="validated",
                pattern_count=validation_result.pattern_count,
                metadata=metadata
            )
            
            self.deployment_config.attack_pack_versions[version] = attack_pack_version
            self.deployment_config.save_to_file("config.yaml")
            
            app_logger.info(f"Successfully installed attack pack version {version}")
            return True, f"Attack pack version {version} installed successfully"
            
        except Exception as e:
            error_msg = f"Failed to install attack pack version {version}: {str(e)}"
            app_logger.error(error_msg)
            return False, error_msg
    
    def activate_attack_pack(self, version: str) -> Tuple[bool, str]:
        """Activate a specific attack pack version."""
        try:
            if version not in self.deployment_config.attack_pack_versions:
                return False, f"Attack pack version {version} not found"
            
            pack_info = self.deployment_config.attack_pack_versions[version]
            
            # Verify file exists
            if not Path(pack_info.file_path).exists():
                return False, f"Attack pack file not found: {pack_info.file_path}"
            
            # Verify checksum
            current_checksum = self.calculate_file_checksum(Path(pack_info.file_path))
            if current_checksum != pack_info.checksum:
                return False, f"Attack pack checksum mismatch for version {version}"
            
            # Deactivate current version
            current_active = self.deployment_config.active_attack_pack_version
            if current_active in self.deployment_config.attack_pack_versions:
                self.deployment_config.attack_pack_versions[current_active].is_active = False
            
            # Activate new version
            pack_info.is_active = True
            self.deployment_config.active_attack_pack_version = version
            
            # Save configuration
            self.deployment_config.save_to_file("config.yaml")
            
            app_logger.info(f"Activated attack pack version {version}")
            return True, f"Attack pack version {version} activated successfully"
            
        except Exception as e:
            error_msg = f"Failed to activate attack pack version {version}: {str(e)}"
            app_logger.error(error_msg)
            return False, error_msg
    
    def rollback_attack_pack(self, target_version: Optional[str] = None) -> Tuple[bool, str]:
        """Rollback to a previous attack pack version."""
        try:
            if target_version is None:
                # Find the most recent non-active version
                versions = sorted(
                    [(v, info) for v, info in self.deployment_config.attack_pack_versions.items() 
                     if not info.is_active],
                    key=lambda x: x[1].deployed_at,
                    reverse=True
                )
                
                if not versions:
                    return False, "No previous version available for rollback"
                
                target_version = versions[0][0]
            
            # Activate the target version
            success, message = self.activate_attack_pack(target_version)
            if success:
                app_logger.warning(f"Rolled back attack pack to version {target_version}")
                return True, f"Rolled back to attack pack version {target_version}"
            else:
                return False, f"Rollback failed: {message}"
                
        except Exception as e:
            error_msg = f"Failed to rollback attack pack: {str(e)}"
            app_logger.error(error_msg)
            return False, error_msg
    
    def list_available_versions(self) -> List[Dict]:
        """List all available attack pack versions."""
        versions = []
        
        for version, pack_info in self.deployment_config.attack_pack_versions.items():
            versions.append({
                'version': version,
                'file_path': pack_info.file_path,
                'checksum': pack_info.checksum,
                'deployed_at': pack_info.deployed_at.isoformat(),
                'is_active': pack_info.is_active,
                'validation_status': pack_info.validation_status,
                'pattern_count': pack_info.pattern_count,
                'metadata': pack_info.metadata
            })
        
        # Sort by deployment date (newest first)
        versions.sort(key=lambda x: x['deployed_at'], reverse=True)
        return versions
    
    def get_version_info(self, version: str) -> Optional[Dict]:
        """Get detailed information about a specific version."""
        if version not in self.deployment_config.attack_pack_versions:
            return None
        
        pack_info = self.deployment_config.attack_pack_versions[version]
        
        # Load metadata if available
        version_dir = self.attack_packs_dir / version
        metadata_file = version_dir / "metadata.json"
        
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                app_logger.warning(f"Failed to load metadata for version {version}: {e}")
        
        return {
            'version': version,
            'file_path': pack_info.file_path,
            'checksum': pack_info.checksum,
            'deployed_at': pack_info.deployed_at.isoformat(),
            'is_active': pack_info.is_active,
            'validation_status': pack_info.validation_status,
            'pattern_count': pack_info.pattern_count,
            'metadata': metadata
        }
    
    def cleanup_old_versions(self, keep_count: int = 5) -> Tuple[int, List[str]]:
        """Clean up old attack pack versions, keeping the most recent ones."""
        try:
            versions = sorted(
                [(v, info) for v, info in self.deployment_config.attack_pack_versions.items()],
                key=lambda x: x[1].deployed_at,
                reverse=True
            )
            
            # Keep active version and most recent versions
            to_keep = set()
            kept_count = 0
            
            for version, info in versions:
                if info.is_active or kept_count < keep_count:
                    to_keep.add(version)
                    kept_count += 1
            
            # Remove old versions
            removed_versions = []
            for version, info in versions:
                if version not in to_keep:
                    # Remove files
                    version_dir = self.attack_packs_dir / version
                    if version_dir.exists():
                        shutil.rmtree(version_dir)
                    
                    # Remove from config
                    del self.deployment_config.attack_pack_versions[version]
                    removed_versions.append(version)
            
            # Save updated config
            if removed_versions:
                self.deployment_config.save_to_file("config.yaml")
            
            app_logger.info(f"Cleaned up {len(removed_versions)} old attack pack versions")
            return len(removed_versions), removed_versions
            
        except Exception as e:
            app_logger.error(f"Failed to cleanup old versions: {e}")
            return 0, []
    
    def check_for_updates(self, update_source: str) -> Tuple[bool, Optional[str], str]:
        """Check for available attack pack updates."""
        try:
            # This is a placeholder for update checking logic
            # In a real implementation, this would check a remote source
            # for newer attack pack versions
            
            app_logger.info(f"Checking for updates from {update_source}")
            
            # For now, return no updates available
            return False, None, "No updates available"
            
        except Exception as e:
            error_msg = f"Failed to check for updates: {str(e)}"
            app_logger.error(error_msg)
            return False, None, error_msg
    
    def export_version(self, version: str, export_path: Path) -> Tuple[bool, str]:
        """Export a specific attack pack version."""
        try:
            if version not in self.deployment_config.attack_pack_versions:
                return False, f"Version {version} not found"
            
            pack_info = self.deployment_config.attack_pack_versions[version]
            source_file = Path(pack_info.file_path)
            
            if not source_file.exists():
                return False, f"Source file not found: {source_file}"
            
            # Copy file to export location
            shutil.copy2(source_file, export_path)
            
            app_logger.info(f"Exported attack pack version {version} to {export_path}")
            return True, f"Exported version {version} successfully"
            
        except Exception as e:
            error_msg = f"Failed to export version {version}: {str(e)}"
            app_logger.error(error_msg)
            return False, error_msg


# Global attack pack manager instance
_attack_pack_manager: Optional[AttackPackManager] = None


def get_attack_pack_manager() -> AttackPackManager:
    """Get the global attack pack manager instance."""
    global _attack_pack_manager
    if _attack_pack_manager is None:
        _attack_pack_manager = AttackPackManager()
    return _attack_pack_manager