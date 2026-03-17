from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_setting, add_payment, update_balance, get_payment, update_payment_status, get_user
from keyboards import coin_packages_keyboard, payment_verify_keyboard, main_menu, back_menu
from config import COIN_PACKAGES, ADMIN_ID
from utils.logger import logger

router = Router()

class PaymentStates(StatesGroup):
    waiting_screenshot = State()
    waiting_package = State()

user_pending_payment = {}

@router.message(F.text == "💰 Coin sotib olish")
async def buy_coins_handler(message: Message):
    await message.answer(
        "💰 <b>Coin sotib olish</b>\n\n"
        "Quyidagi paketlardan birini tanlang:",
        reply_markup=coin_packages_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("buy_"))
async def package_selected(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    coins = int(parts[1])
    price = int(parts[2])
    user_id = call.from_user.id

    card_number = await get_setting("card_number")
    card_holder = await get_setting("card_holder")

    await state.update_data(coins=coins, price=price)
    await state.set_state(PaymentStates.waiting_screenshot)

    text = (
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"📦 Paket: {coins} Space Coin\n"
        f"💵 Summa: {price:,} UZS\n\n"
        f"💳 Karta: <code>{card_number}</code>\n"
        f"👤 Egasi: {card_holder}\n\n"
        f"To'lovni amalga oshiring va skrinshot yuboring."
    )
    await call.message.answer(text, reply_markup=back_menu(), parse_mode="HTML")
    await call.answer()

@router.message(PaymentStates.waiting_screenshot)
async def payment_screenshot_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu(user_id))
        return

    if not message.photo:
        await message.answer("❌ Iltimos, skrinshot rasmi yuboring.")
        return

    data = await state.get_data()
    coins = data.get("coins")
    price = data.get("price")

    photo_id = message.photo[-1].file_id

    payment_id = await add_payment(user_id, price, coins, photo_id)

    payment_channel = await get_setting("payment_channel")

    user = await get_user(user_id)
    username = user.get("username") or str(user_id)

    verify_text = (
        f"🔔 <b>Yangi to'lov so'rovi</b>\n\n"
        f"👤 Foydalanuvchi: @{username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📦 Coins: {coins} Space Coin\n"
        f"💵 Summa: {price:,} UZS\n"
        f"🆔 To'lov ID: #{payment_id}"
    )

    if payment_channel:
        try:
            ch = payment_channel.lstrip("@")
            sent = await message.bot.send_photo(
                chat_id=f"@{ch}",
                photo=photo_id,
                caption=verify_text,
                reply_markup=payment_verify_keyboard(payment_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send payment to channel {payment_channel}: {e}")
            try:
                await message.bot.send_photo(
                    chat_id=message.bot._me.id if hasattr(message.bot, '_me') else user_id,
                    photo=photo_id,
                    caption=verify_text,
                    reply_markup=payment_verify_keyboard(payment_id),
                    parse_mode="HTML"
                )
            except Exception:
                pass
    else:
        from config import ADMIN_ID
        try:
            await message.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_id,
                caption=verify_text,
                reply_markup=payment_verify_keyboard(payment_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send payment to admin: {e}")

    await state.clear()
    await message.answer(
        f"✅ To'lov so'rovingiz yuborildi!\n"
        f"🆔 To'lov ID: #{payment_id}\n"
        f"Admin tekshirganidan so'ng coinlar hisobingizga qo'shiladi.",
        reply_markup=main_menu(user_id)
    )
    logger.info(f"Payment #{payment_id} submitted by user {user_id}, coins={coins}, amount={price}")

@router.message(F.text == "📊 To'lov tarixi")
async def payment_history_handler(message: Message):
    link = await get_setting("payment_history_link")
    if not link:
        await message.answer(
            "📊 <b>To'lov tarixi</b>\n\n"
            "⚠️ To'lov tarixi kanali hali sozlanmagan.\n"
            "Admin sozlashi kerak.",
            parse_mode="HTML"
        )
        return
    url = link if link.startswith("http") else f"https://t.me/{link.lstrip('@')}"
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 To'lov tarixini ko'rish", url=url)]
    ])
    await message.answer(
        "📊 <b>To'lov tarixi</b>\n\n"
        "Quyidagi tugma orqali to'lov tarixini ko'rishingiz mumkin:",
        reply_markup=inline_kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("approve_pay_"))
async def approve_payment(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔ Faqat admin tasdiqlashi mumkin.", show_alert=True)
        return
    payment_id = int(call.data.split("_")[2])
    payment = await get_payment(payment_id)

    if not payment:
        await call.answer("To'lov topilmadi.", show_alert=True)
        return

    if payment["status"] != "pending":
        await call.answer(f"Bu to'lov allaqachon {payment['status']} holati.", show_alert=True)
        return

    await update_payment_status(payment_id, "approved")
    await update_balance(payment["user_id"], payment["coins"], f"payment_{payment_id}")

    try:
        await call.bot.send_message(
            payment["user_id"],
            f"✅ To'lovingiz tasdiqlandi!\n"
            f"💰 +{payment['coins']:,} Space Coin hisobingizga qo'shildi!\n"
            f"🆔 To'lov ID: #{payment_id}"
        )
    except Exception as e:
        logger.error(f"Error notifying user {payment['user_id']}: {e}")

    await call.message.edit_caption(
        caption=call.message.caption + f"\n\n✅ <b>TASDIQLANDI</b>",
        parse_mode="HTML"
    )
    await call.answer("✅ To'lov tasdiqlandi!", show_alert=True)
    logger.info(f"Payment #{payment_id} approved, user={payment['user_id']}, coins={payment['coins']}")

@router.callback_query(F.data.startswith("reject_pay_"))
async def reject_payment(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("⛔ Faqat admin rad etishi mumkin.", show_alert=True)
        return
    payment_id = int(call.data.split("_")[2])
    payment = await get_payment(payment_id)

    if not payment:
        await call.answer("To'lov topilmadi.", show_alert=True)
        return

    if payment["status"] != "pending":
        await call.answer(f"Bu to'lov allaqachon {payment['status']} holati.", show_alert=True)
        return

    await update_payment_status(payment_id, "rejected")

    try:
        await call.bot.send_message(
            payment["user_id"],
            f"❌ To'lovingiz rad etildi.\n"
            f"🆔 To'lov ID: #{payment_id}\n"
            f"Muammo bo'lsa adminga murojaat qiling."
        )
    except Exception as e:
        logger.error(f"Error notifying user {payment['user_id']}: {e}")

    await call.message.edit_caption(
        caption=call.message.caption + f"\n\n❌ <b>RAD ETILDI</b>",
        parse_mode="HTML"
    )
    await call.answer("❌ To'lov rad etildi!", show_alert=True)
    logger.info(f"Payment #{payment_id} rejected, user={payment['user_id']}")
