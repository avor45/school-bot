import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Читаем токен и ID админов из переменных Railway
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Подключаем базу данных
conn = sqlite3.connect("school.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0
)
""")
conn.commit()

# Главное меню
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Мой рейтинг", callback_data="my_points"),
        InlineKeyboardButton("🏆 Топ учеников", callback_data="top_students")
    )
    return kb

# Старт
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cursor.execute("SELECT * FROM students WHERE id=?", (message.from_user.id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO students (id, name) VALUES (?, ?)",
                       (message.from_user.id, message.from_user.full_name))
        conn.commit()
        await message.answer("✅ Ты зарегистрирован в системе рейтинга!", reply_markup=main_menu())
    else:
        await message.answer("👋 С возвращением!", reply_markup=main_menu())

# Мой рейтинг
@dp.callback_query_handler(lambda c: c.data == "my_points")
async def my_points(callback: types.CallbackQuery):
    cursor.execute("SELECT points FROM students WHERE id=?", (callback.from_user.id,))
    points = cursor.fetchone()[0]
    await callback.message.answer(f"📊 У тебя {points} баллов.")

# Топ учеников
@dp.callback_query_handler(lambda c: c.data == "top_students")
async def top_students(callback: types.CallbackQuery):
    cursor.execute("SELECT name, points FROM students ORDER BY points DESC LIMIT 5")
    top = cursor.fetchall()
    text = "🏆 Топ учеников:\n"
    for i, (name, points) in enumerate(top, start=1):
        text += f"{i}. {name} — {points} баллов\n"
    await callback.message.answer(text)

# Добавить баллы (только для админов)
@dp.message_handler(commands=['add'])
async def add_points(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("❌ Нет прав.")
    try:
        _, student_id, pts = message.text.split()
        pts = int(pts)
        cursor.execute("UPDATE students SET points = points + ? WHERE id=?", (pts, student_id))
        conn.commit()
        await message.reply("✅ Баллы добавлены!")
    except:
        await message.reply("Используй формат: /add <id> <баллы>")

# Убрать баллы
@dp.message_handler(commands=['remove'])
async def remove_points(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("❌ Нет прав.")
    try:
        _, student_id, pts = message.text.split()
        pts = int(pts)
        cursor.execute("UPDATE students SET points = points - ? WHERE id=?", (pts, student_id))
        conn.commit()
        await message.reply("✅ Баллы убраны!")
    except:
        await message.reply("Используй формат: /remove <id> <баллы>")

if __name__ == "__main__":
    executor.start_polling(dp)
