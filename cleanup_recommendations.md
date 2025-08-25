# File Cleanup Recommendations

## Files to Remove/Rename

### 1. Duplicate/Legacy Files
- `streamlit_app.py` → Move to `legacy/streamlit_app_legacy.py`
- `debug_streamlit_error.py` → Remove (debug file)
- `nonexistent.json` → Rename to `component_mapping_rules.json`

### 2. Outdated Summary Files (Keep only latest)
- Remove older summary files, keep only:
  - `README.md`
  - `CHANGELOG.md` 
  - `DEPLOYMENT.md`
  - `SECURITY_REVIEW.md`

### 3. Test File Organization
- Move all root-level `test_*.py` files to `app/tests/integration/`
- Update import paths in moved files
- Remove references to non-existent test files

### 4. Documentation Consolidation
- Merge duplicate documentation files
- Remove outdated implementation summaries
- Keep only current feature documentation

## Directory Structure Improvements

```
app/
├── ui/
│   ├── tabs/           # Individual tab components
│   ├── components/     # Reusable UI components  
│   └── utils/          # UI utility functions
├── services/
│   ├── core/           # Core business services
│   ├── integrations/   # External integrations
│   └── ai/             # AI/LLM related services
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```