import uuid
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import TaskCreate, UpdateTask
from app.models import Task

async def create_task(session: AsyncSession, data: TaskCreate) -> Task:
    task = Task(title=data.title, description=data.description)
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task

async def get_task(session: AsyncSession, task_id: uuid.UUID) -> Task | None:
    return await session.get(Task, task_id)

async def list_tasks(session: AsyncSession, *, only_pending: bool=False) -> Sequence[Task]:
    stmt = select(Task).order_by(Task.created_at.desc())
    if only_pending:
        stmt = stmt.where(Task.completed.is_(False))
    res = await session.execute(stmt)
    return res.scalars.all()

async def update_task(session: AsyncSession, task_id: uuid.UUID, data: UpdateTask) ->Task | None:
    task = await session.get(Task, task_id)
    if task is None:
        return None
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(task, field, value)
    await session.flush()
    await session.refresh(task)
    return task

async def delete_task(session: AsyncSession, task_id: uuid.UUID) -> bool:
    task = await session.get(Task, task_id)
    if task is None:
        return False
    await session.delete(task)
    await session.flush()
    return True