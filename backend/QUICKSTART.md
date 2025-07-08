# 🚀 Oasis OS Backend - Quick Start Guide

## Overview

This FastAPI backend integrates with your GUI Agent CLI (`cli_app.py`) to execute workflows via REST API. It automatically handles the model conversion from `gpt-4.1` to `gpt-4o` as requested.

## ⚡ One-Command Start

```bash
cd backend
python start.py
```

This will:
- Install all dependencies automatically
- Create necessary directories
- Start the server at `http://localhost:8000`

## 🔧 Manual Setup (Alternative)

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start server:**
   ```bash
   python run.py
   ```

## 📡 API Usage

### Execute Workflow
```bash
curl -X POST "http://localhost:8000/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Open calculator and compute 2+2", 
    "model": "gpt-4.1"
  }'
```

Response:
```json
{
  "workflow_id": "workflow_abc123456789",
  "status": "running",
  "message": "Workflow execution started successfully",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Check Status
```bash
curl "http://localhost:8000/api/v1/workflow/{workflow_id}/status"
```

## 🎯 Frontend Integration

For your Next.js frontend, use these endpoints:

```javascript
// Execute workflow
const response = await fetch('http://localhost:8000/api/v1/workflow/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: userQuery,
    model: 'gpt-4.1'  // Will auto-convert to gpt-4o
  })
});

const { workflow_id } = await response.json();

// Poll for status
const checkStatus = async () => {
  const statusRes = await fetch(`http://localhost:8000/api/v1/workflow/${workflow_id}/status`);
  const status = await statusRes.json();
  
  if (status.status === 'completed') {
    // Show success notification
    alert('Workflow executed successfully!');
  } else if (status.status === 'failed') {
    // Show error
    alert('Workflow failed: ' + status.message);
  } else {
    // Still running, check again
    setTimeout(checkStatus, 1000);
  }
};

checkStatus();
```

## 🛠 Key Features

- ✅ **Auto Model Conversion**: `gpt-4.1` → `gpt-4o`
- ✅ **Background Processing**: Non-blocking workflow execution
- ✅ **Real-time Status**: Monitor workflow progress
- ✅ **Error Handling**: Comprehensive error responses
- ✅ **CORS Enabled**: Works with frontend at `localhost:3000`
- ✅ **Logging**: Detailed logs in `logs/` directory

## 📊 Available Endpoints

- `POST /api/v1/workflow/execute` - Start workflow
- `GET /api/v1/workflow/{id}/status` - Check status  
- `DELETE /api/v1/workflow/{id}` - Cancel workflow
- `GET /api/v1/workflow/active` - List active workflows
- `GET /health` - Health check
- `GET /docs` - API documentation

## 🧪 Testing

```bash
python test_api.py
```

## 📁 Project Structure

```
backend/
├── main.py              # FastAPI app
├── start.py             # One-command startup
├── run.py               # Manual startup
├── test_api.py          # API tests
├── requirements.txt     # Dependencies
├── models/              # Pydantic models
├── routers/             # API routes
├── services/            # Business logic
└── utils/               # Utilities
```

## 🔄 Workflow Process

1. **Frontend** sends query to `/api/v1/workflow/execute`
2. **Backend** starts `cli_app.py` with specified model
3. **CLI Agent** executes the task using GUI automation
4. **Backend** monitors process and captures output
5. **Frontend** polls status until completion
6. **Success notification** shown to user

That's it! Your backend is ready to handle GUI agent workflows. 🎉 