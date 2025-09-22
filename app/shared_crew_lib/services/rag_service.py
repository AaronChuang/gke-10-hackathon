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
    
    def list_available_endpoints(self) -> List[str]:
        """List all available index endpoints in the project"""
        try:
            endpoints = aiplatform.MatchingEngineIndexEndpoint.list()
            endpoint_names = []
            for endpoint in endpoints:
                # Extract the endpoint name from the resource name
                # Format: projects/PROJECT_ID/locations/LOCATION/indexEndpoints/ENDPOINT_NAME
                parts = endpoint.resource_name.split('/')
                if len(parts) >= 6:
                    endpoint_names.append(parts[-1])  # Get the last part (endpoint name)
            logger.info(f"Available endpoints: {endpoint_names}")
            return endpoint_names
        except Exception as e:
            logger.error(f"Failed to list endpoints: {e}")
            return []

    def _get_index_endpoint(self, index_endpoint_display_name: str) -> MatchingEngineIndexEndpoint:
        """
        Gets a client for a Vector Search endpoint using its Display Name.
        This function queries GCP to find the numeric resource ID corresponding 
        to the display name, and then uses that ID for initialization.
        """
        # If already in cache, return directly to avoid duplicate queries
        if index_endpoint_display_name in self._index_endpoint_cache:
            return self._index_endpoint_cache[index_endpoint_display_name]

        logger.info(f"Querying for Index Endpoint with display name: '{index_endpoint_display_name}'...")
        try:
            # 1. Use the SDK's list function with a filter for the display_name
            endpoints = MatchingEngineIndexEndpoint.list(
                filter=f'display_name="{index_endpoint_display_name}"',
                project=self.project_id,
                location=self.location,
            )
            
            if not endpoints:
                logger.error(f"Could not find any Index Endpoint with display name '{index_endpoint_display_name}'.")
                # For debugging, list all available Endpoints
                all_endpoints = MatchingEngineIndexEndpoint.list(project=self.project_id, location=self.location)
                logger.error(f"Available Endpoints in project: {[ep.display_name for ep in all_endpoints]}")
                raise ValueError(f"Endpoint '{index_endpoint_display_name}' not found.")
            
            # 2. From the query result, get the full resource name of the first match
            # This is the "ID card number" that the API recognizes, which includes the numeric ID
            endpoint_resource_name = endpoints[0].resource_name
            logger.info(f"Successfully found Endpoint resource: {endpoint_resource_name}")

            # 3. Use this correct, full resource name to initialize the client
            endpoint_client = MatchingEngineIndexEndpoint(index_endpoint_name=endpoint_resource_name)
            
            # 4. Store the successfully initialized client in the cache
            self._index_endpoint_cache[index_endpoint_display_name] = endpoint_client
            return endpoint_client

        except Exception as e:
            logger.error(f"A critical error occurred while getting Index Endpoint '{index_endpoint_display_name}': {e}", exc_info=True)
            # Re-raise the exception so the Agent's Tool can catch it
            raise


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

        # Use asyncio.to_thread to run sync Firestore operations in a thread pool
        # This avoids event loop issues
        return await asyncio.to_thread(self._fetch_chunks_sync, kb_id, chunk_ids)
    
    def _fetch_chunks_sync(self, kb_id: str, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """Synchronous helper method to fetch chunks using sync Firestore client"""
        try:
            from app.shared_crew_lib.clients import gcp_clients
            sync_db = gcp_clients.get_firestore_client()
            
            chunks_collection = sync_db.collection("knowledge_base").document(kb_id).collection("chunks")
            
            docs = []
            for chunk_id in chunk_ids:
                try:
                    doc = chunks_collection.document(chunk_id).get()
                    if doc.exists:
                        docs.append(doc.to_dict())
                        logger.info(f"Successfully fetched chunk: {chunk_id}")
                except Exception as e:
                    logger.warning(f"Failed to fetch chunk {chunk_id}: {e}")
                    continue
            
            logger.info(f"Fetched {len(docs)} chunks out of {len(chunk_ids)} requested")
            return docs
        except Exception as e:
            logger.error(f"Error in _fetch_chunks_sync: {e}")
            return []

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
