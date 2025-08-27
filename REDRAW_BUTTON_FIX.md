# Redraw Button Fix

## Problem Identified

The initial redraw button implementation didn't work because:

1. **Original Implementation**: Only set a flag (`force_redraw_{diagram_id} = True`) and called `st.rerun()`
2. **Why It Failed**: Streamlit didn't know to recreate the Mermaid component since the component key remained the same
3. **Why Large View Worked**: It toggled the `show_large` state, which triggered different rendering paths with different heights, forcing component refresh

## Root Cause Analysis

### Streamlit Component Behavior
- Streamlit components are cached based on their parameters and keys
- If the same component is called with the same parameters and key, Streamlit reuses the existing instance
- To force a component refresh, you need to change either:
  - The component parameters (what Large View does)
  - The component key (what the fix does)

### Original Redraw Logic Flaw
```python
# ❌ This didn't work
if st.button("🔄 Redraw"):
    st.session_state[f"force_redraw_{diagram_id}"] = True
    st.rerun()

# Component was still called with same key:
stmd.st_mermaid(mermaid_code, height=500)  # Same key, same parameters
```

## Solution Implemented

### 1. Redraw Counter Mechanism

**For Mermaid Diagrams:**
```python
# ✅ Fixed implementation
if st.button("🔄 Redraw"):
    current_redraw_count = st.session_state.get(f"redraw_count_{diagram_id}", 0)
    st.session_state[f"redraw_count_{diagram_id}"] = current_redraw_count + 1
    st.rerun()

# Component called with unique key:
redraw_count = st.session_state.get(f"redraw_count_{diagram_id}", 0)
stmd.st_mermaid(mermaid_code, height=500, key=f"regular_{diagram_id}_{redraw_count}")
```

**For Infrastructure Diagrams:**
```python
# ✅ Fixed implementation
if st.button("🔄 Redraw"):
    current_redraw_count = st.session_state.get(f"infra_redraw_count_{diagram_id}", 0)
    st.session_state[f"infra_redraw_count_{diagram_id}"] = current_redraw_count + 1
    st.rerun()

# Temporary file created with unique name:
infra_redraw_count = st.session_state.get(f"infra_redraw_count_{diagram_id}", 0)
with tempfile.NamedTemporaryFile(suffix=f'_{infra_redraw_count}.png', delete=False) as tmp_file:
```

### 2. Key Changes Made

#### Mermaid Diagrams (`render_mermaid` method)
- Added redraw counter increment on button click
- Added unique key parameter to `stmd.st_mermaid()` calls
- Applied to both regular and large view modes

#### Infrastructure Diagrams (`render_infrastructure_diagram` method)
- Added redraw counter increment on button click
- Added redraw counter to temporary file naming for uniqueness
- Forces diagram regeneration with new file path

## How The Fix Works

### Step-by-Step Process
1. **User clicks 🔄 Redraw**
2. **Counter increments**: `redraw_count_{diagram_id}` increases by 1
3. **Streamlit reruns**: `st.rerun()` triggers page refresh
4. **New component key**: `regular_{diagram_id}_{new_count}` is different from previous
5. **Component recreated**: Streamlit sees new key and creates fresh component instance
6. **Diagram renders**: New component instance displays the diagram

### Why This Works vs Original
- **Original**: Same key → Streamlit reuses cached component → No refresh
- **Fixed**: Different key → Streamlit creates new component → Fresh render

### Comparison with Large View
- **Large View**: Changes parameters (height 500→700) → Forces refresh
- **Redraw**: Changes key (count 0→1→2...) → Forces refresh

## Testing Results

### Redraw Counter Mechanism Test
```
Initial state:     Component key: regular_abc123_0
After 1st redraw:  Component key: regular_abc123_1  ✅ Different key
After 2nd redraw:  Component key: regular_abc123_2  ✅ Different key
Large view:        Component key: large_abc123_2    ✅ Different prefix
```

### Expected User Experience
1. **Blank diagram appears** → User clicks 🔄 Redraw
2. **Counter increments** → Component key changes
3. **Page refreshes** → New component created
4. **Diagram renders** → Fresh Mermaid rendering

## Files Modified

- `streamlit_app.py`: 
  - Updated redraw button logic in `render_mermaid()`
  - Updated redraw button logic in `render_infrastructure_diagram()`
  - Added unique key parameters to force component refresh

## Benefits of the Fix

### ✅ **Functional Redraw**
- Redraw button now actually forces diagram refresh
- Works for both Mermaid and Infrastructure diagrams
- Provides immediate visual feedback

### ✅ **Consistent Behavior**
- Redraw button behavior now matches user expectations
- Similar effectiveness to Large View button
- Reliable component refresh mechanism

### ✅ **Technical Robustness**
- Uses Streamlit's component key system correctly
- Handles both regular and large view modes
- Maintains all existing functionality

## Future Considerations

### Potential Enhancements
1. **Counter Reset**: Reset counter after successful renders to prevent overflow
2. **Visual Feedback**: Show loading indicator during redraw
3. **Error Recovery**: Clear counter on persistent errors
4. **Performance**: Monitor impact of frequent component recreation

### Monitoring
- Track redraw button usage frequency
- Monitor for any performance impacts
- Collect user feedback on effectiveness

## Conclusion

The redraw button now works correctly by leveraging Streamlit's component key system to force component recreation. This provides users with a reliable way to refresh diagrams without expensive LLM regeneration, matching the effectiveness of the Large View button while serving a different purpose.