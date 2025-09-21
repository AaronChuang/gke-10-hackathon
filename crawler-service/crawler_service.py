from typing import List, Dict, Any, Optional
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from google.cloud import firestore
import hashlib
import time
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_fixed

from rag_service import RAGService
from knowledge_base import KnowledgeBaseEntry, KnowledgeBaseStatus

logger = logging.getLogger(__name__)


class CrawlerService:
    """Service for crawling websites and managing knowledge base indexing."""

    def __init__(self, db: firestore.AsyncClient, project_id: str, location: str):
        self.db = db
        self.project_id = project_id
        self.location = location
        self.collection_name = "knowledge_base"
        self.rag_service = RAGService(project_id=project_id, location=location, db=db)
        self.max_pages_per_site = 50  # Limit page count for hackathon demo speed
        self.max_concurrent_requests = 5

    async def trigger_crawling_from_event(self, url: str) -> str:
        """Triggers the crawling process from a Pub/Sub event and runs it synchronously within the function's lifecycle."""
        kb_id = self._generate_kb_id(url)
        kb_entry = KnowledgeBaseEntry(
            kb_id=kb_id,
            url=url,
            status=KnowledgeBaseStatus.QUEUED
        )
        logger.info(f"Knowledge base entry created: {kb_id}  {kb_entry}")
        await self.db.collection(self.collection_name).document(kb_id).set(kb_entry.model_dump())
        logger.info(f"Knowledge base entry created: {kb_id} for {url}")

        # In a Cloud Function, the task runs in the foreground.
        await self._crawl_and_index_website(kb_id, url)

        return kb_id

    async def _crawl_and_index_website(self, kb_id: str, base_url: str):
        """The main process for crawling and indexing a website."""
        try:
            await self._update_kb_status(kb_id, KnowledgeBaseStatus.CRAWLING)
            pages_data = await self._crawl_website(base_url)

            if not pages_data:
                raise ValueError("No valid content was crawled. Please check the URL or website structure.")

            await self._update_kb_pages(kb_id, len(pages_data), len(pages_data))
            await self._update_kb_status(kb_id, KnowledgeBaseStatus.INDEXING)

            # Key integration point with Vertex AI
            await self._create_vector_index(kb_id, pages_data)

            await self._update_kb_status(kb_id, KnowledgeBaseStatus.ACTIVE)
            logger.info(f"Website indexing completed for {kb_id}, processed {len(pages_data)} pages")

        except Exception as e:
            logger.error(f"Website indexing failed for {kb_id}: {e}", exc_info=True)
            await self._update_kb_status(kb_id, KnowledgeBaseStatus.FAILED, error_message=str(e))

    async def _create_vector_index(self, kb_id: str, pages_data: List[Dict[str, Any]]):
        """Creates a vector index for the page content."""
        # 1. Prepare text chunks with metadata
        text_chunks_with_metadata = []
        all_chunks_content = []
        for page in pages_data:
            chunks = self._split_text_into_chunks(page['content'])
            for i, chunk_content in enumerate(chunks):
                chunk_id = f"{hashlib.md5(page['url'].encode()).hexdigest()}_{i}"
                text_chunks_with_metadata.append({
                    'id': chunk_id,
                    'content': chunk_content,
                    'source_url': page['url'],
                    'title': page['title'],
                    'kb_id': kb_id
                })
                all_chunks_content.append(chunk_content)

        if not all_chunks_content:
            logger.warning(f"No indexable text chunks found for knowledge base {kb_id}.")
            return

        # 2. Batch generate embeddings
        embeddings = await self.rag_service.get_embeddings(all_chunks_content)

        # 3. Combine datapoints for upserting
        datapoints_to_upsert = []
        for i, chunk_meta in enumerate(text_chunks_with_metadata):
            datapoints_to_upsert.append({
                "datapoint_id": chunk_meta['id'],
                "feature_vector": embeddings[i]
            })

        # 4. Setup Vector Search Index and Endpoint via RAGService
        # In a real application, Index/Endpoint creation might be a separate admin task.
        index_object, endpoint_name, deployed_id = await self.rag_service.setup_infrastructure_for_kb(kb_id)

        # 5. Upsert vectors to Vector Search
        await self.rag_service.upsert_to_vector_search(index_object, datapoints_to_upsert)

        # 6. Store metadata in Firestore
        batch = self.db.batch()
        chunks_collection = self.db.collection(self.collection_name).document(kb_id).collection("chunks")
        for chunk_meta in text_chunks_with_metadata:
            doc_ref = chunks_collection.document(chunk_meta['id'])
            batch.set(doc_ref, chunk_meta)
        await batch.commit()

    async def _crawl_website(self, base_url: str) -> List[Dict[str, Any]]:
        """Crawls all pages of a website."""
        pages_data = []
        visited_urls = set()
        urls_to_visit = [base_url]
        
        # Parse the base domain
        base_domain = urlparse(base_url).netloc
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'GKE-Hackathon-Crawler/1.0'}
        ) as session:
            
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            
            while urls_to_visit and len(pages_data) < self.max_pages_per_site:
                # Process URLs in batches
                batch_urls = urls_to_visit[:self.max_concurrent_requests]
                urls_to_visit = urls_to_visit[self.max_concurrent_requests:]
                
                # Crawl concurrently
                tasks = [
                    self._crawl_single_page(session, semaphore, url, base_domain)
                    for url in batch_urls
                    if url not in visited_urls
                ]
                
                if not tasks:
                    continue
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for url, result in zip(batch_urls, results):
                    visited_urls.add(url)
                    
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to crawl page {url}: {result}")
                        continue
                    
                    if result:
                        page_data, new_urls = result
                        pages_data.append(page_data)
                        
                        # Add newly discovered URLs
                        for new_url in new_urls:
                            if (new_url not in visited_urls and 
                                new_url not in urls_to_visit and
                                len(pages_data) + len(urls_to_visit) < self.max_pages_per_site):
                                urls_to_visit.append(new_url)
                
                # Avoid overly frequent requests
                await asyncio.sleep(1)
        
        return pages_data

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def _crawl_single_page(self, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, 
                                url: str, base_domain: str) -> Optional[tuple]:
        """Crawls a single page."""
        async with semaphore:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    content_type = response.headers.get('content-type', '')
                    if 'text/html' not in content_type:
                        return None
                    
                    html_content = await response.text()
                    
                # Parse HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract text content
                text_content = self._extract_text_content(soup)
                
                if not text_content.strip():
                    return None
                
                # Extract page metadata
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""
                
                # Extract all links
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    
                    # Only keep links within the same domain
                    if urlparse(absolute_url).netloc == base_domain:
                        links.append(absolute_url)
                
                page_data = {
                    'url': url,
                    'title': title_text,
                    'content': text_content,
                    'content_length': len(text_content),
                    'crawled_at': datetime.now().timestamp(),
                    'content_hash': hashlib.md5(text_content.encode()).hexdigest()
                }
                
                return page_data, links
                
            except Exception as e:
                logger.error(f"Error crawling page {url}: {e}")
                return None
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extracts plain text content from HTML."""
        # Remove script and style tags
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
        
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text

    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Splits long text into smaller chunks."""
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to split at a sentence-ending punctuation or newline
            chunk_text = text[start:end]
            last_period = chunk_text.rfind('.')
            last_newline = chunk_text.rfind('\n')
            
            split_point = max(last_period, last_newline)
            
            if split_point > start + max_chunk_size // 2:  # Ensure the split point is not too early
                end = start + split_point + 1
            
            chunks.append(text[start:end])
            start = end - overlap  # Add overlap
        
        return chunks
    
    def _generate_kb_id(self, url: str) -> str:
        """Generates a unique knowledge base ID."""
        domain = urlparse(url).netloc
        timestamp = str(int(time.time()))
        return f"kb_{domain.replace('.', '_')}_{timestamp}"
    
    async def _update_kb_status(self, kb_id: str, status: KnowledgeBaseStatus, error_message: Optional[str] = None):
        """Updates the status of the knowledge base entry."""
        try:
            update_data = {
                'status': status.value,
                'updated_at': datetime.now().timestamp()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            await self.db.collection(self.collection_name).document(kb_id).update(update_data)
            
        except Exception as e:
            logger.error(f"Failed to update knowledge base status: {e}")
    
    async def _update_kb_pages(self, kb_id: str, indexed_pages: int, total_pages: int):
        """Updates the page counts for the knowledge base entry."""
        try:
            await self.db.collection(self.collection_name).document(kb_id).update({
                'indexed_pages': indexed_pages,
                'total_pages': total_pages,
                'updated_at': datetime.now().timestamp()
            })
            
        except Exception as e:
            logger.error(f"Failed to update page statistics: {e}")
    
    async def get_knowledge_bases(self) -> List[KnowledgeBaseEntry]:
        """Retrieves all knowledge bases."""
        try:
            docs = await self.db.collection(self.collection_name).stream()
            knowledge_bases = []
            
            async for doc in docs:
                kb_data = doc.to_dict()
                knowledge_bases.append(KnowledgeBaseEntry(**kb_data))
            
            return knowledge_bases
            
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge base list: {e}")
            return []
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """Deletes a knowledge base."""
        try:
            # Delete the main record
            await self.db.collection(self.collection_name).document(kb_id).delete()
            
            # Delete associated text chunks
            chunks_collection = self.db.collection(self.collection_name).document(kb_id).collection("chunks")
            docs = chunks_collection.stream()
            
            batch = self.db.batch()
            async for doc in docs:
                batch.delete(doc.reference)
            await batch.commit()
            
            logger.info(f"Deleted knowledge base: {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge base: {e}")
            return False
