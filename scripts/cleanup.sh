#!/bin/bash
# AAA Repository Cleanup Script
# Removes temporary files and cleans up development artifacts

echo "🧹 Cleaning up AAA repository..."

# Remove Python cache files
echo "Removing Python cache files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove temporary files
echo "Removing temporary files..."
find . -name "*.tmp" -delete
find . -name "*.log" -delete
find . -name ".DS_Store" -delete

# Clean pytest cache
echo "Cleaning pytest cache..."
rm -rf .pytest_cache/

# Clean coverage files (keep .coverage for CI)
echo "Cleaning old coverage files..."
find . -name ".coverage.*" -delete

# Clean any backup files older than 7 days (except technology catalog backup)
echo "Cleaning old backup files..."
find . -name "*.backup" -not -path "./data/technologies.json.backup" -mtime +7 -delete 2>/dev/null || true

# Clean exports older than 30 days
echo "Cleaning old export files..."
find exports/ -name "*.json" -mtime +30 -delete 2>/dev/null || true
find exports/ -name "*.md" -mtime +30 -delete 2>/dev/null || true
find exports/ -name "*.html" -mtime +30 -delete 2>/dev/null || true

echo "✅ Repository cleanup complete!"
echo ""
echo "📊 Current disk usage:"
du -sh . 2>/dev/null || echo "Could not calculate disk usage"