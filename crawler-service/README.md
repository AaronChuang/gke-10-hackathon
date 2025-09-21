# Crawler Service

## Overview

This service is designed to crawl websites, extract their content, and build a knowledge base using Google Cloud's Vertex AI for Retrieval-Augmented Generation (RAG). It provides a simple API endpoint to initiate the indexing process for a given URL.

## Features

- **Asynchronous Web Crawling**: Concurrently crawls a website starting from a given URL, respecting a configurable page limit.
- **Content Extraction**: Extracts clean, meaningful text content from HTML pages by stripping out scripts, styles, and common navigation elements.
- **Vector Indexing**: Splits the extracted content into chunks, generates embeddings using Vertex AI's embedding models, and upserts them into a Vector Search index.
- **Background Processing**: All crawling and indexing tasks are run in the background, allowing the API to respond immediately.
- **Status Tracking**: The status of each indexing job (e.g., `QUEUED`, `CRAWLING`, `INDEXING`, `ACTIVE`, `FAILED`) is tracked in Firestore.

## API Endpoint

### `POST /index`

Initiates the crawling and indexing process for a website.

**Request Body:**

```json
{
  "url": "https://example.com"
}
```

**Success Response (202 Accepted):**

```json
{
  "message": "Knowledge base indexing task has been successfully queued. You can track the progress on the dashboard.",
  "kb_id": "kb_example_com_1678886400",
  "dashboard_url": "https://console.cloud.google.com/firestore/databases/(default)/data/documents/knowledge_base/kb_example_com_1678886400?project=your-gcp-project-id"
}
```

## Environment Setup

This service requires a Google Cloud project with the following APIs enabled:

- Vertex AI API
- Firestore API

Set the following environment variable to specify your Google Cloud project ID:

```bash
export GCP_PROJECT="your-gcp-project-id"
```

## How to Run Locally

1.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

2.  **Authenticate with Google Cloud**:

    Make sure you have the `gcloud` CLI installed and authenticated:

    ```bash
    gcloud auth application-default login
    ```

3.  **Run the Service**:

    The application is served using Gunicorn and Uvicorn.

    ```bash
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080 main:app
    ```

The service will be available at `http://localhost:8080`.
