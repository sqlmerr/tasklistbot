from beanie import PydanticObjectId
from .models import TaskList, User


async def get_user(user_id: int) -> User | None:
    return await User.find_one(User.user_id == user_id)


async def get_task_lists_by_user(user_id: PydanticObjectId) -> list[TaskList]:
    return await TaskList.find_many(
        TaskList.user.id == user_id, fetch_links=True
    ).to_list()
