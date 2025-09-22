from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import Message, CallbackQuery


class DependenciesMiddleware(BaseMiddleware):
    def __init__(self, db, checker, scheduler):
        self.db = db
        self.checker = checker
        self.scheduler = scheduler

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # Внедряем зависимости в data
        data['db'] = self.db
        data['checker'] = self.checker
        data['scheduler'] = self.scheduler

        return await handler(event, data)