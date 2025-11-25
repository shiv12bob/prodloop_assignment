from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.models import TaskCreate, Task, TaskUpdate
from app import pubsub_publisher
from datetime import datetime

router = APIRouter()

# In-memory store
TASK_STORE = {}

@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate):
    task = Task.new_from_create(payload)
    TASK_STORE[task.id] = task
    # Publish event
    event = {
        "event_type": "task.created",
        "task_id": task.id,
        "timestamp": task.created_at.isoformat() + "Z",
        "data": {
            "title": task.title,
            "description": task.description,
            "priority": task.priority
        }
    }
    pubsub_publisher.publish_event(event)
    return task

@router.get("", response_model=List[Task])
async def list_tasks(priority: Optional[str] = None, status: Optional[str] = None):
    tasks = list(TASK_STORE.values())
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if status:
        tasks = [t for t in tasks if t.status == status]
    return tasks

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, payload: TaskUpdate):
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = payload.status
    TASK_STORE[task_id] = task
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    task = TASK_STORE.pop(task_id, None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
