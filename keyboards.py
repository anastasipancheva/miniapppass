from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database import Database
from constants import ROLES
import logging

logger = logging.getLogger(__name__)


def get_main_menu_keyboard(role: str) -> ReplyKeyboardMarkup:
    """Получить главное меню в зависимости от роли"""
    builder = ReplyKeyboardBuilder()
    
    if role == ROLES["STUDENT"]:
        builder.row(KeyboardButton(text="📅 Мои уроки"))
        builder.row(KeyboardButton(text="📚 Мои ДЗ"))
        builder.row(KeyboardButton(text="ℹ️ Помощь"))
        
    elif role == ROLES["ADMIN"]:
        builder.row(KeyboardButton(text="⚙️ Настроить профиль"))
        builder.row(KeyboardButton(text="👥 Мои ученики"), KeyboardButton(text="📚 Задать ДЗ"))
        builder.row(KeyboardButton(text="📊 Управление расписанием"), KeyboardButton(text="🕐 Свободные окна"))
        builder.row(KeyboardButton(text="📋 Заявки учеников"), KeyboardButton(text="📈 Статистика"))
        builder.row(KeyboardButton(text="ℹ️ Помощь"))
        
    elif role == ROLES["SUPERADMIN"]:
        builder.row(KeyboardButton(text="👑 Суперадмин-меню"))
        builder.row(KeyboardButton(text="⚙️ Настроить профиль"))
        builder.row(KeyboardButton(text="👥 Мои ученики"), KeyboardButton(text="📚 Задать ДЗ"))
        builder.row(KeyboardButton(text="📊 Управление расписанием"), KeyboardButton(text="🕐 Свободные окна"))
        builder.row(KeyboardButton(text="📋 Заявки учеников"), KeyboardButton(text="📈 Статистика"))
        builder.row(KeyboardButton(text="ℹ️ Помощь"))
    
    builder.row(KeyboardButton(text="🏠 Главное меню"))
    return builder.as_markup(resize_keyboard=True)


def get_admin_homework_content_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора типа домашнего задания"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📝 Текст", callback_data="hw_type_text"),
        InlineKeyboardButton(text="📷 Фото", callback_data="hw_type_photo")
    )
    builder.row(
        InlineKeyboardButton(text="📁 Файл", callback_data="hw_type_file"),
        InlineKeyboardButton(text="🎤 Голос", callback_data="hw_type_voice")
    )
    builder.row(
        InlineKeyboardButton(text="🎥 Видео", callback_data="hw_type_video")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="hw_type_cancel")
    )
    
    return builder.as_markup()


def get_student_homework_content_keyboard(include_cancel: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для выбора типа сдачи ДЗ студентом"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📝 Текст", callback_data="submit_text"),
        InlineKeyboardButton(text="📷 Фото", callback_data="submit_photo")
    )
    builder.row(
        InlineKeyboardButton(text="📁 Файл", callback_data="submit_file"),
        InlineKeyboardButton(text="🎤 Голос", callback_data="submit_voice")
    )
    builder.row(
        InlineKeyboardButton(text="🎥 Видео", callback_data="submit_video")
    )
    
    if include_cancel:
        builder.row(
            InlineKeyboardButton(text="❌ Отмена", callback_data="submit_cancel")
        )
    
    return builder.as_markup()


async def get_tutors_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру со списком репетиторов"""
    try:
        tutors = await Database.get_all_tutors()
        builder = InlineKeyboardBuilder()
        
        if not tutors:
            builder.add(InlineKeyboardButton(
                text="❌ Нет доступных репетиторов",
                callback_data="no_tutors"
            ))
        else:
            for tutor in tutors:
                tutor_id, name, username, subjects, cost, link = tutor
                display_name = f"👨‍🏫 {name} - {subjects}"
                builder.add(InlineKeyboardButton(
                    text=display_name,
                    callback_data=f"select_tutor_{tutor_id}"
                ))
        
        builder.adjust(1)
        return builder.as_markup()
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания клавиатуры репетиторов: {e}")
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="❌ Ошибка загрузки",
            callback_data="error"
        ))
        return builder.as_markup()


def get_superadmin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура меню суперадмина"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(KeyboardButton(text="➕ Добавить репетитора"))
    builder.row(KeyboardButton(text="🗑️ Удалить репетитора"), KeyboardButton(text="👥 Управление ролями"))
    builder.row(KeyboardButton(text="📊 Статистика системы"), KeyboardButton(text="📋 Список репетиторов"))
    builder.row(KeyboardButton(text="⚙️ Настройки системы"), KeyboardButton(text="ℹ️ Помощь"))
    builder.row(KeyboardButton(text="🏠 Главное меню"))
    
    return builder.as_markup(resize_keyboard=True)


def get_cancel_button() -> ReplyKeyboardMarkup:
    """Кнопка отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"{action}_yes_{item_id}"),
        InlineKeyboardButton(text="❌ Нет", callback_data=f"{action}_no_{item_id}")
    )
    
    return builder.as_markup()


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора роли"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👨‍🎓 Студент", callback_data="role_student"),
        InlineKeyboardButton(text="👨‍🏫 Репетитор", callback_data="role_admin")
    )
    builder.row(
        InlineKeyboardButton(text="👑 Суперадмин", callback_data="role_superadmin"),
        InlineKeyboardButton(text="📁 Архив", callback_data="role_archived")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="role_cancel")
    )
    
    return builder.as_markup()


async def get_tutors_for_deletion_keyboard(tutors) -> InlineKeyboardMarkup:
    """Клавиатура для удаления репетиторов"""
    builder = InlineKeyboardBuilder()
    
    for tutor in tutors:
        tutor_id, name, username, subjects, cost, link = tutor
        builder.add(InlineKeyboardButton(
            text=f"🗑️ {name}",
            callback_data=f"delete_tutor_{tutor_id}"
        ))
    
    builder.adjust(1)
    return builder.as_markup()
