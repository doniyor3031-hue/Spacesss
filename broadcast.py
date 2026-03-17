import json
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter
from database.db import get_all_users
from keyboards import admin_panel_menu, back_menu, main_menu
from config import ADMIN_ID
from utils.logger import logger

router = Router()

class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID

class BroadcastStates(StatesGroup):
    waiting_post_text = State()
    waiting_buttons = State()
    waiting_channels = State()
    confirming = State()

post_drafts = {}

@router.message(IsAdmin(), F.text == "📝 Post yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    await state.set_state(BroadcastStates.waiting_post_text)
    await message.answer(
        "📝 <b>Post yaratish</b>\n\n"
        "Post matnini kiriting (HTML formatda yozishingiz mumkin):",
        parse_mode="HTML",
        reply_markup=back_menu()
    )

@router.message(IsAdmin(), BroadcastStates.waiting_post_text)
async def post_text_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    await state.update_data(post_text=message.text)
    await message.answer(
        "Inline tugmalar qo'shmoqchimisiz?\n\n"
        "Format (har biri yangi qatorda):\n"
        "<code>Matn|URL</code>\n\n"
        "Misol:\n"
        "<code>Bizning kanal|https://t.me/channel</code>\n\n"
        "Tugmalar qo'shmasangiz, /skip yuboring:",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_buttons)

@router.message(IsAdmin(), BroadcastStates.waiting_buttons)
async def post_buttons_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return

    buttons = []
    if message.text != "/skip":
        for line in message.text.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 1)
                if len(parts) == 2:
                    buttons.append({"text": parts[0].strip(), "url": parts[1].strip()})

    await state.update_data(buttons=buttons)
    await message.answer(
        "📢 Qaysi kanallarga yuborasiz?\n"
        "Kanal @username larini yangi qatorda kiriting.\n"
        "Barcha foydalanuvchilarga yuborish uchun /allusers yuboring:"
    )
    await state.set_state(BroadcastStates.waiting_channels)

@router.message(IsAdmin(), BroadcastStates.waiting_channels)
async def post_channels_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return

    await state.update_data(send_to_users=(message.text == "/allusers"))
    if message.text != "/allusers":
        channels = [c.strip() for c in message.text.strip().split("\n") if c.strip()]
        channels = [c if c.startswith("@") else "@" + c for c in channels]
        await state.update_data(channels=channels)
    else:
        await state.update_data(channels=[])

    data = await state.get_data()
    post_text = data.get("post_text", "")
    buttons = data.get("buttons", [])
    send_to_users = data.get("send_to_users", False)
    channels = data.get("channels", [])

    inline_kb = None
    if buttons:
        kb_buttons = [[InlineKeyboardButton(text=b["text"], url=b["url"])] for b in buttons]
        inline_kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)

    await message.answer("👀 Post ko'rinishi:", parse_mode="HTML")
    await message.answer(post_text, reply_markup=inline_kb, parse_mode="HTML")

    confirm_text = (
        f"✅ Yuboriladigan joy:\n"
        f"{'Barcha foydalanuvchilar' if send_to_users else ', '.join(channels)}\n\n"
        f"/send - yuborish\n/cancel - bekor qilish\n/edit - tahrirlash"
    )
    await message.answer(confirm_text)
    await state.set_state(BroadcastStates.confirming)

@router.message(IsAdmin(), BroadcastStates.confirming)
async def post_confirm(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Post bekor qilindi.", reply_markup=admin_panel_menu())
        return

    if message.text == "/edit":
        await state.set_state(BroadcastStates.waiting_post_text)
        await message.answer("Yangi post matnini kiriting:")
        return

    if message.text != "/send":
        await message.answer("/send, /cancel yoki /edit kiriting.")
        return

    data = await state.get_data()
    post_text = data.get("post_text", "")
    buttons = data.get("buttons", [])
    send_to_users = data.get("send_to_users", False)
    channels = data.get("channels", [])

    inline_kb = None
    if buttons:
        kb_buttons = [[InlineKeyboardButton(text=b["text"], url=b["url"])] for b in buttons]
        inline_kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)

    sent_count = 0
    failed_count = 0

    if send_to_users:
        users = await get_all_users()
        await message.answer(f"📤 {len(users)} ta foydalanuvchiga yuborilmoqda...")
        for user in users:
            try:
                await message.bot.send_message(
                    user["user_id"],
                    post_text,
                    reply_markup=inline_kb,
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception:
                failed_count += 1
    else:
        for channel in channels:
            try:
                ch = channel.lstrip("@")
                await message.bot.send_message(
                    f"@{ch}",
                    post_text,
                    reply_markup=inline_kb,
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {channel}: {e}")
                failed_count += 1

    await state.clear()
    await message.answer(
        f"✅ Post yuborildi!\n"
        f"📤 Muvaffaqiyatli: {sent_count}\n"
        f"❌ Muvaffaqiyatsiz: {failed_count}",
        reply_markup=admin_panel_menu()
    )
    logger.info(f"Admin broadcast: sent={sent_count}, failed={failed_count}")
