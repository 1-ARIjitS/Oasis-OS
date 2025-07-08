# Oasis OS Backend API

A FastAPI backend that integrates with the GUI Agent CLI to execute workflows through a REST API.

## Features

- **Workflow Execution**: Execute GUI agent tasks through REST API endpoints
- **Background Processing**: Handle long-running tasks asynchronously
- **Status Monitoring**: Real-time status tracking of workflow execution
- **Error Handling**: Comprehensive error handling and logging
- **CORS Support**: Cross-origin resource sharing for frontend integration

## Quick Start

### Prerequisites

- Python 3.8+
- All GUI agent dependencies installed in the parent project

### Installation

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your API keys if needed
```

3. Start the server:
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Workflow Execution

#### POST `/api/v1/workflow/execute`

Execute a new workflow with the GUI agent.

**Request Body:**
```json
{
    "query": "Open a web browser and search for 'Python tutorials'",
    "model": "gpt-4o"
}
```

**Response:**
```json
{
    "workflow_id": "workflow_abc123456789",
    "status": "running",
    "message": "Workflow execution started successfully",
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/v1/workflow/{workflow_id}/status`

Get the current status of a workflow.

**Response:**
```json
{
    "workflow_id": "workflow_abc123456789",
    "status": "completed",
    "message": "Workflow executed successfully",
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:32:30Z",
    "duration": 150.5,
    "logs": "Task completed successfully..."
}
```

#### DELETE `/api/v1/workflow/{workflow_id}`

Cancel a running workflow.

#### GET `/api/v1/workflow/active`

Get list of all active workflows.

### Health Check

#### GET `/health`

Returns the health status of the API.

## Workflow Status

- `pending`: Workflow is queued for execution
- `running`: Workflow is currently executing
- `completed`: Workflow finished successfully
- `failed`: Workflow encountered an error
- `cancelled`: Workflow was cancelled by user

## Integration with Frontend

The backend is designed to work seamlessly with the Next.js frontend. It handles CORS automatically and provides structured responses that can be easily consumed by the frontend components.

### Example Frontend Integration

```javascript
// Execute a workflow
const response = await fetch('http://localhost:8000/api/v1/workflow/execute', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        query: 'Open calculator and compute 2+2',
        model: 'gpt-4o'
    })
});

const result = await response.json();
console.log('Workflow ID:', result.workflow_id);

// Check status
const statusResponse = await fetch(`http://localhost:8000/api/v1/workflow/${result.workflow_id}/status`);
const status = await statusResponse.json();
console.log('Status:', status.status);
```

## Error Handling

The API provides comprehensive error handling with structured error responses:

```json
{
    "status": "error",
    "message": "Detailed error message",
    "error_code": "VALIDATION_ERROR"
}
```

## Logging

All operations are logged with different levels:
- INFO: General operation logs
- DEBUG: Detailed execution logs
- ERROR: Error conditions

Log files are stored in the `logs/` directory with timestamps.

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── run.py               # Server startup script
├── requirements.txt     # Python dependencies
├── models/             # Pydantic data models
│   └── workflow.py
├── routers/            # API route handlers
│   └── workflow.py
├── services/           # Business logic
│   └── workflow_service.py
└── utils/              # Utility functions
    └── logger.py
```

### Running in Development Mode

```bash
python run.py
```

The server will automatically reload when code changes are detected.

## Production Deployment

For production deployment, consider using a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
``` 