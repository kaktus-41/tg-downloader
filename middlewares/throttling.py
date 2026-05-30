import time
from collections import defaultdict
from aiogram import BaseMiddleware
from aiogram.types import Message

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=3, window=60):
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)

    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            user_id = event.from_user.id
            now = time.time()
            reqs = [t for t in self.requests[user_id] if now - t < self.window]
            self.requests[user_id] = reqs
            if len(reqs) >= self.limit:
                await event.answer("⛔️ Слишком много запросов! Подожди минуту.")
                return
            self.requests[user_id].append(now)
        return await handler(event, data)
