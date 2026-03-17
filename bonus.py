from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import use_bonus_code, update_balance, can_daily_bonus, set_daily_bonus, get_setting
from keyboards import bonus_menu, main_menu
from config import ADMIN_ID
from utils.logger import logger

router = Router()

class BonusStates(StatesGroup):
    waiting_code = State()

@router.message(F.text == "🎁 Bonus")
async def bonus_handler(message: Message):
    await message.answer(
        "🎁 <b>Bonus bo'limi</b>\n\n"
        "Kunlik bonus yoki bonus kod orqali Space Coin oling!",
        reply_markup=bonus_menu(),
        parse_mode="HTML"
    )

@router.message(F.text == "🎁 Kunlik bonus")
async def daily_bonus_handler(message: Message):
    user_id = message.from_user.id
    if await can_daily_bonus(user_id):
        bonus_amount = int(await get_setting("daily_bonus") or "50")
        await update_balance(user_id, bonus_amount, "daily_bonus")
        await set_daily_bonus(user_id)
        await message.answer(
            f"🎁 Kunlik bonus olindi!\n"
            f"💰 +{bonus_amount} Space Coin hisobingizga qo'shildi!"
        )
        logger.info(f"User {user_id} claimed daily bonus: {bonus_amount}")
    else:
        await message.answer("⏰ Siz bugun allaqachon kunlik bonus oldingiz. Ertaga qayta urinib ko'ring.")

@router.message(F.text.in_(["🎫 Bonus kod kiriting", "🎫 Bonus kod"]))
async def enter_bonus_code_start(message: Message, state: FSMContext):
    await state.set_state(BonusStates.waiting_code)
    await message.answer("🎫 Bonus kodingizni kiriting:", reply_markup=None)

@router.message(BonusStates.waiting_code)
async def process_bonus_code(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    code = message.text.strip().upper()

    reward, error = await use_bonus_code(user_id, code)
    if error:
        await message.answer(f"❌ {error}", reply_markup=main_menu(user_id))
    else:
        await update_balance(user_id, reward, "bonus_code")
        await message.answer(
            f"✅ Bonus kod muvaffaqiyatli qo'llandi!\n"
            f"💰 +{reward} Space Coin hisobingizga qo'shildi!",
            reply_markup=main_menu(user_id)
        )
        logger.info(f"User {user_id} used bonus code '{code}', reward={reward}")
