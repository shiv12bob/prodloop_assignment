# System Architecture

> **Enterprise-Grade Microservices Architecture** with Event-Driven Design

## 🏗️ High-Level Architecture

```
┌─────────────────┐
│   REST Clients  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        FastAPI Application (Cloud Run)  │
│  ┌───────────────────────────────────┐  │
│  │  Global Exception Handlers        │  │
│  │  - 404 Not Found                  │  │
│  │  - 422 Validation Error           │  │
│  │  - 500 Internal Server Error      │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Task Routes                      │  │
│  │  - POST /tasks                    │  │
│  │  - GET /tasks                     │  │
│  │  - GET /tasks/{id}                │  │
│  │  - PUT /tasks/{id}                │  │
│  │  - DELETE /tasks/{id}             │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  In-Memory Storage                │  │
│  │  TASK_STORE = {}                  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Event Publisher                  │  │
│  │  - Pub/Sub Integration            │  │
│  │  - Fallback Logging               │  │
│  └───────────────────────────────────┘  │
└─────────────┬──────────────────────────┘
              │
              │ (event: task.created)
              ▼
┌─────────────────────────────────────┐
│   Google Cloud Pub/Sub Topic        │
│   (task-events)                     │
└──────────┬────────────────────────────┘
           │
           │ (automatic trigger)
           ▼
┌─────────────────────────────────────┐
│   Cloud Function                    │
│   (task-subscriber)                 │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Event Logging               │    │
│  │ - Log task details          │    │
│  │ - Track event timestamp     │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ Gemini 2.5 Flash            │    │
│  │ - Summary generation        │    │
│  │ - Sub-task suggestions      │    │
│  │ - Task categorization       │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ Error Handling & Fallback   │    │
│  │ - Graceful degradation      │    │
│  │ - Heuristic categorization  │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
           │
           ▼
    [Cloud Logging]
```

---

## 📦 Component Details

### 1. FastAPI Application (`app/main.py`)

**Responsibilities:**
- Handle HTTP requests/responses
- Apply global exception handlers
- Manage application lifecycle

**Features:**
- ✅ Exception handler for 422 (Validation errors)
- ✅ Exception handler for 500 (Server errors)
- ✅ Metadata: title, description, version
- ✅ Auto-generated documentation

**Status Codes:**
- `200 OK` - Successful GET/PUT
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Validation failed
- `500 Internal Server Error` - Unexpected error

---

### 2. Route Handler (`app/routes/tasks.py`)

**Endpoints:**

#### `POST /tasks` - Create Task
```
Input:  TaskCreate { title, description, priority }
Output: Task { id, title, description, priority, status, created_at }
Status: 201 Created
Events: Publishes task.created event to Pub/Sub
```

#### `GET /tasks` - List Tasks
```
Query:  ?priority=high|medium|low
        ?status=pending|in_progress|completed
Output: List[Task]
Status: 200 OK
```

#### `GET /tasks/{task_id}` - Get Task
```
Output: Task or HTTPException(404)
Status: 200 OK / 404 Not Found
```

#### `PUT /tasks/{task_id}` - Update Task
```
Input:  TaskUpdate { status }
Output: Updated Task
Status: 200 OK / 404 Not Found
```

#### `DELETE /tasks/{task_id}` - Delete Task
```
Output: None
Status: 204 No Content / 404 Not Found
```

---

### 3. Data Models (`app/models.py`)

**Pydantic Models:**

```python
Priority = Literal["low", "medium", "high"]
Status = Literal["pending", "in_progress", "completed"]

class TaskCreate(BaseModel):
    title: str              # Required, min 1 character
    description: Optional[str] = ""
    priority: Priority = "low"

class TaskUpdate(BaseModel):
    status: Status          # Required, enum validated

class Task(BaseModel):
    id: str                 # UUID generated
    title: str
    description: Optional[str]
    priority: Priority
    status: Status = "pending"
    created_at: datetime    # ISO8601 format
```

**Validation:**
- Required fields enforced
- Enum values validated
- Type hints enforced
- Field constraints verified

---

### 4. In-Memory Storage

**Implementation:**
```python
TASK_STORE: Dict[str, Task] = {}
```

**Characteristics:**
- Fast (O(1) lookup)
- Resets on restart
- Not persistent
- Single-threaded safe (uvicorn handles concurrency)

**Lifecycle:**
1. Task created → stored with UUID
2. Task retrieved → O(1) dict lookup
3. Task updated → dict value replaced
4. Task deleted → dict entry removed

---

### 5. Event Publishing (`app/pubsub_publisher.py`)

**Event Schema:**
```json
{
  "event_type": "task.created",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "title": "Fix bug",
    "description": "OAuth issue",
    "priority": "high"
  }
}
```

**Publishing Flow:**
1. Task created via POST /tasks
2. Task object created with UUID and timestamp
3. Event schema constructed
4. `publish_event()` called
5. Google Cloud Pub/Sub publishes event
6. If Pub/Sub unavailable, logs to `/tmp/pubsub_events.log`

**Error Handling:**
```
Success → Log message ID
Failure → Log to file + stdout
Missing Config → Silent logging
```

---

### 6. Cloud Function (`cloud_function/subscriber.py`)

**Trigger:** Pub/Sub topic `task-events`

**Processing Flow:**
```
1. Receive Pub/Sub message
   ├─ Decode base64 payload
   └─ Parse JSON

2. Validate event type
   └─ Only process task.created

3. Extract task data
   ├─ title
   ├─ description
   └─ priority

4. Call Gemini 2.5 Flash
   ├─ Send prompt
   ├─ Parse response
   └─ Handle errors

5. Log results
   ├─ Summary
   ├─ Sub-tasks
   └─ Category
```

**Gemini Integration:**

```
Prompt: "Analyze the task and provide:
1. One-sentence summary
2. 3-5 sub-tasks
3. Category classification"

Response: {
  "summary": "...",
  "subtasks": ["...", "...", "..."],
  "category": "Bug Fix|Feature|DevOps|Documentation|Other"
}
```

**Error Handling:**
- API key missing → Fallback heuristics
- API timeout → Retry logic + fallback
- Invalid response → Parse JSON safely
- Connection failed → Log and continue

---

### 7. Docker Container

**Base Image:** `python:3.11-slim`

**Optimization:**
- Multi-stage build support
- Minimal dependencies
- Efficient caching layers

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### 8. GitHub Actions CI/CD

**Workflow:** `.github/workflows/deploy.yml`

**Pipeline Stages:**

1. **Checkout** - Clone repository
2. **Setup GCloud** - Configure GCP credentials
3. **Docker Auth** - Authenticate to Artifact Registry
4. **Build & Push** - Build image and push to registry
5. **Deploy** - Deploy to Cloud Run with env vars

**Secrets Used:**
- `GCP_SA_KEY` - Service account JSON
- `GCP_PROJECT` - Project ID
- `GCP_REGION` - Deployment region
- `ARTIFACT_REGISTRY_REPO` - Registry repository
- `CLOUD_RUN_SERVICE` - Cloud Run service name
- `PUBSUB_TOPIC` - Pub/Sub topic path
- `GEMINI_API_KEY` - Gemini API key
- `GEMINI_API_URL` - Gemini endpoint

---

## 🔄 Data Flow

### Task Creation Flow

```
Client
  │
  ├─→ POST /tasks
  │    └─→ Validate request (TaskCreate model)
  │         ├─ Success: Generate UUID, timestamp
  │         └─ Failure: Return 422
  │
  ├─→ Store in TASK_STORE
  │
  ├─→ Publish event to Pub/Sub
  │    ├─ Success: Async in background
  │    └─ Failure: Log to file
  │
  └─→ Return 201 + Task object
      └─→ Client receives task with ID
```

### Task Processing Flow (Cloud Function)

```
Pub/Sub
  │
  ├─→ Trigger Cloud Function
  │
  ├─→ Decode and validate event
  │    ├─ Success: Extract data
  │    └─ Failure: Log error
  │
  ├─→ Call Gemini API
  │    ├─ Success: Parse response
  │    │   └─ Log: summary, subtasks, category
  │    └─ Failure: Use fallback heuristics
  │         └─ Log: default values
  │
  └─→ Cloud Logging
       └─ Visible in Cloud Console
```

---

## 🔐 Security Architecture

### Input Validation
- Pydantic model validation on all endpoints
- Type checking enforced
- Required fields validated
- Enum values restricted

### Error Handling
- No sensitive data in error responses
- Stack traces hidden from clients
- Proper HTTP status codes
- Descriptive error messages

### Secrets Management
- Environment variables for all secrets
- No hardcoded credentials
- GitHub Actions secrets encryption
- Service account file only in deployment

### Network Security
- HTTPS in Cloud Run (automatic)
- Service account permissions scoped
- Pub/Sub ACLs enforced
- Function-level authentication

---

## 📊 Performance Characteristics

### Time Complexity
- Task creation: O(1) - dict insert
- Task retrieval: O(1) - dict lookup
- Task listing: O(n) - iterate all tasks
- Task filtering: O(n) - iterate and filter
- Task update: O(1) - dict update
- Task delete: O(1) - dict delete

### Space Complexity
- Per task: O(1) - fixed fields
- Total: O(n) - number of tasks

### API Response Times
- Average: < 100ms (local)
- Cold start: < 500ms (Cloud Run first request)
- Subsequent: < 100ms

### Scalability
- Stateless API (horizontal scaling)
- Event-driven processing (decoupled)
- Auto-scaling Cloud Run enabled
- Pub/Sub handles throughput

---

## 🔄 Deployment Architecture

### Local Development
```
Developer Machine
  ├─ Python venv
  ├─ FastAPI server (port 8080)
  ├─ In-memory storage
  └─ Mock Pub/Sub (file logging)
```

### Cloud Deployment
```
GCP Project
  ├─ Cloud Run
  │  ├─ FastAPI container
  │  ├─ Auto-scaling
  │  └─ Load balancing
  │
  ├─ Pub/Sub Topic
  │  ├─ task-events
  │  └─ Subscriptions
  │
  ├─ Cloud Function
  │  ├─ Python 3.11 runtime
  │  ├─ Gemini integration
  │  └─ Auto-trigger on events
  │
  ├─ Cloud Logging
  │  ├─ API logs
  │  ├─ Function logs
  │  └─ Performance metrics
  │
  └─ Artifact Registry
     └─ Docker images
```

---

## 🧪 Testing Strategy

### Unit Testing
- Model validation tests
- Route handler tests
- Error handling tests

### Integration Testing
- End-to-end API tests
- Event publishing tests
- Pub/Sub integration tests

### Performance Testing
- Response time benchmarks
- Load testing
- Concurrent request handling

---

## 📈 Monitoring & Observability

### Application Metrics
- Request count
- Response time distribution
- Error rate
- Task count

### Cloud Logging
- All API requests logged
- All errors logged with stack trace
- Pub/Sub events tracked
- Cloud Function execution logged

### Alerts
- 500 error rate > 5%
- Response time > 1s (p99)
- Cloud Function timeout
- Pub/Sub delivery failures

---

## 🎯 Design Patterns

### 1. Dependency Injection
- Router receives components
- Easy to test and mock
- Separation of concerns

### 2. Error Handling
- Global exception handlers
- Graceful degradation
- Fallback mechanisms

### 3. Event-Driven
- Asynchronous processing
- Loose coupling
- Scalable architecture

### 4. Configuration Management
- Environment variables
- No hardcoded secrets
- Environment-specific configs

---

## 🚀 Scaling Considerations

### Vertical Scaling
- Increase Cloud Run memory
- Increase Cloud Function timeout
- More CPU for processing

### Horizontal Scaling
- Cloud Run auto-scaling enabled
- Multiple function instances
- Pub/Sub distributes load

### Data Persistence
- Current: In-memory only
- Future: Database integration
- Migrate TASK_STORE to persistence layer

---

## 🔮 Future Enhancements

1. **Database Integration**
   - Replace in-memory storage
   - Add persistence layer
   - Implement migrations

2. **Authentication**
   - API key authentication
   - OAuth2 integration
   - Role-based access control

3. **Caching**
   - Redis integration
   - Query result caching
   - Improved performance

4. **Analytics**
   - Task statistics
   - Performance metrics
   - User analytics

5. **Rate Limiting**
   - Per-user limits
   - DDoS protection
   - Fair resource allocation

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Pub/Sub](https://cloud.google.com/pubsub/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Functions Documentation](https://cloud.google.com/functions/docs)
- [Gemini API Documentation](https://ai.google.dev/)
