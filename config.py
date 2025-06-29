# Конфигурация бота
import os
from typing import List

# Токен бота (замените на свой)
API_TOKEN = '7870294015:AAGA60yYU5xQzpr4O2QNq7VHV51rI12h5OI'
BOT_TOKEN = API_TOKEN  # Алиас для совместимости

# ID администраторов (замените на реальные ID)
ADMINS: List[int] = [1218149074]
ADMIN_IDS = ADMINS  # Алиас для совместимости

# Настройки базы данных
DB_PATH = 'tickets.db'

# Настройки тикетов
MAX_DESCRIPTION_LENGTH = 2000
MIN_DESCRIPTION_LENGTH = 10
MIN_NICKNAME_LENGTH = 2
MAX_EVIDENCE_FILES = 10

# Категории тикетов
TICKET_CATEGORIES = {
    'cat_tech': 'Техническая проблема',
    'cat_report': 'Жалоба на игрока', 
    'cat_pay': 'Вопрос по оплате',
    'cat_other': 'Другое'
}

# Приоритеты тикетов
TICKET_PRIORITIES = {
    'prio_low': 'Низкий',
    'prio_med': 'Средний', 
    'prio_high': 'Высокий'
}

# Статусы тикетов
TICKET_STATUSES = {
    'open': 'Открыт',
    'in_progress': 'В работе',
    'closed': 'Закрыт'
}

# Эмодзи для статусов
STATUS_EMOJIS = {
    'open': '🟢',
    'in_progress': '🟡',
    'closed': '🔴'
}

# Сообщения
MESSAGES = {
    'welcome': '👋 <b>Добро пожаловать в поддержку VoidSeven!</b>\nВыберите действие:',
    'no_access': '❌ Нет доступа',
    'ticket_created': '🎫 <b>Ваш тикет создан!</b>\nОжидайте ответа администратора.',
    'ticket_closed': '✅ <b>Ваш тикет закрыт!</b>\n\nСпасибо за обращение!',
    'ticket_taken': '🛠️ <b>Ваш тикет взят в работу!</b>\n\nТеперь вы можете общаться с администратором здесь.',
    'new_ticket_notification': '🆕 <b>Новый тикет!</b>\n\n👤 Игрок: {nickname}\n🏷️ Категория: {category}\n⚡ Приоритет: {priority}\n📝 Описание: {description}',
    'no_open_tickets': '✅ Нет открытых тикетов.',
    'history_empty': '📜 История сообщений пуста.',
    'active_ticket_reset': '✅ Активный тикет сброшен.',
    'no_active_ticket': 'ℹ️ У вас нет активного тикета.'
}

# Команды
COMMANDS = {
    'start': 'Главное меню',
    'help': 'Справка',
    'stats': 'Статистика тикетов',
    'reset': 'Сбросить активный тикет'
}

# ID канала для логов закрытых тикетов
LOG_CHANNEL_ID = -1002523330020  # Замените на свой ID канала

# ID группы поддержки, где бот будет создавать темы для тикетов
SUPPORT_GROUP_ID = -1002523330020  # Замените на свой ID группы поддержки 