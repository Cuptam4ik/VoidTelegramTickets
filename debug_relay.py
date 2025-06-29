#!/usr/bin/env python3
"""
Отладочный скрипт для проверки работы пересылки сообщений
"""

import asyncio
import aiosqlite

async def debug_relay_system():
    """Отладка системы пересылки сообщений"""
    print("🔍 Отладка системы пересылки сообщений")
    print("=" * 50)
    
    try:
        async with aiosqlite.connect('tickets.db') as db:
            db.row_factory = aiosqlite.Row
            
            # Проверяем тикеты
            cursor = await db.execute('SELECT * FROM tickets ORDER BY id DESC LIMIT 3')
            tickets = await cursor.fetchall()
            
            print(f"📋 Найдено тикетов: {len(tickets)}")
            
            for ticket in tickets:
                print(f"\n🎫 Тикет #{ticket['id']}:")
                print(f"   👤 Пользователь ID: {ticket['user_id']}")
                print(f"   📝 Описание: {ticket['description'][:50]}...")
                print(f"   📊 Статус: {ticket['status']}")
                
                # Проверяем тему для этого тикета
                cursor = await db.execute('SELECT message_thread_id FROM ticket_threads WHERE ticket_id = ?', (ticket['id'],))
                thread = await cursor.fetchone()
                
                if thread:
                    print(f"   🧵 Тема создана: {thread['message_thread_id']}")
                else:
                    print(f"   ❌ Тема НЕ создана!")
                
                # Проверяем сообщения для этого тикета
                cursor = await db.execute('SELECT COUNT(*) as count FROM ticket_messages WHERE ticket_id = ?', (ticket['id'],))
                msg_count = await cursor.fetchone()
                print(f"   💬 Сообщений в истории: {msg_count['count']}")
                
                # Показываем последние сообщения
                cursor = await db.execute('''
                    SELECT message_text, is_admin, created_at 
                    FROM ticket_messages 
                    WHERE ticket_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 3
                ''', (ticket['id'],))
                messages = await cursor.fetchall()
                
                if messages:
                    print(f"   📜 Последние сообщения:")
                    for msg in messages:
                        who = "Админ" if msg['is_admin'] else "Пользователь"
                        print(f"      [{who}] {msg['message_text'][:30]}...")
                else:
                    print(f"   📜 Сообщений нет")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Главная функция"""
    asyncio.run(debug_relay_system())
    
    print("\n" + "=" * 50)
    print("🔧 Возможные проблемы:")
    print("1. Тема не создается при создании тикета")
    print("2. Обработчик сообщений из группы не срабатывает")
    print("3. Неправильный SUPPORT_GROUP_ID в config.py")
    print("4. Бот не добавлен в группу или нет прав")
    print("5. Группа не является супергруппой с включенными темами")
    
    print("\n📝 Для проверки:")
    print("1. Создайте новый тикет")
    print("2. Проверьте, создалась ли тема в группе")
    print("3. Напишите сообщение в тему от имени админа")
    print("4. Проверьте, пришло ли сообщение пользователю")

if __name__ == "__main__":
    main() 