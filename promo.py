from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_balance, update_balance, create_order, get_user
from keyboards import main_menu, back_menu
from config import PROMO_COST, PROMO_TARGET
from utils.logger import logger

router = Router()

class PromoStates(StatesGroup):
    waiting_channel = State()

@router.message(F.text == "📢 Kanal reklama")
async def promo_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    balance = await get_balance(user_id)

    await state.set_state(PromoStates.waiting_channel)
    text = (
        f"📢 <b>Kanal reklama</b>\n\n"
        f"💰 Narxi: <b>{PROMO_COST} Space Coin</b>\n"
        f"👥 Maqsad: <b>{PROMO_TARGET} obunachilar</b>\n\n"
        f"📊 Balansingiz: <b>{balance:,} Space Coin</b>\n\n"
        f"Kanalingiz @username ini kiriting (masalan: @mychannelname):"
    )
    await message.answer(text, reply_markup=back_menu(), parse_mode="HTML")

@router.message(PromoStates.waiting_channel)
async def process_promo_channel(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu(user_id))
        return

    channel = message.text.strip()
    if not channel.startswith("@"):
        channel = "@" + channel

    balance = await get_balance(user_id)
    if balance < PROMO_COST:
        await state.clear()
        await message.answer(
            f"❌ Balansingiz yetarli emas!\n"
            f"💰 Kerak: {PROMO_COST} Space Coin\n"
            f"💳 Sizda: {balance:,} Space Coin",
            reply_markup=main_menu(user_id)
        )
        return

    try:
        ch_username = channel.lstrip("@")
        bot_member = await message.bot.get_chat_member(f"@{ch_username}", (await message.bot.get_me()).id)
        if bot_member.status not in ("administrator", "creator"):
            await state.clear()
            await message.answer(
                f"❌ Bot {channel} kanaliga admin sifatida qo'shilmagan!\n"
                f"Botni admin qilib qo'shing va qayta urinib ko'ring.",
                reply_markup=main_menu(user_id)
            )
            return
    except Exception as e:
        logger.warning(f"Channel check failed for {channel}: {e}")
        await state.clear()
        await message.answer(
            f"⚠️ {channel} kanalini tekshirib bo'lmadi.\n"
            f"Kanal mavjudligini va bot admin ekanligini tekshiring.",
            reply_markup=main_menu(user_id)
        )
        return

    await update_balance(user_id, -PROMO_COST, f"promo_{channel}")
    order_id = await create_order(channel, user_id)

    await state.clear()
    await message.answer(
        f"✅ Reklama buyurtmasi qabul qilindi!\n\n"
        f"📢 Kanal: {channel}\n"
        f"🆔 Buyurtma ID: #{order_id}\n"
        f"👥 Maqsad: {PROMO_TARGET} obunachilar\n\n"
        f"Vazifalar bo'limida buyurtmangiz ko'rinadi va foydalanuvchilar obuna bo'lishlari mumkin!",
        reply_markup=main_menu(user_id)
    )
    logger.info(f"Promo order #{order_id} created by user {user_id}, channel={channel}")
