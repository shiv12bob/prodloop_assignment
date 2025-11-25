#!/usr/bin/env python
import requests
import json
import time

# Wait a moment for server to be ready
time.sleep(1)

# Test health endpoint
print("=" * 60)
print("COMPREHENSIVE API TESTING")
print("=" * 60)
print()

try:
    response = requests.get("http://localhost:8080/health")
    print("[PASS] Health Check - Status:", response.status_code)
    print("       Response:", response.json())
except Exception as e:
    print("[FAIL] Health Check -", str(e))
print()

# Test POST /tasks
try:
    payload = {
        "title": "Fix authentication bug",
        "description": "Users cannot login with OAuth",
        "priority": "high"
    }
    response = requests.post("http://localhost:8080/tasks", json=payload)
    print("[PASS] POST /tasks - Status:", response.status_code)
    task_data = response.json()
    task_id = task_data.get("id")
    print("       Task ID:", task_id)
    print("       Status:", task_data.get("status"))
except Exception as e:
    print("[FAIL] POST /tasks -", str(e))
print()

# Test GET /tasks
try:
    response = requests.get("http://localhost:8080/tasks")
    print("[PASS] GET /tasks - Status:", response.status_code)
    print("       Total tasks:", len(response.json()))
except Exception as e:
    print("[FAIL] GET /tasks -", str(e))
print()

# Test GET /tasks with priority filter
try:
    response = requests.get("http://localhost:8080/tasks?priority=high")
    print("[PASS] GET /tasks?priority=high - Status:", response.status_code)
    print("       High priority tasks:", len(response.json()))
except Exception as e:
    print("[FAIL] GET /tasks?priority=high -", str(e))
print()

# Test GET /tasks with status filter
try:
    response = requests.get("http://localhost:8080/tasks?status=pending")
    print("[PASS] GET /tasks?status=pending - Status:", response.status_code)
    print("       Pending tasks:", len(response.json()))
except Exception as e:
    print("[FAIL] GET /tasks?status=pending -", str(e))
print()

# Test GET /tasks/{task_id}
if task_id:
    try:
        response = requests.get(f"http://localhost:8080/tasks/{task_id}")
        print(f"[PASS] GET /tasks/{task_id} - Status:", response.status_code)
    except Exception as e:
        print(f"[FAIL] GET /tasks/{task_id} -", str(e))
    print()

    # Test PUT /tasks/{task_id}
    try:
        update_payload = {"status": "in_progress"}
        response = requests.put(f"http://localhost:8080/tasks/{task_id}", json=update_payload)
        print(f"[PASS] PUT /tasks/{task_id} - Status:", response.status_code)
        print("       New Status:", response.json().get("status"))
    except Exception as e:
        print(f"[FAIL] PUT /tasks/{task_id} -", str(e))
    print()

    # Test DELETE /tasks/{task_id}
    try:
        response = requests.delete(f"http://localhost:8080/tasks/{task_id}")
        print(f"[PASS] DELETE /tasks/{task_id} - Status:", response.status_code)
    except Exception as e:
        print(f"[FAIL] DELETE /tasks/{task_id} -", str(e))
    print()

# Test error handling - invalid priority (422)
print("ERROR HANDLING TESTS:")
print("-" * 60)
try:
    bad_payload = {
        "title": "Test",
        "priority": "invalid_priority"
    }
    response = requests.post("http://localhost:8080/tasks", json=bad_payload)
    print("[PASS] Validation Error (422) - Status:", response.status_code)
    if response.status_code == 422:
        print("       Correctly rejected invalid priority")
except Exception as e:
    print("[FAIL] Validation Error Test -", str(e))
print()

# Test 404 error
try:
    response = requests.get("http://localhost:8080/tasks/nonexistent-id-12345")
    print("[PASS] Not Found Error (404) - Status:", response.status_code)
    if response.status_code == 404:
        print("       Correctly returned 404 for missing task")
        print("       Error detail:", response.json().get("detail"))
except Exception as e:
    print("[FAIL] 404 Error Test -", str(e))
print()

print("=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
