import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.db import get_active_tasks, get_task, complete_task, update_balance, log_anti_cheat, get_user
from keyboards import tasks_keyboard, main_menu
from utils.logger import logger

router = Router()

@router.message(F.text == "📋 Vazifalar")
async def tasks_handler(message: Message):
    user_id = message.from_user.id
    tasks = await get_active_tasks()

    if not tasks:
        await message.answer("📋 Hozirda faol vazifalar yo'q.", reply_markup=main_menu(user_id))
        return

    for task in tasks:
        completed_list = json.loads(task.get("completed_users") or "[]")
        task["completed_users_list"] = completed_list

    text = (
        "📋 <b>Vazifalar</b>\n\n"
        "Quyidagi kanallarga obuna bo'ling va Space Coin oling!\n"
        "Har bir kanal uchun mukofot ko'rsatilgan."
    )
    await message.answer(
        text,
        reply_markup=tasks_keyboard(tasks, user_id),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("task_"))
async def task_callback(call: CallbackQuery):
    user_id = call.from_user.id
    task_id = int(call.data.split("_")[1])

    task = await get_task(task_id)
    if not task:
        await call.answer("Vazifa topilmadi.", show_alert=True)
        return

    if not task.get("active"):
        await call.answer("Bu vazifa yakunlandi.", show_alert=True)
        return

    completed = json.loads(task.get("completed_users") or "[]")
    if user_id in completed:
        await call.answer("✅ Siz bu vazifani allaqachon bajargansiz!", show_alert=True)
        return

    channel = task["channel"]
    ch_username = channel.lstrip("@")

    try:
        member = await call.bot.get_chat_member(f"@{ch_username}", user_id)
        if member.status in ("left", "kicked", "banned"):
            await call.answer(
                f"❌ Siz {channel} kanaliga obuna emassiz!\n"
                f"Obuna bo'lib qayta bosing.",
                show_alert=True
            )
            return
    except Exception as e:
        logger.error(f"Error checking membership for {user_id} in {channel}: {e}")
        await call.answer(
            f"⚠️ Kanal tekshirishda xatolik yuz berdi: {channel}\n"
            f"Kanal to'g'ri ekanligini tekshiring.",
            show_alert=True
        )
        return

    max_users = task.get("max_users", 0)
    if max_users and len(completed) >= max_users:
        await call.answer("Bu vazifada maksimal foydalanuvchilar soni to'ldi.", show_alert=True)
        return

    success = await complete_task(task_id, user_id)
    if success:
        reward = task["reward"]
        await update_balance(user_id, reward, f"task_{task_id}")
        await call.answer(
            f"✅ Vazifa bajarildi!\n+{reward} Space Coin olindi!",
            show_alert=True
        )
        logger.info(f"User {user_id} completed task {task_id}, reward={reward}")
    else:
        await call.answer("✅ Bu vazifani allaqachon bajargansiz!", show_alert=True)
