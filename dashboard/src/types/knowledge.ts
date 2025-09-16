export interface KnowledgeEntry {
  kb_id: string
  url: string
  status: KnowledgeStatus
  created_at: number
  updated_at: number
  indexed_pages: number
  total_pages: number
  error_message: string | null
  metadata: Record<string, any>
}

export type KnowledgeStatus = 
  | 'QUEUED'
  | 'CRAWLING'
  | 'INDEXING'
  | 'ACTIVE'
  | 'FAILED'

export interface IndexWebsiteRequest {
  url: string
}

export interface KnowledgeTableRow {
  id: string
  url: string
  status: KnowledgeStatus
  indexedPages: number
  totalPages: number
  createdAt: string
  isActive: boolean
  errorMessage?: string
}
