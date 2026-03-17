from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import COIN_PACKAGES, ADMIN_ID

def main_menu(user_id: int = None) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="👤 Profil"), KeyboardButton(text="💰 Coin sotib olish")],
        [KeyboardButton(text="🎁 Bonus"), KeyboardButton(text="📋 Vazifalar")],
        [KeyboardButton(text="📢 Kanal reklama"), KeyboardButton(text="💸 Coin yuborish")],
        [KeyboardButton(text="👥 Referral"), KeyboardButton(text="🎉 Konkurs")],
        [KeyboardButton(text="📊 To'lov tarixi")],
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙ Admin Panel"), KeyboardButton(text="📝 Post yuborish")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def profile_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 Coin yuborish"), KeyboardButton(text="🎫 Bonus kod kiriting")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )

def back_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )

def coin_packages_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for pkg in COIN_PACKAGES:
        buttons.append([InlineKeyboardButton(
            text=f"{pkg['coins']} Space Coin = {pkg['price']:,} UZS",
            callback_data=f"buy_{pkg['coins']}_{pkg['price']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_panel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 To'lov sozlamalari"), KeyboardButton(text="📢 To'lov kanali")],
            [KeyboardButton(text="📊 Tarixi havola"), KeyboardButton(text="➕ Vazifa qo'shish")],
            [KeyboardButton(text="🎁 Bonus kod yaratish"), KeyboardButton(text="👤 Foydalanuvchi boshqarish")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🚫 Foydalanuvchini ban qilish")],
            [KeyboardButton(text="📄 Loglar"), KeyboardButton(text="🎉 Konkurs boshqarish")],
            [KeyboardButton(text="📝 Post yuborish"), KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )

def payment_verify_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_pay_{payment_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_pay_{payment_id}"),
        ]
    ])

def tasks_keyboard(tasks: list, user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks:
        completed = user_id in (task.get("completed_users_list") or [])
        status = "✅" if completed else "📋"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {task['channel']} (+{task['reward']} 🪙)",
            callback_data=f"task_{task['task_id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def contest_keyboard(contest_id: int, channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        ch_username = ch.lstrip("@")
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ch}",
            url=f"https://t.me/{ch_username}"
        )])
    buttons.append([InlineKeyboardButton(
        text="✅ Tekshirish",
        callback_data=f"check_contest_{contest_id}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def bonus_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Kunlik bonus"), KeyboardButton(text="🎫 Bonus kod kiriting")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )
