from aiogram import Router, F
from aiogram.types import Message
from database.db import get_user
from keyboards import profile_menu, main_menu
from config import ADMIN_ID

router = Router()

@router.message(F.text == "👤 Profil")
async def profile_handler(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        await message.answer("Iltimos /start bosing.")
        return

    text = (
        f"👤 <b>Profil</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"👤 Username: @{user['username'] or 'yoq'}\n"
        f"💰 Balans: <b>{user['balance']:,} Space Coin</b>\n"
        f"👥 Referallar: <b>{user['referrals_count']}</b>\n"
        f"📅 Ro'yxatdan o'tgan: {user['joined_at'][:10]}\n"
    )
    await message.answer(text, reply_markup=profile_menu(), parse_mode="HTML")
