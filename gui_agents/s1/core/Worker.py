import logging
import os
import re
from typing import Dict, List, Tuple
import platform

from gui_agents.s1.aci.ACI import ACI
from gui_agents.s1.core.BaseModule import BaseModule
from gui_agents.s1.core.Knowledge import KnowledgeBase
from gui_agents.s1.core.ProceduralMemory import PROCEDURAL_MEMORY
from gui_agents.s1.utils import common_utils
from gui_agents.s1.utils.common_utils import Node, calculate_tokens, call_llm_safe
from gui_agents.s1.mllm.MultimodalEngine import LMMEngineGroq, LMMEngineOllama  # local import to avoid circular

logger = logging.getLogger("desktopenv.agent")


class Worker(BaseModule):
    def __init__(
        self,
        engine_params: Dict,
        grounding_agent: ACI,
        local_kb_path: str,
        platform: str = platform.system().lower(),
        enable_reflection: bool = True,
        use_subtask_experience: bool = True,
    ):
        """
        Worker receives a subtask list and active subtask and generates the next action for the to execute.
        Args:
            engine_params: Dict
                Parameters for the multimodal engine
            grounding_agent: Agent
                The grounding agent to use
            local_kb_path: str
                Path to knowledge base
            enable_reflection: bool
                Whether to enable reflection
            use_subtask_experience: bool
                Whether to use subtask experience
        """
        super().__init__(engine_params, platform)

        self.grounding_agent = grounding_agent
        self.local_kb_path = local_kb_path
        self.enable_reflection = enable_reflection
        self.use_subtask_experience = use_subtask_experience
        self.reset()

    def flush_messages(self):
        """Keep the last `max_trajectory_length` exchanges to control prompt length."""
        # generator messages alternate user/assistant, so there are 2 per turn after the system prompt
        if len(self.generator_agent.messages) > 2 * self.max_trajectory_length + 1:
            # always preserve system prompt at index 0
            self.generator_agent.remove_message_at(1)
            self.generator_agent.remove_message_at(1)

        # reflection agent messages are single user entries per turn after the system prompt
        if hasattr(self, "reflection_agent") and len(self.reflection_agent.messages) > self.max_trajectory_length + 1:
            self.reflection_agent.remove_message_at(1)

    def reset(self):
        self.generator_agent = self._create_agent(
            PROCEDURAL_MEMORY.construct_worker_procedural_memory(
                type(self.grounding_agent)
            ).replace("CURRENT_OS", self.platform)
        )
        self.reflection_agent = self._create_agent(
            PROCEDURAL_MEMORY.REFLECTION_ON_TRAJECTORY
        )

        self.knowledge_base = KnowledgeBase(
            local_kb_path=self.local_kb_path,
            platform=self.platform,
            engine_params=self.engine_params,
        )

        self.turn_count = 0
        self.planner_history = []
        self.reflections = []
        self.cost_this_turn = 0
        self.tree_inputs = []
        self.screenshot_inputs = []
        # Maximum (user,assistant) message pairs to keep in generator history
        self.max_trajectory_length = 8
        
        # Enhanced state tracking for better execution
        self.previous_actions = []  # Track recent actions to prevent repetition
        self.previous_states = []   # Track UI states to detect progress
        self.action_attempts = {}   # Track failed action attempts for retry logic
        self.stuck_detection_window = 3  # Number of actions to check for stuck patterns
        self.max_retry_attempts = 2  # Maximum retries for failed actions

    # TODO: Experimental
    def remove_ids_from_history(self):
        for message in self.generator_agent.messages:
            if isinstance(message, dict) and message.get("role") == "user":
                content_list = message.get("content", [])
                if isinstance(content_list, list):
                    for content in content_list:
                        if isinstance(content, dict) and content.get("type") == "text":
                            text_content = content.get("text", "")
                            if isinstance(text_content, str):
                                # Regex pattern to match lines that start with a number followed by spaces and remove the number
                                pattern = r"^\d+\s+"

                                # Apply the regex substitution on each line
                                processed_lines = [
                                    re.sub(pattern, "", line)
                                    for line in text_content.splitlines()
                                ]

                                # Join the processed lines back into a single string
                                result = "\n".join(processed_lines)

                                result = result.replace("id\t", "")

                                # replace message content
                                content["text"] = result

    def _detect_stuck_pattern(self, current_action: str) -> bool:
        """Detect if the agent is stuck in a repetitive pattern"""
        if len(self.previous_actions) < self.stuck_detection_window:
            return False
        
        # Check for exact repetition of actions
        recent_actions = self.previous_actions[-self.stuck_detection_window:]
        if all(action == current_action for action in recent_actions):
            logger.warning(f"Detected stuck pattern: repeating action '{current_action}'")
            return True
        
        # Check for alternating pattern (A-B-A-B)
        if len(recent_actions) >= 2:
            if recent_actions[-1] == current_action and recent_actions[-2] != current_action:
                alternating_count = 0
                for i in range(len(recent_actions) - 1, 0, -2):
                    if i < len(recent_actions) and recent_actions[i] == current_action:
                        alternating_count += 1
                    else:
                        break
                if alternating_count >= 2:
                    logger.warning(f"Detected alternating pattern with action '{current_action}'")
                    return True
        
        return False

    def _track_action_attempt(self, action: str, success: bool) -> bool:
        """Track action attempts and determine if retry should be attempted"""
        action_key = action.strip()
        
        if action_key not in self.action_attempts:
            self.action_attempts[action_key] = {'attempts': 0, 'last_success': None}
        
        self.action_attempts[action_key]['attempts'] += 1
        self.action_attempts[action_key]['last_success'] = success
        
        # Return True if we should retry, False if we've exceeded max attempts
        return self.action_attempts[action_key]['attempts'] <= self.max_retry_attempts

    def _generate_state_signature(self, obs: Dict) -> str:
        """Generate a signature of the current UI state for comparison"""
        tree_input = self.grounding_agent.linearize_and_annotate_tree(obs)
        # Create a simplified signature focusing on key elements
        lines = tree_input.split('\n')[1:]  # Skip header
        signature_elements = []
        
        for line in lines[:20]:  # Limit to first 20 elements for efficiency
            parts = line.split('\t')
            if len(parts) >= 3:
                # Include element type and name for signature
                element_type = parts[1] if len(parts) > 1 else ""
                element_name = parts[2] if len(parts) > 2 else ""
                if element_type and element_name:
                    signature_elements.append(f"{element_type}:{element_name}")
        
        return "|".join(signature_elements)

    def _check_progress_made(self, current_state: str) -> bool:
        """Check if progress has been made since the last few actions"""
        if len(self.previous_states) < 2:
            return True  # Assume progress if we don't have enough history
        
        # Check if current state is different from recent states
        recent_states = self.previous_states[-2:]
        return current_state not in recent_states

    def _suggest_alternative_action(self, stuck_action: str, obs: Dict) -> str:
        """Suggest an alternative action when stuck"""
        # Common alternative strategies
        alternatives = {
            "click": "Try using hotkeys like Enter, Tab, or Escape instead of clicking",
            "type": "Try using Ctrl+A to select all first, then type the text",
            "scroll": "Try using Page Up/Page Down or arrow keys instead of scrolling",
            "hotkey": "Try clicking on the element first to ensure focus, then use hotkey",
        }
        
        action_type = "unknown"
        for action_key in alternatives.keys():
            if action_key in stuck_action.lower():
                action_type = action_key
                break
        
        return alternatives.get(action_type, "Try a different approach or break the task into smaller steps")

    def _prepare_reflection_context(self, subtask: str, subtask_info: str) -> str:
        """Prepare enhanced context for reflection analysis"""
        context = (
            f"SUBTASK ANALYSIS:\n"
            f"Current Subtask: {subtask}\n"
            f"Subtask Instructions: {subtask_info}\n\n"
            f"EXECUTION TRAJECTORY:\n"
        )
        
        # Add recent action history with pattern detection
        if self.previous_actions:
            context += f"Recent Actions: {self.previous_actions[-5:]}\n"
            
            # Detect patterns in recent actions
            if len(self.previous_actions) >= 3:
                last_three = self.previous_actions[-3:]
                if len(set(last_three)) == 1:
                    context += f"PATTERN DETECTED: Repeating same action '{last_three[0]}'\n"
                elif len(set(last_three)) == 2 and last_three[0] == last_three[2]:
                    context += f"PATTERN DETECTED: Alternating actions between '{last_three[0]}' and '{last_three[1]}'\n"
        
        # Add planner history
        if self.planner_history:
            context += f"\nPlanning History:\n"
            context += "\n".join(self.planner_history[-3:])  # Last 3 plans
        
        # Add reflection history to avoid repetition
        if self.reflections:
            context += f"\nPrevious Reflections:\n"
            context += "\n".join(self.reflections[-2:])  # Last 2 reflections
            context += "\nNOTE: Avoid repeating previous reflection guidance.\n"
        
        return context

    def generate_next_action(
        self,
        instruction: str,
        subtask: str,
        subtask_info: str,
        future_tasks: List[Node],
        done_task: List[Node],
        obs: Dict,
    ) -> Tuple[Dict, List]:
        """
        Predict the next action(s) based on the current observation.
        """
        # Provide the top_app to the Grounding Agent to remove all other applications from the tree. At t=0, top_app is None
        agent = self.grounding_agent

        self.active_apps = agent.get_active_apps(obs)

        # Get RAG knowledge, only update system message at t=0
        if self.turn_count == 0:
            # TODO: uncomment and fix for subtask level RAG
            if self.use_subtask_experience:
                subtask_query_key = (
                    "Task:\n"
                    + instruction
                    + "\n\nSubtask: "
                    + subtask
                    + "\nSubtask Instruction: "
                    + subtask_info
                )
                retrieved_similar_subtask, retrieved_subtask_experience = (
                    self.knowledge_base.retrieve_episodic_experience(subtask_query_key)
                )
                logger.info(
                    "SIMILAR SUBTASK EXPERIENCE: %s",
                    retrieved_similar_subtask
                    + "\n"
                    + retrieved_subtask_experience.strip(),
                )
                instruction += "\nYou may refer to some similar subtask experience if you think they are useful. {}".format(
                    retrieved_similar_subtask + "\n" + retrieved_subtask_experience
                )

            self.generator_agent.add_system_prompt(
                self.generator_agent.system_prompt.replace(
                    "SUBTASK_DESCRIPTION", subtask
                )
                .replace("TASK_DESCRIPTION", instruction)
                .replace("FUTURE_TASKS", ", ".join([f.name for f in future_tasks]))
                .replace("DONE_TASKS", ",".join(d.name for d in done_task))
            )

        # Trim history to avoid context bloat
        self.flush_messages()

        # Enhanced reflection generation with pattern detection
        reflection = None
        if self.enable_reflection and self.turn_count > 0:
            # Prepare enhanced trajectory information for reflection
            trajectory_summary = self._prepare_reflection_context(subtask, subtask_info)
            
            self.reflection_agent.add_message(trajectory_summary)
            reflection = call_llm_safe(self.reflection_agent)
            
            # Convert reflection to string if it's a Dag object
            reflection_text = str(reflection) if reflection else ""
            
            # Only keep reflection if it provides actionable guidance
            if reflection_text and len(reflection_text.strip()) > 20:  # Filter out empty/minimal reflections
                self.reflections.append(reflection_text)
                self.reflection_agent.add_message(reflection_text)
                logger.info("ACTIONABLE REFLECTION: %s", reflection_text)
                reflection = reflection_text  # Use the string version
            else:
                reflection = None  # Clear non-actionable reflection

        # Plan Generation
        tree_input = agent.linearize_and_annotate_tree(obs)
        current_state = self._generate_state_signature(obs)
        
        # Check for progress and stuck patterns
        progress_made = self._check_progress_made(current_state)
        stuck_warning = ""
        
        if not progress_made and len(self.previous_actions) > 0:
            stuck_warning = f"\nWARNING: No progress detected in recent actions. Consider alternative approaches.\nLast actions: {self.previous_actions[-3:]}\nSuggestion: {self._suggest_alternative_action(self.previous_actions[-1] if self.previous_actions else '', obs)}\n"

        self.remove_ids_from_history()

        # Enhanced terminal message with progress tracking
        generator_message = (
            (
                f"\nReflection on previous trajectory: {reflection}\n"
                if reflection
                else ""
            )
            + stuck_warning
            + f"Accessibility Tree: {tree_input}\n"
            f"Text Buffer = [{','.join(agent.notes)}]. "
            f"The current open applications are {agent.get_active_apps(obs)} and the active app is {agent.get_top_app(obs)}.\n"
            f"Progress Status: {'Making progress' if progress_made else 'No recent progress - consider alternative approach'}\n"
        )

        print("ACTIVE APP IS: ", agent.get_top_app(obs))
        # Only provide subinfo in the very first message to avoid over influence and redundancy
        if self.turn_count == 0:
            generator_message += f"Remeber only complete the subtask: {subtask}\n"
            generator_message += f"You can use this extra information for completing the current subtask: {subtask_info}.\n"

        logger.info("GENERATOR MESSAGE: %s", generator_message)

        # Groq-hosted models currently allow max 5 images per request. Skip screenshots to avoid 400 errors.
        if isinstance(self.generator_agent.engine, LMMEngineGroq) or isinstance(self.generator_agent.engine, LMMEngineOllama):
            self.generator_agent.add_message(generator_message)
        else:
            self.generator_agent.add_message(generator_message, image_content=obs["screenshot"])

        plan = call_llm_safe(self.generator_agent)
        self.planner_history.append(plan)
        logger.info("PLAN: %s", plan)  # type: ignore[arg-type]

        self.generator_agent.add_message(plan)

        # Calculate input and output tokens
        input_tokens, output_tokens = calculate_tokens(self.generator_agent.messages)

        # Set Cost based on GPT-4o
        cost = input_tokens * (0.0050 / 1000) + output_tokens * (0.0150 / 1000)
        self.cost_this_turn += cost
        logger.info("EXECTUOR COST: %s", self.cost_this_turn)  # type: ignore[arg-type]

        # Ensure we are working with text. If the LLM returned a Dag object, convert it to string.
        plan_text = str(plan) if not isinstance(plan, str) else plan

        plan_code_raw = common_utils.parse_single_code_from_string(
            plan_text.split("Grounded Action")[-1]
        )
        plan_code_raw = common_utils.sanitize_code(plan_code_raw)
        plan_code = common_utils.extract_first_agent_function(plan_code_raw)

        # If extraction failed, default to a brief wait to allow the next planning round.
        if not plan_code:
            plan_code = "agent.wait(1.0)"

        try:
            exec_code = eval(plan_code)
        except Exception:
            # Any unexpected error during eval should not crash the loop. Fall back to WAIT.
            plan_code = "agent.wait(1.0)"
            exec_code = eval(plan_code)

        # If agent selects an element that was out of range, it should not be executed just send a WAIT command.
        # TODO: should provide this as code feedback to the agent?
        if agent.index_out_of_range_flag:
            plan_code = "agent.wait(1.0)"
            exec_code = eval(plan_code)
            agent.index_out_of_range_flag = False

        executor_info = {
            "current_subtask": subtask,
            "current_subtask_info": subtask_info,
            "executor_plan": plan,
            "linearized_accessibility_tree": tree_input,
            "plan_code": plan_code,
            "reflection": reflection,
            "num_input_tokens_executor": input_tokens,
            "num_output_tokens_executor": output_tokens,
            "executor_cost": cost,
        }
        self.turn_count += 1

        self.tree_inputs.append(tree_input)
        self.screenshot_inputs.append(obs["screenshot"])
        
        # Update state tracking for next iteration
        self.previous_states.append(current_state)
        self.previous_actions.append(plan_code)
        
        # Keep only recent history to prevent memory bloat
        if len(self.previous_states) > 10:
            self.previous_states = self.previous_states[-10:]
        if len(self.previous_actions) > 10:
            self.previous_actions = self.previous_actions[-10:]

        return executor_info, [exec_code]
