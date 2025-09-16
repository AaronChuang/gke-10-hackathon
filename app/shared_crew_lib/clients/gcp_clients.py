import os
from google.cloud import pubsub_v1, firestore

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gcp-project-id")
GCP_FIRESTORE_NAME = os.getenv("GCP_FIRESTORE_NAME", "gcp-firestore-name")

# 初始化客戶端，使其在應用程式中可以被重複使用 (Singleton-like)
try:
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    db = firestore.Client(project=PROJECT_ID, database=GCP_FIRESTORE_NAME)
    print("Successfully initialized GCP clients.")
except Exception as e:
    print(f"Error initializing GCP clients: {e}")
    publisher = None
    subscriber = None
    db = None

def get_firestore_client():
    """返回 Firestore 客戶端實例"""
    return db

def get_publisher_client():
    """返回 Pub/Sub Publisher 客戶端實例"""
    return publisher

def get_subscriber_client():
    """返回 Pub/Sub Subscriber 客戶端實例"""
    return subscriber
