import json
from cloud_function import subscriber

def run_sample():
    with open("cloud_function/sample_event.json") as f:
        data = json.load(f)
    # Simulate Pub/Sub envelope: base64 encode data
    import base64
    payload = base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
    event = {"data": payload}
    result = subscriber.pubsub_handler(event, None)
    print("Result:", result)

if __name__ == "__main__":
    run_sample()
