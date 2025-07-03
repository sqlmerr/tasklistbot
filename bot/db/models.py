from beanie import Document, Indexed, Link
from typing import Annotated

from pydantic import BaseModel


class User(Document):
    user_id: Annotated[int, Indexed(unique=True)]


class TaskOption(BaseModel):
    name: str
    completed: bool = False


class TaskList(Document):
    title: str
    user: Link[User]
    options: list[TaskOption]
