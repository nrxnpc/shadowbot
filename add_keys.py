import asyncio
import aiosqlite

DATABASE = 'database.db'  # Укажите путь к вашей базе данных

async def add_keys_to_db(keys):
    async with aiosqlite.connect(DATABASE) as db:
        for key in keys:
            try:
                await db.execute("INSERT INTO keys_pool (key) VALUES (?)", (key,))
                print(f'Ключ "{key}" успешно добавлен.')
            except Exception as e:
                print(f'Ошибка при добавлении ключа "{key}": {e}')
        await db.commit()
    print('Все ключи обработаны.')

# Список ключей для добавления
keys_list = [
    '1.ss://1',
    '2.ss://2',
    '3.ss://1',
    # Добавьте остальные ключи здесь
]

if __name__ == '__main__':
    asyncio.run(add_keys_to_db(keys_list))
