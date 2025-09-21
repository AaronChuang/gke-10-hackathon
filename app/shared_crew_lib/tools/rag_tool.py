import logging

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

    async def _run(self, query: str) -> str:
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
            logging.error(f"Error during RAG tool execution: {e}")
            return "An error occurred while searching the knowledge base."