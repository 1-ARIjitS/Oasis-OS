from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowRequest(BaseModel):
    """Request model for workflow execution"""
    query: str = Field(..., min_length=1, max_length=2000, description="Task description for the AI agent")
    model: str = Field(default="gpt-4.1", description="AI model to use for execution")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Open a web browser and search for 'Python tutorials'",
                "model": "gpt-4o-mini"
            }
        }

class WorkflowResponse(BaseModel):
    """Response model for workflow execution"""
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    status: WorkflowStatus = Field(..., description="Current workflow status")
    message: str = Field(..., description="Status message")
    created_at: str = Field(..., description="Workflow creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "workflow_123456789",
                "status": "running",
                "message": "Workflow execution started successfully",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status check"""
    workflow_id: str = Field(..., description="Workflow identifier")
    status: WorkflowStatus = Field(..., description="Current workflow status")
    message: str = Field(..., description="Status message or error details")
    started_at: Optional[str] = Field(None, description="Workflow start timestamp")
    completed_at: Optional[str] = Field(None, description="Workflow completion timestamp")
    duration: Optional[float] = Field(None, description="Execution duration in seconds")
    logs: Optional[str] = Field(None, description="Execution logs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "workflow_123456789",
                "status": "completed",
                "message": "Workflow executed successfully",
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:32:30Z",
                "duration": 150.5,
                "logs": "Task completed successfully..."
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field(default="error", description="Response status")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details") 