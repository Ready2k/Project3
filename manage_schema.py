#!/usr/bin/env python3
"""
Schema Management CLI Tool

A command-line interface for managing configurable validation enums
in the AAA pattern schema system.

Usage:
    python manage_schema.py list                           # List all enums
    python manage_schema.py show <enum_name>               # Show enum details
    python manage_schema.py add <enum_name> <value>        # Add value to enum
    python manage_schema.py remove <enum_name> <value>     # Remove value from enum
    python manage_schema.py validate <enum_name> <value>   # Validate a value
    python manage_schema.py export [filename]              # Export configuration
    python manage_schema.py import <filename>              # Import configuration
"""

import sys
import json
import argparse
from pathlib import Path

# Add app to path
sys.path.append('app')

from pattern.dynamic_schema_loader import dynamic_schema_loader


def list_enums():
    """List all available enums."""
    print("📋 Available Schema Enums")
    print("=" * 50)
    
    try:
        enums = dynamic_schema_loader.get_available_enums()
        
        if not enums:
            print("No configurable enums found.")
            return
        
        for enum_name, enum_config in enums.items():
            values_count = len(enum_config.get('values', []))
            extensible = "✅ Yes" if enum_config.get('user_extensible', False) else "❌ No"
            description = enum_config.get('description', 'No description')
            
            print(f"\n🔹 {enum_name}")
            print(f"   Description: {description}")
            print(f"   Values: {values_count}")
            print(f"   User Extensible: {extensible}")
            
    except Exception as e:
        print(f"❌ Error listing enums: {e}")


def show_enum(enum_name: str):
    """Show details of a specific enum."""
    print(f"🔍 Enum Details: {enum_name}")
    print("=" * 50)
    
    try:
        enums = dynamic_schema_loader.get_available_enums()
        
        if enum_name not in enums:
            print(f"❌ Enum '{enum_name}' not found.")
            print(f"Available enums: {', '.join(enums.keys())}")
            return
        
        enum_config = enums[enum_name]
        values = enum_config.get('values', [])
        
        print(f"Description: {enum_config.get('description', 'No description')}")
        print(f"User Extensible: {'✅ Yes' if enum_config.get('user_extensible', False) else '❌ No'}")
        print(f"Values ({len(values)}):")
        
        for i, value in enumerate(values, 1):
            print(f"  {i:2d}. {value}")
            
    except Exception as e:
        print(f"❌ Error showing enum: {e}")


def add_value(enum_name: str, value: str):
    """Add a value to an enum."""
    print(f"➕ Adding '{value}' to '{enum_name}'")
    print("=" * 50)
    
    try:
        success = dynamic_schema_loader.add_enum_value(enum_name, value)
        
        if success:
            print(f"✅ Successfully added '{value}' to '{enum_name}'")
        else:
            print(f"❌ Failed to add '{value}' to '{enum_name}'")
            print("This enum may not be user extensible.")
            
    except Exception as e:
        print(f"❌ Error adding value: {e}")


def remove_value(enum_name: str, value: str):
    """Remove a value from an enum."""
    print(f"🗑️ Removing '{value}' from '{enum_name}'")
    print("=" * 50)
    
    try:
        config = dynamic_schema_loader.load_config()
        enum_config = config.get("schema_enums", {}).get(enum_name, {})
        
        if not enum_config:
            print(f"❌ Enum '{enum_name}' not found.")
            return
        
        if not enum_config.get('user_extensible', False):
            print(f"❌ Enum '{enum_name}' is not user extensible.")
            return
        
        values = enum_config.get('values', [])
        
        if value not in values:
            print(f"❌ Value '{value}' not found in '{enum_name}'.")
            print(f"Available values: {', '.join(values)}")
            return
        
        values.remove(value)
        enum_config['values'] = values
        
        # Save updated config
        with open(dynamic_schema_loader.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        dynamic_schema_loader.clear_cache()
        print(f"✅ Successfully removed '{value}' from '{enum_name}'")
        
    except Exception as e:
        print(f"❌ Error removing value: {e}")


def validate_value(enum_name: str, value: str):
    """Validate if a value is allowed for an enum."""
    print(f"🔍 Validating '{value}' for '{enum_name}'")
    print("=" * 50)
    
    try:
        is_valid = dynamic_schema_loader.validate_enum_value(enum_name, value)
        
        if is_valid:
            print(f"✅ '{value}' is valid for '{enum_name}'")
        else:
            print(f"❌ '{value}' is not valid for '{enum_name}'")
            
        # Show allowed values
        allowed_values = dynamic_schema_loader.get_enum_values(enum_name)
        print(f"\nAllowed values: {', '.join(allowed_values)}")
        
    except Exception as e:
        print(f"❌ Error validating value: {e}")


def export_config(filename: str = None):
    """Export schema configuration."""
    if not filename:
        filename = "schema_config_export.json"
    
    print(f"📤 Exporting configuration to '{filename}'")
    print("=" * 50)
    
    try:
        config = dynamic_schema_loader.load_config()
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration exported to '{filename}'")
        
    except Exception as e:
        print(f"❌ Error exporting configuration: {e}")


def import_config(filename: str):
    """Import schema configuration."""
    print(f"📥 Importing configuration from '{filename}'")
    print("=" * 50)
    
    try:
        if not Path(filename).exists():
            print(f"❌ File '{filename}' not found.")
            return
        
        with open(filename, 'r') as f:
            imported_config = json.load(f)
        
        # Validate basic structure
        if "schema_enums" not in imported_config or "validation_settings" not in imported_config:
            print("❌ Invalid configuration file format.")
            print("Required keys: 'schema_enums', 'validation_settings'")
            return
        
        # Backup current config
        backup_filename = f"{dynamic_schema_loader.config_path}.backup"
        current_config = dynamic_schema_loader.load_config()
        with open(backup_filename, 'w') as f:
            json.dump(current_config, f, indent=2)
        
        print(f"📋 Created backup: {backup_filename}")
        
        # Import new config
        with open(dynamic_schema_loader.config_path, 'w') as f:
            json.dump(imported_config, f, indent=2)
        
        dynamic_schema_loader.clear_cache()
        print(f"✅ Configuration imported from '{filename}'")
        
    except Exception as e:
        print(f"❌ Error importing configuration: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage AAA Schema Configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List all available enums')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show details of a specific enum')
    show_parser.add_argument('enum_name', help='Name of the enum to show')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a value to an enum')
    add_parser.add_argument('enum_name', help='Name of the enum')
    add_parser.add_argument('value', help='Value to add')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a value from an enum')
    remove_parser.add_argument('enum_name', help='Name of the enum')
    remove_parser.add_argument('value', help='Value to remove')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a value for an enum')
    validate_parser.add_argument('enum_name', help='Name of the enum')
    validate_parser.add_argument('value', help='Value to validate')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export configuration')
    export_parser.add_argument('filename', nargs='?', help='Output filename (optional)')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import configuration')
    import_parser.add_argument('filename', help='Input filename')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    if args.command == 'list':
        list_enums()
    elif args.command == 'show':
        show_enum(args.enum_name)
    elif args.command == 'add':
        add_value(args.enum_name, args.value)
    elif args.command == 'remove':
        remove_value(args.enum_name, args.value)
    elif args.command == 'validate':
        validate_value(args.enum_name, args.value)
    elif args.command == 'export':
        export_config(args.filename)
    elif args.command == 'import':
        import_config(args.filename)


if __name__ == "__main__":
    main()