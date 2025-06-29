from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура пользователя

def get_user_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📝 Создать тикет'), KeyboardButton(text='📊 Статистика')]
        ],
        resize_keyboard=True
    )

# Клавиатура админа

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📝 Создать тикет'), KeyboardButton(text='📊 Статистика')]
        ],
        resize_keyboard=True
    )

# Клавиатура "Назад"
def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='⬅️ Назад')]
        ],
        resize_keyboard=True
    )

# Клавиатура выбора категории

def get_category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🔧 Техническая проблема', callback_data='cat_tech'),
                InlineKeyboardButton(text='🚨 Жалоба на игрока', callback_data='cat_report')
            ],
            [
                InlineKeyboardButton(text='💳 Вопрос по оплате', callback_data='cat_payment'),
                InlineKeyboardButton(text='❓ Другое', callback_data='cat_other')
            ]
        ]
    )

# Клавиатура выбора приоритета

def get_priority_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🟢 Низкий', callback_data='prio_low'),
                InlineKeyboardButton(text='🟡 Средний', callback_data='prio_medium'),
                InlineKeyboardButton(text='🔴 Высокий', callback_data='prio_high')
            ]
        ]
    )

# Клавиатура "Готово"
def get_done_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Готово', callback_data='evidence_done')]
        ]
    )

# Клавиатура действий с тикетом

def get_ticket_actions_keyboard(ticket_id: int, status: str = 'open') -> InlineKeyboardMarkup:
    rows = []
    if status in ('open', 'in_progress'):
        row = [InlineKeyboardButton(text='💬 Чат с игроком', callback_data=f'chat_ticket_{ticket_id}')]
        if status == 'open':
            row.append(InlineKeyboardButton(text='🛠️ Взять в работу', callback_data=f'take_ticket_{ticket_id}'))
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text='📜 История', callback_data=f'history_ticket_{ticket_id}'),
        InlineKeyboardButton(text='📎 Файлы', callback_data=f'files_ticket_{ticket_id}')
    ])
    if status == 'in_progress':
        rows.append([InlineKeyboardButton(text='🔒 Закрыть', callback_data=f'close_ticket_{ticket_id}')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# Клавиатура быстрых ответов

def get_quick_replies_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='👋 Приветствие', callback_data='quick_greeting'),
                InlineKeyboardButton(text='⏳ Подождите', callback_data='quick_wait')
            ],
            [
                InlineKeyboardButton(text='✅ Решено', callback_data='quick_solved'),
                InlineKeyboardButton(text='🔒 Закрыть', callback_data='quick_closed')
            ],
            [
                InlineKeyboardButton(text='🔄 Передать', callback_data='quick_escalate'),
                InlineKeyboardButton(text='ℹ️ Инфо', callback_data='quick_info')
            ],
            [InlineKeyboardButton(text='⬅️ Назад к панели', callback_data='back_to_panel')],
            [InlineKeyboardButton(text='❌ Завершить чат', callback_data='end_chat')]
        ]
    )

def get_inline_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_priority')]
        ]
    )

def get_chat_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⬅️ Выйти из чата', callback_data='back_to_main')]
        ]
    )

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[]
    )