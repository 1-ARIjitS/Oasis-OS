import asyncio
import subprocess
import uuid
import time
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import BackgroundTasks
from pathlib import Path

from models.workflow import WorkflowRequest, WorkflowStatusResponse, WorkflowStatus

logger = logging.getLogger(__name__)

class WorkflowService:
    """Service for managing workflow execution using the GUI agent CLI"""
    
    def __init__(self):
        self.active_workflows: Dict[str, Dict] = {}
        self.completed_workflows: Dict[str, Dict] = {}
        
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"
    
    async def start_workflow(self, request: WorkflowRequest, background_tasks: BackgroundTasks) -> str:
        """Start a new workflow execution"""
        workflow_id = f"workflow_{uuid.uuid4().hex[:12]}"
        
        # Store workflow info
        workflow_info = {
            "id": workflow_id,
            "query": request.query,
            "model": request.model,
            "status": WorkflowStatus.PENDING,
            "created_at": self.get_current_timestamp(),
            "started_at": None,
            "completed_at": None,
            "process": None,
            "logs": "",
            "error": None
        }
        
        self.active_workflows[workflow_id] = workflow_info
        
        # Start execution in background
        background_tasks.add_task(self._execute_workflow, workflow_id)
        
        logger.info(f"Workflow {workflow_id} queued for execution")
        return workflow_id
    
    async def _execute_workflow(self, workflow_id: str):
        """Execute the workflow using the CLI app"""
        workflow_info = self.active_workflows.get(workflow_id)
        if not workflow_info:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        try:
            # Update status to running
            workflow_info["status"] = WorkflowStatus.RUNNING
            workflow_info["started_at"] = self.get_current_timestamp()
            
            logger.info(f"Starting workflow execution: {workflow_id}")
            
            # Prepare the command - handle gpt-4.1 to valid model mapping
            model = workflow_info["model"]
            if model == "gpt-4.1":
                # Map gpt-4.1 to a valid OpenAI model
                actual_model = "gpt-4o"
                logger.info(f"Converting gpt-4.1 to {actual_model} for workflow {workflow_id}")
            else:
                actual_model = model
                logger.info(f"Executing workflow {workflow_id} with model: {actual_model}")
            
            cmd = [
                sys.executable, "-m", "gui_agents.s1.cli_app",
                "--model", actual_model
            ]
            
            # Determine the workspace root directory (two levels up from backend/services)
            workspace_root = Path(__file__).resolve().parents[2]

            # Prepare environment so that `gui_agents` is importable regardless of CWD
            env = os.environ.copy()
            existing_pythonpath = env.get("PYTHONPATH", "")
            if str(workspace_root) not in existing_pythonpath.split(":"):
                env["PYTHONPATH"] = (
                    f"{existing_pythonpath}:{workspace_root}" if existing_pythonpath else str(workspace_root)
                )

            logger.debug(
                f"Launching CLI for workflow {workflow_id} with PYTHONPATH={env['PYTHONPATH']} and cwd={workspace_root}"
            )

            # Create the process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(workspace_root),
                env=env,
            )
            
            workflow_info["process"] = process
            
            # Send the query to the process
            query_input = f"{workflow_info['query']}\nn\n"  # Query + "n" to not continue
            
            # Write query and close stdin
            if process.stdin:
                process.stdin.write(query_input.encode())
                await process.stdin.drain()
                process.stdin.close()
            
            # Read output
            output_lines = []
            while True:
                try:
                    line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                    if not line:
                        break
                    
                    decoded_line = line.decode('utf-8', errors='replace').strip()
                    if decoded_line:
                        output_lines.append(decoded_line)
                        # Log at INFO level so it appears in server logs
                        logger.info(f"CLI [{workflow_id}]: {decoded_line}")
                        
                        # Check for completion indicators
                        if any(indicator in decoded_line.lower() for indicator in 
                               ["task completed", "workflow successfully executed", "done", "task finished"]):
                            logger.info(f"Workflow {workflow_id} completed successfully")
                            break
                            
                except asyncio.TimeoutError:
                    # Check if process is still running
                    if process.returncode is not None:
                        break
                    continue
                except Exception as e:
                    logger.error(f"Error reading process output: {e}")
                    break
            
            # Wait for process completion with extended timeout for complex tasks
            try:
                await asyncio.wait_for(process.wait(), timeout=300.0)  # 5 minutes timeout
            except asyncio.TimeoutError:
                logger.warning(f"Process timeout for workflow {workflow_id}, terminating...")
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.error(f"Force killing process for workflow {workflow_id}")
                    process.kill()
                    await process.wait()
            
            # Collect final output
            # Read any remaining output after process exit
            if process.stdout:
                try:
                    remaining = await process.stdout.read()
                    if remaining:
                        decoded_remaining = remaining.decode('utf-8', errors='replace')
                        output_lines.append(decoded_remaining)
                        logger.info(f"CLI [{workflow_id}] (remaining): {decoded_remaining}")
                except Exception as e:
                    logger.error(f"Error reading remaining output: {e}")

            workflow_info["logs"] = "\n".join(output_lines)
            
            # Determine final status
            if process.returncode == 0:
                workflow_info["status"] = WorkflowStatus.COMPLETED
                logger.info(f"Workflow {workflow_id} completed successfully")
            else:
                workflow_info["status"] = WorkflowStatus.FAILED
                workflow_info["error"] = f"Process exited with code {process.returncode}"
                logger.error(f"Workflow {workflow_id} failed with exit code {process.returncode}")
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
            workflow_info["status"] = WorkflowStatus.FAILED
            workflow_info["error"] = str(e)
        
        finally:
            # Clean up
            workflow_info["completed_at"] = self.get_current_timestamp()
            workflow_info["process"] = None
            
            # Move to completed workflows
            self.completed_workflows[workflow_id] = workflow_info
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatusResponse]:
        """Get the status of a workflow"""
        # Check active workflows first
        workflow_info = self.active_workflows.get(workflow_id)
        if not workflow_info:
            # Check completed workflows
            workflow_info = self.completed_workflows.get(workflow_id)
        
        if not workflow_info:
            return None
        
        # Calculate duration if available
        duration = None
        if workflow_info.get("started_at") and workflow_info.get("completed_at"):
            start_time = datetime.fromisoformat(workflow_info["started_at"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(workflow_info["completed_at"].replace("Z", "+00:00"))
            duration = (end_time - start_time).total_seconds()
        
        # Create status-specific messages
        if workflow_info["status"] == WorkflowStatus.COMPLETED:
            message = "Workflow successfully executed"
        elif workflow_info["status"] == WorkflowStatus.FAILED:
            message = workflow_info.get("error", "Workflow execution failed")
        elif workflow_info["status"] == WorkflowStatus.RUNNING:
            message = "AI agent is executing your task..."
        elif workflow_info["status"] == WorkflowStatus.PENDING:
            message = "Workflow queued for execution"
        elif workflow_info["status"] == WorkflowStatus.CANCELLED:
            message = "Workflow cancelled by user"
        else:
            message = "Workflow in progress"
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=workflow_info["status"],
            message=message,
            started_at=workflow_info.get("started_at"),
            completed_at=workflow_info.get("completed_at"),
            duration=duration,
            logs=workflow_info.get("logs", "")
        )
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        workflow_info = self.active_workflows.get(workflow_id)
        if not workflow_info:
            return False
        
        if workflow_info["status"] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            return False
        
        # Terminate the process if running
        if workflow_info.get("process"):
            try:
                workflow_info["process"].terminate()
                await workflow_info["process"].wait()
            except Exception as e:
                logger.error(f"Error terminating process for workflow {workflow_id}: {e}")
        
        # Update status
        workflow_info["status"] = WorkflowStatus.CANCELLED
        workflow_info["completed_at"] = self.get_current_timestamp()
        workflow_info["error"] = "Workflow cancelled by user"
        
        # Move to completed
        self.completed_workflows[workflow_id] = workflow_info
        del self.active_workflows[workflow_id]
        
        logger.info(f"Workflow {workflow_id} cancelled")
        return True
    
    async def get_active_workflows(self) -> List[Dict]:
        """Get list of active workflows"""
        return [
            {
                "workflow_id": workflow_id,
                "query": info["query"][:100] + "..." if len(info["query"]) > 100 else info["query"],
                "status": info["status"],
                "created_at": info["created_at"]
            }
            for workflow_id, info in self.active_workflows.items()
        ] 