import logging
import asyncio
from typing import List, Dict, Any, Tuple

from google.cloud import aiplatform
from google.cloud import firestore
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint
from langchain_google_vertexai import VertexAIEmbeddings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "gemini-embedding-001"

EMBEDDING_DIMENSIONS = 3072


class RAGService:

    def __init__(self, project_id: str, location: str, db: firestore.AsyncClient):
        self.project_id = project_id
        self.location = location
        self.db = db

        aiplatform.init(project=project_id, location=location)
        self.embedding_model = VertexAIEmbeddings(model_name=EMBEDDING_MODEL_NAME)

        self._index_endpoint_cache: Dict[str, MatchingEngineIndexEndpoint] = {}

    def _get_index_endpoint(self, index_endpoint_name: str) -> MatchingEngineIndexEndpoint:
        if index_endpoint_name not in self._index_endpoint_cache:
            endpoint_resource_name = f"projects/{self.project_id}/locations/{self.location}/indexEndpoints/{index_endpoint_name}"
            self._index_endpoint_cache[index_endpoint_name] = MatchingEngineIndexEndpoint(
                index_endpoint_name=endpoint_resource_name
            )
        return self._index_endpoint_cache[index_endpoint_name]

    async def get_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        logger.info(f"Generating embeddings for {len(text_chunks)} text chunks...")
        embeddings = await self.embedding_model.aembed_documents(text_chunks)
        logger.info("Finished generating embeddings.")
        return embeddings

    async def upsert_to_vector_search(self, index: aiplatform.MatchingEngineIndex, datapoints: List[Dict[str, Any]]):
        # Use the index object directly instead of creating a new one

        # The upsert_datapoints method is synchronous, so we run it in a thread pool
        # For batching large amount of data
        # Note: 1000 is the limit for each upsert in the API
        for i in range(0, len(datapoints), 1000):
            batch = datapoints[i:i + 1000]
            await asyncio.to_thread(index.upsert_datapoints, datapoints=batch)
            logger.info(f"Upserted batch {i // 1000 + 1} to index {index.display_name}")

        logger.info(f"Successfully upserted {len(datapoints)} datapoints to index {index.display_name}")

    async def query(self, query_text: str, index_endpoint_name: str, deployed_index_id: str, top_k: int = 5) -> List[
        Tuple[str, float]]:
        logger.info(f"Executing vector search for query '{query_text[:50]}...'")

        query_embedding = await self.embedding_model.aembed_query(query_text)

        index_endpoint = self._get_index_endpoint(index_endpoint_name)

        # The find_neighbors method is synchronous
        response = await asyncio.to_thread(
            index_endpoint.find_neighbors,
            deployed_index_id=deployed_index_id,
            queries=[query_embedding],
            num_neighbors=top_k
        )

        results = []
        if response and response[0]:
            for neighbor in response[0]:
                results.append((neighbor.id, neighbor.distance))

        logger.info(f"Vector search found {len(results)} relevant results.")
        return results

    async def fetch_chunks_by_ids(self, kb_id: str, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        if not chunk_ids:
            return []

        chunks_collection = self.db.collection("knowledge_base").document(kb_id).collection("chunks")
        doc_refs = [chunks_collection.document(chunk_id) for chunk_id in chunk_ids]

        docs = await self.db.get_all(doc_refs)

        return [doc.to_dict() for doc in docs if doc.exists]

    async def setup_infrastructure_for_kb(self, kb_id: str) -> Tuple[str, str, str]:
        """
        Checks for and creates Vector Search Index and Index Endpoint if they don't exist.
        This is a time-consuming, one-time setup process.
        """
        # For display names (allow hyphens)
        display_base_name = kb_id.replace('_', '-').lower()
        index_display_name = f"{display_base_name}-index"
        endpoint_display_name = f"{display_base_name}-endpoint"
        
        # For deployed index ID (only letters, numbers, underscores)
        deployed_base_name = kb_id.lower()  # Keep underscores, remove hyphens if any
        deployed_index_id = f"deployed_{deployed_base_name}"

        indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name="{index_display_name}"')
        if indexes:
            my_index = indexes[0]
            logger.info(f"Found existing Index: {my_index.resource_name}")
        else:
            logger.info(f"Creating new Index: {index_display_name}...")
            my_index = await asyncio.to_thread(
                aiplatform.MatchingEngineIndex.create_tree_ah_index,
                display_name=index_display_name,
                description=f"Index for knowledge base {kb_id}",
                dimensions=EMBEDDING_DIMENSIONS,
                approximate_neighbors_count=150,
                leaf_node_embedding_count=1000,
                leaf_nodes_to_search_percent=80,
                index_update_method="STREAM_UPDATE",
            )
            logger.info(f"Successfully created Index: {my_index.resource_name}")

        endpoints = MatchingEngineIndexEndpoint.list(filter=f'display_name="{endpoint_display_name}"')

        if endpoints:
            my_endpoint = endpoints[0]
            logger.info(f"Found existing Index Endpoint: {my_endpoint.resource_name}")
        else:
            logger.info(f"Creating new Index Endpoint: {endpoint_display_name}...")
            my_endpoint = await asyncio.to_thread(
                MatchingEngineIndexEndpoint.create,
                display_name=endpoint_display_name,
                description=f"Endpoint for knowledge base {kb_id}",
                public_endpoint_enabled=True
            )
            logger.info(f"Successfully created Index Endpoint: {my_endpoint.resource_name}")

        # --- 3. 檢查並部署索引到端點 ---
        is_deployed = any(
            deployed_index.id == deployed_index_id for deployed_index in my_endpoint.deployed_indexes
        )
        if is_deployed:
            logger.info(
                f"Index {my_index.display_name} is already deployed to Endpoint {my_endpoint.display_name} with ID {deployed_index_id}.")
        else:
            logger.warning(f"Deploying Index to Endpoint. THIS WILL TAKE A LONG TIME (15-30+ minutes)...")
            await asyncio.to_thread(
                my_endpoint.deploy_index,
                index=my_index,
                deployed_index_id=deployed_index_id,
            )
            logger.info(f"Successfully deployed Index to Endpoint.")

        return my_index, my_endpoint.display_name, deployed_index_id
