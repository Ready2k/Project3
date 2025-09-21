#!/usr/bin/env python3
"""Migration script for existing catalog entries to use enhanced metadata."""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.validator import CatalogValidator
from app.utils.imports import require_service


class CatalogMigrator:
    """Migrates existing catalog entries to enhanced format."""
    
    def __init__(self):
        self.catalog_path = Path("data/technologies.json")
        self.backup_path = Path("data/technologies.json.backup.migration")
        self.catalog_manager = IntelligentCatalogManager()
        self.catalog_validator = CatalogValidator()
        
        # Setup logging
        try:
            self.logger = require_service('logger', context='CatalogMigrator')
        except:
            import logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('CatalogMigrator')
    
    def migrate_catalog(self) -> Dict[str, Any]:
        """Migrate the entire catalog to enhanced format.
        
        Returns:
            Migration results dictionary
        """
        try:
            self.logger.info("Starting catalog migration to enhanced format")
            
            # Create backup
            if not self._create_backup():
                return {"success": False, "error": "Failed to create backup"}
            
            # Load current catalog
            current_catalog = self._load_current_catalog()
            if not current_catalog:
                return {"success": False, "error": "Failed to load current catalog"}
            
            # Migrate technologies
            migration_results = self._migrate_technologies(current_catalog)
            
            # Validate migrated catalog
            validation_results = self._validate_migrated_catalog(migration_results["migrated_catalog"])
            
            # Save migrated catalog if validation passes
            if validation_results["valid"]:
                save_success = self._save_migrated_catalog(migration_results["migrated_catalog"])
                if save_success:
                    self.logger.info("Catalog migration completed successfully")
                    return {
                        "success": True,
                        "migration_results": migration_results,
                        "validation_results": validation_results,
                        "backup_path": str(self.backup_path)
                    }
                else:
                    return {"success": False, "error": "Failed to save migrated catalog"}
            else:
                return {
                    "success": False, 
                    "error": "Migrated catalog failed validation",
                    "validation_errors": validation_results["errors"]
                }
                
        except Exception as e:
            self.logger.error(f"Catalog migration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_backup(self) -> bool:
        """Create backup of current catalog.
        
        Returns:
            True if backup created successfully
        """
        try:
            if self.catalog_path.exists():
                shutil.copy2(self.catalog_path, self.backup_path)
                self.logger.info(f"Created catalog backup at {self.backup_path}")
                return True
            else:
                self.logger.warning("No existing catalog found to backup")
                return True
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def _load_current_catalog(self) -> Dict[str, Any]:
        """Load current catalog from file.
        
        Returns:
            Current catalog dictionary
        """
        try:
            if not self.catalog_path.exists():
                self.logger.warning("No existing catalog found")
                return {}
            
            with open(self.catalog_path, 'r') as f:
                catalog = json.load(f)
            
            self.logger.info(f"Loaded catalog with {len(catalog.get('technologies', {}))} technologies")
            return catalog
            
        except Exception as e:
            self.logger.error(f"Failed to load current catalog: {e}")
            return {}
    
    def _migrate_technologies(self, current_catalog: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate technologies to enhanced format.
        
        Args:
            current_catalog: Current catalog structure
            
        Returns:
            Migration results with migrated catalog
        """
        results = {
            "migrated": [],
            "failed": [],
            "enhanced": [],
            "migrated_catalog": {}
        }
        
        try:
            # Start with current catalog structure
            migrated_catalog = current_catalog.copy()
            
            # Ensure technologies section exists
            if "technologies" not in migrated_catalog:
                migrated_catalog["technologies"] = {}
            
            # Migrate each technology
            for tech_id, tech_info in current_catalog.get("technologies", {}).items():
                try:
                    enhanced_tech = self._enhance_technology_entry(tech_id, tech_info)
                    migrated_catalog["technologies"][tech_id] = enhanced_tech
                    
                    if enhanced_tech != tech_info:
                        results["enhanced"].append(tech_id)
                    
                    results["migrated"].append(tech_id)
                    
                except Exception as e:
                    self.logger.error(f"Failed to migrate technology {tech_id}: {e}")
                    results["failed"].append({"tech_id": tech_id, "error": str(e)})
                    # Keep original entry if migration fails
                    migrated_catalog["technologies"][tech_id] = tech_info
            
            # Add migration metadata
            migrated_catalog["_migration_metadata"] = {
                "migrated_at": datetime.now().isoformat(),
                "migration_version": "1.0",
                "enhanced_entries": len(results["enhanced"]),
                "total_entries": len(results["migrated"]),
                "failed_entries": len(results["failed"])
            }
            
            results["migrated_catalog"] = migrated_catalog
            
            self.logger.info(f"Migration completed: {len(results['migrated'])} migrated, "
                           f"{len(results['enhanced'])} enhanced, {len(results['failed'])} failed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Technology migration failed: {e}")
            results["migrated_catalog"] = current_catalog  # Return original on failure
            return results
    
    def _enhance_technology_entry(self, tech_id: str, tech_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a single technology entry with new metadata.
        
        Args:
            tech_id: Technology identifier
            tech_info: Current technology information
            
        Returns:
            Enhanced technology entry
        """
        enhanced_entry = tech_info.copy()
        
        # Add missing required fields with defaults
        if "aliases" not in enhanced_entry:
            enhanced_entry["aliases"] = self._generate_aliases(tech_id, tech_info)
        
        if "integrates_with" not in enhanced_entry:
            enhanced_entry["integrates_with"] = self._infer_integrations(tech_id, tech_info)
        
        if "alternatives" not in enhanced_entry:
            enhanced_entry["alternatives"] = self._suggest_alternatives(tech_id, tech_info)
        
        if "ecosystem" not in enhanced_entry:
            enhanced_entry["ecosystem"] = self._determine_ecosystem(tech_id, tech_info)
        
        if "maturity" not in enhanced_entry:
            enhanced_entry["maturity"] = self._assess_maturity(tech_id, tech_info)
        
        if "license" not in enhanced_entry:
            enhanced_entry["license"] = self._determine_license(tech_id, tech_info)
        
        # Add enhanced metadata
        enhanced_entry["auto_generated"] = False
        enhanced_entry["pending_review"] = False
        enhanced_entry["confidence_score"] = 0.9  # High confidence for existing entries
        enhanced_entry["source_context"] = "catalog_migration"
        enhanced_entry["last_updated"] = datetime.now().isoformat()
        
        return enhanced_entry
    
    def _generate_aliases(self, tech_id: str, tech_info: Dict[str, Any]) -> List[str]:
        """Generate aliases for a technology.
        
        Args:
            tech_id: Technology identifier
            tech_info: Technology information
            
        Returns:
            List of aliases
        """
        aliases = []
        name = tech_info.get("name", tech_id)
        
        # Common alias patterns
        if " " in name:
            # Add acronym
            words = name.split()
            if len(words) > 1:
                acronym = "".join(word[0].upper() for word in words)
                aliases.append(acronym)
        
        # Technology-specific aliases
        alias_map = {
            "fastapi": ["Fast API", "FastAPI"],
            "postgresql": ["Postgres", "PostgreSQL", "psql"],
            "mongodb": ["Mongo", "MongoDB"],
            "elasticsearch": ["Elastic", "ES"],
            "kubernetes": ["k8s", "K8s"],
            "docker": ["Docker Engine"],
            "redis": ["Redis Cache"],
            "aws_lambda": ["Lambda", "AWS Lambda"],
            "azure_functions": ["Azure Functions"],
            "gcp": ["Google Cloud", "Google Cloud Platform"],
            "aws": ["Amazon Web Services"],
            "azure": ["Microsoft Azure"]
        }
        
        if tech_id in alias_map:
            aliases.extend(alias_map[tech_id])
        
        return list(set(aliases))  # Remove duplicates
    
    def _infer_integrations(self, tech_id: str, tech_info: Dict[str, Any]) -> List[str]:
        """Infer common integrations for a technology.
        
        Args:
            tech_id: Technology identifier
            tech_info: Technology information
            
        Returns:
            List of integration technologies
        """
        # Common integration patterns
        integration_map = {
            "fastapi": ["postgresql", "redis", "docker"],
            "django": ["postgresql", "redis", "celery"],
            "flask": ["postgresql", "redis"],
            "postgresql": ["sqlalchemy", "docker"],
            "mongodb": ["docker", "mongoose"],
            "redis": ["docker", "celery"],
            "docker": ["kubernetes", "nginx"],
            "kubernetes": ["docker", "helm"],
            "aws_lambda": ["aws_s3", "aws_dynamodb", "aws_api_gateway"],
            "azure_functions": ["azure_storage", "azure_cosmos_db"],
            "elasticsearch": ["kibana", "logstash", "docker"],
            "nginx": ["docker", "ssl_certificates"]
        }
        
        return integration_map.get(tech_id, [])
    
    def _suggest_alternatives(self, tech_id: str, tech_info: Dict[str, Any]) -> List[str]:
        """Suggest alternatives for a technology.
        
        Args:
            tech_id: Technology identifier
            tech_info: Technology information
            
        Returns:
            List of alternative technologies
        """
        # Common alternatives
        alternatives_map = {
            "fastapi": ["django", "flask", "express"],
            "django": ["fastapi", "flask"],
            "flask": ["fastapi", "django"],
            "postgresql": ["mysql", "mongodb"],
            "mongodb": ["postgresql", "couchdb"],
            "redis": ["memcached", "hazelcast"],
            "docker": ["podman", "containerd"],
            "kubernetes": ["docker_swarm", "nomad"],
            "aws": ["azure", "gcp"],
            "azure": ["aws", "gcp"],
            "gcp": ["aws", "azure"],
            "elasticsearch": ["solr", "opensearch"],
            "nginx": ["apache", "traefik"]
        }
        
        return alternatives_map.get(tech_id, [])
    
    def _determine_ecosystem(self, tech_id: str, tech_info: Dict[str, Any]) -> str:
        """Determine the ecosystem for a technology.
        
        Args:
            tech_id: Technology identifier
            tech_info: Technology information
            
        Returns:
            Ecosystem identifier
        """
        if tech_id.startswith("aws_") or "aws" in tech_id:
            return "aws"
        elif tech_id.startswith("azure_") or "azure" in tech_id:
            return "azure"
        elif tech_id.startswith("gcp_") or "gcp" in tech_id:
            return "gcp"
        elif tech_id in ["docker", "kubernetes", "postgresql", "redis", "nginx"]:
            return "open_source"
        else:
            return "independent"
    
    def _assess_maturity(self, tech_id: str, tech_info: Dict[str, Any]) -> str:
        """Assess the maturity level of a technology.
        
        Args:
            tech_id: Technology identifier
            tech_info: Technology information
            
        Returns:
            Maturity level
        """
        # Well-established technologies
        mature_techs = [
            "postgresql", "mysql", "redis", "nginx", "apache", "docker",
            "kubernetes", "elasticsearch", "mongodb", "django", "flask"
        ]
        
        # Newer but stable technologies
        stable_techs = [
            "fastapi", "vue", "react", "nodejs", "express"
        ]
        
        if tech_id in mature_techs:
            return "mature"
        elif tech_id in stable_techs:
            return "stable"
        else:
            return "emerging"
    
    def _determine_license(self, tech_id: str, tech_info: Dict[str, Any]) -> str:
        """Determine the license type for a technology.
        
        Args:
            tech_id: Technology identifier
            tech_info: Technology information
            
        Returns:
            License type
        """
        # Common license mappings
        license_map = {
            "postgresql": "PostgreSQL License",
            "mysql": "GPL/Commercial",
            "redis": "BSD",
            "nginx": "BSD",
            "docker": "Apache 2.0",
            "kubernetes": "Apache 2.0",
            "elasticsearch": "Elastic License",
            "mongodb": "SSPL",
            "django": "BSD",
            "flask": "BSD",
            "fastapi": "MIT",
            "vue": "MIT",
            "react": "MIT",
            "nodejs": "MIT"
        }
        
        if tech_id.startswith("aws_"):
            return "Commercial"
        elif tech_id.startswith("azure_"):
            return "Commercial"
        elif tech_id.startswith("gcp_"):
            return "Commercial"
        else:
            return license_map.get(tech_id, "Unknown")
    
    def _validate_migrated_catalog(self, migrated_catalog: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the migrated catalog.
        
        Args:
            migrated_catalog: Migrated catalog to validate
            
        Returns:
            Validation results
        """
        try:
            validation_result = self.catalog_validator.validate_catalog(migrated_catalog)
            
            self.logger.info(f"Catalog validation: {'PASSED' if validation_result.is_valid else 'FAILED'}")
            
            return {
                "valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "summary": validation_result.summary
            }
            
        except Exception as e:
            self.logger.error(f"Catalog validation failed: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {e}"],
                "warnings": [],
                "summary": {}
            }
    
    def _save_migrated_catalog(self, migrated_catalog: Dict[str, Any]) -> bool:
        """Save the migrated catalog to file.
        
        Args:
            migrated_catalog: Migrated catalog to save
            
        Returns:
            True if saved successfully
        """
        try:
            with open(self.catalog_path, 'w') as f:
                json.dump(migrated_catalog, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved migrated catalog to {self.catalog_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save migrated catalog: {e}")
            return False
    
    def rollback_migration(self) -> bool:
        """Rollback migration by restoring from backup.
        
        Returns:
            True if rollback successful
        """
        try:
            if self.backup_path.exists():
                shutil.copy2(self.backup_path, self.catalog_path)
                self.logger.info("Migration rolled back successfully")
                return True
            else:
                self.logger.error("No backup found for rollback")
                return False
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False


def main():
    """Main migration script entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate catalog entries to enhanced format")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without saving")
    parser.add_argument("--rollback", action="store_true", help="Rollback previous migration")
    parser.add_argument("--validate-only", action="store_true", help="Only validate current catalog")
    
    args = parser.parse_args()
    
    migrator = CatalogMigrator()
    
    if args.rollback:
        success = migrator.rollback_migration()
        print(f"Rollback {'successful' if success else 'failed'}")
        return 0 if success else 1
    
    if args.validate_only:
        current_catalog = migrator._load_current_catalog()
        validation_results = migrator._validate_migrated_catalog(current_catalog)
        print(f"Validation: {'PASSED' if validation_results['valid'] else 'FAILED'}")
        if validation_results['errors']:
            print("Errors:")
            for error in validation_results['errors']:
                print(f"  - {error}")
        return 0 if validation_results['valid'] else 1
    
    # Perform migration
    results = migrator.migrate_catalog()
    
    if results["success"]:
        print("Migration completed successfully!")
        print(f"Backup created at: {results['backup_path']}")
        migration_stats = results["migration_results"]
        print(f"Migrated: {len(migration_stats['migrated'])}")
        print(f"Enhanced: {len(migration_stats['enhanced'])}")
        print(f"Failed: {len(migration_stats['failed'])}")
    else:
        print(f"Migration failed: {results['error']}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())