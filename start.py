from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from database.db import get_user, register_user, update_balance, add_referral_count, get_referrer
from keyboards import main_menu
from config import ADMIN_ID, REFERRAL_REWARD, BOT_USERNAME
from utils.logger import logger

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or str(user_id)

    args = message.text.split()
    referral_id = None
    if len(args) > 1:
        try:
            referral_id = int(args[1])
            if referral_id == user_id:
                referral_id = None
        except ValueError:
            referral_id = None

    existing = await get_user(user_id)

    if existing is None:
        await register_user(user_id, username, referral_id)
        logger.info(f"New user registered: {user_id} (@{username}), referral_id={referral_id}")

        if referral_id:
            referrer = await get_user(referral_id)
            if referrer:
                await update_balance(referral_id, REFERRAL_REWARD, "referral_reward")
                await add_referral_count(referral_id)
                try:
                    await message.bot.send_message(
                        referral_id,
                        f"🎉 Yangi foydalanuvchi @{username} siz orqali qo'shildi!\n"
                        f"💰 +{REFERRAL_REWARD} Space Coin hisobingizga qo'shildi!"
                    )
                except Exception:
                    pass

        await message.answer(
            f"👋 Xush kelibsiz, {message.from_user.first_name}!\n\n"
            f"🚀 <b>Space Coin Bot</b>ga xush kelibsiz!\n"
            f"💰 Space Coin yig'ing, topshiriqlar bajaring va do'stlaringizni taklif qiling!",
            reply_markup=main_menu(user_id),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"👋 Qaytib keldingiz, {message.from_user.first_name}!\n"
            f"💰 Balansingiz: <b>{existing['balance']:,} Space Coin</b>",
            reply_markup=main_menu(user_id),
            parse_mode="HTML"
        )
