import os
import sys
import json
from pathlib import Path
from .executor import WorkflowExecutor
from dotenv import load_dotenv
import time

load_dotenv()
def launch_required_apps(session_name):
    """Open applications required for this workflow"""
    app_map = {
        "whatsapp": ["WhatsApp.exe", "WhatsApp"],
        "excel": ["EXCEL.EXE", "Microsoft Excel"],
        "chrome": ["chrome.exe", "Google Chrome"]
    }
    # Get workflow-specific requirements (simplified example)
    if "whatsapp" in session_name.lower():
        apps = ["whatsapp", "chrome"]
    elif "excel" in session_name.lower():
        apps = ["excel"]
    else:
        apps = ["chrome"]
    
    print("\n🚀 Launching required applications:")
    for app in apps:
        try:
            os.startfile(app_map[app][0])  # Windows
            print(f"  - {app_map[app][1]}")
            time.sleep(2)  # Allow app to launch
        except:
            print(f"⚠️ Could not launch {app_map[app][1]}")

def run_workflow(session_name):
    session_path = Path(__file__).resolve().parent / "teach_sessions" / session_name
    print(session_path)
    workflow_file = session_path / "workflow.json"
    
    if not workflow_file.exists():
        print(f"❌ Workflow not found for session: {session_name}")
        return
    
    print(f"\n Executing workflow: {session_name}")
    
    # Verify workflow has steps
    with workflow_file.open('r') as f:
        workflow_data = json.load(f)
    
    if not workflow_data.get('steps'):
        print("⚠️ No executable steps found in workflow")
        print("Possible reasons:")
        print("- No actions were recorded during teaching")
        print("- Voice commands weren't recognized")
        print("- Workflow building failed")
        return
    
    print(f"Found {len(workflow_data['steps'])} steps with " +
          f"{workflow_data['metadata'].get('total_actions', 0)} total actions")
    
    # Execute workflow
    executor = WorkflowExecutor(str(workflow_file))
    executor.execute()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        session_name = sys.argv[1]
    else:
        session_name = input("Enter session name to execute: ")
    
    run_workflow(session_name)