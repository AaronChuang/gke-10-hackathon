import os
import json
import logging
from typing import Dict, Any, List, Optional
from google.cloud import firestore

from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.schemas.agent_task_message import AgentTaskMessage

logger = logging.getLogger(__name__)

class AgentCommunicationService:
    """Agent Communication Service"""
    
    def __init__(self):
        self.publisher = gcp_clients.get_publisher_client()
        self.db = gcp_clients.get_firestore_client()
        self.project_id = os.getenv("GCP_PROJECT_ID")
    
    async def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get all available agents list"""
        try:
            agents_ref = self.db.collection("agents")
            agents = agents_ref.where("status", "==", "DEPLOYED").stream()
            
            agent_list = []
            for agent in agents:
                agent_data = agent.to_dict()
                agent_list.append({
                    "agent_id": agent_data.get("agent_id"),
                    "agent_type": agent_data.get("agent_type"),
                    "role": agent_data.get("role"),
                    "capabilities": agent_data.get("capabilities", []),
                    "status": agent_data.get("status"),
                    "created_at": agent_data.get("created_at")
                })
            
            return agent_list
            
        except Exception as e:
            logger.error(f"Failed to get agents list: {e}")
            return []
    
    async def find_suitable_agent(self, task_description: str, required_capabilities: List[str] = None) -> Optional[Dict[str, Any]]:
        """Find suitable agent based on task description and required capabilities"""
        try:
            available_agents = await self.get_available_agents()
            
            if not available_agents:
                return None
            
            # If required capabilities are specified, prioritize matching
            if required_capabilities:
                for agent in available_agents:
                    agent_capabilities = agent.get("capabilities", [])
                    if any(cap in agent_capabilities for cap in required_capabilities):
                        return agent
            
            # Keyword matching based on task description
            task_lower = task_description.lower()
            
            # Technical keywords
            tech_keywords = ["technical", "architecture", "programming", "code", "system", "development", "api", "database", "cloud"]
            if any(keyword in task_lower for keyword in tech_keywords):
                tech_agent = next((agent for agent in available_agents if "tech" in agent.get("agent_type", "").lower()), None)
                if tech_agent:
                    return tech_agent
            
            # Design keywords
            design_keywords = ["design", "style", "aesthetic", "ui", "ux", "interface", "visual"]
            if any(keyword in task_lower for keyword in design_keywords):
                design_agent = next((agent for agent in available_agents if "design" in agent.get("agent_type", "").lower()), None)
                if design_agent:
                    return design_agent
            
            # Default return general agent
            proxy_agent = next((agent for agent in available_agents if agent.get("agent_type") == "proxy_agent"), None)
            return proxy_agent or available_agents[0] if available_agents else None
            
        except Exception as e:
            logger.error(f"Failed to find suitable agent: {e}")
            return None
    
    async def forward_task_to_agent(self, target_agent_id: str, task_data: Dict[str, Any], source_agent_id: str = None) -> Dict[str, Any]:
        """Forward task to specified agent"""
        try:
            # Build task message
            task_message = AgentTaskMessage(
                task_id=task_data.get("task_id"),
                agent_id=target_agent_id,
                input_data=task_data.get("input_data", {}),
                source_agent_id=source_agent_id,
                forwarded=True
            )
            
            # Send to target agent's topic
            topic_path = self.publisher.topic_path(self.project_id, f"{target_agent_id}-topic")
            
            message_data = task_message.dict()
            
            future = self.publisher.publish(
                topic_path,
                json.dumps(message_data).encode('utf-8')
            )
            
            message_id = future.result()
            
            logger.info(f"Task forwarded successfully: {task_data.get('task_id')} -> {target_agent_id}")
            
            return {
                "status": "SUCCESS",
                "message_id": message_id,
                "target_agent": target_agent_id,
                "task_id": task_data.get("task_id")
            }
            
        except Exception as e:
            logger.error(f"Task forwarding failed: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "target_agent": target_agent_id,
                "task_id": task_data.get("task_id")
            }
    
    async def broadcast_agent_registry_update(self, action: str, agent_data: Dict[str, Any]):
        """Broadcast agent registry update"""
        try:
            registry_topic = self.publisher.topic_path(self.project_id, "agent-registry-updates")
            
            message_data = {
                "action": action,  # AGENT_ADDED, AGENT_REMOVED, AGENT_UPDATED
                "agent_data": agent_data,
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            
            future = self.publisher.publish(
                registry_topic,
                json.dumps(message_data, default=str).encode('utf-8')
            )
            
            message_id = future.result()
            logger.info(f"Broadcast agent registry update: {action} - {agent_data.get('agent_id')}")
            
            return {"status": "SUCCESS", "message_id": message_id}
            
        except Exception as e:
            logger.error(f"Failed to broadcast registry update: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get specified agent's capabilities list"""
        try:
            agent_doc = self.db.collection("agents").document(agent_id).get()
            if agent_doc.exists:
                agent_data = agent_doc.to_dict()
                return agent_data.get("capabilities", [])
            return []
            
        except Exception as e:
            logger.error(f"Failed to get agent capabilities: {e}")
            return []
    
    async def update_agent_capabilities(self, agent_id: str, capabilities: List[str]):
        """Update agent's capabilities list"""
        try:
            self.db.collection("agents").document(agent_id).update({
                "capabilities": capabilities,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
            # Broadcast update
            agent_doc = self.db.collection("agents").document(agent_id).get()
            if agent_doc.exists:
                await self.broadcast_agent_registry_update("AGENT_UPDATED", agent_doc.to_dict())
            
            logger.info(f"Updated agent capabilities: {agent_id}")
            return {"status": "SUCCESS"}
            
        except Exception as e:
            logger.error(f"Failed to update agent capabilities: {e}")
            return {"status": "ERROR", "error": str(e)}
