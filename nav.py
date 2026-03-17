from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards import main_menu
from config import ADMIN_ID

router = Router()

@router.message(F.text == "🔙 Orqaga")
async def back_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu", reply_markup=main_menu(message.from_user.id))
