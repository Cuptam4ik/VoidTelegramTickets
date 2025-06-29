"""
Утилиты для Telegram бота системы тикетов
"""
import aiosqlite
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from config import DB_PATH, TICKET_STATUSES, STATUS_EMOJIS

async def get_ticket_stats():
    """Получить статистику тикетов"""
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        
        # Общее количество тикетов
        cursor = await db.execute("SELECT COUNT(*) FROM tickets")
        result = await cursor.fetchone()
        stats['total'] = result[0] if result else 0
        
        # По статусам
        for status in TICKET_STATUSES.keys():
            cursor = await db.execute(f"SELECT COUNT(*) FROM tickets WHERE status='{status}'")
            result = await cursor.fetchone()
            stats[status] = result[0] if result else 0
        
        # По категориям
        cursor = await db.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category")
        category_stats = await cursor.fetchall()
        stats['categories'] = {row[0]: row[1] for row in category_stats} if category_stats else {}
        
        return stats

async def get_recent_tickets(limit: int = 10):
    """Получить последние тикеты"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, nickname, description, status, category, priority, created_at FROM tickets ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return await cursor.fetchall()

async def get_ticket_messages(ticket_id: int, limit: int = 50):
    """Получить сообщения тикета"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT sender, text, timestamp FROM ticket_messages WHERE ticket_id=? ORDER BY id ASC LIMIT ?",
            (ticket_id, limit)
        )
        return await cursor.fetchall()

async def get_admin_tickets(admin_id: int):
    """Получить тикеты, обрабатываемые администратором"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, nickname, description, status, category, priority FROM tickets WHERE admin_id=? ORDER BY id DESC",
            (admin_id,)
        )
        return await cursor.fetchall()

async def get_user_tickets(user_id: int):
    """Получить тикеты пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, description, status, category, priority, created_at FROM tickets WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        )
        return await cursor.fetchall()

async def update_ticket_status(ticket_id: int, status: str, admin_id: Optional[int] = None) -> bool:
    """Обновить статус тикета"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            if admin_id:
                await db.execute(
                    "UPDATE tickets SET status=?, admin_id=? WHERE id=?",
                    (status, admin_id, ticket_id)
                )
            else:
                await db.execute(
                    "UPDATE tickets SET status=? WHERE id=?",
                    (status, ticket_id)
                )
            await db.commit()
            return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении статуса тикета {ticket_id}: {e}")
        return False

async def add_ticket_message(ticket_id: int, sender: str, sender_id: int, text: str) -> bool:
    """Добавить сообщение в тикет"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO ticket_messages (ticket_id, sender, sender_id, text) VALUES (?, ?, ?, ?)",
                (ticket_id, sender, sender_id, text)
            )
            await db.commit()
            return True
    except Exception as e:
        logging.error(f"Ошибка при добавлении сообщения в тикет {ticket_id}: {e}")
        return False

def format_ticket_info(ticket_data):
    """Форматировать информацию о тикете"""
    ticket_id, nickname, description, status, category, priority = ticket_data
    status_emoji = STATUS_EMOJIS.get(status, '❓')
    short_desc = description[:100] + '...' if len(description) > 100 else description
    
    return (
        f'🎫 <b>Тикет #{ticket_id}</b>\n'
        f'👤 <b>Игрок:</b> {nickname}\n'
        f'🏷️ <b>Категория:</b> {category}\n'
        f'⚡ <b>Приоритет:</b> {priority}\n'
        f'📝 <b>Описание:</b> {short_desc}\n'
        f'<b>Статус:</b> {status_emoji} {status.capitalize()}'
    )

def format_stats(stats):
    """Форматировать статистику"""
    text = (
        f'📊 <b>Статистика системы тикетов</b>\n\n'
        f'🎫 <b>Всего тикетов:</b> {stats.get("total", 0)}\n'
        f'🟢 <b>Открытых:</b> {stats.get("open", 0)}\n'
        f'🟡 <b>В работе:</b> {stats.get("in_progress", 0)}\n'
        f'🔴 <b>Закрытых:</b> {stats.get("closed", 0)}\n\n'
    )
    
    categories = stats.get('categories', {})
    if categories and isinstance(categories, dict):
        text += '📈 <b>По категориям:</b>\n'
        for category, count in categories.items():
            text += f'• {category}: {count}\n'
    
    return text

def format_message_history(messages):
    """Форматировать историю сообщений"""
    if not messages:
        return '📜 История сообщений пуста.'
    
    history = []
    for sender, text, timestamp in messages:
        sender_label = '👤 Игрок' if sender == 'user' else '🛡️ Админ'
        time_str = timestamp[11:16] if timestamp else '--:--'
        history.append(f'<b>{sender_label}</b> [{time_str}]: {text}')
    
    return '📜 <b>История сообщений:</b>\n\n' + '\n\n'.join(history)

def validate_nickname(nickname: str) -> bool:
    """Проверить валидность никнейма"""
    return len(nickname) >= 2 and len(nickname) <= 50

def validate_description(description: str) -> bool:
    """Проверить валидность описания"""
    return len(description) >= 10 and len(description) <= 2000

def get_priority_emoji(priority: str) -> str:
    """Получить эмодзи для приоритета"""
    emojis = {
        'Низкий': '🟢',
        'Средний': '🟡', 
        'Высокий': '🔴'
    }
    return emojis.get(priority, '❓')

def get_category_emoji(category: str) -> str:
    """Получить эмодзи для категории"""
    emojis = {
        'Техническая проблема': '🛠️',
        'Жалоба на игрока': '🚩',
        'Вопрос по оплате': '💸',
        'Другое': '❓'
    }
    return emojis.get(category, '📝') 