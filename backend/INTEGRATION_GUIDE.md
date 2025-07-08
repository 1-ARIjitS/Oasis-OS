# Oasis OS Backend Integration Guide

This guide explains how to integrate the FastAPI backend with your frontend and the GUI agent CLI system.

## Overview

The integration creates a seamless workflow where:
1. User enters a query in the frontend "Perform Custom Workflows" text field
2. Frontend sends the query to the backend API
3. Backend executes `python -m gui_agents.s1.cli_app --model gpt-4.1`
4. Backend automatically provides the query to the CLI when prompted
5. CLI executes the task using the gpt-4.1 model
6. Backend monitors execution and returns completion status
7. Frontend displays "Workflow successfully executed" notification

## API Endpoints

### 1. Execute Workflow
- **URL**: `POST /api/v1/workflow/execute`
- **Purpose**: Start a new workflow execution
- **Request Body**:
```json
{
  "query": "Open Chrome and navigate to Google",
  "model": "gpt-4.1"
}
```
- **Response**:
```json
{
  "workflow_id": "workflow_abc123def456",
  "status": "pending",
  "message": "Workflow queued for execution",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Check Workflow Status
- **URL**: `GET /api/v1/workflow/{workflow_id}/status`
- **Purpose**: Get current status of a workflow
- **Response**:
```json
{
  "workflow_id": "workflow_abc123def456",
  "status": "completed",
  "message": "Workflow successfully executed",
  "started_at": "2024-01-15T10:30:01Z",
  "completed_at": "2024-01-15T10:32:15Z",
  "duration": 134.5,
  "logs": "Execution logs here..."
}
```

### 3. Cancel Workflow
- **URL**: `DELETE /api/v1/workflow/{workflow_id}`
- **Purpose**: Cancel a running workflow
- **Response**:
```json
{
  "success": true,
  "message": "Workflow cancelled successfully"
}
```

### 4. Get Active Workflows
- **URL**: `GET /api/v1/workflow/active`
- **Purpose**: List all currently active workflows
- **Response**:
```json
[
  {
    "workflow_id": "workflow_abc123def456",
    "query": "Open Chrome and navigate to Google",
    "status": "running",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

## Workflow Status Types

- `pending`: Workflow is queued for execution
- `running`: AI agent is executing the task
- `completed`: Workflow finished successfully
- `failed`: Workflow execution failed
- `cancelled`: Workflow was cancelled by user

## Frontend Integration

### Required HTML Elements

Your frontend needs these elements:

```html
<!-- Query input field -->
<input type="text" id="workflow-query-input" placeholder="Describe any task in detail and let AI execute it for you" />

<!-- Execute button -->
<button id="execute-button">Execute Query</button>

<!-- Optional: Cancel button -->
<button id="cancel-button" style="display: none;">Cancel</button>

<!-- Status display -->
<div id="status-display"></div>

<!-- Notification area -->
<div id="notification-area"></div>
```

### Basic Integration Steps

1. **Include the WorkflowManager**: Use the provided `frontend_integration_example.js` or create your own implementation.

2. **Handle Execute Button Click**:
```javascript
async function onExecuteClick() {
    const query = document.getElementById('workflow-query-input').value;
    
    if (!query.trim()) {
        showNotification('Please enter a task description', 'error');
        return;
    }
    
    try {
        // Start workflow
        const workflowId = await workflowManager.executeWorkflow(query, 'gpt-4.1');
        
        // Poll for completion
        const result = await workflowManager.pollWorkflowStatus(workflowId, (status) => {
            updateStatusDisplay(status.message);
        });
        
        // Show success notification
        showNotification('Workflow successfully executed', 'success');
        
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}
```

3. **Poll for Status Updates**: The example includes automatic polling that updates the UI in real-time.

4. **Handle Completion**: When status becomes `completed`, show the success notification.

## Backend Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend
```bash
# Simple startup (installs dependencies and starts server)
python start.py

# Or manual startup
python main.py
```

### 3. Verify Backend is Running
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## CLI Integration Details

The backend automatically handles CLI integration:

1. **Command Execution**: Runs `python -m gui_agents.s1.cli_app --model gpt-4.1`
2. **Query Input**: Automatically provides the user query when CLI prompts for input
3. **Completion Detection**: Monitors output for completion indicators
4. **Process Management**: Handles timeouts, cleanup, and error recovery

### CLI Input Sequence
When the CLI runs, it follows this sequence:
```
CLI: "Query: "
Backend: Sends user query + "\n"
CLI: "Would you like to provide another query? (y/n): "
Backend: Sends "n\n" to exit after completion
```

## Error Handling

The system handles various error scenarios:

1. **Invalid Query**: Frontend validates input before sending
2. **CLI Failure**: Backend captures exit codes and error messages
3. **Process Timeout**: Automatic termination after timeout period
4. **Network Issues**: Frontend handles API communication errors
5. **Cancellation**: Graceful workflow termination

## Testing the Integration

### 1. Manual Testing
```bash
# Start backend
cd backend
python start.py

# Test API directly
curl -X POST "http://localhost:8000/api/v1/workflow/execute" \
     -H "Content-Type: application/json" \
     -d '{"query": "Open calculator", "model": "gpt-4.1"}'
```

### 2. Use Test Script
```bash
cd backend
python test_api.py
```

### 3. Browser Testing
1. Open your frontend
2. Enter a simple query like "Open calculator"
3. Click execute
4. Watch status updates
5. Verify completion notification

## Configuration

### Environment Variables
```bash
# Optional: Custom API host/port
export HOST=0.0.0.0
export PORT=8000

# Optional: Debug mode
export DEBUG=true

# Optional: Log level
export LOG_LEVEL=info
```

### Frontend Configuration
Update the API base URL in your frontend:
```javascript
const workflowManager = new WorkflowManager('http://localhost:8000/api/v1');
```

## Security Considerations

1. **CORS**: Backend is configured for localhost:3000 frontend
2. **Input Validation**: All inputs are validated on both frontend and backend
3. **Process Isolation**: Each workflow runs in a separate process
4. **Timeout Protection**: Prevents runaway processes

## Troubleshooting

### Common Issues

1. **"Connection Refused"**: Ensure backend is running on port 8000
2. **"CLI Not Found"**: Ensure gui_agents module is in Python path
3. **"Workflow Stuck"**: Check logs in backend/logs/ directory
4. **"CORS Errors"**: Verify frontend URL in CORS configuration

### Logs Location
- Backend logs: `backend/logs/`
- Workflow execution logs: Included in status response

### Debug Mode
Enable debug mode for detailed logging:
```bash
export DEBUG=true
python start.py
```

## Example Queries to Test

Try these queries to test the integration:

1. **Simple**: "Open calculator"
2. **Web**: "Open Chrome and navigate to Google"
3. **File**: "Open Notepad and type 'Hello World'"
4. **Multi-step**: "Open Excel, create a new workbook, and add some sample data"

## Performance Notes

- **Startup Time**: First workflow may take longer due to CLI initialization
- **Polling Interval**: Frontend polls every 2 seconds for status updates
- **Timeout**: Workflows timeout after 10 minutes by default
- **Concurrent Workflows**: Backend supports multiple concurrent executions

## Next Steps

1. Customize the frontend integration for your specific UI framework
2. Add error recovery and retry mechanisms
3. Implement workflow history and logging
4. Add authentication if needed for production use

For more details, see the `frontend_integration_example.js` file for a complete working example. 