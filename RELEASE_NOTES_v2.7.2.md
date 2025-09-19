# Release Notes - Version 2.7.2

**Release Date**: September 19, 2025  
**Focus**: Service Registry Fixes & Diagram Rendering

## 🎯 Overview

This release resolves critical diagram rendering issues that were preventing users from viewing generated Mermaid and Infrastructure diagrams. The fixes address service registry architecture problems and improve the overall reliability of the diagram generation system.

## 🐛 Critical Fixes

### Mermaid Diagram Service Issues ✅
**Problem**: Users experiencing "Mermaid service not available. Please check service configuration." errors

**Solution**:
- Replaced incorrect service registry pattern with direct `streamlit_mermaid` library imports
- Updated all Mermaid rendering calls from service-based to direct library usage
- Enhanced error messages with clear guidance about package requirements
- Added proper availability checks with graceful fallbacks

**Impact**: All Mermaid diagrams (Context, Container, Sequence, Agent Interaction) now render correctly

### Infrastructure Diagram Service Issues ✅
**Problem**: Users seeing "Infrastructure Diagrams Not Available - The infrastructure diagram service is not registered" errors

**Solution**:
- Created missing `InfrastructureDiagramService` wrapper class for service registry compatibility
- Added infrastructure diagram service to core service registration
- Fixed service lookup names and library availability checks
- Added module-level service initialization for proper service availability

**Impact**: Infrastructure diagrams now generate successfully (AWS, GCP, Azure, Kubernetes, On-Premise)

## 🏗️ Architecture Improvements

### Service Registry Enhancements
- **Clear Separation**: External libraries now imported directly, service registry reserved for internal services
- **Better Initialization**: Module-level service initialization ensures services are available when needed
- **Enhanced Error Handling**: Informative error messages with installation guidance

### Code Quality
- Added comprehensive test suite (`test_infrastructure_diagram_fix.py`)
- Improved service health checks and availability detection
- Better separation of concerns between external libraries and internal services

## 📊 Verification Results

All fixes have been thoroughly tested and verified:

- ✅ **Mermaid Diagrams**: All types render correctly without service errors
- ✅ **Infrastructure Diagrams**: Generate successfully (tested with 37KB PNG output)
- ✅ **Service Health**: All diagram services pass health checks
- ✅ **Streamlit Integration**: Both diagram types work properly in the UI
- ✅ **Test Suite**: Comprehensive validation of all fixes

## 🔧 Technical Details

### Files Modified
- `streamlit_app.py` - Fixed service lookup and added module-level initialization
- `app/ui/analysis_display.py` - Replaced service calls with direct imports
- `app/ui/mermaid_diagrams.py` - Updated to use direct streamlit_mermaid imports
- `app/diagrams/infrastructure.py` - Added service wrapper and fixed library imports
- `app/core/service_registration.py` - Added infrastructure diagram service registration

### Dependencies
- `streamlit-mermaid>=0.3.0` - Direct import for Mermaid diagram rendering
- `diagrams>=0.23.0` - Infrastructure diagram generation library
- `graphviz` - Required by diagrams library for actual diagram generation

## 🚀 Upgrade Instructions

This release is backward compatible. Simply pull the latest changes:

```bash
git pull origin main
# No additional setup required - fixes are automatic
```

## 📈 Impact

This release significantly improves user experience by:
- **Eliminating Diagram Errors**: Users can now view all generated diagrams without service issues
- **Better Error Messages**: Clear guidance when dependencies are missing
- **Improved Reliability**: More robust service architecture with proper initialization
- **Enhanced Testing**: Comprehensive test coverage ensures fixes remain stable

## 🔮 Next Steps

With diagram rendering now fully functional, future releases will focus on:
- Enhanced diagram customization options
- Additional diagram types and formats
- Performance optimizations for large diagrams
- Extended export capabilities

---

**Full Changelog**: [CHANGELOG.md](CHANGELOG.md)  
**Technical Details**: [INFRASTRUCTURE_DIAGRAM_SERVICE_FIX_SUMMARY.md](INFRASTRUCTURE_DIAGRAM_SERVICE_FIX_SUMMARY.md)