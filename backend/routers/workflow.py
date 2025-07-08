from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from typing import Dict

from models.workflow import WorkflowRequest, WorkflowResponse, WorkflowStatusResponse, ErrorResponse
from services.workflow_service import WorkflowService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize workflow service
workflow_service = WorkflowService()

# Preflight handled by CORSMiddleware; explicit handler removed

@router.post("/workflow/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """
    Execute a workflow with the given query using the GUI agent
    """
    try:
        logger.info(f"Received workflow execution request: {request.query[:100]}...")
        
        # Validate the request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Start workflow execution in background
        workflow_id = await workflow_service.start_workflow(request, background_tasks)
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="running",
            message="Workflow execution started successfully",
            created_at=workflow_service.get_current_timestamp()
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start workflow execution")

@router.get("/workflow/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """
    Get the current status of a workflow
    """
    try:
        status = await workflow_service.get_workflow_status(workflow_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workflow status")

@router.delete("/workflow/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """
    Cancel a running workflow
    """
    try:
        success = await workflow_service.cancel_workflow(workflow_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or already completed")
        
        return {"message": "Workflow cancelled successfully", "workflow_id": workflow_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling workflow: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel workflow")

@router.get("/workflow/active")
async def get_active_workflows():
    """
    Get list of all active workflows
    """
    try:
        workflows = await workflow_service.get_active_workflows()
        return {"active_workflows": workflows}
        
    except Exception as e:
        logger.error(f"Error getting active workflows: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get active workflows") 