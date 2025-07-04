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
    rule_type: ClassVar[SecurityRuleType]


class EveryoneRule(SecurityRule):
    rule_type = SecurityRuleType.EVERYONE


class SelectedRule(SecurityRule):
    rule_type = SecurityRuleType.SELECTED
    users: list[int]


class OwnerRule(SecurityRule):
    rule_type = SecurityRuleType.OWNER


Rule: TypeAlias = EveryoneRule | SelectedRule | OwnerRule


class TaskListSecurity(BaseModel):
    read: Rule = EveryoneRule()
    mark_tasks_as_completed: Rule = OwnerRule()
    add_new_tasks: Rule = OwnerRule()
    edit_tasks: Rule = OwnerRule()
    delete_tasks: Rule = OwnerRule()


SecurityPermissions = tuple(TaskListSecurity().__dict__.keys())


class TaskList(Document):
    title: str
    user: Link[User]
    options: list[TaskOption]
    security: TaskListSecurity = Field(default=TaskListSecurity())
