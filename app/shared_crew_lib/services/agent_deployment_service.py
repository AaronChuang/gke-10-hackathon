import os
import json
import logging
from typing import Dict, Any
from google.cloud import firestore
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pydantic import BaseModel, Field

from app.shared_crew_lib.clients import gcp_clients
from app.shared_crew_lib.schemas.agent_registry import AgentRegistryEntry

logger = logging.getLogger(__name__)

class AgentInfo(BaseModel):
    agent_id: str = Field(..., description="代理人唯一識別碼")
    agent_type: str = Field(..., description="代理人類型")
    name: str = Field(default="", description="代理人名稱")
    description: str = Field(default="", description="代理人描述")
    role: str = Field(default="", description="代理人角色")
    goal: str = Field(default="", description="代理人目標")
    backstory: str = Field(default="", description="代理人背景故事")
    capabilities: list = Field(default_factory=list, description="代理人能力列表")
    status: str = Field(default="CREATING", description="代理人狀態")
    
    @classmethod
    def from_registry_entry(cls, entry: AgentRegistryEntry) -> "AgentInfo":
        """從註冊表項目創建部署資訊"""
        # 從 agent_id 推斷 agent_type (例如: tech-analyst -> tech_analyst)
        agent_type = entry.agent_id.replace('-', '_')
        return cls(
            agent_id=entry.agent_id,
            agent_type=agent_type,
            name=entry.name,
            description=entry.description,
            capabilities=entry.capabilities,
            status=entry.status.value
        )

class AgentDeploymentService:
    """代理人部署服務"""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.cluster_name = os.getenv("GKE_CLUSTER_NAME", "ai-agents-cluster")
        self.cluster_zone = os.getenv("GKE_CLUSTER_ZONE", "asia-east1-a")
        self.namespace = "ai-agents"
        
        self.publisher = gcp_clients.get_publisher_client()
        self.subscriber = gcp_clients.get_subscriber_client()
        self.db = gcp_clients.get_firestore_client()

        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()  # 本地開發
        
        self.k8s_apps_v1 = client.AppsV1Api()
        self.k8s_core_v1 = client.CoreV1Api()
    
    async def create_agent_resources(self, agent_info: AgentInfo) -> Dict[str, Any]:
        try:
            topic_result = await self._create_pubsub_resources(agent_info)
            
            deployment_result = await self._create_k8s_deployment(agent_info)
            
            await self._update_agent_status(agent_info.agent_id, "DEPLOYED")
            
            return {
                "status": "SUCCESS",
                "topic": topic_result,
                "deployment": deployment_result,
                "agent_id": agent_info.agent_id
            }
            
        except Exception as e:
            logger.error(f"創建代理人資源失敗: {e}")
            await self._update_agent_status(agent_info.agent_id, "FAILED")
            return {
                "status": "ERROR",
                "error": str(e),
                "agent_id": agent_info.agent_id
            }
    
    async def delete_agent_resources(self, agent_id: str) -> Dict[str, Any]:
        try:
            agent_doc = self.db.collection("agents").document(agent_id).get()
            if not agent_doc.exists:
                return {"status": "ERROR", "error": "代理人不存在"}
            
            agent_data = agent_doc.to_dict()
            
            await self._delete_k8s_deployment(agent_id)

            await self._delete_pubsub_resources(agent_data)
            
            agent_doc.reference.delete()
            
            # 5. 通知其他代理人
            await self._broadcast_agent_removal(agent_id)
            
            return {
                "status": "SUCCESS",
                "agent_id": agent_id
            }
            
        except Exception as e:
            logger.error(f"刪除代理人資源失敗: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "agent_id": agent_id
            }
    
    async def _create_pubsub_resources(self, agent_info: AgentInfo) -> Dict[str, str]:
        topic_name = f"{agent_info.agent_id}-topic"
        subscription_name = f"{agent_info.agent_id}-sub"
        
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        subscription_path = self.subscriber.subscription_path(self.project_id, subscription_name)
        
        # 創建主題
        try:
            self.publisher.create_topic(request={"name": topic_path})
            logger.info(f"創建主題: {topic_path}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise e
        
        try:
            self.subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "ack_deadline_seconds": 60
                }
            )
            logger.info(f"創建訂閱: {subscription_path}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise e
        
        return {
            "topic": topic_name,
            "subscription": subscription_name,
            "topic_path": topic_path,
            "subscription_path": subscription_path
        }
    
    async def _create_k8s_deployment(self, agent_info: AgentInfo) -> Dict[str, str]:
        deployment_yaml = self._generate_deployment_yaml(agent_info)
        
        try:
            # 創建部署
            self.k8s_apps_v1.create_namespaced_deployment(
                namespace=self.namespace,
                body=deployment_yaml
            )
            logger.info(f"創建 K8s 部署: {agent_info.agent_id}")
            
            return {
                "deployment_name": agent_info.agent_id,
                "namespace": self.namespace,
                "status": "CREATED"
            }
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"部署已存在: {agent_info.agent_id}")
                return {
                    "deployment_name": agent_info.agent_id,
                    "namespace": self.namespace,
                    "status": "EXISTS"
                }
            else:
                raise e
    
    def _generate_deployment_yaml(self, agent_info: AgentInfo) -> Dict[str, Any]:
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": agent_info.agent_id,
                "namespace": self.namespace,
                "labels": {
                    "app": agent_info.agent_id,
                    "agent-type": agent_info.agent_type,
                    "managed-by": "orchestrator"
                }
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": agent_info.agent_id
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": agent_info.agent_id,
                            "agent-type": agent_info.agent_type
                        }
                    },
                    "spec": {
                        "serviceAccountName": "ai-agent-ksa",
                        "containers": [{
                            "name": f"{agent_info.agent_id}-container",
                            "image": "asia-east1-docker.pkg.dev/gke-10-hackathon-471902/ai-agents-repo/ai-agent-base:latest",
                            "command": ["python", f"/workspace/app/workers/{agent_info.agent_type}_worker.py"],
                            "resources": {
                                "requests": {
                                    "cpu": "250m",
                                    "memory": "256Mi"
                                },
                                "limits": {
                                    "cpu": "500m",
                                    "memory": "512Mi"
                                }
                            },
                            "env": [
                                {"name": "GCP_PROJECT_ID", "value": self.project_id},
                                {"name": "GCP_FIRESTORE_NAME", "value": "gke-10-hackathon"},
                                {"name": f"{agent_info.agent_id.upper().replace('-', '_')}_SUBSCRIPTION_ID", 
                                 "value": f"{agent_info.agent_id}-sub"},
                                {"name": "AGENT_ID", "value": agent_info.agent_id},
                                {"name": "AGENT_TYPE", "value": agent_info.agent_type},
                                {"name": "PYTHONPATH", "value": "/workspace"}
                            ],
                            "workingDir": "/workspace"
                        }]
                    }
                }
            }
        }
    
    async def _delete_k8s_deployment(self, agent_id: str):
        try:
            self.k8s_apps_v1.delete_namespaced_deployment(
                name=agent_id,
                namespace=self.namespace
            )
            logger.info(f"刪除 K8s 部署: {agent_id}")
        except ApiException as e:
            if e.status != 404:  # Not found is OK
                raise e
    
    async def _delete_pubsub_resources(self, agent_data: Dict[str, Any]):
        agent_id = agent_data.get("agent_id")
        topic_name = f"{agent_id}-topic"
        subscription_name = f"{agent_id}-sub"
        
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        subscription_path = self.subscriber.subscription_path(self.project_id, subscription_name)

        try:
            self.subscriber.delete_subscription(request={"subscription": subscription_path})
            logger.info(f"刪除訂閱: {subscription_path}")
        except Exception as e:
            logger.warning(f"刪除訂閱失敗: {e}")
        try:
            self.publisher.delete_topic(request={"topic": topic_path})
            logger.info(f"刪除主題: {topic_path}")
        except Exception as e:
            logger.warning(f"刪除主題失敗: {e}")
    
    async def _update_agent_status(self, agent_id: str, status: str):
        """更新代理人狀態"""
        self.db.collection("agents").document(agent_id).update({
            "status": status,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
    
    async def _broadcast_agent_removal(self, agent_id: str):
        registry_topic = self.publisher.topic_path(self.project_id, "agent-registry-updates")
        
        message_data = {
            "action": "AGENT_REMOVED",
            "agent_id": agent_id,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        try:
            self.publisher.publish(
                registry_topic,
                json.dumps(message_data).encode('utf-8')
            )
            logger.info(f"廣播代理人移除: {agent_id}")
        except Exception as e:
            logger.error(f"廣播失敗: {e}")
