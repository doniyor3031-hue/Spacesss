import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_active_contest, join_contest
from keyboards import contest_keyboard, main_menu
from utils.logger import logger

router = Router()

@router.message(F.text == "🎉 Konkurs")
async def contest_handler(message: Message):
    user_id = message.from_user.id
    contest = await get_active_contest()

    if not contest:
        await message.answer(
            "🎉 <b>Konkurs</b>\n\nHozirda faol konkurs yo'q.",
            parse_mode="HTML"
        )
        return

    channels = json.loads(contest.get("channels") or "[]")
    text = (
        f"🎉 <b>Konkurs!</b>\n\n"
        f"{contest['post_text']}\n\n"
        f"Ishtirok etish uchun quyidagi kanallarga obuna bo'ling va <b>Tekshirish</b> tugmasini bosing."
    )
    await message.answer(
        text,
        reply_markup=contest_keyboard(contest["contest_id"], channels),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("check_contest_"))
async def check_contest(call: CallbackQuery):
    user_id = call.from_user.id
    contest_id = int(call.data.split("_")[2])

    from database.db import get_contest
    contest = await get_contest(contest_id)
    if not contest:
        await call.answer("Konkurs topilmadi.", show_alert=True)
        return

    channels = json.loads(contest.get("channels") or "[]")

    not_subscribed = []
    for channel in channels:
        ch_username = channel.lstrip("@")
        try:
            member = await call.bot.get_chat_member(f"@{ch_username}", user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(channel)
        except Exception as e:
            logger.warning(f"Error checking {channel} for user {user_id}: {e}")
            not_subscribed.append(channel)

    if not_subscribed:
        channels_text = "\n".join(not_subscribed)
        await call.answer(
            f"❌ Siz quyidagi kanallarga obuna emassiz:\n{channels_text}",
            show_alert=True
        )
        return

    username = call.from_user.username or str(user_id)
    joined = await join_contest(contest_id, user_id, username)

    if joined:
        await call.answer(
            "✅ Siz muvaffaqiyatli konkursga qo'shildingiz!",
            show_alert=True
        )
        logger.info(f"User {user_id} joined contest {contest_id}")
    else:
        await call.answer(
            "ℹ️ Siz allaqachon bu konkursda qatnashmoqdasiz.",
            show_alert=True
        )
