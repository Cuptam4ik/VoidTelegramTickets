from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS, SUPPORT_GROUP_ID
from keyboards import get_user_keyboard, get_admin_keyboard

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    help_text = "🎮 Помощь по системе тикетов Void\n\n"
    help_text += "📝 Основные команды:\n"
    help_text += "/start - Запуск бота\n"
    help_text += "/help - Показать эту справку\n\n"
    
    if is_admin:
        help_text += "👨‍💼 Админские функции:\n"
        help_text += "• Просмотр всех тикетов\n"
        help_text += "• Взятие тикетов в работу\n"
        help_text += "• Чат с пользователями\n"
        help_text += "• Закрытие тикетов\n"
        help_text += "• Быстрые ответы\n"
        help_text += "• Просмотр статистики\n"
        help_text += "• /check_group_status - Проверка статуса группы\n\n"
        help_text += "💡 Используйте кнопки в меню для навигации."
        await message.answer(help_text, reply_markup=get_admin_keyboard())
    else:
        help_text += "🎯 Пользовательские функции:\n"
        help_text += "• Создание тикетов\n"
        help_text += "• Просмотр статистики своих тикетов\n"
        help_text += "• Получение уведомлений\n\n"
        help_text += "💡 Используйте кнопки в меню для навигации."
        await message.answer(help_text, reply_markup=get_user_keyboard())

@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    """Обработчик команды /cancel для отмены текущего действия"""
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    await message.answer(
        "❌ Действие отменено",
        reply_markup=get_admin_keyboard() if is_admin else get_user_keyboard()
    )

@router.message(F.text & ~F.text.startswith('/'))
async def handle_unknown_message(message: Message):
    """Обработчик неизвестных сообщений"""
    if message.chat.id == SUPPORT_GROUP_ID:
        return
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    await message.answer(
        "❓ Неизвестная команда. Используйте /help для получения справки.",
        reply_markup=get_admin_keyboard() if is_admin else get_user_keyboard()
    ) 