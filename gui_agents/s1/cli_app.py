import argparse
import datetime
import io
import logging
import os
import platform
import sys
import time

import pyautogui

from gui_agents.s1.core.AgentS import GraphSearchAgent, UIAgent
from gui_agents.s1.utils.teach_mode import EventRecorder, save_demonstration

current_platform = platform.system().lower()

if current_platform == "darwin":
    from gui_agents.s1.aci.MacOSACI import MacOSACI, UIElement
elif current_platform == "linux":
    from gui_agents.s1.aci.LinuxOSACI import LinuxACI, UIElement
elif current_platform == "windows":
    from gui_agents.s1.aci.WindowsOSACI import WindowsACI, UIElement
else:
    raise ValueError(f"Unsupported platform: {current_platform}")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

datetime_str: str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

file_handler = logging.FileHandler(
    os.path.join("logs", "normal-{:}.log".format(datetime_str)), encoding="utf-8"
)
debug_handler = logging.FileHandler(
    os.path.join("logs", "debug-{:}.log".format(datetime_str)), encoding="utf-8"
)
stdout_handler = logging.StreamHandler(sys.stdout)
sdebug_handler = logging.FileHandler(
    os.path.join("logs", "sdebug-{:}.log".format(datetime_str)), encoding="utf-8"
)

file_handler.setLevel(logging.INFO)
debug_handler.setLevel(logging.DEBUG)
stdout_handler.setLevel(logging.INFO)
sdebug_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    fmt="\x1b[1;33m[%(asctime)s \x1b[31m%(levelname)s \x1b[32m%(module)s/%(lineno)d-%(processName)s\x1b[1;33m] \x1b[0m%(message)s"
)
file_handler.setFormatter(formatter)
debug_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)
sdebug_handler.setFormatter(formatter)

stdout_handler.addFilter(logging.Filter("desktopenv"))
sdebug_handler.addFilter(logging.Filter("desktopenv"))

logger.addHandler(file_handler)
logger.addHandler(debug_handler)
logger.addHandler(stdout_handler)
logger.addHandler(sdebug_handler)

platform_os = platform.system()


def show_permission_dialog(code: str, action_description: str):
    """Show a platform-specific permission dialog and return True if approved."""
    if platform.system() == "Darwin":
        result = os.system(
            f'osascript -e \'display dialog "Do you want to execute this action?\n\n{code} which will try to {action_description}" with title "Action Permission" buttons {{"Cancel", "OK"}} default button "OK" cancel button "Cancel"\''
        )
        return result == 0
    elif platform.system() == "Linux":
        result = os.system(
            f'zenity --question --title="Action Permission" --text="Do you want to execute this action?\n\n{code}" --width=400 --height=200'
        )
        return result == 0
    return False


def run_agent(agent: UIAgent, instruction: str):
    obs = {}
    traj = "Task:\n" + instruction
    subtask_traj = ""
    for _ in range(15):
        obs["accessibility_tree"] = UIElement.systemWideElement()  # type: ignore[attr-defined]

        # Get screen shot using pyautogui.
        # Take a screenshot
        screenshot = pyautogui.screenshot()

        # Save the screenshot to a BytesIO object
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")

        # Get the byte value of the screenshot
        screenshot_bytes = buffered.getvalue()
        # Convert to base64 string.
        obs["screenshot"] = screenshot_bytes

        # Get next action code from the agent
        try:
            info, code = agent.predict(instruction=instruction, observation=obs)
        except Exception as e:
            print(f"ERROR GETTING PREDICTION FROM AGENT: {e}")
            print("The agent encountered an error during planning. Retrying...")
            time.sleep(2.0)
            continue

        # Validate that we have valid code
        if not code or len(code) == 0:
            print("ERROR: Agent returned empty code. Retrying...")
            time.sleep(2.0)
            continue

        if "done" in code[0].lower() or "fail" in code[0].lower():
            if platform.system() == "Darwin":
                os.system(
                    f'osascript -e \'display dialog "Task Completed" with title "OpenACI Agent" buttons "OK" default button "OK"\''
                )
            elif platform.system() == "Linux":
                os.system(
                    f'zenity --info --title="OpenACI Agent" --text="Task Completed" --width=200 --height=100'
                )

            agent.update_narrative_memory(traj)
            break

        if "next" in code[0].lower():
            continue

        if "wait" in code[0].lower():
            time.sleep(5)
            continue

        else:
            time.sleep(1.0)
            print("EXECUTING CODE:", code[0])

            try:
                # Ask for permission before executing
                exec(code[0])
                time.sleep(1.0)
            except Exception as e:
                print(f"ERROR EXECUTING CODE: {e}")
                print(f"CODE THAT FAILED: {code[0]}")
                print("The agent will continue with the next action...")
                time.sleep(2.0)

            # Update task and subtask trajectories and optionally the episodic memory
            traj += (
                "\n\nReflection:\n"
                + str(info["reflection"])
                + "\n\n----------------------\n\nPlan:\n"
                + info["executor_plan"]
            )
            subtask_traj = agent.update_episodic_memory(info, subtask_traj)


def main():
    parser = argparse.ArgumentParser(
        description="Run GraphSearchAgent with specified model."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="Specify the model to use (e.g., gpt-4o)",
    )
    parser.add_argument(
        "--teach",
        action="store_true",
        help="Enable teaching mode: record a manual demonstration instead of running the agent.",
    )
    parser.add_argument(
        "--engine-type",
        type=str,
        choices=["openai", "anthropic", "groq", "azure", "vllm", "ollama"],
        default=None,
        help="Explicitly specify the LLM engine type (overrides automatic detection).",
    )
    args = parser.parse_args()

    if current_platform == "darwin":
        grounding_agent = MacOSACI()
    elif current_platform == "windows":
        grounding_agent = WindowsACI()
    elif current_platform == "linux":
        grounding_agent = LinuxACI()
    else:
        raise ValueError(f"Unsupported platform: {current_platform}")

    while True:
        query = input("Query: ")

        # Determine engine type
        if args.engine_type is not None:
            engine_type = args.engine_type
        else:
            model_lower = args.model.lower()
            if "gpt" in model_lower:
                engine_type = "openai"
            elif "claude" in model_lower:
                engine_type = "anthropic"
            # Heuristics: Prefer Groq only when API key is configured, otherwise default to local (vLLM/Ollama)
            elif any(k in model_lower for k in ["llama", "deepseek", "maverick", "scout"]):
                engine_type = "groq" if os.getenv("GROQ_API_KEY") else "ollama"
            else:
                # Default to ollama for local models
                engine_type = "ollama"

        engine_params = {
            "engine_type": engine_type,
            "model": args.model,
        }

        agent = GraphSearchAgent(
            engine_params,
            grounding_agent,
            platform=current_platform,
            action_space="pyautogui",
            observation_type="mixed",
        )

        agent.reset()

        if args.teach:
            print("Teaching mode active — press Enter to start recording, then perform the task manually. Press Enter again when done.")
            input()
            rec = EventRecorder()
            rec.start()
            input("Recording… press Enter to stop.")
            events = rec.stop()
            demo_path = save_demonstration(query, events, os.path.join(os.getcwd(), "kb_s1"), current_platform)
            print(f"Demonstration saved to {demo_path}")
            response = input("Teach another? (y/n): ")
            if response.lower() != "y":
                break
            else:
                continue

        # Run the agent on your own device
        run_agent(agent, query)

        response = input("Would you like to provide another query? (y/n): ")
        if response.lower() != "y":
            break


if __name__ == "__main__":
    main()

def setup_logging():
    """Setup logging configuration with proper error handling"""
    try:
        # Ensure logs directory exists
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
            
        datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Setup main logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # Console handler for normal output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handlers with error handling
        try:
            debug_handler = logging.FileHandler(
                os.path.join(logs_dir, f"debug-{datetime_str}.log"), 
                encoding="utf-8",
                mode='w'
            )
            debug_handler.setLevel(logging.DEBUG)
        except (OSError, IOError) as e:
            print(f"Warning: Could not create debug log file: {e}")
            debug_handler = None
            
        try:
            sdebug_handler = logging.FileHandler(
                os.path.join(logs_dir, f"sdebug-{datetime_str}.log"), 
                encoding="utf-8",
                mode='w'
            )
            sdebug_handler.setLevel(logging.DEBUG)
            sdebug_handler.addFilter(logging.Filter("desktopenv"))
        except (OSError, IOError) as e:
            print(f"Warning: Could not create sdebug log file: {e}")
            sdebug_handler = None
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Add formatter to handlers
        console_handler.setFormatter(formatter)
        if debug_handler:
            debug_handler.setFormatter(formatter)
        if sdebug_handler:
            sdebug_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        if debug_handler:
            logger.addHandler(debug_handler)
        if sdebug_handler:
            logger.addHandler(sdebug_handler)
            
        print(f"Logging initialized. Log files will be saved to: {logs_dir}/")
        return logger
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Fallback to basic console logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger()