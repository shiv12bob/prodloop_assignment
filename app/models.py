from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

Priority = Literal["low", "medium", "high"]
Status = Literal["pending", "in_progress", "completed"]

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    priority: Priority = "low"

class TaskUpdate(BaseModel):
    status: Status

class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    priority: Priority
    status: Status = "pending"
    created_at: datetime

    @staticmethod
    def new_from_create(payload: TaskCreate) -> "Task":
        return Task(
            id=str(uuid.uuid4()),
            title=payload.title,
            description=payload.description or "",
            priority=payload.priority,
            status="pending",
            created_at=datetime.utcnow()
        )
