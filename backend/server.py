from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os
import gc
import re
import uvicorn
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Local imports – these reside inside backend/teach_mode
from teach_mode.teach_mode import TeachModeRecorder
from teach_mode.workflow_builder import WorkflowBuilder
from teach_mode.run_workflow import run_workflow as execute_workflow

# Load environment variables early so downstream modules can access them
load_dotenv()

app = FastAPI(title="Oasis Teach-Mode API")

# Enable CORS for frontend access (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Internal state management
# ---------------------------

current_recorder: Optional[TeachModeRecorder] = None
current_session_name: Optional[str] = None

# Helper to make filesystem-safe session names
def _clean_session_name(name: str) -> str:
    """Return a filesystem-safe version of *name* (keep alnum & underscore)."""
    name = name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    return cleaned or "session"

# ------------------------------------------------
#                     Endpoints
# ------------------------------------------------

@app.post("/start_recording/{session_name}")
def start_recording(session_name: str):
    """Begin a teach-mode recording session."""
    global current_recorder, current_session_name

    if current_recorder is not None:
        raise HTTPException(status_code=400, detail="A recording session is already in progress. Call /stop_recording first.")

    clean_name = _clean_session_name(session_name)
    try:
        current_recorder = TeachModeRecorder(clean_name)
        current_recorder.start_recording()
        current_session_name = clean_name
        return JSONResponse({"status": "recording_started", "session_name": clean_name})
    except Exception as e:
        current_recorder = None
        current_session_name = None
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {e}")


@app.post("/stop_recording")
def stop_recording():
    """Stop the active recording session and build its workflow."""
    global current_recorder, current_session_name

    if current_recorder is None or current_session_name is None:
        raise HTTPException(status_code=400, detail="No active recording session to stop.")

    try:
        # 1. Stop the recorder
        current_recorder.stop_recording()
        # Explicitly clean up the recorder object to free resources
        current_recorder = None
        gc.collect()

        # 2. Build the workflow for this session
        groq_api_key = os.getenv("GROQ_API_KEY")
        builder = WorkflowBuilder(current_session_name, groq_api_key=groq_api_key)
        workflow = builder.build_workflow()

        # Extract some basic stats
        steps = len(workflow.get("steps", [])) if workflow else 0
        actions = workflow.get("metadata", {}).get("total_actions", 0) if workflow else 0

        # Reset session name after workflow is built
        finished_session = current_session_name
        current_session_name = None

        return JSONResponse({
            "status": "recording_stopped",
            "workflow_built": bool(workflow),
            "steps": steps,
            "actions": actions,
            "session_name": finished_session
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop recording/build workflow: {e}")


@app.post("/run_workflow/{session_name}")
def run_workflow_endpoint(session_name: str):
    """Execute a previously recorded workflow."""
    try:
        execute_workflow(session_name)
        return JSONResponse({"status": "workflow_executed", "session_name": session_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {e}")


# ---------------------------
# Uvicorn entry-point
# ---------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
