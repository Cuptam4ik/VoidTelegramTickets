from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
import aiosqlite
import logging
from config import ADMIN_IDS, LOG_CHANNEL_ID, SUPPORT_GROUP_ID
from keyboards import get_admin_keyboard, get_ticket_actions_keyboard, get_quick_replies_keyboard, get_admin_panel_keyboard

router = Router()
logger = logging.getLogger(__name__)

class AdminChat(StatesGroup):
    chatting_with_user = State()

# Словарь для хранения активных чатов админов
admin_active_chats = {}

@router.message(F.text == "📋 Админ-панель")
async def admin_panel(message: Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    """Показ админ-панели: для каждого тикета отправляется отдельная карточка с кнопками"""
    logger.info(f"Админ {message.from_user.id} открыл админ-панель")
    if message.from_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM tickets ORDER BY status DESC, created_at ASC')
        tickets = await cursor.fetchall()
    if not tickets:
        await message.answer("🔍 Нет тикетов в системе.")
        return
    for ticket in tickets:
        if ticket['status'] == 'closed':
            continue
        text = (
            f"<b>🗂️ Тикет #{ticket['id']}</b>\n"
            f"👤 Игрок: <b>{ticket['nickname']}</b>\n"
            f"🏷️ Категория: {get_category_icon(ticket['category'])} {get_category_name(ticket['category'])}\n"
            f"⚡ Приоритет: {get_priority_icon(ticket['priority'])} {get_priority_name(ticket['priority'])}\n"
            f"📝 Описание: {ticket['description']}\n"
            f"{get_status_icon(ticket['status'])} Статус: {get_status_name(ticket['status'])}"
        )
        keyboard = get_ticket_actions_keyboard(ticket['id'], ticket['status'])
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Вспомогательные функции для иконок и названий

def get_category_icon(category: str) -> str:
    return {
        'cat_tech': '🔧',
        'cat_report': '🚨',
        'cat_payment': '💳',
        'cat_other': '❓',
    }.get(category, '❓')

def get_category_name(category: str) -> str:
    return {
        'cat_tech': 'Техническая проблема',
        'cat_report': 'Жалоба на игрока',
        'cat_payment': 'Вопрос по оплате',
        'cat_other': 'Другое',
    }.get(category, 'Другое')

def get_priority_icon(priority: str) -> str:
    return {
        'low': '🟢',
        'medium': '🟡',
        'high': '🔴',
        'Низкий': '🟢',
        'Средний': '🟡',
        'Высокий': '🔴',
    }.get(priority, '⚪')

def get_priority_name(priority: str) -> str:
    return {
        'low': 'Низкий',
        'medium': 'Средний',
        'high': 'Высокий',
    }.get(priority, priority)

def get_status_icon(status: str) -> str:
    return {
        'open': '🟢',
        'in_progress': '🟡',
        'closed': '🔒',
    }.get(status, '⚪')

def get_status_name(status: str) -> str:
    return {
        'open': 'Открыт',
        'in_progress': 'В работе',
        'closed': 'Закрыт',
    }.get(status, status)

@router.message(F.text == "📊 Статистика")
async def admin_statistics(message: Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    """Статистика для админа"""
    logger.info(f"Админ {message.from_user.id} запросил статистику")
    if message.from_user.id not in ADMIN_IDS:
        return
    
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
                SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_count
            FROM tickets
        ''')
        stats = await cursor.fetchone()
        
        # Статистика по категориям
        cursor = await db.execute('''
            SELECT category, COUNT(*) as count 
            FROM tickets 
            GROUP BY category
        ''')
        categories = await cursor.fetchall()
        
        stats_text = f"📊 Статистика тикетов:\n\n"
        stats_text += f"📋 Всего тикетов: {stats['total']}\n"
        stats_text += f"🆕 Открытых: {stats['open_count']}\n"
        stats_text += f"🛠️ В работе: {stats['in_progress_count']}\n"
        stats_text += f"✅ Закрытых: {stats['closed_count']}\n\n"
        stats_text += "📂 По категориям:\n"
        
        for cat in categories:
            stats_text += f"• {cat['category']}: {cat['count']}\n"
    
    await message.answer(stats_text)

async def notify_admins_new_ticket(ticket_id: int, ticket_data: dict, user):
    """Уведомление админов о новом тикете"""
    notification = f"🆕 Новый тикет #{ticket_id}\n\n"
    notification += f"👤 От: {user.username or user.first_name}\n"
    notification += f"📋 Категория: {ticket_data.get('category', 'Другое')}\n"
    notification += f"🎯 Приоритет: {ticket_data.get('priority', 'Средний')}\n"
    notification += f"📝 Описание: {ticket_data.get('description', 'Нет описания')}\n"
    
    for admin_id in ADMIN_IDS:
        try:
            await user.bot.send_message(admin_id, notification)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")

@router.message()
async def relay_admin_to_user(message: Message):
    # Только сообщения из SUPPORT_GROUP_ID и из темы (топика) и не от бота
    if message.chat.id != SUPPORT_GROUP_ID:
        return
    if not getattr(message, 'message_thread_id', None):
        return
    if message.from_user.is_bot:
        return
    # Получить ticket_id по message_thread_id
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT ticket_id FROM ticket_threads WHERE message_thread_id = ?', (message.message_thread_id,))
        row = await cursor.fetchone()
    
    if not row:
        return
    
    ticket_id = row['ticket_id']
    
    # Получить user_id по ticket_id
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT user_id FROM tickets WHERE id = ?', (ticket_id,))
        ticket = await cursor.fetchone()
    
    if not ticket:
        return
    
    user_id = ticket['user_id']
    
    # Проверяем, что отправитель является админом
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # Пересылаем сообщение пользователю
    try:
        if message.text:
            await message.bot.send_message(user_id, f"💬 Админ: {message.text}")
            message_text = message.text
        elif message.photo:
            caption = f"💬 Админ: {message.caption}" if message.caption else "💬 Админ: [Фото]"
            await message.bot.send_photo(user_id, message.photo[-1].file_id, caption=caption)
            message_text = message.caption or "[Фото]"
        elif message.document:
            caption = f"💬 Админ: {message.caption}" if message.caption else "💬 Админ: [Документ]"
            await message.bot.send_document(user_id, message.document.file_id, caption=caption)
            message_text = message.caption or f"[Документ: {message.document.file_name}]"
        elif message.video:
            caption = f"💬 Админ: {message.caption}" if message.caption else "💬 Админ: [Видео]"
            await message.bot.send_video(user_id, message.video.file_id, caption=caption)
            message_text = message.caption or "[Видео]"
        else:
            # Для других типов сообщений
            await message.bot.send_message(user_id, "💬 Админ: [Сообщение]")
            message_text = "[Сообщение]"
        
        # Сохраняем сообщение в базу данных
        async with aiosqlite.connect('tickets.db') as db:
            await db.execute(
                "INSERT INTO ticket_messages (ticket_id, user_id, message_text, is_admin) VALUES (?, ?, ?, ?)",
                (ticket_id, message.from_user.id, message_text, True)
            )
            await db.commit()
            
    except Exception as e:
        logger.error(f"Ошибка пересылки сообщения админа пользователю {user_id}: {e}")
        # Отправляем уведомление админу об ошибке
        try:
            await message.reply(f"❌ Ошибка отправки сообщения пользователю: {e}")
        except:
            pass

@router.message(Command("check_group_status"))
async def check_group_status(message: Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    """Проверка статуса группы поддержки"""
    print(f"DEBUG: Получена команда check_group_status от пользователя {message.from_user.id}")
    logger.info(f"Админ {message.from_user.id} запросил проверку статуса группы")
    
    if message.from_user.id not in ADMIN_IDS:
        print(f"DEBUG: Пользователь {message.from_user.id} не в списке админов")
        await message.answer("❌ Доступ запрещен")
        return
    
    print(f"DEBUG: Пользователь {message.from_user.id} является админом, продолжаем")
    
    try:
        # Получаем информацию о группе
        chat = await message.bot.get_chat(SUPPORT_GROUP_ID)
        
        status_text = f"📋 <b>Статус группы поддержки</b>\n\n"
        status_text += f"🆔 ID группы: <code>{SUPPORT_GROUP_ID}</code>\n"
        status_text += f"📝 Название: {chat.title}\n"
        status_text += f"👥 Тип: {chat.type}\n"
        status_text += f"🔗 Ссылка: {chat.invite_link or 'Не настроена'}\n\n"
        
        # Проверяем, является ли группой
        if hasattr(chat, 'is_forum'):
            status_text += f"🏛️ Форум: {'✅ Да' if chat.is_forum else '❌ Нет'}\n"
        else:
            status_text += f"🏛️ Форум: ⚠️ Неизвестно (старая версия aiogram)\n"
        
        # Проверяем, является ли супергруппой
        if chat.type == 'supergroup':
            status_text += f"🚀 Супергруппа: ✅ Да\n"
        else:
            status_text += f"🚀 Супергруппа: ❌ Нет\n"
        
        # Проверяем права бота
        try:
            bot_member = await message.bot.get_chat_member(SUPPORT_GROUP_ID, message.bot.id)
            status_text += f"🤖 Права бота: {bot_member.status}\n"
            
            if hasattr(bot_member, 'can_post_messages'):
                status_text += f"📝 Может отправлять сообщения: {'✅ Да' if bot_member.can_post_messages else '❌ Нет'}\n"
            if hasattr(bot_member, 'can_manage_topics'):
                status_text += f"🏛️ Может управлять темами: {'✅ Да' if bot_member.can_manage_topics else '❌ Нет'}\n"
        except Exception as e:
            status_text += f"🤖 Ошибка проверки прав бота: {e}\n"
        
        # Рекомендации
        status_text += "\n💡 <b>Рекомендации:</b>\n"
        
        if chat.type != 'supergroup':
            status_text += "• Преобразуйте группу в супергруппу\n"
        
        if not getattr(chat, 'is_forum', False):
            status_text += "• Включите темы (форумы) в настройках группы\n"
        
        if chat.type == 'supergroup' and getattr(chat, 'is_forum', False):
            status_text += "✅ Группа настроена правильно для создания тем!\n"
        
        print(f"DEBUG: Отправляем ответ пользователю {message.from_user.id}")
        await message.answer(status_text, parse_mode="HTML")
        
    except Exception as e:
        print(f"DEBUG: Ошибка при проверке группы: {e}")
        error_text = f"❌ Ошибка при проверке группы:\n{str(e)}\n\n"
        error_text += f"Проверьте:\n"
        error_text += f"• Правильность SUPPORT_GROUP_ID в config.py\n"
        error_text += f"• Добавлен ли бот в группу\n"
        error_text += f"• Есть ли у бота права администратора"
        
        await message.answer(error_text)
        logger.error(f"Ошибка проверки статуса группы: {e}")

# Новые обработчики для работы в темах

@router.callback_query(lambda c: c.data.startswith('topic_quick_'))
async def topic_quick_reply(callback: CallbackQuery):
    """Быстрые ответы в темах"""
    if callback.message.chat.id != SUPPORT_GROUP_ID:
        return
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.answer()
    
    # Получить ticket_id по message_thread_id
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT ticket_id FROM ticket_threads WHERE message_thread_id = ?', (callback.message.message_thread_id,))
        row = await cursor.fetchone()
    
    if not row:
        await callback.answer("❌ Тикет не найден", show_alert=True)
        return
    
    ticket_id = row['ticket_id']
    
    # Получить user_id по ticket_id
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT user_id FROM tickets WHERE id = ?', (ticket_id,))
        ticket = await cursor.fetchone()
    
    if not ticket:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    user_id = ticket['user_id']
    
    quick_replies = {
        'topic_quick_greeting': '👋 Здравствуйте! Спасибо за обращение. Мы рассмотрим ваш тикет в ближайшее время.',
        'topic_quick_wait': '⏳ Пожалуйста, подождите. Мы работаем над решением вашей проблемы.',
        'topic_quick_solved': '✅ Ваша проблема решена! Если у вас есть еще вопросы, создайте новый тикет.',
        'topic_quick_closed': '🔒 Тикет закрыт. Если проблема не решена, создайте новый тикет.',
        'topic_quick_escalate': '🔄 Ваш тикет передан другому специалисту. Ожидайте ответа.',
        'topic_quick_info': 'ℹ️ Для получения дополнительной информации обратитесь к администрации.'
    }
    
    reply_text = quick_replies.get(callback.data, 'Сообщение отправлено')
    
    try:
        # Отправляем быстрый ответ пользователю
        await callback.bot.send_message(user_id, f"💬 Админ (тикет #{ticket_id}):\n\n{reply_text}")
        
        # Отправляем сообщение в тему
        await callback.bot.send_message(
            SUPPORT_GROUP_ID,
            f"💬 Быстрый ответ отправлен:\n\n{reply_text}",
            message_thread_id=callback.message.message_thread_id
        )
        
        # Сохраняем быстрый ответ в историю
        async with aiosqlite.connect('tickets.db') as db:
            await db.execute(
                "INSERT INTO ticket_messages (ticket_id, user_id, message_text, is_admin) VALUES (?, ?, ?, ?)",
                (ticket_id, callback.from_user.id, reply_text, True)
            )
            await db.commit()
        
        await callback.answer("✅ Быстрый ответ отправлен")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка отправки: {e}", show_alert=True)
        logger.error(f"Ошибка отправки быстрого ответа в теме: {e}")

@router.callback_query(lambda c: c.data.startswith('topic_close_'))
async def topic_close_ticket(callback: CallbackQuery):
    """Закрытие тикета из темы"""
    if callback.message.chat.id != SUPPORT_GROUP_ID:
        return
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.answer()
    
    # Получить ticket_id по message_thread_id
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT ticket_id FROM ticket_threads WHERE message_thread_id = ?', (callback.message.message_thread_id,))
        row = await cursor.fetchone()
    
    if not row:
        await callback.answer("❌ Тикет не найден", show_alert=True)
        return
    
    ticket_id = row['ticket_id']
    
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            UPDATE tickets SET status = 'closed' WHERE id = ?
        ''', (ticket_id,))
        await db.commit()
        
        if cursor.rowcount == 0:
            await callback.answer("❌ Тикет не найден", show_alert=True)
            return
        
        # Получаем информацию о тикете
        cursor = await db.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
        ticket = await cursor.fetchone()

        # Получаем историю сообщений тикета
        cursor = await db.execute('SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY created_at ASC', (ticket_id,))
        messages = await cursor.fetchall()

    # Отправляем историю в лог-канал
    if messages:
        history = f"🗂️ История тикета #{ticket_id} (закрыт):\n\n"
        for msg in messages:
            who = "Админ" if msg['is_admin'] else "Пользователь"
            history += f"[{who}] {msg['message_text']}\n"
        try:
            await callback.bot.send_message(LOG_CHANNEL_ID, history)
        except Exception as e:
            logger.error(f'Ошибка отправки истории тикета в лог-канал: {e}')

    # Уведомляем пользователя
    try:
        await callback.bot.send_message(
            ticket['user_id'],
            f"🔒 Ваш тикет #{ticket_id} закрыт администратором {callback.from_user.first_name}"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")
    
    # Отправляем сообщение в тему о закрытии
    await callback.bot.send_message(
        SUPPORT_GROUP_ID,
        f"🔒 Тикет #{ticket_id} закрыт администратором {callback.from_user.first_name}",
        message_thread_id=callback.message.message_thread_id
    )
    
    await callback.answer("✅ Тикет закрыт")

@router.callback_query(lambda c: c.data.startswith('topic_actions_'))
async def topic_show_actions(callback: CallbackQuery):
    """Показать кнопки действий в теме"""
    if callback.message.chat.id != SUPPORT_GROUP_ID:
        return
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.answer()
    
    # Создаем клавиатуру с действиями для темы
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='👋 Приветствие', callback_data='topic_quick_greeting'),
            InlineKeyboardButton(text='⏳ Подождите', callback_data='topic_quick_wait')
        ],
        [
            InlineKeyboardButton(text='✅ Решено', callback_data='topic_quick_solved'),
            InlineKeyboardButton(text='🔄 Передать', callback_data='topic_quick_escalate')
        ],
        [
            InlineKeyboardButton(text='ℹ️ Инфо', callback_data='topic_quick_info'),
            InlineKeyboardButton(text='🔒 Закрыть тикет', callback_data='topic_close_ticket')
        ]
    ])
    
    await callback.message.edit_text(
        "🔧 Действия с тикетом:",
        reply_markup=keyboard
    ) 