import os
import datetime
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from google.cloud import firestore
from langchain_google_vertexai import ChatVertexAI
from crewai import Agent, Task, Crew, Process

from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.schemas.agent_registry import AgentRegistryEntry
from app.shared_crew_lib.schemas.firestore_task import TokenUsage, TaskLogEntry
from app.shared_crew_lib.schemas.agent_output import AgentResponse

logger = logging.getLogger(__name__)


class BaseAgentWrapper(ABC):
    """
    Enhanced base class for agents, integrating core functionalities like RAG, token monitoring, and task guardrails.
    All agents should inherit from this class.
    """

    # Static guardrails: Universal rules that all agents inheriting this base class must follow
    BASE_GUARDRAILS = [
        "You must never answer questions outside the scope of your core capabilities.",
        "If you do not know the answer, or if the question is unrelated to your duties, you must explicitly respond with 'I don't know' or 'This question is beyond my scope to answer'.",
        "Providing any form of illegal, unethical, or dangerous advice is strictly prohibited.",
        "Never invent non-existent information or data in your responses.",
        "CRITICAL JSON FORMAT RULE: You MUST respond with ONLY a valid JSON structure - NO additional text, explanations, or commentary before or after the JSON.",
        "Your response must start with { and end with } - nothing else!",
        "Do NOT include phrases like 'Final Answer:', 'Here is the response:', or any other text outside the JSON structure.",
    ]

    def __init__(self, agent_id: str, task_id: str = None):
        self.agent_id = agent_id
        self.task_id = task_id
        self._current_task_id = None

        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError("GCP_PROJECT_ID environment variable not set.")

        self.llm = self.get_llm(project_id)
        self.db = gcp_clients.get_firestore_client()

        self.peer_agents = {}
        self.task_ref = None
        self.agent_registry_entry: Optional[AgentRegistryEntry] = None
        self.agent = None

        self.initialize(task_id)
        logger.info(f"Initializing agent: {agent_id}")

    def _load_registry_entry(self) -> Optional[AgentRegistryEntry]:
        """Load this agent's registration information from Firestore"""
        try:
            doc_ref = self.db.collection("agents").document(self.agent_id)
            doc = doc_ref.get()
            if doc.exists:
                return AgentRegistryEntry(**doc.to_dict())
            else:
                logger.warning(f"Agent '{self.agent_id}' not found in registry. This may be expected during system initialization.")
                return None
        except Exception as e:
            logger.error(f"Failed to load agent registry entry: {e}")
            return None

    def _assemble_prompt_context(self, conversation_history: str = "", rag_content: str = "") -> str:
        """
        Assemble the different parts of the PromptStructure into a complete system prompt
        """
        if not self.agent_registry_entry:
            # Return a basic prompt if registry entry is not available
            logger.warning(f"Agent registry entry not loaded for {self.agent_id}. Using basic prompt.")
            peer_summary = self.get_peer_agents_summary()
            basic_prompt = f"""
--- Your Role & Objective ---
You are {self.agent_id}, an AI agent in a multi-agent system.

--- Available Peer Agents ---
{peer_summary}

--- Rules & Guardrails You Must Follow ---
""" + "\n".join(f"- {rule}" for rule in self.BASE_GUARDRAILS) + f"""

--- CRITICAL OUTPUT FORMAT REQUIREMENTS ---
- Your response MUST be a valid JSON object only
- Do NOT add any text before the JSON (no 'Final Answer:', 'Here is:', etc.)
- Do NOT add any text after the JSON
- Start directly with {{ and end with }}
- Example: {{"thought": "...", "action": "RESPOND", "response_content": "..."}}
"""
            return basic_prompt

        ps = self.agent_registry_entry.prompt_structure

        # Combine all rules
        all_rules = ps.rules + self.BASE_GUARDRAILS

        # Assemble peer agent information so the LLM knows who it can forward tasks to
        peer_summary = self.get_peer_agents_summary()

        # Structurally assemble the prompt
        prompt_parts = [
            f"--- 1. Your Role & Objective (Task Context) ---\n{ps.task_context}\n",
            f"--- 2. Your Communication Tone (Tone Context) ---\n{ps.tone_context}\n",
            f"--- 3. Available Peer Agents ---\n{peer_summary}\n",
            f"--- 4. Rules & Guardrails You Must Follow ---\n" + "\n".join(f"- {rule}" for rule in all_rules) + "\n",
            f"--- 5. CRITICAL OUTPUT FORMAT REQUIREMENTS ---\n" +
            "- Your final output MUST be a valid JSON object.\n" +
            "- You MUST enclose the entire JSON object within <result> and </result> tags.\n" +
            "- Do NOT add any text or explanations before the opening <result> tag or after the closing </result> tag.\n" +
            "- Your entire response should contain only the tags and the JSON within them.\n" +
            "- Example: <result>{{\"thought\": \"...\", \"action\": \"RESPOND\", \"response_content\": \"...\"}}</result>\n",
        ]

        if ps.examples:
            prompt_parts.append(f"--- Examples ---\n{ps.examples}\n")

        if rag_content and ps.background_data_placeholder:
            # Inject RAG content into the background data section
            background_section = ps.background_data_placeholder.replace("[[DOCUMENT]]", rag_content)
            prompt_parts.insert(2, f"--- Background Data ---\n{background_section}\n")

        # Thinking prompt
        if ps.thinking_step:
            prompt_parts.append(f"--- Thinking Prompt ---\n{ps.thinking_step}\n")

        return "\n".join(prompt_parts)

    @abstractmethod
    def create_agent(self) -> Agent:
        """
        Create and return a CrewAI Agent instance using the assembled prompt
        """
        pass

    def initialize(self, task_id:str):
        if self.task_id:
            self.db = gcp_clients.get_firestore_client()
            self.task_ref = self.db.collection('tasks').document(self.task_id)

        # Load registry entry if not already loaded
        if not self.agent_registry_entry:
            self.agent_registry_entry = self._load_registry_entry()
        
        # Initialize peer registry
        self._initialize_peer_registry()
        
        # Create agent if not already created
        if not self.agent:
            self.agent = self.create_agent()
            self.agent.verbose = True
            self.agent.max_iter = 1
            self.agent.allow_delegation = False

    @abstractmethod
    def get_llm(self, project_id:str) -> ChatVertexAI:
        pass

    @abstractmethod
    def create_task(self, input_data: Dict[str, Any]) -> Task:
        pass


    @staticmethod
    def extract_and_parse_json(response: str) -> AgentResponse | None:
        """
        Extracts content from between <result> tags and parses it into a Python dict.
        """
        match = re.search(r"<result>(.*?)</result>", response, re.DOTALL)
        if not match:
            logger.error("Error: Could not find <result> tags in the response.")
            return None
        
        json_content = match.group(1).strip()
        
        try:
            return AgentResponse.model_validate_json(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"Error: Failed to decode JSON. Content was: '{json_content}'")
            logger.error(f"JSONDecodeError: {e}")
            return None

    async def run(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to execute the agent's task with structured output.
        """
        self._current_task_id = task_id
        self._current_input_data = input_data

        try:
            self.task = self.create_task(input_data)
            crew = Crew(agents=[self.agent], tasks=[self.task], process=Process.sequential, verbose=True)
            logger.info(f"Starting crew execution...")
            result = crew.kickoff()
            if result is None:
                raise ValueError("Agent execution returned a None result, indicating a problem in the workflow.")

            # Estimate token usage
            estimated_tokens = TokenUsage(
                input_tokens=getattr(result.token_usage, 'prompt_tokens', 0),
                output_tokens=getattr(result.token_usage, 'completion_tokens', 0),
                total_tokens=getattr(result.token_usage, 'total_tokens', 0),
                price=0
            )

            logger.info(f"Extracting structured response from result raw: {result.raw}")
            agent_response = self.extract_and_parse_json(result.raw)

            if not agent_response:
                # If <result> tag parsing fails, attempt a fallback raw string parsing.
                logger.warning(
                    f"Could not parse AgentResponse from <result> tags. Attempting fallback raw string parsing...")
                try:
                    json_matches = list(re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', str(result.raw), re.DOTALL))
                    if json_matches:
                        json_str = json_matches[-1].group(0)
                        agent_response = AgentResponse.model_validate_json(json_str)
                        logger.info("Successfully parsed AgentResponse using fallback raw string parsing.")
                    else:
                        raise ValueError("No valid JSON object found in the raw output.")
                except Exception as parse_error:
                    logger.error(f"Fallback JSON parsing also failed: {parse_error}")
                    # When all parsing fails, raise an exception to be handled by the outer block.
                    raise ValueError(
                        f"Failed to parse a valid response structure from the agent's output: {result.raw}")

            action = agent_response.action
            logger.info(f"Action determined: {action}")

            if action == "FORWARD":
                if agent_response.forward_to_agent:
                    peer_agent_id = agent_response.forward_to_agent.agent_id

                    if peer_agent_id in self.peer_agents:
                        logger.info(f"Agent {self.agent_id} forwarding task to {peer_agent_id}")
                        # ... (Your forwarding logic remains here)
                        # Example placeholder for your forwarding data
                        forward_task_data = {
                            "original_task_id": task_id,
                            "forwarded_by": self.agent_id,
                            "input": agent_response.forward_to_agent.required_info
                        }
                        return await self.forward_to_peer(peer_agent_id, forward_task_data)
                    else:
                        raise ValueError(f"Invalid target agent for forwarding: {peer_agent_id}")
                else:
                    raise ValueError("FORWARD action specified but no 'forward_to_agent' details were provided.")

            elif action == "RESPOND":
                final_response = agent_response.response_content or "No response content generated."
                full_agent_data = {
                    "output": final_response,
                    "thought": agent_response.thought,
                    "action": agent_response.action,
                    "full_response": agent_response.model_dump()
                }
                await self._log_task_event("Task Completed", {"agent_response": agent_response.model_dump()},
                                           estimated_tokens)
                await self._update_task_status(task_id, "COMPLETED", result=full_agent_data,
                                               token_usage=estimated_tokens)

                result_to_return = {"output": final_response, "status": "COMPLETED"}
                logger.info(f"Task completed successfully. Returning response to user.")
                return result_to_return

            else:
                # Handle REJECT or other undefined actions
                unhandled_action_msg = f"Unhandled action '{agent_response.action}'. Treating as a completed task."
                logger.warning(unhandled_action_msg)
                # For the frontend, a REJECT is still a complete workflow.
                return {"output": agent_response.response_content, "status": "COMPLETED"}

        except Exception as e:
            # --- KEY CHANGE HERE ---
            # 1. For debugging, still log the full technical error message in the backend.
            error_msg = f"Agent execution failed in run method: {str(e)}"
            logger.error(error_msg, exc_info=True)  # exc_info=True logs the full traceback.

            # 2. Still update the task status to FAILED in Firestore with the technical error reason.
            await self._update_task_status(task_id, "FAILED", error=error_msg)

            # 3. Return a fixed, user-friendly "unable to process" message to the frontend.
            #    This response has the same structure as a successful one for easier frontend handling.
            user_friendly_response = {
                "output": "I'm sorry, I was unable to process your request. This may be beyond my current capabilities. Please try again later.",
                "status": "COMPLETED"
                # Return COMPLETED so the frontend can display the message normally instead of triggering an error flow.
            }
            return user_friendly_response

    async def _log_task_event(self, event: str, details: Dict[str, Any] = None,
                              token_usage: Optional[TokenUsage] = None):
        """Log task execution events"""
        logger.info(f"Logging task event: {event}")
        if not self._current_task_id:
            logger.warning(f"No current task ID, skipping log")
            return

        try:
            # 檢查任務文檔是否存在
            task_doc_ref = self.db.collection('tasks').document(self._current_task_id)
            task_doc = task_doc_ref.get()
            
            if not task_doc.exists:
                logger.warning(f"Task document {self._current_task_id} does not exist, skipping log event")
                return
            
            log_entry = TaskLogEntry(
                event=event,
                agent_id=self.agent_id,
                token_usage=token_usage,
                details=details or {}
            )

            task_doc_ref.update({
                'log': firestore.ArrayUnion([log_entry.model_dump()])
            })
            logger.info(f"Log entry updated successfully for task {self._current_task_id}")

        except Exception as e:
            logger.error(f"Failed to log task event: {e}")

    async def _update_task_status(self, task_id: str, status: str, result: Dict[str, Any] = None, error: str = None, token_usage: Optional[TokenUsage] = None):
        """Update task status in Firestore"""
        try:
            # 檢查文檔是否存在
            task_doc_ref = self.db.collection('tasks').document(task_id)
            task_doc = task_doc_ref.get()
            
            if not task_doc.exists:
                logger.warning(f"Task document {task_id} does not exist, skipping status update")
                return
            
            update_data = {
                'status': status,
                'updated_at': datetime.datetime.now().timestamp()
            }

            if result:
                update_data['result'] = result

            if error:
                update_data['error'] = error
                
            # 更新 token 使用統計
            if token_usage:
                existing_data = task_doc.to_dict()
                existing_tokens = existing_data.get('total_tokens', {'input_tokens': 0, 'output_tokens': 0})
                
                new_total_tokens = TokenUsage(
                    input_tokens=existing_tokens.get('input_tokens', 0) + token_usage.input_tokens,
                    output_tokens=existing_tokens.get('output_tokens', 0) + token_usage.output_tokens
                )
                update_data['total_tokens'] = new_total_tokens.model_dump()

            task_doc_ref.update(update_data)

        except Exception as e:
            logger.error(f"Failed to update task status: {e}")

    def _initialize_peer_registry(self):
        """Initialize peer agent registry from Firestore"""
        try:
            agents_ref = self.db.collection("agents")
            agents = agents_ref.where("status", "==", "DEPLOYED").stream()

            for agent in agents:
                agent_data = agent.to_dict()
                agent_id = agent_data.get("agent_id")
                if agent_id and agent_id != self.agent_id:
                    self.peer_agents[agent_id] = {
                        "agent_type": agent_data.get("agent_type"),
                        "role": agent_data.get("role"),
                        "capabilities": agent_data.get("capabilities", []),
                        "status": agent_data.get("status")
                    }

            logger.info(f"{self.agent_id} loaded {len(self.peer_agents)} peer agents")

        except Exception as e:
            logger.warning(f"Failed to initialize peer registry: {e}. This may be expected during system initialization.")

    def get_peer_agents_summary(self) -> str:
        """Get summary of available peer agents"""
        if not self.peer_agents:
            return "No other agents are currently available."

        summary_parts = ["Available peer agents:"]
        for agent_id, agent_info in self.peer_agents.items():
            role = agent_info.get("role", "Unknown role")
            capabilities = ", ".join(agent_info.get("capabilities", []))
            summary_parts.append(f"- {agent_id}: {role} (capabilities: {capabilities})")

        return "\n".join(summary_parts)

    async def forward_to_peer(self, peer_agent_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward task to peer agent"""
        try:
            from app.shared_crew_lib.services.agent_communication_service import AgentCommunicationService
            
            comm_service = AgentCommunicationService()
            result = await comm_service.forward_task_to_agent(
                peer_agent_id, task_data, self.agent_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to forward task to peer agent: {e}")
            return {"status": "ERROR", "error": str(e)}

