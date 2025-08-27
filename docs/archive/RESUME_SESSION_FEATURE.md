# Resume Previous Session Feature

## Overview

The AAA system now supports resuming previous analysis sessions, allowing users to return to their work at any time using a session ID.

## How to Use

### 1. Starting a New Analysis
When you start any analysis (Text Input, File Upload, or Jira Integration), the system creates a unique session ID that looks like:
```
7249c0d9-7896-4fdf-931b-4f4aafbc44e0
```

### 2. Finding Your Session ID
You can find your session ID in several places:
- **During Analysis**: Displayed in the "Processing Progress" section
- **After Completion**: Shown at the bottom of the Analysis tab with a "Copy Session ID" button
- **Export Files**: Session ID is included in export file names
- **URL**: Session ID may appear in the browser URL during analysis

### 3. Resuming a Session

1. Go to the **Analysis** tab
2. Select **"Resume Previous Session"** from the input method options
3. Enter your session ID in the text field
4. Click **"Resume Session"**

The system will:
- Validate the session ID format
- Check if the session exists
- Load the session state and requirements
- Display the current progress and results

### 4. Session ID Format
Session IDs follow the UUID format: `8-4-4-4-12` hexadecimal characters
- ✅ Valid: `7249c0d9-7896-4fdf-931b-4f4aafbc44e0`
- ❌ Invalid: `invalid-session-id`

## Features

### Session Information Display
When you have an active session, the Analysis tab shows:
- Current session ID
- Copy to clipboard button
- Session status and progress

### Error Handling
The system provides helpful error messages for:
- Invalid session ID format
- Session not found
- Expired sessions
- Network timeouts

### Session Persistence
Sessions are stored using the existing `DiskCacheStore` system and persist across:
- Browser refreshes
- Application restarts
- Different devices (if using the same backend)

## Technical Implementation

### API Integration
- Uses existing `/status/{session_id}` endpoint
- Validates session existence before loading
- Loads complete session state including requirements and recommendations

### UI Components
- New "Resume Previous Session" input method
- Session ID validation with regex pattern matching
- Copy to clipboard functionality
- Comprehensive error handling and user guidance

### Session State Management
- Integrates with existing Streamlit session state
- Loads all session data: phase, progress, requirements, recommendations
- Maintains compatibility with existing workflow

## Testing

You can test the feature using the provided test script:
```bash
python3 test_resume_session.py
```

This will:
1. Validate session ID format checking
2. Test API endpoint connectivity
3. Create a test session for resume testing

## Example Usage

### Scenario 1: Interrupted Analysis
1. User starts analysis but closes browser
2. Later, user returns and selects "Resume Previous Session"
3. Enters saved session ID
4. Continues from where they left off

### Scenario 2: Sharing Results
1. User completes analysis
2. Copies session ID and shares with colleague
3. Colleague uses "Resume Previous Session" to view results
4. Both can access the same analysis data

### Scenario 3: Long-Running Analysis
1. User starts complex analysis that takes time
2. Saves session ID and continues other work
3. Returns later to check progress
4. Resumes session to see completion status

## Benefits

- **Continuity**: Never lose your analysis progress
- **Collaboration**: Share session IDs with team members
- **Flexibility**: Return to analysis at any time
- **Reliability**: Recover from browser crashes or network issues
- **Audit Trail**: Keep track of previous analyses

## Session Lifecycle

1. **Creation**: Session created during `/ingest` API call
2. **Processing**: Session progresses through phases (PARSING → VALIDATING → QNA → MATCHING → RECOMMENDING → DONE)
3. **Persistence**: Session data stored in cache/disk storage
4. **Resume**: Session can be resumed at any phase
5. **Completion**: Final results available indefinitely (subject to storage policies)