import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    description: str |None = Field(default=None, max_length=2000)

class UpdateTask(BaseModel):
    title: str = Field(default=None, min_length=1, max_length=250)
    description: str |None = Field(default=None, max_length=2000)
    completed: bool |None = None

class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    updated_at: datetime