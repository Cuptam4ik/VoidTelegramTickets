from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
import aiosqlite
import logging
from config import ADMIN_IDS, SUPPORT_GROUP_ID
from keyboards import get_user_keyboard, get_back_keyboard, get_category_keyboard, get_priority_keyboard, get_done_keyboard, get_inline_back_keyboard, get_chat_back_keyboard
import re

router = Router()
logger = logging.getLogger(__name__)

class TicketCreation(StatesGroup):
    waiting_for_category = State()
    waiting_for_priority = State()
    waiting_for_nickname = State()
    waiting_for_description = State()
    waiting_for_evidence = State()

class UserChat(StatesGroup):
    chatting_with_admin = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    welcome_text = "🎮 Добро пожаловать в систему тикетов Void!\n\n"
    if is_admin:
        welcome_text += "👨‍💼 Вы вошли как администратор.\n"
        welcome_text += "Доступные функции:\n"
        welcome_text += "• Создание тикетов\n"
        welcome_text += "• Просмотр админ-панели\n"
        welcome_text += "• Просмотр статистики\n"
        from keyboards import get_admin_keyboard
        await message.answer(welcome_text, reply_markup=get_admin_keyboard())
    else:
        welcome_text += "🎯 Вы можете создать тикет для получения помощи.\n"
        welcome_text += "Доступные функции:\n"
        welcome_text += "• Создание тикетов\n"
        welcome_text += "• Просмотр статистики\n"
        await message.answer(welcome_text, reply_markup=get_user_keyboard())

@router.message(F.text == "📝 Создать тикет")
async def handle_create_ticket_button(message: Message, state: FSMContext):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    await create_ticket_start(message, state)

@router.message(F.text == "📋 Админ-панель")
async def handle_admin_panel_button(message: Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    from handlers.admin import admin_panel
    await admin_panel(message)

@router.message(F.text == "📊 Статистика")
async def handle_statistics_button(message: Message):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    await message.answer("📊 Функция статистики пока не реализована.")

@router.callback_query(lambda c: c.data.startswith('cat_'))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    logger.info(f"Пользователь {callback.from_user.id} выбрал категорию: {callback.data}")
    await callback.answer()
    
    category = callback.data.split('_')[1]
    category_names = {
        'tech': 'Техническая проблема',
        'report': 'Жалоба на игрока', 
        'payment': 'Вопрос по оплате',
        'other': 'Другое'
    }
    
    await state.update_data(category=category_names.get(category, 'Другое'))
    await state.set_state(TicketCreation.waiting_for_priority)
    
    await callback.message.edit_text(
        f"📋 Категория: {category_names.get(category, 'Другое')}\n\n"
        "🎯 Выберите приоритет:",
        reply_markup=get_priority_keyboard()
    )

@router.callback_query(lambda c: c.data.startswith('prio_'))
async def process_priority_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора приоритета"""
    logger.info(f"Пользователь {callback.from_user.id} выбрал приоритет: {callback.data}")
    await callback.answer()
    
    priority = callback.data.split('_')[1]
    priority_names = {
        'low': 'Низкий',
        'medium': 'Средний',
        'high': 'Высокий'
    }
    
    await state.update_data(priority=priority_names.get(priority, 'Средний'))
    await state.set_state(TicketCreation.waiting_for_nickname)
    await callback.message.edit_text(
        f"🎯 Приоритет: {priority_names.get(priority, 'Средний')}\n\n"
        "👤 Введите ваш игровой никнейм:",
        reply_markup=get_inline_back_keyboard()
    )

@router.callback_query(lambda c: c.data == 'back_to_priority')
async def back_to_priority(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(TicketCreation.waiting_for_priority)
    await callback.message.edit_text(
        "🎯 Выберите приоритет:",
        reply_markup=get_priority_keyboard()
    )

@router.message(TicketCreation.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    if message.text == "⬅️ Назад":
        await state.set_state(TicketCreation.waiting_for_priority)
        await message.answer(
            "🎯 Выберите приоритет:",
            reply_markup=get_priority_keyboard()
        )
        return

    nickname = message.text.strip()
    if len(nickname) < 3 or not re.fullmatch(r'[A-Za-z0-9_]+', nickname):
        await message.answer("❗ Никнейм должен содержать не менее 3 символов, только латинские буквы, цифры и подчёркивания. Введите корректный никнейм:")
        return

    await state.update_data(nickname=nickname)
    await state.set_state(TicketCreation.waiting_for_description)
    await message.answer(
        "📝 Опишите вашу проблему:",
        reply_markup=get_back_keyboard()
    )

@router.message(TicketCreation.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания тикета"""
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    if message.text == "⬅️ Назад":
        await state.set_state(TicketCreation.waiting_for_priority)
        await message.answer(
            "🎯 Выберите приоритет:",
            reply_markup=get_priority_keyboard()
        )
        return
    
    if len(message.text) < 10:
        await message.answer("❗ Причина должна быть не менее 10 символов. Опишите подробнее:")
        return

    await state.update_data(description=message.text)
    await state.set_state(TicketCreation.waiting_for_evidence)
    
    await message.answer(
        "📎 Отправьте скриншот или файл (или нажмите 'Готово'):",
        reply_markup=get_done_keyboard()
    )

@router.message(TicketCreation.waiting_for_evidence)
async def process_evidence(message: Message, state: FSMContext):
    """Обработка доказательств"""
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    if message.text == "⬅️ Назад":
        await state.set_state(TicketCreation.waiting_for_description)
        await message.answer(
            "📝 Опишите вашу проблему:",
            reply_markup=get_back_keyboard()
        )
        return

    file_id = None
    file_type = None
    file_name = None
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.document:
        file_id = message.document.file_id
        file_type = 'document'
        file_name = message.document.file_name
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
        file_name = getattr(message.video, 'file_name', None)

    if file_id and file_type:
        # Сохраняем файл во временное хранилище в state
        files = (await state.get_data()).get('files', [])
        files.append({'file_id': file_id, 'file_type': file_type, 'file_name': file_name})
        await state.update_data(files=files)
        await message.answer(
            "📎 Файл сохранен! Отправьте еще файлы или нажмите 'Готово':",
            reply_markup=get_done_keyboard()
        )
    else:
        await message.answer(
            "❗ Пожалуйста, отправьте файл (фото, документ или видео) или нажмите 'Готово'.",
            reply_markup=get_done_keyboard()
        )

def get_user_ticket_keyboard(ticket_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Войти в чат тикета", callback_data=f"user_chat_{ticket_id}")]
        ]
    )

@router.callback_query(lambda c: c.data == 'evidence_done')
async def finish_ticket_creation(callback: CallbackQuery, state: FSMContext):
    """Завершение создания тикета"""
    logger.info(f"Пользователь {callback.from_user.id} завершает создание тикета")
    await callback.answer()

    data = await state.get_data()

    if not data.get('description'):
        await callback.answer("❌ Описание обязательно!", show_alert=True)
        return
    if not data.get('nickname'):
        await callback.answer("❌ Никнейм обязателен!", show_alert=True)
        return
    # Сохраняем тикет в БД
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            INSERT INTO tickets (user_id, nickname, category, priority, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            callback.from_user.id,
            data.get('nickname', callback.from_user.username or callback.from_user.first_name),
            data.get('category', 'Другое'),
            data.get('priority', 'Средний'),
            data.get('description'),
            'open'
        ))
        await db.commit()
        ticket_id = cursor.lastrowid

        # Сохраняем все файлы из state в ticket_files
        files = data.get('files', [])
        for f in files:
            await db.execute('''
                INSERT INTO ticket_files (ticket_id, file_id, file_type, file_name)
                VALUES (?, ?, ?, ?)
            ''', (ticket_id, f['file_id'], f['file_type'], f['file_name']))
        await db.commit()

    # Создаём тему в группе поддержки
    print(f"🔍 DEBUG: Создание темы для тикета #{ticket_id}")
    print(f"   📋 Группа: {SUPPORT_GROUP_ID}")
    print(f"   👤 Пользователь: {data.get('nickname', callback.from_user.username or callback.from_user.first_name)}")
    
    try:
        topic = await callback.bot.create_forum_topic(
            chat_id=SUPPORT_GROUP_ID,
            name=f"Тикет #{ticket_id}: {data.get('nickname', callback.from_user.username or callback.from_user.first_name)}"
        )
        message_thread_id = topic.message_thread_id
        print(f"   ✅ Тема создана с thread_id: {message_thread_id}")
        
        # Сохраняем соответствие ticket_id <-> message_thread_id
        async with aiosqlite.connect('tickets.db') as db:
            await db.execute('INSERT INTO ticket_threads (ticket_id, message_thread_id) VALUES (?, ?)', (ticket_id, message_thread_id))
            await db.commit()
            print(f"   💾 Связь сохранена в БД")
        
        # Отправляем кнопки действий в тему
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
        
        await callback.bot.send_message(
            SUPPORT_GROUP_ID,
            f"🆕 Новый тикет #{ticket_id}\n\n"
            f"👤 От: {data.get('nickname', callback.from_user.username or callback.from_user.first_name)}\n"
            f"📋 Категория: {data.get('category', 'Другое')}\n"
            f"🎯 Приоритет: {data.get('priority', 'Средний')}\n"
            f"📝 Описание: {data.get('description', 'Нет описания')}\n\n"
            f"🔧 Быстрые действия:",
            message_thread_id=message_thread_id,
            reply_markup=keyboard
        )
        
        # Пересылаем все файлы тикета в тему
        files = data.get('files', [])
        for idx, f in enumerate(files, 1):
            caption = f"📎 Файл от игрока"
            if f.get('file_name'):
                caption += f" ({f['file_name']})"
            caption += f" [{idx}/{len(files)}]"
            try:
                if f['file_type'] == 'photo':
                    await callback.bot.send_photo(SUPPORT_GROUP_ID, f['file_id'], caption=caption, message_thread_id=message_thread_id)
                elif f['file_type'] == 'video':
                    await callback.bot.send_video(SUPPORT_GROUP_ID, f['file_id'], caption=caption, message_thread_id=message_thread_id)
                elif f['file_type'] == 'document':
                    await callback.bot.send_document(SUPPORT_GROUP_ID, f['file_id'], caption=caption, message_thread_id=message_thread_id)
                else:
                    await callback.bot.send_message(SUPPORT_GROUP_ID, f"{caption}: <code>{f['file_id']}</code>", message_thread_id=message_thread_id, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Ошибка отправки файла в тему тикета: {e}")
        
        logger.info(f"Создана тема для тикета #{ticket_id} с thread_id {message_thread_id}")
        
    except Exception as e:
        print(f"   ❌ Ошибка создания темы: {e}")
        logger.error(f"Ошибка создания форум-темы для тикета #{ticket_id}: {e}")
        # Продолжаем работу без создания темы
        message_thread_id = None

    # Уведомляем админов
    from handlers.admin import notify_admins_new_ticket
    await notify_admins_new_ticket(ticket_id, data, callback.from_user)

    # Сбрасываем состояние
    await state.clear()

    # Отправляем подтверждение пользователю и кнопку для чата
    user_id = callback.from_user.id
    is_admin = user_id in ADMIN_IDS

    await callback.message.edit_text(
        f"✅ Тикет #{ticket_id} успешно создан!\n\n"
        f"📋 Категория: {data.get('category', 'Другое')}\n"
        f"🎯 Приоритет: {data.get('priority', 'Средний')}\n"
        f"📝 Описание: {data.get('description')}\n\n"
        "⏳ Ожидайте ответа от администрации."
    )

    # Сразу переводим пользователя в режим чата с поддержкой по тикету
    await state.set_state(UserChat.chatting_with_admin)
    await state.update_data(ticket_id=ticket_id, message_thread_id=message_thread_id)
    if message_thread_id:
        await callback.message.answer(
            f"✉️ Вы можете написать сообщение в тикет #{ticket_id}. Просто отправьте текст или файл:",
            reply_markup=get_chat_back_keyboard()
        )
    else:
        await callback.message.answer(
            f"✉️ Вы можете написать сообщение в тикет #{ticket_id}. Просто отправьте текст или файл:\n\n⚠️ <i>Тема не была создана, сообщения будут отправляться в общий чат группы</i>",
            reply_markup=get_chat_back_keyboard(),
            parse_mode="HTML"
        )

    if is_admin:
        from keyboards import get_admin_keyboard
        await callback.message.answer("Главное меню:", reply_markup=get_admin_keyboard())

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    """Показ статистики тикетов"""
    logger.info(f"Пользователь {message.from_user.id} запросил статистику")
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        
        if is_admin:
            # Статистика для админа
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
                    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_count
                FROM tickets
            ''')
            stats = await cursor.fetchone()
            
            stats_text = f"📊 Статистика тикетов:\n\n"
            stats_text += f"📋 Всего тикетов: {stats['total']}\n"
            stats_text += f"🆕 Открытых: {stats['open_count']}\n"
            stats_text += f"🛠️ В работе: {stats['in_progress_count']}\n"
            stats_text += f"✅ Закрытых: {stats['closed_count']}\n"
        else:
            # Статистика для пользователя
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
                    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_count
                FROM tickets WHERE user_id = ?
            ''', (user_id,))
            stats = await cursor.fetchone()
            
            stats_text = f"📊 Ваши тикеты:\n\n"
            stats_text += f"📋 Всего тикетов: {stats['total']}\n"
            stats_text += f"🆕 Открытых: {stats['open_count']}\n"
            stats_text += f"🛠️ В работе: {stats['in_progress_count']}\n"
            stats_text += f"✅ Закрытых: {stats['closed_count']}\n"
    
    await message.answer(stats_text)

@router.callback_query(lambda c: c.data.startswith('user_chat_'))
async def start_user_chat(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split('_')[2])
    # Получить message_thread_id
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT message_thread_id FROM ticket_threads WHERE ticket_id = ?', (ticket_id,))
        row = await cursor.fetchone()
    
    message_thread_id = row['message_thread_id'] if row else None
    
    await state.set_state(UserChat.chatting_with_admin)
    await state.update_data(ticket_id=ticket_id, message_thread_id=message_thread_id)
    
    if message_thread_id:
        await callback.message.edit_text(
            f"✉️ Вы можете написать сообщение в тикет #{ticket_id}. Просто отправьте текст или файл:",
            reply_markup=get_chat_back_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"✉️ Вы можете написать сообщение в тикет #{ticket_id}. Просто отправьте текст или файл:\n\n⚠️ <i>Тема не была создана, сообщения будут отправляться в общий чат группы</i>",
            reply_markup=get_chat_back_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.message(UserChat.chatting_with_admin)
async def relay_user_to_admin(message: Message, state: FSMContext):
    """Пересылка сообщений пользователя из бота в тему группы поддержки"""
    from config import SUPPORT_GROUP_ID
    
    # Проверяем, не является ли это кнопкой "Назад"
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("🔙 Вы вышли из режима чата", reply_markup=get_user_keyboard())
        return

    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    thread_id = data.get('message_thread_id')

    if not ticket_id:
        await message.answer("❌ Ошибка: не найден ID тикета")
        return

    # Проверяем статус тикета
    async with aiosqlite.connect('tickets.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT status FROM tickets WHERE id = ?', (ticket_id,))
        row = await cursor.fetchone()
    if row is None:
        await state.clear()
        await message.answer("❌ Тикет не найден. Вы больше не можете отправлять сообщения по этому тикету.", reply_markup=get_user_keyboard())
        return
    if row['status'] == 'closed':
        await state.clear()
        await message.answer("❌ Тикет закрыт. Вы больше не можете отправлять сообщения по этому тикету.", reply_markup=get_user_keyboard())
        return
    
    # Если тема не была создана, отправляем обычное сообщение в группу
    if not thread_id:
        try:
            # Пересылаем текст/файл в группу без темы
            if message.text:
                await message.bot.send_message(SUPPORT_GROUP_ID, f"👤 Игрок (тикет #{ticket_id}): {message.text}")
                message_text = message.text
            elif message.photo:
                caption = f"👤 Игрок (тикет #{ticket_id}): {message.caption}" if message.caption else f"👤 Игрок (тикет #{ticket_id}): [Фото]"
                await message.bot.send_photo(SUPPORT_GROUP_ID, message.photo[-1].file_id, caption=caption)
                message_text = message.caption or "[Фото]"
            elif message.document:
                caption = f"👤 Игрок (тикет #{ticket_id}): {message.caption}" if message.caption else f"👤 Игрок (тикет #{ticket_id}): [Документ]"
                await message.bot.send_document(SUPPORT_GROUP_ID, message.document.file_id, caption=caption)
                message_text = message.caption or f"[Документ: {message.document.file_name}]"
            elif message.video:
                caption = f"👤 Игрок (тикет #{ticket_id}): {message.caption}" if message.caption else f"👤 Игрок (тикет #{ticket_id}): [Видео]"
                await message.bot.send_video(SUPPORT_GROUP_ID, message.video.file_id, caption=caption)
                message_text = message.caption or "[Видео]"
            else:
                await message.bot.send_message(SUPPORT_GROUP_ID, f"👤 Игрок (тикет #{ticket_id}): [Сообщение]")
                message_text = "[Сообщение]"
            
            # Сохраняем сообщение в базу данных
            async with aiosqlite.connect('tickets.db') as db:
                await db.execute(
                    "INSERT INTO ticket_messages (ticket_id, user_id, message_text, is_admin) VALUES (?, ?, ?, ?)",
                    (ticket_id, message.from_user.id, message_text, False)
                )
                await db.commit()
            
            await message.answer("✅ Сообщение отправлено в поддержку (без темы)")
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователя в группу: {e}")
            await message.answer("❌ Ошибка отправки сообщения")
        return
    
    # Пересылаем сообщение в тему
    try:
        if message.text:
            await message.bot.send_message(SUPPORT_GROUP_ID, f"👤 Игрок: {message.text}", message_thread_id=thread_id)
            message_text = message.text
        elif message.photo:
            caption = f"👤 Игрок: {message.caption}" if message.caption else "👤 Игрок: [Фото]"
            await message.bot.send_photo(SUPPORT_GROUP_ID, message.photo[-1].file_id, caption=caption, message_thread_id=thread_id)
            message_text = message.caption or "[Фото]"
        elif message.document:
            caption = f"👤 Игрок: {message.caption}" if message.caption else "👤 Игрок: [Документ]"
            await message.bot.send_document(SUPPORT_GROUP_ID, message.document.file_id, caption=caption, message_thread_id=thread_id)
            message_text = message.caption or f"[Документ: {message.document.file_name}]"
        elif message.video:
            caption = f"👤 Игрок: {message.caption}" if message.caption else "👤 Игрок: [Видео]"
            await message.bot.send_video(SUPPORT_GROUP_ID, message.video.file_id, caption=caption, message_thread_id=thread_id)
            message_text = message.caption or "[Видео]"
        else:
            await message.bot.send_message(SUPPORT_GROUP_ID, "👤 Игрок: [Сообщение]", message_thread_id=thread_id)
            message_text = "[Сообщение]"
        
        # Сохраняем сообщение в базу данных
        async with aiosqlite.connect('tickets.db') as db:
            await db.execute(
                "INSERT INTO ticket_messages (ticket_id, user_id, message_text, is_admin) VALUES (?, ?, ?, ?)",
                (ticket_id, message.from_user.id, message_text, False)
            )
            await db.commit()
        
        await message.answer("✅ Сообщение отправлено в поддержку")
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователя в тему: {e}")
        await message.answer("❌ Ошибка отправки сообщения")

@router.callback_query(lambda c: c.data == 'back_to_main')
async def back_to_main_from_chat(callback: CallbackQuery, state: FSMContext):
    """Выход из режима чата по inline кнопке"""
    await state.clear()
    await callback.message.edit_text(
        "🔙 Вы вышли из режима чата",
        reply_markup=get_user_keyboard()
    )
    await callback.answer()

async def create_ticket_start(message: Message, state: FSMContext):
    """Начало создания тикета"""
    logger.info(f"Пользователь {message.from_user.id} начал создание тикета")
    await state.set_state(TicketCreation.waiting_for_category)
    await message.answer(
        "📋 Выберите категорию тикета:",
        reply_markup=get_category_keyboard()
    ) 