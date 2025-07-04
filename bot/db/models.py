from beanie import Document, Indexed, Link
from typing import Annotated, ClassVar, TypeAlias

from enum import StrEnum, auto

from pydantic import BaseModel, Field


class User(Document):
    user_id: Annotated[int, Indexed(unique=True)]


class TaskOption(BaseModel):
    name: str
    completed: bool = False


class SecurityRuleType(StrEnum):
    EVERYONE = auto()
    SELECTED = auto()
    OWNER = auto()


SecurityRuleTypes = [
    SecurityRuleType.EVERYONE,
    SecurityRuleType.SELECTED,
    SecurityRuleType.OWNER,
]


class SecurityRule(BaseModel):
    rule_type: SecurityRuleType = SecurityRuleType.OWNER
    users: list[int] | None = None

Rule: TypeAlias = SecurityRule

class TaskListSecurity(BaseModel):
    read: Rule = SecurityRule(rule_type=SecurityRuleType.EVERYONE)
    mark_tasks_as_completed: Rule = SecurityRule(rule_type=SecurityRuleType.OWNER)
    add_new_tasks: Rule = SecurityRule(rule_type=SecurityRuleType.OWNER)
    edit_tasks: Rule = SecurityRule(rule_type=SecurityRuleType.OWNER)
    delete_tasks: Rule = SecurityRule(rule_type=SecurityRuleType.OWNER)


SecurityPermissions = tuple(TaskListSecurity().__dict__.keys())


class TaskList(Document):
    title: str
    user: Link[User]
    options: list[TaskOption]
    security: TaskListSecurity = Field(default=TaskListSecurity())
