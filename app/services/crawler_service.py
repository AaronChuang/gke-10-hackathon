from typing import List, Dict, Any, Optional
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from google.cloud import firestore
from google.cloud import aiplatform
import hashlib
import time
from datetime import datetime
from ..shared_crew_lib.schemas.knowledge_base import KnowledgeBaseEntry, KnowledgeBaseStatus
from ..shared_crew_lib.services.rag_service import RAGService

logger = logging.getLogger(__name__)

class CrawlerService:
    """網站爬取和索引服務 - 支援知識庫管理"""
    
    def __init__(self, db: firestore.Client, project_id: str, location: str = "us-central1"):
        self.db = db
        self.project_id = project_id
        self.location = location
        self.collection_name = "knowledge_base"
        self.max_pages_per_site = 100  # 每個網站最多爬取頁面數
        self.max_concurrent_requests = 5  # 最大並發請求數
        
    async def start_website_indexing(self, url: str) -> str:
        """開始網站索引流程"""
        try:
            # 生成知識庫 ID
            kb_id = self._generate_kb_id(url)
            
            # 創建知識庫項目
            kb_entry = KnowledgeBaseEntry(
                kb_id=kb_id,
                url=url,
                status=KnowledgeBaseStatus.QUEUED
            )
            
            # 保存到 Firestore
            self.db.collection(self.collection_name).document(kb_id).set(kb_entry.model_dump())
            logger.info(f"創建知識庫項目: {kb_id} for {url}")
            
            # 異步開始爬取流程
            asyncio.create_task(self._crawl_and_index_website(kb_id, url))
            
            return kb_id
            
        except Exception as e:
            logger.error(f"開始網站索引失敗: {e}")
            raise
    
    async def _crawl_and_index_website(self, kb_id: str, base_url: str):
        """爬取和索引網站的主要流程"""
        try:
            # 更新狀態為爬取中
            await self._update_kb_status(kb_id, KnowledgeBaseStatus.CRAWLING)
            
            # 爬取網站頁面
            pages_data = await self._crawl_website(base_url)
            
            # 更新頁面統計
            await self._update_kb_pages(kb_id, len(pages_data), len(pages_data))
            
            # 更新狀態為索引中
            await self._update_kb_status(kb_id, KnowledgeBaseStatus.INDEXING)
            
            # 建立向量索引
            await self._create_vector_index(kb_id, pages_data)
            
            # 更新狀態為活躍
            await self._update_kb_status(kb_id, KnowledgeBaseStatus.ACTIVE)
            
            logger.info(f"網站索引完成: {kb_id}, 共處理 {len(pages_data)} 個頁面")
            
        except Exception as e:
            logger.error(f"網站索引失敗: {e}")
            await self._update_kb_status(
                kb_id, 
                KnowledgeBaseStatus.FAILED, 
                error_message=str(e)
            )
    
    async def _crawl_website(self, base_url: str) -> List[Dict[str, Any]]:
        """爬取網站所有頁面"""
        pages_data = []
        visited_urls = set()
        urls_to_visit = [base_url]
        
        # 解析基礎域名
        base_domain = urlparse(base_url).netloc
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'GKE-Hackathon-Crawler/1.0'}
        ) as session:
            
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            
            while urls_to_visit and len(pages_data) < self.max_pages_per_site:
                # 批次處理 URL
                batch_urls = urls_to_visit[:self.max_concurrent_requests]
                urls_to_visit = urls_to_visit[self.max_concurrent_requests:]
                
                # 並發爬取
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
                        logger.warning(f"爬取頁面失敗 {url}: {result}")
                        continue
                    
                    if result:
                        page_data, new_urls = result
                        pages_data.append(page_data)
                        
                        # 添加新發現的 URL
                        for new_url in new_urls:
                            if (new_url not in visited_urls and 
                                new_url not in urls_to_visit and
                                len(pages_data) + len(urls_to_visit) < self.max_pages_per_site):
                                urls_to_visit.append(new_url)
                
                # 避免過於頻繁的請求
                await asyncio.sleep(1)
        
        return pages_data
    
    async def _crawl_single_page(self, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, 
                                url: str, base_domain: str) -> Optional[tuple]:
        """爬取單個頁面"""
        async with semaphore:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    content_type = response.headers.get('content-type', '')
                    if 'text/html' not in content_type:
                        return None
                    
                    html_content = await response.text()
                    
                # 解析 HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取文本內容
                text_content = self._extract_text_content(soup)
                
                if not text_content.strip():
                    return None
                
                # 提取頁面元數據
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""
                
                # 提取所有鏈接
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    
                    # 只保留同域名的鏈接
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
                logger.error(f"爬取頁面錯誤 {url}: {e}")
                return None
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """從 HTML 中提取純文本內容"""
        # 移除腳本和樣式標籤
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # 提取主要內容區域
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
        
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
        
        # 清理文本
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def _create_vector_index(self, kb_id: str, pages_data: List[Dict[str, Any]]):
        """為頁面內容創建向量索引"""
        try:
            # 將頁面內容切分為較小的塊
            text_chunks = []
            
            for page in pages_data:
                chunks = self._split_text_into_chunks(
                    page['content'], 
                    max_chunk_size=1000,
                    overlap=100
                )
                
                for i, chunk in enumerate(chunks):
                    text_chunks.append({
                        'id': f"{kb_id}_{page['url']}_{i}",
                        'content': chunk,
                        'source_url': page['url'],
                        'title': page['title'],
                        'kb_id': kb_id,
                        'chunk_index': i
                    })
            
            # 生成嵌入向量並存儲
            # 注意：這裡需要實際的向量數據庫實現
            # 目前先將文本塊存儲到 Firestore 作為臨時方案
            
            batch = self.db.batch()
            chunks_collection = self.db.collection(f'kb_chunks_{kb_id}')
            
            for chunk_data in text_chunks:
                doc_ref = chunks_collection.document(chunk_data['id'])
                batch.set(doc_ref, chunk_data)
            
            batch.commit()
            
            logger.info(f"創建向量索引完成: {kb_id}, 共 {len(text_chunks)} 個文本塊")
            
        except Exception as e:
            logger.error(f"創建向量索引失敗: {e}")
            raise
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """將長文本切分為較小的塊"""
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # 嘗試在句號或換行符處切分
            chunk_text = text[start:end]
            last_period = chunk_text.rfind('.')
            last_newline = chunk_text.rfind('\n')
            
            split_point = max(last_period, last_newline)
            
            if split_point > start + max_chunk_size // 2:  # 確保切分點不會太早
                end = start + split_point + 1
            
            chunks.append(text[start:end])
            start = end - overlap  # 添加重疊
        
        return chunks
    
    def _generate_kb_id(self, url: str) -> str:
        """生成知識庫 ID"""
        domain = urlparse(url).netloc
        timestamp = str(int(time.time()))
        return f"kb_{domain.replace('.', '_')}_{timestamp}"
    
    async def _update_kb_status(self, kb_id: str, status: KnowledgeBaseStatus, error_message: Optional[str] = None):
        """更新知識庫狀態"""
        try:
            update_data = {
                'status': status.value,
                'updated_at': datetime.now().timestamp()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            self.db.collection(self.collection_name).document(kb_id).update(update_data)
            
        except Exception as e:
            logger.error(f"更新知識庫狀態失敗: {e}")
    
    async def _update_kb_pages(self, kb_id: str, indexed_pages: int, total_pages: int):
        """更新知識庫頁面統計"""
        try:
            self.db.collection(self.collection_name).document(kb_id).update({
                'indexed_pages': indexed_pages,
                'total_pages': total_pages,
                'updated_at': datetime.now().timestamp()
            })
            
        except Exception as e:
            logger.error(f"更新頁面統計失敗: {e}")
    
    async def get_knowledge_bases(self) -> List[KnowledgeBaseEntry]:
        """獲取所有知識庫"""
        try:
            docs = self.db.collection(self.collection_name).stream()
            knowledge_bases = []
            
            for doc in docs:
                kb_data = doc.to_dict()
                knowledge_bases.append(KnowledgeBaseEntry(**kb_data))
            
            return knowledge_bases
            
        except Exception as e:
            logger.error(f"獲取知識庫列表失敗: {e}")
            return []
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """刪除知識庫"""
        try:
            # 刪除主記錄
            self.db.collection(self.collection_name).document(kb_id).delete()
            
            # 刪除相關的文本塊
            chunks_collection = self.db.collection(f'kb_chunks_{kb_id}')
            docs = chunks_collection.stream()
            
            batch = self.db.batch()
            for doc in docs:
                batch.delete(doc.reference)
            batch.commit()
            
            logger.info(f"刪除知識庫: {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"刪除知識庫失敗: {e}")
            return False
