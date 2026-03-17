import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter
from database.db import (
    get_setting, set_setting, create_bonus_code, get_stats, add_task, delete_task,
    get_active_tasks, ban_user, unban_user, get_user, get_all_users,
    get_all_transactions, get_all_payments, create_contest, get_active_contest,
    update_balance, get_balance
)
from keyboards import admin_panel_menu, main_menu, back_menu
from config import ADMIN_ID
from utils.logger import logger

router = Router()

class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID

class AdminStates(StatesGroup):
    waiting_card_number = State()
    waiting_card_holder = State()
    waiting_payment_channel = State()
    waiting_history_link = State()
    waiting_task_channel = State()
    waiting_task_reward = State()
    waiting_bonus_reward = State()
    waiting_user_id = State()
    waiting_ban_id = State()
    waiting_contest_text = State()
    waiting_contest_channels = State()
    waiting_delete_task = State()
    waiting_send_coins_id = State()
    waiting_send_coins_amount = State()

@router.message(IsAdmin(), F.text == "⚙ Admin Panel")
async def admin_panel(message: Message):
    await message.answer("⚙ <b>Admin Panel</b>", reply_markup=admin_panel_menu(), parse_mode="HTML")

@router.message(IsAdmin(), F.text == "💳 To'lov sozlamalari")
async def payment_settings(message: Message, state: FSMContext):
    card_number = await get_setting("card_number")
    card_holder = await get_setting("card_holder")
    await message.answer(
        f"💳 <b>Joriy to'lov ma'lumotlari</b>\n\n"
        f"Karta: <code>{card_number}</code>\n"
        f"Egasi: {card_holder}\n\n"
        f"Yangi karta raqamini kiriting:",
        parse_mode="HTML",
        reply_markup=back_menu()
    )
    await state.set_state(AdminStates.waiting_card_number)

@router.message(IsAdmin(), AdminStates.waiting_card_number)
async def set_card_number(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    await set_setting("card_number", message.text.strip())
    await message.answer("Endi karta egasining ismini kiriting:")
    await state.set_state(AdminStates.waiting_card_holder)

@router.message(IsAdmin(), AdminStates.waiting_card_holder)
async def set_card_holder(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    await set_setting("card_holder", message.text.strip())
    await state.clear()
    await message.answer("✅ To'lov ma'lumotlari yangilandi!", reply_markup=admin_panel_menu())
    logger.info(f"Admin updated payment card info")

@router.message(IsAdmin(), F.text == "📢 To'lov kanali")
async def payment_channel_settings(message: Message, state: FSMContext):
    current = await get_setting("payment_channel")
    await message.answer(
        f"📢 <b>To'lov Tekshirish Kanali</b>\n\n"
        f"Joriy kanal: {current or 'belgilanmagan'}\n\n"
        f"Yangi kanal @username kiriting:",
        parse_mode="HTML",
        reply_markup=back_menu()
    )
    await state.set_state(AdminStates.waiting_payment_channel)

@router.message(IsAdmin(), AdminStates.waiting_payment_channel)
async def set_payment_channel(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    channel = message.text.strip().lstrip("@")
    await set_setting("payment_channel", channel)
    await state.clear()
    await message.answer(f"✅ To'lov kanali @{channel} ga o'rnatildi!", reply_markup=admin_panel_menu())
    logger.info(f"Admin set payment channel to @{channel}")

@router.message(IsAdmin(), F.text == "📊 Tarixi havola")
async def history_link_settings(message: Message, state: FSMContext):
    current = await get_setting("payment_history_link")
    await message.answer(
        f"📊 <b>To'lov tarixi havola</b>\n\n"
        f"Joriy havola: {current or 'belgilanmagan'}\n\n"
        f"Foydalanuvchilar bu tugma orqali to'lov tarixi kanaliga kirishadi.\n"
        f"Kanal @username yoki to'liq URL kiriting\n"
        f"(masalan: @tollov_tarixi yoki https://t.me/tollov_tarixi):",
        parse_mode="HTML",
        reply_markup=back_menu()
    )
    await state.set_state(AdminStates.waiting_history_link)

@router.message(IsAdmin(), AdminStates.waiting_history_link)
async def set_history_link(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    link = message.text.strip()
    await set_setting("payment_history_link", link)
    await state.clear()
    await message.answer(
        f"✅ To'lov tarixi havola saqlandi!\n{link}\n\n"
        f"Endi foydalanuvchilar '📊 To'lov tarixi' tugmasi orqali ushbu kanalga kira olishadi.",
        reply_markup=admin_panel_menu()
    )
    logger.info(f"Admin set payment history link: {link}")

@router.message(IsAdmin(), F.text == "➕ Vazifa qo'shish")
async def add_task_handler(message: Message, state: FSMContext):
    tasks = await get_active_tasks()
    tasks_text = ""
    if tasks:
        for t in tasks:
            tasks_text += f"#{t['task_id']} - {t['channel']} (+{t['reward']}🪙)\n"
    else:
        tasks_text = "Hozirda faol vazifalar yo'q.\n"

    await message.answer(
        f"📋 <b>Faol vazifalar:</b>\n{tasks_text}\n"
        f"Yangi kanal @username kiriting yoki /deltask [id] buyrug'ini yuboring:",
        parse_mode="HTML",
        reply_markup=back_menu()
    )
    await state.set_state(AdminStates.waiting_task_channel)

@router.message(IsAdmin(), AdminStates.waiting_task_channel)
async def task_channel_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    if message.text.startswith("/deltask"):
        parts = message.text.split()
        if len(parts) == 2:
            try:
                task_id = int(parts[1])
                await delete_task(task_id)
                await message.answer(f"✅ Vazifa #{task_id} o'chirildi.", reply_markup=admin_panel_menu())
                await state.clear()
                return
            except ValueError:
                pass
    channel = message.text.strip()
    if not channel.startswith("@"):
        channel = "@" + channel
    await state.update_data(task_channel=channel)
    await message.answer(f"Mukofot miqdorini kiriting (coins):")
    await state.set_state(AdminStates.waiting_task_reward)

@router.message(IsAdmin(), AdminStates.waiting_task_reward)
async def task_reward_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    try:
        reward = int(message.text.strip())
        data = await state.get_data()
        channel = data["task_channel"]
        task_id = await add_task(channel, reward)
        await state.clear()
        await message.answer(
            f"✅ Yangi vazifa qo'shildi!\n"
            f"📢 Kanal: {channel}\n"
            f"💰 Mukofot: {reward} Space Coin\n"
            f"🆔 Vazifa ID: #{task_id}",
            reply_markup=admin_panel_menu()
        )
        logger.info(f"Admin added task #{task_id}, channel={channel}, reward={reward}")
    except ValueError:
        await message.answer("❌ Iltimos son kiriting.")

@router.message(IsAdmin(), F.text == "🎁 Bonus kod yaratish")
async def create_bonus_handler(message: Message, state: FSMContext):
    current_reward = await get_setting("bonus_code_reward")
    await message.answer(
        f"🎁 <b>Bonus kod yaratish</b>\n\n"
        f"Joriy mukofot: {current_reward} Space Coin\n\n"
        f"Mukofot miqdorini kiriting (yoki /default bosing {current_reward} uchun):",
        parse_mode="HTML",
        reply_markup=back_menu()
    )
    await state.set_state(AdminStates.waiting_bonus_reward)

@router.message(IsAdmin(), AdminStates.waiting_bonus_reward)
async def bonus_reward_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    if message.text == "/default":
        reward_str = await get_setting("bonus_code_reward")
        reward = int(reward_str or "100")
    else:
        try:
            reward = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Iltimos son kiriting.")
            return

    await set_setting("bonus_code_reward", str(reward))
    code = await create_bonus_code(reward)
    await state.clear()
    await message.answer(
        f"✅ Yangi bonus kod yaratildi!\n\n"
        f"🎫 Kod: <code>{code}</code>\n"
        f"💰 Mukofot: {reward} Space Coin\n"
        f"⏰ Amal qilish muddati: 24 soat\n\n"
        f"Bu kodni foydalanuvchilarga yuboring!",
        parse_mode="HTML",
        reply_markup=admin_panel_menu()
    )
    logger.info(f"Admin created bonus code '{code}', reward={reward}")

@router.message(IsAdmin(), F.text == "📊 Statistika")
async def stats_handler(message: Message):
    stats = await get_stats()
    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👤 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"🚫 Ban qilingan: <b>{stats['banned_users']}</b>\n"
        f"💳 Tasdiqlangan to'lovlar: <b>{stats['approved_payments']}</b>\n"
        f"⏳ Kutilayotgan to'lovlar: <b>{stats['pending_payments']}</b>\n"
        f"📦 Faol buyurtmalar: <b>{stats['active_orders']}</b>\n"
        f"📋 Faol vazifalar: <b>{stats['active_tasks']}</b>\n"
        f"🎉 Faol konkurslar: <b>{stats['active_contests']}</b>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(IsAdmin(), F.text == "👤 Foydalanuvchi boshqarish")
async def user_manage_handler(message: Message, state: FSMContext):
    await message.answer(
        "👤 <b>Foydalanuvchi boshqarish</b>\n\n"
        "Foydalanuvchi ID sini kiriting (ma'lumot ko'rish uchun):\n"
        "Yoki /sendcoins [user_id] [amount] - Coin yuborish",
        parse_mode="HTML",
        reply_markup=back_menu()
    )
    await state.set_state(AdminStates.waiting_user_id)

@router.message(IsAdmin(), AdminStates.waiting_user_id)
async def user_info_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return

    if message.text.startswith("/sendcoins"):
        parts = message.text.split()
        if len(parts) == 3:
            try:
                target_id = int(parts[1])
                amount = int(parts[2])
                await update_balance(target_id, amount, "admin_send")
                await state.clear()
                await message.answer(
                    f"✅ {amount:,} Space Coin foydalanuvchi {target_id} ga yuborildi!",
                    reply_markup=admin_panel_menu()
                )
                try:
                    await message.bot.send_message(
                        target_id,
                        f"🎁 Admin sizga {amount:,} Space Coin yubordi!"
                    )
                except Exception:
                    pass
                return
            except ValueError:
                await message.answer("❌ Format: /sendcoins [user_id] [amount]")
                return

    try:
        uid = int(message.text.strip())
        user = await get_user(uid)
        if not user:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            return

        ban_status = "Ha" if user['banned'] else "Yo'q"
        username_val = user.get('username') or 'yo\'q'
        text = (
            f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
            f"🆔 ID: <code>{user['user_id']}</code>\n"
            f"👤 Username: @{username_val}\n"
            f"💰 Balans: <b>{user['balance']:,} Space Coin</b>\n"
            f"👥 Referallar: {user['referrals_count']}\n"
            f"📅 Ro'yxatdan o'tgan: {user['joined_at'][:10]}\n"
            f"🚫 Ban: {ban_status}"
        )
        await message.answer(text, parse_mode="HTML")
        await state.clear()
        await message.answer("Boshqa amal bajarish uchun menyudan tanlang.", reply_markup=admin_panel_menu())
    except ValueError:
        await message.answer("❌ Iltimos faqat son kiriting.")

@router.message(IsAdmin(), F.text == "🚫 Foydalanuvchini ban qilish")
async def ban_handler(message: Message, state: FSMContext):
    await message.answer(
        "🚫 Ban/unban qilish uchun:\n"
        "/ban [user_id] - ban qilish\n"
        "/unban [user_id] - ban ochish",
        reply_markup=back_menu()
    )
    await state.set_state(AdminStates.waiting_ban_id)

@router.message(IsAdmin(), AdminStates.waiting_ban_id)
async def ban_action_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return

    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("❌ Format: /ban [user_id] yoki /unban [user_id]")
        return

    cmd, uid_str = parts
    try:
        uid = int(uid_str)
    except ValueError:
        await message.answer("❌ Iltimos son kiriting.")
        return

    if cmd == "/ban":
        await ban_user(uid)
        await state.clear()
        await message.answer(f"✅ Foydalanuvchi {uid} ban qilindi.", reply_markup=admin_panel_menu())
        logger.info(f"Admin banned user {uid}")
        try:
            await message.bot.send_message(uid, "🚫 Siz botdan ban qilingansiz.")
        except Exception:
            pass
    elif cmd == "/unban":
        await unban_user(uid)
        await state.clear()
        await message.answer(f"✅ Foydalanuvchi {uid} ban ochildi.", reply_markup=admin_panel_menu())
        logger.info(f"Admin unbanned user {uid}")
        try:
            await message.bot.send_message(uid, "✅ Sizning baningiz olib tashlandi.")
        except Exception:
            pass
    else:
        await message.answer("❌ /ban yoki /unban kiriting.")

@router.message(IsAdmin(), F.text == "📄 Loglar")
async def logs_handler(message: Message):
    try:
        with open("logs/bot.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
        last_lines = "".join(lines[-30:]) if lines else "Log bo'sh."
        await message.answer(f"📄 <b>So'nggi loglar:</b>\n\n<pre>{last_lines[:3500]}</pre>", parse_mode="HTML")
    except FileNotFoundError:
        await message.answer("📄 Log fayli topilmadi.")

@router.message(IsAdmin(), F.text == "🎉 Konkurs boshqarish")
async def contest_manage_handler(message: Message, state: FSMContext):
    contest = await get_active_contest()
    if contest:
        parts_text = json.loads(contest.get("participants") or "[]")
        text = (
            f"🎉 <b>Faol Konkurs</b>\n\n"
            f"📝 Matn: {contest['post_text'][:200]}\n"
            f"👥 Ishtirokchilar: <b>{contest['participant_count']}</b>\n\n"
            f"Yangi konkurs yaratish uchun tugmani bosing."
        )
        await message.answer(text, parse_mode="HTML")

        if parts_text:
            participants_info = "\n".join([
                f"👤 @{p.get('username', 'N/A')} (ID: {p.get('user_id')})"
                for p in parts_text[:50]
            ])
            if participants_info:
                await message.answer(
                    f"📋 Ishtirokchilar ro'yxati:\n{participants_info}",
                )
    else:
        await message.answer("Hozirda faol konkurs yo'q.")

    await message.answer(
        "Yangi konkurs matni kiriting:",
        reply_markup=back_menu()
    )
    await state.set_state(AdminStates.waiting_contest_text)

@router.message(IsAdmin(), AdminStates.waiting_contest_text)
async def contest_text_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    await state.update_data(contest_text=message.text)
    await message.answer(
        "Sponsor kanallar @username larini kiriting (har biri yangi qatorda):"
    )
    await state.set_state(AdminStates.waiting_contest_channels)

@router.message(IsAdmin(), AdminStates.waiting_contest_channels)
async def contest_channels_received(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_menu())
        return
    channels = [c.strip() for c in message.text.strip().split("\n") if c.strip()]
    channels = [c if c.startswith("@") else "@" + c for c in channels]
    data = await state.get_data()
    contest_id = await create_contest(data["contest_text"], channels)
    await state.clear()
    await message.answer(
        f"✅ Yangi konkurs yaratildi!\n"
        f"🆔 ID: #{contest_id}\n"
        f"📢 Kanallar: {', '.join(channels)}",
        reply_markup=admin_panel_menu()
    )
    logger.info(f"Admin created contest #{contest_id}")

@router.message(IsAdmin(), F.text == "🔙 Orqaga")
async def back_from_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu", reply_markup=main_menu(ADMIN_ID))
