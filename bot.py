import logging
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import Command
from aiogram.types import (
    Message, LabeledPrice, ReplyKeyboardMarkup, KeyboardButton, PreCheckoutQuery
)
import config

BOT_TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID
DATABASE = 'database.db'
PRICE_XTR = 100 * 100

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS keys_pool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                is_sold BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key TEXT NOT NULL
            )
        """)
        await db.commit()

async def check_or_add_user(user_id):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if not await cursor.fetchone():
                await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                await db.commit()

async def get_unsold_key():
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT key FROM keys_pool WHERE is_sold = 0 LIMIT 1") as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
            return None

async def mark_key_as_sold(key):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("UPDATE keys_pool SET is_sold = 1 WHERE key = ?", (key,))
        await db.commit()

async def add_user_key(user_id, key):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("INSERT INTO user_keys (user_id, key) VALUES (?, ?)", (user_id, key))
        await db.commit()

async def get_user_keys(user_id):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT key FROM user_keys WHERE user_id = ?", (user_id,)) as cursor:
            return [key[0] for key in await cursor.fetchall()]

user_state = {}

@dp.message(Command(commands=['start', 'help']))
async def welcome_handler(message: Message):
    user_id = message.from_user.id
    await check_or_add_user(user_id)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Купить ключ'),
                KeyboardButton(text='Мои ключи')
            ]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Добро пожаловать! Вы можете купить ключ за 100 ⭐️.",
        reply_markup=keyboard)

@dp.message(F.text == 'Купить ключ')
async def buy_key_handler(message: Message):
    user_id = message.from_user.id
    key = await get_unsold_key()
    if key:
        user_state[user_id] = {'pending_key': key}
        prices = [LabeledPrice(label="Ключ", amount=PRICE_XTR)]
        await bot.send_invoice(
            chat_id=user_id,
            title="Покупка ключа",
            description="Ключ доступа за 100 ⭐️",
            payload="key_purchase",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="purchase_key"
        )
    else:
        await message.answer("Извините, все ключи проданы.")

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    if payload == "key_purchase":
        user_info = user_state.get(user_id)
        if user_info and 'pending_key' in user_info:
            key = user_info['pending_key']
            await add_user_key(user_id, key)
            await mark_key_as_sold(key)
            await message.answer(f"Поздравляем! Ваш ключ: {key}")
            del user_state[user_id]
        else:
            await message.answer("Ошибка: не удалось найти ваш ключ.")

@dp.message(F.text == 'Мои ключи')
async def my_keys_handler(message: Message):
    user_id = message.from_user.id
    keys = await get_user_keys(user_id)
    if keys:
        keys_list = '\n'.join([f'`{key}`' for key in keys])
        await message.answer(f"Ваши ключи:\n{keys_list}", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("У вас пока нет ключей.")

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())