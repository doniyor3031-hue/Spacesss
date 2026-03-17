from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_user, get_user_by_username, get_balance, update_balance
from keyboards import main_menu, back_menu
from utils.logger import logger

router = Router()

class TransferStates(StatesGroup):
    waiting_input = State()

@router.message(F.text == "💸 Coin yuborish")
async def transfer_handler(message: Message, state: FSMContext):
    await state.set_state(TransferStates.waiting_input)
    await message.answer(
        "💸 <b>Coin yuborish</b>\n\n"
        "Format: <code>@username miqdor</code>\n"
        "Misol: <code>@user123 500</code>",
        reply_markup=back_menu(),
        parse_mode="HTML"
    )

@router.message(TransferStates.waiting_input)
async def process_transfer(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu(user_id))
        return

    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("❌ Format noto'g'ri! Misol: <code>@user123 500</code>", parse_mode="HTML")
        return

    username, amount_str = parts
    try:
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Miqdor musbat son bo'lishi kerak.")
        return

    if amount < 10:
        await message.answer("❌ Minimal yuborish miqdori 10 Space Coin.")
        return

    sender_balance = await get_balance(user_id)
    if sender_balance < amount:
        await message.answer(
            f"❌ Balansingiz yetarli emas!\n"
            f"💰 Balansingiz: {sender_balance:,} Space Coin\n"
            f"📤 Yubormoqchi: {amount:,} Space Coin"
        )
        return

    receiver = await get_user_by_username(username)
    if not receiver:
        await message.answer(f"❌ {username} foydalanuvchi topilmadi. Ular botdan foydalanmagandir.")
        return

    receiver_id = receiver["user_id"]
    if receiver_id == user_id:
        await message.answer("❌ O'zingizga coin yubora olmaysiz.")
        return

    await update_balance(user_id, -amount, f"transfer_to_{receiver_id}")
    await update_balance(receiver_id, amount, f"transfer_from_{user_id}")

    await state.clear()
    await message.answer(
        f"✅ {amount:,} Space Coin muvaffaqiyatli yuborildi!\n"
        f"📤 Kimga: {username}",
        reply_markup=main_menu(user_id)
    )

    try:
        sender_username = message.from_user.username or str(user_id)
        await message.bot.send_message(
            receiver_id,
            f"💰 Sizga {amount:,} Space Coin yuborildi!\n"
            f"📥 Kimdan: @{sender_username}"
        )
    except Exception:
        pass

    logger.info(f"Transfer: {user_id} -> {receiver_id}, amount={amount}")
