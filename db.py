import aiosqlite
import asyncio
import json
import random
import string
from datetime import datetime, timedelta
from config import DB_PATH, ADMIN_ID, ADMIN_START_BALANCE, BONUS_CODE_REWARD, BONUS_CODE_LENGTH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()

        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()
        await db.execute()

        admin = await get_user(ADMIN_ID)
        if admin is None:
            now = datetime.now().isoformat()
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, balance, joined_at) VALUES (?, ?, ?, ?)",
                (ADMIN_ID, "Admin", ADMIN_START_BALANCE, now)
            )
            await db.execute(
                "INSERT INTO transactions (user_id, amount, type, date) VALUES (?, ?, ?, ?)",
                (ADMIN_ID, ADMIN_START_BALANCE, "admin_init", now)
            )

        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def register_user(user_id: int, username: str, referral_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, balance, referral_id, joined_at) VALUES (?, ?, 0, ?, ?)",
            (user_id, username, referral_id, now)
        )
        await db.commit()

async def update_balance(user_id: int, amount: int, transaction_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        now = datetime.now().isoformat()
        await db.execute(
            "INSERT INTO transactions (user_id, amount, type, date) VALUES (?, ?, ?, ?)",
            (user_id, amount, transaction_type, now)
        )
        await db.commit()

async def get_balance(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_setting(key: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()

async def add_payment(user_id: int, amount: int, coins: int, screenshot: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            "INSERT INTO payments (user_id, amount, coins, screenshot, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
            (user_id, amount, coins, screenshot, now)
        )
        await db.commit()
        return cursor.lastrowid

async def get_payment(payment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_payment_status(payment_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status = ? WHERE payment_id = ?",
            (status, payment_id)
        )
        await db.commit()

async def create_bonus_code(reward: int) -> str:
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=BONUS_CODE_LENGTH))
    now = datetime.now()
    expires = (now + timedelta(hours=24)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO bonus_codes (code, reward, created_at, expires_at, used_users) VALUES (?, ?, ?, ?, '[]')",
            (code, reward, now.isoformat(), expires)
        )
        await db.commit()
    return code

async def use_bonus_code(user_id: int, code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bonus_codes WHERE code = ?", (code,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return None, "Kod topilmadi"
        row = dict(row)
        expires = datetime.fromisoformat(row["expires_at"])
        if datetime.now() > expires:
            return None, "Kod muddati tugagan"
        used = json.loads(row["used_users"])
        if user_id in used:
            return None, "Siz bu kodni allaqachon ishlatgansiz"
        used.append(user_id)
        await db.execute(
            "UPDATE bonus_codes SET used_users = ? WHERE code = ?",
            (json.dumps(used), code)
        )
        await db.commit()
        return row["reward"], None

async def get_active_tasks():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks WHERE active = 1") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def add_task(channel: str, reward: int, max_users: int = 0) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (channel, reward, max_users, completed_users, active) VALUES (?, ?, ?, '[]', 1)",
            (channel, reward, max_users)
        )
        await db.commit()
        return cursor.lastrowid

async def complete_task(task_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return False
        row = dict(row)
        completed = json.loads(row["completed_users"])
        if user_id in completed:
            return False
        completed.append(user_id)
        await db.execute(
            "UPDATE tasks SET completed_users = ? WHERE task_id = ?",
            (json.dumps(completed), task_id)
        )
        await db.commit()
        if row.get("order_id"):
            await _update_order_progress(row["order_id"], db)
        return True

async def _update_order_progress(order_id: int, db):
    db.row_factory = aiosqlite.Row
    async with db.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        return
    row = dict(row)
    new_subs = row["current_subs"] + 1
    await db.execute(
        "UPDATE orders SET current_subs = ? WHERE order_id = ?",
        (new_subs, order_id)
    )
    if new_subs >= row["target_subs"]:
        await db.execute(
            "UPDATE orders SET status = 'completed' WHERE order_id = ?",
            (order_id,)
        )
        await db.execute(
            "UPDATE tasks SET active = 0 WHERE order_id = ?",
            (order_id,)
        )
    await db.commit()

async def create_order(channel: str, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            "INSERT INTO orders (channel, user_id, target_subs, current_subs, reward_per_sub, status, created_at) VALUES (?, ?, 50, 0, 4, 'active', ?)",
            (channel, user_id, now)
        )
        order_id = cursor.lastrowid
        task_cursor = await db.execute(
            "INSERT INTO tasks (channel, reward, max_users, completed_users, active, order_id) VALUES (?, 4, 50, '[]', 1, ?)",
            (channel, order_id)
        )
        await db.commit()
        return order_id

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE banned = 1") as c:
            banned_users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM payments WHERE status = 'approved'") as c:
            approved_payments = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'") as c:
            pending_payments = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'active'") as c:
            active_orders = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM tasks WHERE active = 1") as c:
            active_tasks = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM contests WHERE active = 1") as c:
            active_contests = (await c.fetchone())[0]
        return {
            "total_users": total_users,
            "banned_users": banned_users,
            "approved_payments": approved_payments,
            "pending_payments": pending_payments,
            "active_orders": active_orders,
            "active_tasks": active_tasks,
            "active_contests": active_contests,
        }

async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def unban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False

async def can_daily_bonus(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        if not row or not row[0]:
            return True
        last = datetime.fromisoformat(row[0])
        return (datetime.now() - last).total_seconds() >= 86400

async def set_daily_bonus(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_daily = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        await db.commit()

async def get_user_by_username(username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        uname = username.lstrip("@")
        async with db.execute("SELECT * FROM users WHERE username = ?", (uname,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def create_contest(post_text: str, channels: list) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO contests (post_text, channels, participants, participant_count, active) VALUES (?, ?, '[]', 0, 1)",
            (post_text, json.dumps(channels))
        )
        await db.commit()
        return cursor.lastrowid

async def get_active_contest():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM contests WHERE active = 1 ORDER BY contest_id DESC LIMIT 1") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def join_contest(contest_id: int, user_id: int, username: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM contests WHERE contest_id = ?", (contest_id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return False
        row = dict(row)
        participants = json.loads(row["participants"])
        if any(p["user_id"] == user_id for p in participants):
            return False
        participants.append({"user_id": user_id, "username": username})
        await db.execute(
            "UPDATE contests SET participants = ?, participant_count = participant_count + 1 WHERE contest_id = ?",
            (json.dumps(participants), contest_id)
        )
        await db.commit()
        return True

async def get_contest(contest_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM contests WHERE contest_id = ?", (contest_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def log_anti_cheat(user_id: int, action: str, details: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO anti_cheat_log (user_id, action, details, date) VALUES (?, ?, ?, ?)",
            (user_id, action, details, datetime.now().isoformat())
        )
        await db.commit()

async def get_referrer(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT referral_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def add_referral_count(referrer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = ?",
            (referrer_id,)
        )
        await db.commit()

async def delete_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tasks SET active = 0 WHERE task_id = ?", (task_id,))
        await db.commit()

async def get_all_transactions(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_all_payments(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments ORDER BY payment_id DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_user_transactions(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 20", (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
