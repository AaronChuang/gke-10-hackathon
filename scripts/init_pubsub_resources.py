#!/usr/bin/env python3
"""
初始化 Pub/Sub 資源腳本 - 創建系統所需的基礎主題和訂閱
"""

import os
import logging
from google.cloud import pubsub_v1
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境變數
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

if not PROJECT_ID:
    raise RuntimeError("必要的環境變數未設定：GCP_PROJECT_ID")

# 初始化客戶端
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

def create_topic_if_not_exists(topic_name: str) -> str:
    """創建主題（如果不存在）"""
    topic_path = publisher.topic_path(PROJECT_ID, topic_name)
    
    try:
        publisher.create_topic(request={"name": topic_path})
        logger.info(f"✅ 創建主題: {topic_name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info(f"ℹ️  主題已存在: {topic_name}")
        else:
            logger.error(f"❌ 創建主題失敗 {topic_name}: {e}")
            raise e
    
    return topic_path

def create_subscription_if_not_exists(topic_path: str, subscription_name: str) -> str:
    """創建訂閱（如果不存在）"""
    subscription_path = subscriber.subscription_path(PROJECT_ID, subscription_name)
    
    try:
        subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
                "ack_deadline_seconds": 60
            }
        )
        logger.info(f"✅ 創建訂閱: {subscription_name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info(f"ℹ️  訂閱已存在: {subscription_name}")
        else:
            logger.error(f"❌ 創建訂閱失敗 {subscription_name}: {e}")
            raise e
    
    return subscription_path

def main():
    """主函數"""
    logger.info("🚀 開始初始化 Pub/Sub 資源...")
    
    # 基礎系統主題和訂閱
    resources = [
        # 代理人註冊表更新
        {
            "topic": "agent-registry-updates",
            "subscriptions": ["agent-registry-updates-sub"]
        },
        # OmniAgent
        {
            "topic": "omni-agent-topic",
            "subscriptions": ["omni-agent-sub"]
        },
        # ProxyAgent
        {
            "topic": "proxy-agent-topic", 
            "subscriptions": ["proxy-agent-sub"]
        },
        # 向後兼容的舊主題
        {
            "topic": "tech-analyst-topic",
            "subscriptions": ["tech-analyst-sub"]
        },
        {
            "topic": "architect-topic",
            "subscriptions": ["architect-sub"]
        },
        {
            "topic": "stylist-topic",
            "subscriptions": ["stylist-sub"]
        }
    ]
    
    try:
        for resource in resources:
            topic_name = resource["topic"]
            subscriptions = resource["subscriptions"]
            
            # 創建主題
            topic_path = create_topic_if_not_exists(topic_name)
            
            # 創建訂閱
            for sub_name in subscriptions:
                create_subscription_if_not_exists(topic_path, sub_name)
        
        logger.info("🎉 Pub/Sub 資源初始化完成！")
        
        # 顯示摘要
        logger.info("\n📋 已創建的資源摘要：")
        for resource in resources:
            logger.info(f"  📢 主題: {resource['topic']}")
            for sub in resource['subscriptions']:
                logger.info(f"    📥 訂閱: {sub}")
        
    except Exception as e:
        logger.error(f"❌ 初始化失敗: {e}")
        raise e

if __name__ == "__main__":
    main()
