import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
# Add memory management environment variables
os.environ['PYTHONMALLOC'] = 'malloc'
os.environ['MALLOC_ARENA_MAX'] = '1'

import json
import gc
import sys
from dotenv import load_dotenv
from pathlib import Path
from teach_mode import TeachModeRecorder
from workflow_builder import WorkflowBuilder
import time

# Load environment variables
load_dotenv()

def get_session_name():
    """Get session name from user with validation"""
    while True:
        name = input("\n📝 Enter a name for this task (e.g. 'WhatsApp_Expenses'): ").strip()
        if not name:
            print("⚠️ Please enter a name")
            continue
            
        # Clean name for filesystem safety
        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()
        return clean_name.replace(' ', '_')

def main():
    recorder = None
    try:
        # Get Groq API key
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Get session name from user
        session_name = get_session_name()
        session_path = os.path.join("teach_sessions", session_name)
        
        # Create session directory
        os.makedirs(session_path, exist_ok=True)
        
        # 1. Teach Mode
        print(f"\n🎯 Initializing recorder for: {session_name}")
        recorder = TeachModeRecorder(session_name)
        
        print("\n" + "="*50)
        print(f"Starting recording for: {session_name}")
        print("🔴 Recording tips:")
        print("- Perform actions deliberately")
        print("- Use keyboard shortcuts for copy/paste")
        print("- Speak commands clearly for voice actions")
        print("- Press Enter when finished...")
        print("="*50 + "\n")
        
        # Start recording
        recorder.start_recording()
        
        # Wait for user to press Enter
        input()
        
        # Stop recording with proper cleanup
        print("\n🛑 Stopping recording...")
        recorder.stop_recording()
        
        # Force cleanup of recorder resources
        recorder = None
        gc.collect()  # Force garbage collection
        
        # Add longer delay to ensure all threads are cleaned up
        print("⏳ Finalizing session data...")
        time.sleep(3)
        
        # 2. Verify Recording
        print(f"\n📁 Session saved to: {os.path.abspath(session_path)}")
        
        # Show session statistics
        json_path = os.path.join(session_path, "session.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                print(f"  🖱️ Mouse events: {len(data.get('mouse_events', []))}")
                print(f"  ⌨️ Key events: {len(data.get('key_events', []))}")
                print(f"  🎤 Voice commands: {len(data.get('voice_commands', []))}")
                print(f"  🖼️ Frames captured: {len(data.get('frames', []))}")
                
                # Clear data from memory
                data = None
                gc.collect()
                
            except Exception as e:
                print(f"⚠️ Error reading session data: {e}")
                return
        
        # 3. Build Workflow (in a separate process-like approach)
        print("\n🧠 Building workflow from session...")
        try:
            # Add delay before creating workflow builder
            time.sleep(1)
            
            # Create workflow builder with error handling
            builder = WorkflowBuilder(session_path, groq_api_key=groq_api_key)
            workflow = builder.build_workflow()
            
            if workflow and workflow.get('steps'):
                total_actions = workflow['metadata'].get('total_actions', 0)
                print(f"\n✅ Workflow built with {len(workflow['steps'])} steps and {total_actions} actions.")
                print(f"Execute anytime using: python run_workflow.py {session_name}")
            else:
                print("❌ Failed to build workflow. Check session data.")
                
        except Exception as e:
            print(f"❌ Error building workflow: {e}")
            import traceback
            traceback.print_exc()
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        if recorder:
            recorder.stop_recording()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        if recorder:
            try:
                recorder.stop_recording()
            except:
                pass
    finally:
        # Final cleanup
        if recorder:
            recorder = None
        gc.collect()
        print("\n🔄 Cleanup completed")

if __name__ == "__main__":
    main()