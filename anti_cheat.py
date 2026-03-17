from aiogram import BaseMiddleware
from aiogram.types import Message
from collections import defaultdict
import time
from database.db import is_banned, log_anti_cheat
from utils.logger import logger

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_last_action = defaultdict(float)
        self.user_action_count = defaultdict(int)
        self.user_window_start = defaultdict(float)

    async def __call__(self, handler, event, data):
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return await handler(event, data)

        if await is_banned(user_id):
            await event.answer("🚫 Siz botdan ban qilingansiz.")
            return

        now = time.time()
        window = 10
        if now - self.user_window_start[user_id] > window:
            self.user_window_start[user_id] = now
            self.user_action_count[user_id] = 0

        self.user_action_count[user_id] += 1
        if self.user_action_count[user_id] > 20:
            logger.warning(f"[ANTI-CHEAT] Rapid actions from {user_id}")
            await log_anti_cheat(user_id, "rapid_actions", f"count={self.user_action_count[user_id]}")
            await event.answer("⚠️ Juda tez harakat qilyapsiz. Biroz kuting.")
            return

        elapsed = now - self.user_last_action[user_id]
        if elapsed < self.rate_limit:
            return

        self.user_last_action[user_id] = now
        return await handler(event, data)
