#!/usr/bin/env python3
"""
Example script demonstrating catalog management CLI tools usage.

This script shows how to use the various CLI tools for managing
the technology catalog programmatically and through command-line interfaces.
"""

import subprocess
import sys
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any


class CatalogManagementExample:
    """Example class demonstrating catalog management operations."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
    
    def run_cli_command(self, command_args: List[str]) -> subprocess.CompletedProcess:
        """Run a CLI command and return the result."""
        cmd = [sys.executable, '-m', 'app.cli.main'] + command_args
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        print("-" * 50)
        
        return result
    
    def demonstrate_basic_operations(self):
        """Demonstrate basic catalog operations."""
        print("=== BASIC CATALOG OPERATIONS ===\n")
        
        # 1. Show catalog overview
        print("1. Showing catalog overview:")
        self.run_cli_command(['dashboard', 'overview'])
        
        # 2. List all technologies
        print("2. Listing all technologies:")
        self.run_cli_command(['catalog', 'list'])
        
        # 3. Search for technologies
        print("3. Searching for 'fast' technologies:")
        self.run_cli_command(['catalog', 'search', 'fast'])
        
        # 4. Show catalog statistics
        print("4. Showing catalog statistics:")
        self.run_cli_command(['catalog', 'stats'])
        
        # 5. Validate catalog
        print("5. Validating catalog:")
        self.run_cli_command(['catalog', 'validate'])
    
    def demonstrate_technology_management(self):
        """Demonstrate adding and managing technologies."""
        print("=== TECHNOLOGY MANAGEMENT ===\n")
        
        # 1. Add a new technology
        print("1. Adding a new technology:")
        self.run_cli_command([
            'catalog', 'add',
            '--name', 'Example Framework',
            '--category', 'frameworks',
            '--description', 'An example framework for demonstration purposes',
            '--ecosystem', 'open_source',
            '--maturity', 'beta',
            '--license', 'MIT',
            '--aliases', 'example-fw', 'examplefw',
            '--integrates-with', 'python', 'javascript',
            '--alternatives', 'other-framework',
            '--tags', 'example', 'demo', 'framework',
            '--use-cases', 'web_development', 'api_development'
        ])
        
        # 2. Show the added technology
        print("2. Showing the added technology:")
        self.run_cli_command(['catalog', 'show', 'example_framework'])
        
        # 3. Update the technology
        print("3. Updating the technology:")
        self.run_cli_command([
            'catalog', 'update', 'example_framework',
            '--description', 'Updated: An example framework for demonstration purposes',
            '--add-alias', 'new-alias',
            '--add-tag', 'updated'
        ])
        
        # 4. Search for the updated technology
        print("4. Searching for the updated technology:")
        self.run_cli_command(['catalog', 'search', 'example'])
    
    def demonstrate_review_management(self):
        """Demonstrate review queue management."""
        print("=== REVIEW QUEUE MANAGEMENT ===\n")
        
        # 1. List pending reviews
        print("1. Listing pending reviews:")
        self.run_cli_command(['review', 'list'])
        
        # 2. Show review statistics
        print("2. Showing review statistics:")
        self.run_cli_command(['review', 'stats'])
        
        # Note: We won't actually approve/reject in the example
        # as it would modify the real catalog
        
        print("3. Example commands for review operations:")
        print("   # Approve a technology:")
        print("   python -m app.cli.main review approve tech_id --reviewer 'admin' --notes 'Looks good'")
        print("   # Reject a technology:")
        print("   python -m app.cli.main review reject tech_id --reviewer 'admin' --notes 'Invalid technology'")
        print("   # Batch approve high-confidence entries:")
        print("   python -m app.cli.main review batch-approve --reviewer 'admin' --min-confidence 0.9")
    
    def demonstrate_bulk_operations(self):
        """Demonstrate bulk import/export operations."""
        print("=== BULK OPERATIONS ===\n")
        
        # 1. Export catalog to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = Path(f.name)
        
        try:
            print("1. Exporting catalog to JSON:")
            self.run_cli_command(['bulk', 'export', str(export_path)])
            
            # 2. Show export file info
            if export_path.exists():
                print(f"2. Export file created: {export_path}")
                print(f"   File size: {export_path.stat().st_size} bytes")
                
                # Show first few lines of export
                with open(export_path, 'r') as f:
                    content = f.read()
                    if content:
                        data = json.loads(content)
                        print(f"   Technologies exported: {len(data.get('technologies', {}))}")
            
            # 3. Create a backup
            print("3. Creating a backup:")
            self.run_cli_command(['bulk', 'backup'])
            
        finally:
            # Cleanup
            if export_path.exists():
                export_path.unlink()
    
    def demonstrate_health_monitoring(self):
        """Demonstrate health monitoring and dashboard features."""
        print("=== HEALTH MONITORING ===\n")
        
        # 1. Show health report
        print("1. Showing health report:")
        self.run_cli_command(['dashboard', 'health'])
        
        # 2. Show trends
        print("2. Showing trends and analytics:")
        self.run_cli_command(['dashboard', 'trends'])
        
        # 3. Show quality report
        print("3. Showing quality report:")
        self.run_cli_command(['dashboard', 'quality'])
    
    def demonstrate_programmatic_access(self):
        """Demonstrate programmatic access to catalog management."""
        print("=== PROGRAMMATIC ACCESS ===\n")
        
        try:
            from app.services.catalog.intelligent_manager import IntelligentCatalogManager
            from app.services.catalog.models import TechEntry, EcosystemType, MaturityLevel
            
            print("1. Creating catalog manager instance:")
            manager = IntelligentCatalogManager()
            
            print("2. Getting catalog statistics:")
            stats = manager.get_catalog_statistics()
            print(f"   Total technologies: {stats.total_entries}")
            print(f"   Pending review: {stats.pending_review}")
            print(f"   Auto-generated: {stats.auto_generated}")
            
            print("3. Searching for technologies:")
            results = manager.search_technologies("python", limit=3)
            for result in results:
                print(f"   - {result.tech_entry.name} (score: {result.match_score:.2f})")
            
            print("4. Validating catalog consistency:")
            validation_result = manager.validate_catalog_consistency()
            print(f"   Is valid: {validation_result.is_valid}")
            print(f"   Errors: {len(validation_result.errors)}")
            print(f"   Warnings: {len(validation_result.warnings)}")
            
            print("5. Getting pending review queue:")
            pending = manager.get_pending_review_queue()
            print(f"   Pending technologies: {len(pending)}")
            
        except Exception as e:
            print(f"Error in programmatic access: {e}")
    
    def run_all_examples(self):
        """Run all example demonstrations."""
        print("TECHNOLOGY CATALOG MANAGEMENT EXAMPLES")
        print("=" * 60)
        print()
        
        try:
            self.demonstrate_basic_operations()
            print()
            
            self.demonstrate_technology_management()
            print()
            
            self.demonstrate_review_management()
            print()
            
            self.demonstrate_bulk_operations()
            print()
            
            self.demonstrate_health_monitoring()
            print()
            
            self.demonstrate_programmatic_access()
            print()
            
            print("=" * 60)
            print("EXAMPLES COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
        except Exception as e:
            print(f"Error running examples: {e}")
            return False
        
        return True


def main():
    """Main function to run the examples."""
    example = CatalogManagementExample()
    
    print("This script demonstrates the catalog management CLI tools.")
    print("It will run various commands to show how to use the system.")
    print()
    
    response = input("Do you want to run the examples? [y/N]: ")
    if response.lower() != 'y':
        print("Examples cancelled.")
        return
    
    print()
    success = example.run_all_examples()
    
    if success:
        print("\nFor more information, see:")
        print("- Documentation: Project3/docs/catalog_management.md")
        print("- CLI Help: python -m app.cli.main --help")
        print("- Individual tool help: python -m app.cli.main <tool> --help")
    else:
        print("\nSome examples failed. Check the error messages above.")
        print("Make sure you're running from the Project3 directory.")


if __name__ == '__main__':
    main()