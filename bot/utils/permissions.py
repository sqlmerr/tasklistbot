from bot.db.models import Rule, SecurityRuleType, TaskList


def ensure_user_has_permission(
    tasklist: TaskList, user_id: int, permission: str
) -> bool:
    if tasklist.user.user_id == user_id:
        return True
    attr: Rule | None = getattr(tasklist.security, permission)
    if not attr:
        return False

    if attr.rule_type == SecurityRuleType.OWNER and tasklist.user.id != user_id:
        return False

    if attr.rule_type == SecurityRuleType.SELECTED and user_id not in attr.users:
        return False

    return True
