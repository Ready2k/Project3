# Integration Guide: Dynamic Component Mapping

## 🎯 **Quick Integration Steps**

### **1. Add Management Tab to Streamlit App**

Add this to your main Streamlit application (`streamlit_app.py`):

```python
# Import the management interface
from app.ui.component_mapping_manager import render_component_mapping_tab

# Add to your tab structure
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Analysis", 
    "Pattern Library", 
    "Technology Catalog",
    "Component Mapping",  # New tab
    "Export"
])

with tab4:
    render_component_mapping_tab()
```

### **2. Update Infrastructure Generation**

The infrastructure generator is already updated to use dynamic mapping as a fallback. No additional changes needed.

### **3. Test the Integration**

```bash
# Run the test suite
python3 test_dynamic_component_mapping.py

# Start Streamlit and test the new tab
streamlit run streamlit_app.py
```

## 🔧 **Configuration Management**

### **Default Rules Location**
- **File**: `data/component_mapping_rules.json`
- **Auto-created**: If missing, default rules are generated automatically
- **Editable**: Through UI or direct JSON editing

### **Adding New Technology Support**

**Example**: Adding support for "Mistral AI" API

1. **Through UI**:
   - Go to "Component Mapping" tab
   - Click "Add Rule" 
   - Pattern: `(mistral|mistral[_-]?ai).*api`
   - Component Type: `saas`
   - Deployment Model: `saas`

2. **Through JSON**:
```json
{
  "technology_pattern": "(mistral|mistral[_-]?ai).*api",
  "component_type": "saas", 
  "deployment_model": "saas",
  "specific_component": "Snowflake",
  "tags": ["ai", "api", "llm"],
  "description": "Mistral AI API services"
}
```

## 📊 **Migration from Hardcoded Mappings**

### **Current State**
```python
# In infrastructure.py - hardcoded
"agentic": {
    "langchain_orchestrator": onprem_compute.Server,
    "crewai_coordinator": onprem_compute.Server,
    # ... more hardcoded mappings
}
```

### **Future State** 
```json
// In component_mapping_rules.json - configurable
{
  "technology_pattern": "(langchain|crewai).*orchestrator",
  "component_type": "compute",
  "deployment_model": "onprem",
  "specific_component": "Server"
}
```

### **Migration Steps**
1. **Keep Both**: Current system uses dynamic as fallback
2. **Test Extensively**: Validate all existing diagrams still work
3. **Gradual Migration**: Move rules one category at a time
4. **Remove Hardcoded**: Once confident, remove static mappings

## 🧪 **Testing New Rules**

### **Through UI**
1. Go to "Component Mapping" → "Test Mapping" tab
2. Enter technology names to test
3. See immediate results

### **Programmatically**
```python
from app.diagrams.dynamic_component_mapper import DynamicComponentMapper

mapper = DynamicComponentMapper()
provider, component = mapper.map_technology_to_component("new_technology")
print(f"Maps to: {provider}/{component}")
```

## 🎛️ **Management Features**

### **Available Through UI**
- ✅ **View Rules**: Browse all current mapping rules
- ✅ **Add Rules**: Create new technology mappings
- ✅ **Test Mappings**: Validate rules before deployment
- ✅ **Statistics**: Monitor system usage and effectiveness

### **Advanced Features**
- 🔄 **Cache Management**: Clear mapping cache when needed
- 📊 **Analytics**: See which rules are used most
- 🧪 **Bulk Testing**: Test multiple technologies at once
- 📁 **Export/Import**: Share rule sets between environments

## 🚀 **Benefits Realized**

### **Immediate**
- **No Code Changes**: New technologies work automatically
- **Faster Iteration**: Rules updated in seconds, not development cycles
- **Better Testing**: Isolated rule validation
- **Consistent Architecture**: Aligns with system philosophy

### **Long-term**
- **Future-Proof**: Adapts to AI/ML evolution automatically
- **Maintainable**: Clear separation of concerns
- **Scalable**: Unlimited technology support
- **Configurable**: Business users can manage mappings

## 📋 **Recommended Next Steps**

1. **Add to Main App**: Integrate the management tab
2. **Team Training**: Educate team on new system
3. **Rule Migration**: Start converting hardcoded mappings
4. **Documentation**: Create user guides for rule management
5. **Monitoring**: Track system usage and effectiveness

This dynamic system transforms infrastructure diagram generation from a maintenance burden into a self-adapting, future-proof capability.