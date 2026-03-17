from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import get_user
from keyboards import main_menu
from config import REFERRAL_REWARD
import state

router = Router()

@router.message(F.text == "👥 Referral")
async def referral_handler(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        await message.answer("Iltimos /start bosing.")
        return

    bot_username = state.BOT_USERNAME
    link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        f"👥 <b>Referral tizimi</b>\n\n"
        f"💰 Siz har bir taklif uchun <b>{REFERRAL_REWARD} Space Coin</b> olasiz!\n\n"
        f"👤 Sizning referallaringiz: <b>{user['referrals_count']}</b>\n"
        f"💵 Jami topgan: <b>{user['referrals_count'] * REFERRAL_REWARD:,} Space Coin</b>\n\n"
        f"🔗 Havolangizni do'stlaringizga yuboring:"
    )
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Referal havolam", url=link)]
    ])
    await message.answer(text, reply_markup=inline_kb, parse_mode="HTML")
