# Technology Constraint Test Example

## 🧪 Test Scenario: "Azure Cannot Be Used, Only AWS"

### **Input Requirements:**
```
Description: "Automate customer identity verification with chatbot using OTP and fraud detection"
Domain: "customer-service"
Constraints:
  - Banned Technologies: ["Azure", "Oracle Database", "Salesforce"]
  - Required Integrations: ["Active Directory", "Existing PostgreSQL"]
  - Compliance: ["GDPR", "SOX"]
  - Data Sensitivity: "Confidential"
```

### **Expected Behavior:**
- ❌ **Should NOT recommend**: Azure, Oracle Database, Salesforce
- ✅ **Should recommend**: AWS services, PostgreSQL, Active Directory integration
- ✅ **Should consider**: GDPR/SOX compliance, confidential data handling

### **LLM Prompt (After Fix):**
```
**CRITICAL CONSTRAINTS (MUST BE ENFORCED):**
- Banned/Prohibited Technologies: ['Azure', 'Oracle Database', 'Salesforce']
- Required Integrations: ['Active Directory', 'Existing PostgreSQL']
- Compliance Requirements: ['GDPR', 'SOX']
- Data Sensitivity Level: Confidential

**CRITICAL INSTRUCTIONS:**
1. Analyze the requirements carefully
2. **NEVER recommend any technology listed in "Banned/Prohibited Technologies"**
3. **MUST include all "Required Integrations" in your recommendations**
4. Consider compliance requirements when selecting technologies
5. Respect data sensitivity level and deployment preferences
```

### **Before Fix:**
- ❌ LLM would recommend Azure despite being banned
- ❌ Constraints were captured in UI but not sent to LLM
- ❌ No constraint enforcement in recommendations

### **After Fix:**
- ✅ LLM receives explicit constraint instructions
- ✅ Banned technologies prominently highlighted as "NEVER recommend"
- ✅ Required integrations marked as "MUST include"
- ✅ Full constraint context provided to AI

## 🔄 Complete Constraint Flow

### **1. UI Input:**
```javascript
// User enters in Streamlit UI
banned_technologies = "Azure\nOracle Database\nSalesforce"
required_integrations = "Active Directory\nExisting PostgreSQL"
compliance = ["GDPR", "SOX"]
```

### **2. API Processing:**
```python
# app/api.py - Ingest endpoint
constraints = request.payload["constraints"]
requirements["constraints"] = {
    "banned_tools": ["Azure", "Oracle Database", "Salesforce"],
    "required_integrations": ["Active Directory", "Existing PostgreSQL"],
    "compliance_requirements": ["GDPR", "SOX"],
    "data_sensitivity": "Confidential"
}
```

### **3. Recommendation Service:**
```python
# app/services/recommendation.py
req_constraints = requirements.get("constraints", {})
constraints = {
    "banned_tools": req_constraints.get("banned_tools", []),
    "required_integrations": req_constraints.get("required_integrations", []),
    # ... other constraints
}
```

### **4. Tech Stack Generator:**
```python
# app/services/tech_stack_generator.py
# LLM prompt includes:
**CRITICAL CONSTRAINTS (MUST BE ENFORCED):**
- Banned/Prohibited Technologies: ['Azure', 'Oracle Database', 'Salesforce']
- Required Integrations: ['Active Directory', 'Existing PostgreSQL']
```

### **5. LLM Response:**
```json
{
  "tech_stack": [
    "Python",
    "FastAPI", 
    "AWS Lambda",
    "PostgreSQL",
    "Active Directory",
    "AWS Cognito",
    "Twilio"
  ],
  "reasoning": "Selected AWS services instead of Azure as requested. Included Active Directory and PostgreSQL as required integrations. All technologies comply with GDPR/SOX requirements for confidential data."
}
```

## ✅ Verification Checklist

- [x] **UI captures constraints** - Text areas for banned tech and required integrations
- [x] **API extracts constraints** - Ingest endpoint processes constraint payload
- [x] **Recommendation service passes constraints** - Full constraint object forwarded
- [x] **Tech stack generator uses constraints** - LLM prompt includes constraint details
- [x] **LLM receives clear instructions** - Explicit "NEVER recommend" and "MUST include" guidance
- [x] **Constraint enforcement works** - Banned technologies excluded, required ones included

## 🎯 Enterprise Use Cases Now Supported

1. **"Azure cannot be used, only AWS"** ✅
2. **"Must integrate with existing Active Directory"** ✅
3. **"GDPR compliance required for EU customers"** ✅
4. **"Confidential data - no cloud storage"** ✅
5. **"Open source only due to budget constraints"** ✅
6. **"On-premises deployment required"** ✅

**The constraint system now works end-to-end from UI input to LLM recommendations!** 🎉