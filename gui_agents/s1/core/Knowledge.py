import json
# mypy: ignore-errors  # The module relies on dynamic runtime types
# pyright: reportGeneralTypeIssues=false, reportUnknownMemberType=false
import os
from typing import Dict, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from gui_agents.s1.core.BaseModule import BaseModule
from gui_agents.s1.core.ProceduralMemory import PROCEDURAL_MEMORY
from gui_agents.s1.mllm.MultimodalEngine import OpenAIEmbeddingEngine
from gui_agents.s1.utils.common_utils import (
    load_embeddings,
    load_knowledge_base,
    save_embeddings,
)


class KnowledgeBase(BaseModule):
    def __init__(
        self,
        local_kb_path: str,
        platform: str,
        engine_params: Dict,
        use_image_for_search: bool = False,
    ):
        super().__init__(engine_params, platform)

        self.local_kb_path = local_kb_path

        # initialize embedding engine
        # TODO: Support other embedding engines
        self.embedding_engine = OpenAIEmbeddingEngine(
            api_key=(
                engine_params["api_key"]
                if "api_key" in engine_params
                else os.getenv("OPENAI_API_KEY")
            )
        )

        # Initialize paths for different memory types
        self.episodic_memory_path = os.path.join(
            self.local_kb_path, self.platform, "episodic_memory.json"
        )
        self.narrative_memory_path = os.path.join(
            self.local_kb_path, self.platform, "narrative_memory.json"
        )
        self.embeddings_path = os.path.join(
            self.local_kb_path, self.platform, "embeddings.pkl"
        )

        self.rag_module_system_prompt = PROCEDURAL_MEMORY.RAG_AGENT.replace(
            "CURRENT_OS", self.platform
        )

        # Simple RAG prompt for local knowledge only
        self.llm_search_agent = self._create_agent(self.rag_module_system_prompt)

        self.use_image_for_search = use_image_for_search

    def retrieve_narrative_experience(self, instruction: str) -> Tuple[str, str]:
        """Retrieve narrative experience using embeddings"""
        knowledge_base = load_knowledge_base(self.narrative_memory_path)
        if not knowledge_base:
            return "None", "None"

        embeddings = load_embeddings(self.embeddings_path)

        # Get or create instruction embedding
        instruction_embedding = embeddings.get(instruction)

        if instruction_embedding is None:
            instruction_embedding = self.embedding_engine.get_embeddings(instruction)
            embeddings[instruction] = instruction_embedding

        # Get or create embeddings for knowledge base entries
        candidate_embeddings = []
        for key in knowledge_base:
            candidate_embedding = embeddings.get(key)
            if candidate_embedding is None:
                candidate_embedding = self.embedding_engine.get_embeddings(key)
                embeddings[key] = candidate_embedding

            candidate_embeddings.append(candidate_embedding)

        save_embeddings(self.embeddings_path, embeddings)

        similarities = cosine_similarity(
            instruction_embedding, np.vstack(candidate_embeddings)
        )[0]
        sorted_indices = np.argsort(similarities)[::-1]

        keys = list(knowledge_base.keys())
        idx = 1 if keys[sorted_indices[0]] == instruction else 0
        return keys[sorted_indices[idx]], knowledge_base[keys[sorted_indices[idx]]]

    def retrieve_episodic_experience(self, instruction: str) -> Tuple[str, str]:
        """Retrieve similar task experience using embeddings"""
        knowledge_base = load_knowledge_base(self.episodic_memory_path)
        if not knowledge_base:
            return "None", "None"

        # --- NEW: merge manually-taught demonstrations --------------------
        manual_folder = os.path.join(self.local_kb_path, self.platform, "episodic_manual")
        if os.path.isdir(manual_folder):
            for fname in os.listdir(manual_folder):
                if not fname.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(manual_folder, fname), "r", encoding="utf-8") as f:
                        demo = json.load(f)
                    # Key by the original natural-language instruction
                    key = demo.get("instruction", "")
                    if key and key not in knowledge_base:
                        # Prefer the human-readable summary if provided, otherwise
                        # fall back to a simple serialisation of the raw events.
                        if "summary" in demo:
                            knowledge_base[key] = demo["summary"]
                        else:
                            events_txt = "\n".join([
                                e.get("type", "evt") + str(e.get("info", {})) for e in demo.get("events", [])
                            ])
                            knowledge_base[key] = events_txt
                except Exception:
                    continue

        embeddings = load_embeddings(self.embeddings_path)

        # Get or create instruction embedding
        instruction_embedding = embeddings.get(instruction)

        if instruction_embedding is None:
            instruction_embedding = self.embedding_engine.get_embeddings(instruction)
            embeddings[instruction] = instruction_embedding

        # Get or create embeddings for knowledge base entries
        candidate_embeddings = []
        for key in knowledge_base:
            candidate_embedding = embeddings.get(key)
            if candidate_embedding is None:
                candidate_embedding = self.embedding_engine.get_embeddings(key)
                embeddings[key] = candidate_embedding

            candidate_embeddings.append(candidate_embedding)

        save_embeddings(self.embeddings_path, embeddings)

        similarities = cosine_similarity(
            instruction_embedding, np.vstack(candidate_embeddings)
        )[0]
        sorted_indices = np.argsort(similarities)[::-1]

        keys = list(knowledge_base.keys())
        idx = 1 if keys[sorted_indices[0]] == instruction else 0
        return keys[sorted_indices[idx]], knowledge_base[keys[sorted_indices[idx]]]
