import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import platform

from gui_agents.s1.aci.ACI import ACI
from gui_agents.s1.core.BaseModule import BaseModule
from gui_agents.s1.core.Knowledge import KnowledgeBase
from gui_agents.s1.core.ProceduralMemory import PROCEDURAL_MEMORY
from gui_agents.s1.utils.common_utils import (
    Dag,
    Node,
    calculate_tokens,
    call_llm_safe,
    parse_dag,
)
from gui_agents.s1.mllm.MultimodalEngine import LMMEngineGroq, LMMEngineOllama

logger = logging.getLogger("desktopenv.agent")

NUM_IMAGE_TOKEN = 1105  # Value set of screen of size 1920x1080 for openai vision


class Manager(BaseModule):
    def __init__(
        self,
        engine_params: Dict,
        grounding_agent: ACI,
        local_kb_path: str,
        multi_round: bool = False,
        platform: str = platform.system().lower(),
    ):
        # TODO: move the prompt to Procedural Memory
        super().__init__(engine_params, platform)

        # Initialize the ACI
        self.grounding_agent = grounding_agent

        # Initialize the submodules of the Manager
        self.generator_agent = self._create_agent(PROCEDURAL_MEMORY.MANAGER_PROMPT)
        self.dag_translator_agent = self._create_agent(
            PROCEDURAL_MEMORY.DAG_TRANSLATOR_PROMPT
        )
        self.narrative_summarization_agent = self._create_agent(
            PROCEDURAL_MEMORY.TASK_SUMMARIZATION_PROMPT
        )
        self.episode_summarization_agent = self._create_agent(
            PROCEDURAL_MEMORY.SUBTASK_SUMMARIZATION_PROMPT
        )

        self.local_kb_path = local_kb_path

        self.knowledge_base = KnowledgeBase(self.local_kb_path, platform, engine_params)

        self.planner_history = []

        self.turn_count = 0
        self.multi_round = multi_round
        self.platform = platform
        
        # Enhanced planning state tracking
        self.plan_attempts = 0
        self.max_plan_attempts = 3
        self.previous_failed_plans = []
        self.successful_subtasks = []
        self.failed_subtasks = []

    def summarize_episode(self, trajectory):
        """Summarize the episode experience for lifelong learning reflection
        Args:
            trajectory: str: The episode experience to be summarized
        """

        # Create Reflection on whole trajectories for next round trial, keep earlier messages as exemplars
        self.episode_summarization_agent.add_message(trajectory)
        subtask_summarization = call_llm_safe(self.episode_summarization_agent)
        self.episode_summarization_agent.add_message(subtask_summarization)

        return subtask_summarization

    def summarize_narrative(self, trajectory):
        """Summarize the narrative experience for lifelong learning reflection
        Args:
            trajectory: str: The narrative experience to be summarized
        """
        # Create Reflection on whole trajectories for next round trial
        self.narrative_summarization_agent.add_message(trajectory)
        lifelong_learning_reflection = call_llm_safe(self.narrative_summarization_agent)

        return lifelong_learning_reflection

    def _analyze_planning_failure(self, failure_feedback: str, instruction: str) -> str:
        """Analyze why planning failed and generate better guidance for replanning"""
        self.plan_attempts += 1
        
        failure_analysis = {
            "attempt": self.plan_attempts,
            "feedback": failure_feedback,
            "failed_subtasks": self.failed_subtasks.copy(),
            "successful_subtasks": self.successful_subtasks.copy()
        }
        self.previous_failed_plans.append(failure_analysis)
        
        # Generate enhanced failure feedback for better replanning
        enhanced_feedback = failure_feedback
        
        if self.plan_attempts > 1:
            enhanced_feedback += f"\n\nPREVIOUS PLANNING FAILURES:\n"
            for i, failure in enumerate(self.previous_failed_plans[-2:], 1):  # Last 2 failures
                enhanced_feedback += f"Attempt {failure['attempt']}: {failure['feedback']}\n"
            
            enhanced_feedback += f"\nSUCCESSFUL SUBTASKS (don't repeat): {self.successful_subtasks}\n"
            enhanced_feedback += f"FAILED SUBTASKS (need alternative approach): {self.failed_subtasks}\n"
            
            # Add specific guidance based on failure patterns
            if self.plan_attempts >= 2:
                enhanced_feedback += f"\nREPLANNING GUIDANCE:\n"
                enhanced_feedback += f"- Break down complex tasks into smaller, more atomic steps\n"
                enhanced_feedback += f"- Prioritize keyboard shortcuts over mouse interactions\n"
                enhanced_feedback += f"- Ensure each step has clear success criteria\n"
                enhanced_feedback += f"- Consider alternative approaches for previously failed subtasks\n"
                
            if self.plan_attempts >= self.max_plan_attempts:
                enhanced_feedback += f"\nFINAL ATTEMPT: This is the last replanning attempt. Create the simplest possible plan that directly achieves the goal.\n"
        
        return enhanced_feedback

    def _update_subtask_tracking(self, subtask: str, success: bool):
        """Track successful and failed subtasks"""
        if success:
            if subtask not in self.successful_subtasks:
                self.successful_subtasks.append(subtask)
            # Remove from failed list if it was there
            if subtask in self.failed_subtasks:
                self.failed_subtasks.remove(subtask)
        else:
            if subtask not in self.failed_subtasks:
                self.failed_subtasks.append(subtask)

    def _generate_step_by_step_plan(
        self, observation: Dict, instruction: str, failure_feedback: str = ""
    ) -> Tuple[Dict, str]:
        agent = self.grounding_agent

        self.active_apps = agent.get_active_apps(observation)

        tree_input = agent.linearize_and_annotate_tree(observation)
        observation["linearized_accessibility_tree"] = tree_input

        # Analyze failure feedback for better replanning
        if failure_feedback and failure_feedback.strip():
            failure_feedback = self._analyze_planning_failure(failure_feedback, instruction)
            logger.info(f"Enhanced failure feedback for replanning: {failure_feedback}")

        # Perform Retrieval only at the first planning step or when replanning with failures
        if self.turn_count == 0 or failure_feedback:
            retrieved_experience = ""
            # Retrieve most similar narrative (task) experience
            most_similar_task, retrieved_experience = (
                self.knowledge_base.retrieve_narrative_experience(instruction)
            )
            logger.info(
                "SIMILAR TASK EXPERIENCE: %s",
                most_similar_task + "\n" + retrieved_experience.strip(),
            )

            # Add the retrieved experience to the task instruction in the system prompt
            if retrieved_experience and retrieved_experience.strip() and retrieved_experience != "None":
                instruction += f"\nYou may refer to some retrieved experience if you think it is useful: {retrieved_experience}"

            self.generator_agent.add_system_prompt(
                self.generator_agent.system_prompt.replace(
                    "TASK_DESCRIPTION", instruction
                )
            )

        generator_message = (
            f"Accessibility Tree: {tree_input}\n"
            f"The clipboard contains: {agent.clipboard}."
            f"The current open applications are {agent.get_active_apps(observation)}"
            + (
                f" Previous plan failed at step: {failure_feedback}"
                if failure_feedback
                else ""
            )
        )

        if isinstance(self.generator_agent.engine, LMMEngineGroq) or isinstance(self.generator_agent.engine, LMMEngineOllama):
            self.generator_agent.add_message(generator_message)
        else:
            self.generator_agent.add_message(
                generator_message, image_content=observation.get("screenshot", None)
            )

        logger.info("GENERATING HIGH LEVEL PLAN")

        plan = call_llm_safe(self.generator_agent)

        if plan == "":
            error_msg = (
                "Plan generation failed. This could be due to:\n"
                "1. Invalid or missing API key\n"
                "2. Model is overloaded or unavailable\n"
                "3. Input too long or malformed\n"
                "4. Network connectivity issues\n"
                "Please check your configuration and try again."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info("HIGH LEVEL STEP BY STEP PLAN: %s", plan)

        self.generator_agent.add_message(plan)

        self.planner_history.append(plan)

        self.turn_count += 1

        input_tokens, output_tokens = calculate_tokens(self.generator_agent.messages)

        # Set Cost based on GPT-4o
        cost = input_tokens * (0.0050 / 1000) + output_tokens * (0.0150 / 1000)

        planner_info = {
            "goal_plan": plan,
            "num_input_tokens_plan": input_tokens,
            "num_output_tokens_plan": output_tokens,
            "goal_plan_cost": cost,
        }

        assert type(plan) == str

        return planner_info, plan

    def _generate_dag(self, instruction: str, plan: str) -> Tuple[Dict, Dag]:
        # Add initial instruction and plan to the agent's message history
        self.dag_translator_agent.add_message(
            f"Instruction: {instruction}\nPlan: {plan}"
        )

        logger.info("GENERATING DAG")

        # Generate DAG
        dag_raw = call_llm_safe(self.dag_translator_agent)

        dag = parse_dag(dag_raw)

        # Fallback: if parsing failed, build a linear DAG from plan steps
        if not isinstance(dag, Dag):
            logger.warning("Failed to parse DAG; falling back to linear plan execution.")
            steps = [s.strip() for s in plan.split("\n") if s.strip()]
            nodes = [Node(name=f"step_{i+1}", info=step) for i, step in enumerate(steps)]
            edges = [[nodes[i], nodes[i + 1]] for i in range(len(nodes) - 1)] if len(nodes) > 1 else []
            dag = Dag(nodes=nodes, edges=edges)

        logger.info("Generated DAG: %s", dag_raw)

        self.dag_translator_agent.add_message(dag_raw)

        input_tokens, output_tokens = calculate_tokens(
            self.dag_translator_agent.messages
        )

        cost = input_tokens * (0.0050 / 1000) + output_tokens * (0.0150 / 1000)

        dag_info = {
            "dag": dag_raw,
            "num_input_tokens_dag": input_tokens,
            "num_output_tokens_dag": output_tokens,
            "dag_cost": cost,
        }

        return dag_info, dag

    def _topological_sort(self, dag: Dag) -> List[Node]:
        """Topological sort of the DAG using DFS
        dag: Dag: Object representation of the DAG with nodes and edges
        """

        def dfs(node_name, visited, stack):
            visited[node_name] = True
            for neighbor in adj_list[node_name]:
                if not visited[neighbor]:
                    dfs(neighbor, visited, stack)
            stack.append(node_name)

        # Convert edges to adjacency list
        adj_list = defaultdict(list)
        for u, v in dag.edges:
            adj_list[u.name].append(v.name)

        visited = {node.name: False for node in dag.nodes}
        stack = []

        for node in dag.nodes:
            if not visited[node.name]:
                dfs(node.name, visited, stack)

        # Return the nodes in topologically sorted order
        sorted_nodes = [
            next(n for n in dag.nodes if n.name == name) for name in stack[::-1]
        ]
        return sorted_nodes

    def get_action_queue(
        self,
        instruction: str,
        observation: Dict,
        failure_feedback: Optional[str] = None,
    ):
        """Generate the action list based on the instruction
        instruction:str: Instruction for the task
        """
        # Generate the high level plan
        planner_info, plan = self._generate_step_by_step_plan(
            observation, instruction, failure_feedback or ""
        )

        # Generate the DAG
        dag_info, dag = self._generate_dag(instruction, plan)

        # Topological sort of the DAG
        action_queue = self._topological_sort(dag)

        planner_info.update(dag_info)

        return planner_info, action_queue
