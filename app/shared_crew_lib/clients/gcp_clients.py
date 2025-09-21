import os
import logging
from google.cloud import pubsub_v1, firestore

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_FIRESTORE_NAME = os.getenv("GCP_FIRESTORE_NAME")

publisher = None
subscriber = None
db = None

def initialize_gcp_clients():
    global publisher, subscriber, db
    
    if not PROJECT_ID:
        error_msg = "GCP_PROJECT_ID environment variable is required but not set"
        logger.error(error_msg)
        logger.error("Please set GCP_PROJECT_ID in your .env file or environment")
        raise ValueError(error_msg)
    try:
        logger.info(f"Initializing GCP clients for project: {PROJECT_ID}")
        
        publisher = pubsub_v1.PublisherClient()
        subscriber = pubsub_v1.SubscriberClient()
        logger.info("Successfully initialized Pub/Sub clients")
        
        if GCP_FIRESTORE_NAME:
            logger.info(f"Using Firestore database: {GCP_FIRESTORE_NAME}")
            db = firestore.Client(project=PROJECT_ID, database=GCP_FIRESTORE_NAME)
        else:
            logger.info("Using default Firestore database")
            db = firestore.Client(project=PROJECT_ID)
        
        try:
            collections = list(db.collections())
            logger.info("Successfully connected to Firestore")
        except Exception as test_e:
            logger.warning(f"Firestore connection test failed, but client initialized: {test_e}")
        
        logger.info("GCP clients initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing GCP clients: {e}")
        logger.error(f"Project ID: {PROJECT_ID}")
        logger.error(f"Firestore DB: {GCP_FIRESTORE_NAME or 'default'}")
        raise

def get_firestore_client():
    if db is None:
        logger.warning("Firestore client not initialized, attempting to initialize...")
        initialize_gcp_clients()
    return db

def get_publisher_client():
    if publisher is None:
        logger.warning("Publisher client not initialized, attempting to initialize...")
        initialize_gcp_clients()
    return publisher

def get_subscriber_client():
    if subscriber is None:
        logger.warning("Subscriber client not initialized, attempting to initialize...")
        initialize_gcp_clients()
    return subscriber

try:
    initialize_gcp_clients()
    logger.info("GCP clients initialized successfully on module load")
except Exception as e:
    logger.warning(f"Failed to initialize GCP clients on module load: {e}")
    logger.warning("Clients will be initialized on first use")
