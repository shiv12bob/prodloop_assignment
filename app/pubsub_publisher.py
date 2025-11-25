import os, json, time
from google.cloud import pubsub_v1
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC")  # expected full path: projects/PROJECT/topics/TOPIC_NAME

# Simple fallback logger when Pub/Sub is not configured
def publish_event(event: Dict):
    if not GCP_PROJECT_ID or not PUBSUB_TOPIC:
        # Fallback: log to /tmp/pubsub_events.log and stdout
        try:
            with open('/tmp/pubsub_events.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass
        print("PUBSUB (mock) - event:", json.dumps(event))
        return None

    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = PUBSUB_TOPIC
        data = json.dumps(event).encode('utf-8')
        future = publisher.publish(topic_path, data=data)
        result = future.result(timeout=10)
        print(f"Published message id: {result}")
        return result
    except Exception as e:
        print("Failed to publish to Pub/Sub:", e)
        # also write locally
        try:
            with open('/tmp/pubsub_events.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"error": str(e), "event": event}) + "\n")
        except Exception:
            pass
        return None
