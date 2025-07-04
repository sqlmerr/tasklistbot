from bot.db.models import Rule, SecurityRuleType, TaskList


def ensure_user_has_permission(
    tasklist: TaskList, user_id: int, permission: str
) -> bool:
    print(" - ensuring ", tasklist.title, user_id, tasklist.security)
    if tasklist.user.id == user_id:
        print("t")
        return True
    attr: Rule | None = getattr(tasklist.security, permission)
    if not attr:
        print("f")
        return False

    if attr.rule_type == SecurityRuleType.OWNER and tasklist.user.id != user_id:
        print("f")
        return False

    if attr.rule_type == SecurityRuleType.SELECTED and user_id not in attr.users:
        print("f")
        return False

    print("t")
    print(" ----")
    return True
