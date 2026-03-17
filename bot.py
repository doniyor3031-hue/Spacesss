import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from database.db import init_db
from middlewares.anti_cheat import RateLimitMiddleware
from utils.logger import logger
import state

from handlers import (
    start,
    profile,
    bonus,
    tasks,
    payment,
    transfer,
    referral,
    promo,
    contest,
    admin,
    broadcast,
    nav,
)

async def main():
    logger.info("Starting Space Coin Bot...")

    await init_db()
    logger.info("Database initialized.")

    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(RateLimitMiddleware(rate_limit=0.3))

    dp.include_router(start.router)
    dp.include_router(nav.router)
    dp.include_router(profile.router)
    dp.include_router(bonus.router)
    dp.include_router(tasks.router)
    dp.include_router(payment.router)
    dp.include_router(transfer.router)
    dp.include_router(referral.router)
    dp.include_router(promo.router)
    dp.include_router(contest.router)
    dp.include_router(broadcast.router)
    dp.include_router(admin.router)

    me = await bot.get_me()
    state.BOT_USERNAME = me.username
    logger.info(f"Bot started: @{me.username}")

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())
