import logging
import asyncio

from crewai.tools import BaseTool

from app.shared_crew_lib.services.rag_service import RAGService


class RAGKnowledgeSearchTool(BaseTool):
    name: str = "Knowledge Base Search"
    description: str = (
        "Searches the company's knowledge base for relevant information on products, "
        "styling tips, and company policies. Use this tool to find factual, "
        "up-to-date information to answer user questions."
    )
    rag_service: RAGService
    kb_id: str
    index_endpoint_name: str
    deployed_index_id: str

    def _run(self, query: str) -> str:
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an event loop, we need to use asyncio.create_task
                # But since _run is sync, we need to handle this differently
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, query)
                    return future.result()
            except RuntimeError:
                # No event loop running, safe to create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._async_run(query))
                finally:
                    loop.close()
        except Exception as e:
            logging.error(f"Error during RAG tool execution: {e}")
            logging.error(f"RAG tool error details - kb_id: {self.kb_id}, endpoint: {self.index_endpoint_name}, deployed_index: {self.deployed_index_id}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return f"Knowledge base search is temporarily unavailable. Error: {str(e)[:100]}"
    
    def _run_in_new_loop(self, query: str) -> str:
        """Helper method to run async code in a new event loop in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._async_run(query))
        finally:
            loop.close()
    
    async def _async_run(self, query: str) -> str:
        try:
            neighbor_results = await self.rag_service.query(
                query_text=query,
                index_endpoint_name=self.index_endpoint_name,
                deployed_index_id=self.deployed_index_id,
                top_k=3
            )

            if not neighbor_results:
                return "No relevant context information found in the knowledge base."

            chunk_ids = [result[0] for result in neighbor_results]

            chunk_docs = await self.rag_service.fetch_chunks_by_ids(self.kb_id, chunk_ids)

            if not chunk_docs:
                return "Found relevant IDs but could not retrieve content. The knowledge base might be inconsistent."

            context_parts = []
            for doc in chunk_docs:
                context_parts.append(f"Source: {doc.get('source_url', 'N/A')}\nContent: {doc.get('content', '')}")

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            logging.error(f"Error during async RAG tool execution: {e}")
            import traceback
            logging.error(f"Async RAG tool full traceback: {traceback.format_exc()}")
            
            # Check if it's an endpoint not found error
            if "400 Request contains an invalid argument" in str(e):
                return "The knowledge base search service is not properly configured. The search endpoint may not exist or may not be accessible."
            else:
                return f"Knowledge base search failed. Error: {str(e)[:100]}"