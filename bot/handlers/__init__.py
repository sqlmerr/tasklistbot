from aiogram import Router
from . import basic, view


def register_routers() -> Router:
    router = Router()

    router.include_routers(basic.router, view.router)

    return router
