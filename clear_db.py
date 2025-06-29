#!/usr/bin/env python3
"""
Скрипт для очистки базы данных тикетов
"""

import asyncio
import aiosqlite

async def clear_database():
    """Очистка всех таблиц базы данных"""
    try:
        async with aiosqlite.connect('tickets.db') as db:
            # Очищаем все таблицы
            tables = ['ticket_messages', 'ticket_files', 'ticket_threads', 'tickets']
            
            for table in tables:
                await db.execute(f'DELETE FROM {table}')
                print(f"✅ Очищена таблица: {table}")
            
            await db.commit()
            print("\n🎉 База данных полностью очищена!")
            
            # Проверяем, что таблицы пустые
            for table in tables:
                cursor = await db.execute(f'SELECT COUNT(*) as count FROM {table}')
                result = await cursor.fetchone()
                print(f"📊 {table}: {result[0]} записей")
                
    except Exception as e:
        print(f"❌ Ошибка при очистке базы данных: {e}")

if __name__ == "__main__":
    print("🧹 Очистка базы данных тикетов...")
    asyncio.run(clear_database()) 