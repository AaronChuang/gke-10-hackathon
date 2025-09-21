import asyncio
import os
import logging
import base64
import json
import functions_framework
from google.cloud import firestore_v1 as firestore
from crawler_service import CrawlerService
from knowledge_base import IndexWebsiteRequest

# Cloud Run/Functions environment variables
PROJECT_ID = os.getenv("GCP_PROJECT", "gke-10-hackathon-471902")
LOCATION = "asia-east1"

logging.basicConfig(level=logging.INFO)

# Initialize global clients
db = firestore.AsyncClient(project=PROJECT_ID, database="gke-10-hackathon")
crawler_service = CrawlerService(db=db, project_id=PROJECT_ID, location=LOCATION)

@functions_framework.cloud_event
async def process_pubsub_message(cloud_event):
    """This function is triggered by a Pub/Sub message."""
    try:
        # Decode the Pub/Sub message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
        logging.info(f"Received message: {message_data}")

        # Parse the message content
        request_data = json.loads(message_data)
        request = IndexWebsiteRequest(**request_data)

        logging.info(f"Starting indexing for URL: {request.url}")

        # Trigger the crawling process
        # The function will wait for this to complete
        kb_id = await crawler_service.trigger_crawling_from_event(request.url)

        logging.info(f"Successfully completed indexing for {request.url}, kb_id: {kb_id}")

    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from message: {message_data}, error: {e}")
    except KeyError as e:
        logging.error(f"Missing expected key in Pub/Sub message: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        # Depending on the function's retry policy, this might cause a retry.
        # Consider raising the exception to force a retry if needed.
        raise e