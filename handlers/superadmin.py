import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import (
    get_superadmin_menu_keyboard, get_tutors_for_deletion_keyboard,
    get_confirmation_keyboard, get_cancel_button, get_role_selection_keyboard
)
from states import SuperadminStates
from constants import ROLES, has_role, SUPERADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()


async def check_superadmin_rights(user_id: int) -> bool:
    """Проверка прав суперадмина с отладкой"""
    logger.info(f"🔍 Проверка прав суперадмина для пользователя {user_id}")

    # Проверяем SUPERADMIN_IDS
    if user_id in SUPERADMIN_IDS:
        logger.info(f"✅ Пользователь {user_id} найден в SUPERADMIN_IDS")
        return True
    else:
        logger.info(f"❌ Пользователь {user_id} НЕ найден в SUPERADMIN_IDS: {SUPERADMIN_IDS}")

    # Проверяем функцию has_role
    if has_role(user_id, ROLES["SUPERADMIN"]):
        logger.info(f"✅ Пользователь {user_id} прошел проверку has_role")
        return True
    else:
        logger.info(f"❌ Пользователь {user_id} НЕ прошел проверку has_role")

    # Проверяем базу данных
    try:
        user = await Database.get_user(user_id)
        if user:
            logger.info(f"👤 Пользователь {user_id} найден в БД с ролью: {user[3]}")
            if user[3] == ROLES["SUPERADMIN"]:
                logger.info(f"✅ Пользователь {user_id} имеет роль суперадмина в БД")
                return True
        else:
            logger.info(f"❌ Пользователь {user_id} НЕ найден в БД")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке пользователя {user_id} в БД: {e}")

    logger.info(f"❌ Пользователь {user_id} НЕ имеет прав суперадмина")
    return False


def check_superadmin_rights_decorator(func):
    """Декоратор для проверки прав суперадмина - НЕ применяется к функциям регистрации"""

    async def wrapper(message_or_callback, *args, **kwargs):
        user_id = message_or_callback.from_user.id

        # Проверяем права суперадмина
        if not await check_superadmin_rights(user_id):
            if hasattr(message_or_callback, 'answer'):
                await message_or_callback.answer("❌ У вас нет прав суперадмина.")
            else:
                await message_or_callback.message.answer("❌ У вас нет прав суперадмина.")
            return

        return await func(message_or_callback, *args, **kwargs)

    return wrapper


@router.message(F.text == "/check_rights")
async def debug_check_rights(message: Message):
    """Отладочная команда для проверки прав"""
    user_id = message.from_user.id
    has_rights = await check_superadmin_rights(user_id)

    debug_info = f"""🔍 <b>Отладка прав для пользователя {user_id}:</b>

📋 <b>Проверки:</b>
• В SUPERADMIN_IDS: {'✅' if user_id in SUPERADMIN_IDS else '❌'}
• has_role(): {'✅' if has_role(user_id, ROLES['SUPERADMIN']) else '❌'}
• Итоговый результат: {'✅ ЕСТЬ ПРАВА' if has_rights else '❌ НЕТ ПРАВ'}

📊 <b>Данные:</b>
• SUPERADMIN_IDS: {SUPERADMIN_IDS}
• Ваш ID: {user_id}"""

    try:
        user = await Database.get_user(user_id)
        if user:
            debug_info += f"\n• Роль в БД: {user[3]}"
        else:
            debug_info += f"\n• В БД: НЕ НАЙДЕН"
    except Exception as e:
        debug_info += f"\n• Ошибка БД: {e}"

    await message.answer(debug_info)


# Главное меню суперадмина
@router.message(F.text == "👑 Суперадмин-меню")
async def superadmin_menu(message: Message):
    """Главное меню суперадмина"""
    try:
        user_id = message.from_user.id
        logger.info(f"🔍 Попытка доступа к суперадмин-меню от пользователя {user_id}")

        user = await Database.get_user(user_id)
        if not user:
            logger.info(f"❌ Пользователь {user_id} не зарегистрирован - не проверяем права суперадмина")
            await message.answer("❌ Сначала зарегистрируйтесь в системе командой /start")
            return

        if not await check_superadmin_rights(user_id):
            logger.warning(f"❌ Пользователь {user_id} НЕ имеет прав суперадмина")
            await message.answer("❌ У вас нет прав суперадмина.")
            return

        logger.info(f"✅ Пользователь {user_id} получил доступ к суперадмин-меню")
        await message.answer(
            "👑 <b>Добро пожаловать в панель суперадмина!</b>\n\n"
            "🛠️ <b>Управление системой:</b>\n"
            "• ➕ Добавить репетитора - регистрация новых репетиторов\n"
            "• 🗑️ Удалить репетитора - удаление из системы\n"
            "• 👥 Управление ролями - изменение прав пользователей\n"
            "• 📊 Статистика системы - общие показатели\n"
            "• 📋 Список репетиторов - просмотр списка репетиторов\n"
            "• ⚙️ Настройки системы - системные параметры\n\n"
            "⚠️ <b>Внимание!</b> Все изменения влияют на всю систему.\n"
            "Будьте осторожны при управлении пользователями.\n\n"
            "🕐 <b>Все время указано по Москве (МСК)</b>",
            reply_markup=get_superadmin_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"❌ Ошибка в superadmin_menu: {e}")
        await message.answer("❌ Произошла ошибка при открытии меню.")


# Управление ролями
@router.message(F.text == "👥 Управление ролями")
async def role_management_menu(message: Message, state: FSMContext):
    """Меню управления ролями"""
    try:
        if not await check_superadmin_rights(message.from_user.id):
            await message.answer("❌ У вас нет прав суперадмина.")
            return

        await state.clear()

        role_text = """👥 <b>Управление ролями пользователей</b>

🔧 <b>Доступные действия:</b>
• 🔄 Изменить роль пользователя
• 👀 Просмотреть роли всех пользователей
• 🔍 Найти пользователя по ID

⚠️ <b>Внимание!</b> Изменение ролей влияет на доступ к функциям бота.

📝 Введите ID пользователя для изменения роли:"""

        await message.answer(role_text, reply_markup=get_cancel_button())
        await state.set_state(SuperadminStates.waiting_for_role_user_id)

    except Exception as e:
        logger.error(f"❌ Ошибка в role_management_menu: {e}")
        await message.answer("❌ Произошла ошибка при открытии управления ролями.")


@router.message(SuperadminStates.waiting_for_role_user_id)
async def process_role_user_id(message: Message, state: FSMContext):
    """Обработка ID пользователя для изменения роли"""
    try:
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("🚫 Управление ролями отменено.", reply_markup=get_superadmin_menu_keyboard())
            return

        try:
            user_id = int(message.text)
        except ValueError:
            await message.answer("❌ Неверный формат ID. Введите числовой ID:")
            return

        user = await Database.get_user(user_id)
        if not user:
            await message.answer("❌ Пользователь с таким ID не найден.")
            return

        await state.update_data(target_user_id=user_id)

        current_role = user[3]
        username = user[1] or "Без username"
        name = user[2] or "Имя не указано"

        await message.answer(
            f"👤 <b>Пользователь найден:</b>\n"
            f"📱 Username: @{username}\n"
            f"👤 Имя: {name}\n"
            f"🔧 Текущая роль: {current_role}\n\n"
            f"📝 Выбе��ите новую роль:",
            reply_markup=get_role_selection_keyboard()
        )
        await state.set_state(SuperadminStates.waiting_for_new_role)

    except Exception as e:
        logger.error(f"❌ Ошибка в process_role_user_id: {e}")
        await message.answer("❌ Произошла ошибка при обработке ID.")


@router.callback_query(SuperadminStates.waiting_for_new_role, F.data.startswith("role_"))
async def process_new_role(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора новой роли"""
    try:
        new_role = callback.data.split("_")[1]
        data = await state.get_data()
        target_user_id = data['target_user_id']

        # Получаем информацию о пользователе
        user = await Database.get_user(target_user_id)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден.")
            await callback.answer()
            return

        # Обновляем роль
        success = await Database.update_user_role(target_user_id, new_role)

        if success:
            await callback.message.edit_text(
                f"✅ <b>Роль успешно изменена!</b>\n\n"
                f"👤 <b>Пользователь:</b> {user[2]}\n"
                f"🔧 <b>Новая роль:</b> {new_role}\n\n"
                f"🎉 Изменения вступили в силу немедленно."
            )
        else:
            await callback.message.edit_text("❌ Произошла ошибка при изменении роли.")

        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в process_new_role: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при изменении роли.")
        await callback.answer()


# Удаление репетитора
@router.message(F.text == "🗑️ Удалить репетитора")
async def delete_tutor_menu(message: Message, state: FSMContext):
    """Меню удаления репетитора"""
    try:
        if not await check_superadmin_rights(message.from_user.id):
            await message.answer("❌ У вас нет прав суперадмина.")
            return

        await state.clear()

        # Получаем список репетиторов
        tutors = await Database.get_all_tutors()
        if not tutors:
            await message.answer(
                "📭 <b>В системе нет активных репетиторов для удаления.</b>",
                reply_markup=get_superadmin_menu_keyboard()
            )
            return

        delete_text = f"🗑️ <b>Удаление репетитора</b>\n\n"
        delete_text += f"📋 <b>Доступные репетиторы ({len(tutors)}):</b>\n\n"

        for tutor in tutors:
            tutor_id, name, username, subjects, cost, link = tutor
            delete_text += f"👨‍🏫 <b>{name}</b>\n"
            delete_text += f"🆔 ID: {tutor_id}\n"
            delete_text += f"📱 @{username or 'не указан'}\n"
            delete_text += f"📚 {subjects or 'Предметы не указаны'}\n\n"

        delete_text += "💡 Нажмите на репетитора для удаления:"

        await message.answer(
            delete_text,
            reply_markup=await get_tutors_for_deletion_keyboard(tutors)
        )

    except Exception as e:
        logger.error(f"❌ Ошибка в delete_tutor_menu: {e}")
        await message.answer("❌ Произошла ошибка при открытии удаления репетиторов.")


@router.callback_query(F.data.startswith("delete_tutor_"))
async def confirm_delete_tutor(callback: CallbackQuery, state: FSMContext):
    """ИСПРАВЛЕНО: Подтверждение удаления репетитора"""
    try:
        # Исправляем парсинг callback_data
        parts = callback.data.split("_")
        if len(parts) >= 3:
            tutor_id = int(parts[2])
        else:
            await callback.message.edit_text("❌ Ошибка в данных запроса.")
            await callback.answer()
            return

        # Получаем информацию о репетиторе
        tutor = await Database.get_tutor(tutor_id)
        if not tutor:
            await callback.message.edit_text("❌ Репетитор не найден.")
            await callback.answer()
            return

        tutor_name = tutor[1]

        await callback.message.edit_text(
            f"🗑️ <b>Удаление репетитора</b>\n\n"
            f"👨‍🏫 <b>Репетитор:</b> {tutor_name}\n"
            f"🆔 <b>ID:</b> {tutor_id}\n\n"
            f"⚠️ <b>ВНИМАНИЕ!</b> Это действие нельзя отменить!\n\n"
            f"❓ <b>Вы уверены, что хотите удалить этого репетитора?</b>",
            reply_markup=get_confirmation_keyboard("delete_tutor", tutor_id)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в confirm_delete_tutor: {e}")
        await callback.message.edit_text("❌ Произошла ошибка.")
        await callback.answer()


@router.callback_query(F.data.startswith("delete_tutor_yes_"))
async def execute_delete_tutor(callback: CallbackQuery, state: FSMContext):
    """Выполнение удаления репетитора"""
    try:
        tutor_id = int(callback.data.split("_")[3])

        # Получаем информацию о репетиторе перед удалением
        tutor = await Database.get_tutor(tutor_id)
        tutor_name = tutor[1] if tutor else f"Репетитор {tutor_id}"

        # Удаляем репетитора
        success = await Database.delete_tutor_info(tutor_id)

        if success:
            await callback.message.edit_text(
                f"✅ <b>Репетитор удален!</b>\n\n"
                f"👨‍🏫 <b>Репетитор:</b> {tutor_name}\n\n"
                f"🗑️ Репетитор деактивирован в системе."
            )
        else:
            await callback.message.edit_text("❌ Произошла ошибка при удалении репетитора.")

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в execute_delete_tutor: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении репетитора.")
        await callback.answer()


# Настройки системы
@router.message(F.text == "⚙️ Настройки системы")
async def system_settings_menu(message: Message):
    """Меню настроек системы"""
    try:
        if not await check_superadmin_rights(message.from_user.id):
            return

        settings_text = """⚙️ <b>Настройки системы</b>

🔧 <b>Текущие настройки:</b>
• 🔔 Напоминания об уроках: за 1 час до начала
• 📝 Напоминания о ДЗ: отключены (по запросу)
• 🌅 Утренние напоминания: отключены
• ⏰ Время отмены урока: за 24 часа
• 💰 Валюта системы: рубли (₽)

📊 <b>Системная информация:</b>
• 🗄️ База данных: SQLite
• 🔄 Автоматические уведомления: включены
• 📱 Поддержка файлов: включена
• 🎥 Поддержка видео/аудио: включена

✅ <b>Все настройки оптимизированы для работы</b>

💡 <b>Рекомендации:</b>
• Регулярно проверяйте статистику системы
• Следите за активностью пользователей
• Обновляйте список репетиторов при необходимости"""

        await message.answer(settings_text, reply_markup=get_superadmin_menu_keyboard())

    except Exception as e:
        logger.error(f"❌ Ошибка в system_settings_menu: {e}")
        await message.answer("❌ Произошла ошибка при открытии настроек системы.")


# Добавить репетитора
@router.message(F.text == "➕ Добавить репетитора")
async def add_tutor_start(message: Message, state: FSMContext):
    """Начало процесса добавления репетитора"""
    try:
        if not await check_superadmin_rights(message.from_user.id):
            await message.answer("❌ У вас нет прав суперадмина.")
            return

        await message.answer(
            "👨‍🏫 <b>Добавление нового репетитора</b>\n\n"
            "📝 Введите Telegram ID пользователя, которого хотите сделать репетитором:\n\n"
            "💡 <i>ID можно узнать у пользователя или через @userinfobot</i>",
            reply_markup=get_cancel_button()
        )
        await state.set_state(SuperadminStates.waiting_for_tutor_id)
    except Exception as e:
        logger.error(f"❌ Ошибка в add_tutor_start: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(SuperadminStates.waiting_for_tutor_id)
async def process_tutor_id(message: Message, state: FSMContext):
    """Обработка ID репетитора"""
    try:
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer(
                "🚫 Добавление репетитора отменено.",
                reply_markup=get_superadmin_menu_keyboard()
            )
            return

        try:
            tutor_id = int(message.text)
        except ValueError:
            await message.answer("❌ Неверный формат ID. Введите числовой ID:")
            return

        user = await Database.get_user(tutor_id)
        if not user:
            await message.answer("❌ Пользователь с таким ID не найден в системе.")
            return

        if user[3] == ROLES["ADMIN"]:
            await message.answer("❌ Этот пользователь уже является репетитором.")
            return

        await state.update_data(tutor_id=tutor_id)
        username = user[1] or "Без username"
        name = user[2] or "Имя не указано"

        await message.answer(
            f"👤 <b>Пользователь найден:</b>\n"
            f"📱 Username: @{username}\n"
            f"👤 Имя: {name}\n\n"
            f"📝 Введите имя репетитора для системы:",
            reply_markup=get_cancel_button()
        )
        await state.set_state(SuperadminStates.waiting_for_tutor_name)

    except Exception as e:
        logger.error(f"❌ Ошибка в process_tutor_id: {e}")
        await message.answer("❌ Произошла ошибка при обработке ID.")


@router.message(SuperadminStates.waiting_for_tutor_name)
async def process_tutor_name(message: Message, state: FSMContext):
    """Обработка имени репетитора"""
    try:
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer(
                "🚫 Добавление репетитора отменено.",
                reply_markup=get_superadmin_menu_keyboard()
            )
            return

        await state.update_data(tutor_name=message.text)
        await message.answer(
            "📱 <b>Username репетитора</b>\n\n"
            "Введите username репетитора в Telegram (без @) или напишите 'нет' если его нет:\n\n"
            "💡 <i>Например: ivan_tutor</i>",
            reply_markup=get_cancel_button()
        )
        await state.set_state(SuperadminStates.waiting_for_tutor_username)

    except Exception as e:
        logger.error(f"❌ Ошибка в process_tutor_name: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(SuperadminStates.waiting_for_tutor_username)
async def process_tutor_username(message: Message, state: FSMContext):
    """Обработка username репетитора"""
    try:
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer(
                "🚫 Добавление репетитора отменено.",
                reply_markup=get_superadmin_menu_keyboard()
            )
            return

        username = None if message.text.lower() == "нет" else message.text.replace("@", "")
        await state.update_data(tutor_username=username)

        await message.answer(
            "📚 <b>Предметы репетитора</b>\n\n"
            "Введите предметы, которые преподает репетитор (через запятую):\n\n"
            "💡 <i>Например: Математика, Физика, Химия</i>",
            reply_markup=get_cancel_button()
        )
        await state.set_state(SuperadminStates.waiting_for_tutor_subjects)

    except Exception as e:
        logger.error(f"❌ Ошибка в process_tutor_username: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(SuperadminStates.waiting_for_tutor_subjects)
async def process_tutor_subjects(message: Message, state: FSMContext):
    """Обработка предметов репетитора"""
    try:
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer(
                "🚫 Добавление репетитора отменено.",
                reply_markup=get_superadmin_menu_keyboard()
            )
            return

        await state.update_data(tutor_subjects=message.text)
        await message.answer(
            "💰 <b>Стоимость урока</b>\n\n"
            "Введите стоимость урока в рублях:\n\n"
            "💡 <i>Например: 1500</i>",
            reply_markup=get_cancel_button()
        )
        await state.set_state(SuperadminStates.waiting_for_tutor_cost)

    except Exception as e:
        logger.error(f"❌ Ошибка в process_tutor_subjects: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(SuperadminStates.waiting_for_tutor_cost)
async def process_tutor_cost(message: Message, state: FSMContext):
    """Обработка стоимости урока"""
    try:
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer(
                "🚫 Добавление репетитора отменено.",
                reply_markup=get_superadmin_menu_keyboard()
            )
            return

        try:
            cost = float(message.text)
            if cost < 0:
                await message.answer("❌ Стоимость не может быть отрицательной.")
                return
        except ValueError:
            await message.answer("❌ Неверный формат стоимости. Введите число:")
            return

        await state.update_data(tutor_cost=cost)
        await message.answer(
            "🔗 <b>Ссылка на урок</b>\n\n"
            "Введите ссылку на урок (Zoom, Meet и т.д.) или напишите 'нет' если ссылки нет:\n\n"
            "💡 <i>Например: https://zoom.us/j/123456789</i>",
            reply_markup=get_cancel_button()
        )
        await state.set_state(SuperadminStates.waiting_for_tutor_link)

    except Exception as e:
        logger.error(f"❌ Ошибка в process_tutor_cost: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(SuperadminStates.waiting_for_tutor_link)
async def process_tutor_link(message: Message, state: FSMContext):
    """Обработка ссылки на урок"""
    try:
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer(
                "🚫 Добавление репетитора отменено.",
                reply_markup=get_superadmin_menu_keyboard()
            )
            return

        link = None if message.text.lower() == "нет" else message.text
        data = await state.get_data()

        # Обновляем роль пользователя
        await Database.update_user_role(data["tutor_id"], ROLES["ADMIN"])

        # Добавляем информацию о репетиторе
        await Database.add_tutor_with_username(
            data["tutor_id"],
            data["tutor_name"],
            data["tutor_subjects"],
            data["tutor_cost"],
            link,
            data.get("tutor_username")
        )

        await message.answer(
            f"✅ <b>Репетитор успешно добавлен!</b>\n\n"
            f"👨‍🏫 <b>Имя:</b> {data['tutor_name']}\n"
            f"📱 <b>Username:</b> @{data.get('tutor_username', 'Не указан')}\n"
            f"📚 <b>Предметы:</b> {data['tutor_subjects']}\n"
            f"💰 <b>Стоимость:</b> {data['tutor_cost']} руб/урок\n"
            f"🔗 <b>Ссылка:</b> {link or 'Не указана'}\n\n"
            f"🎉 Репетитор может начинать работу!",
            reply_markup=get_superadmin_menu_keyboard()
        )
        await state.clear()

    except Exception as e:
        logger.error(f"❌ Ошибка в process_tutor_link: {e}")
        await message.answer("❌ Произошла ошибка при добавлении репетитора.")


# ИСПРАВЛЕНО: Список репетиторов
@router.message(F.text == "📋 Список репетиторов")
async def tutors_list(message: Message):
    """Показать список всех репетиторов"""
    try:
        if not await check_superadmin_rights(message.from_user.id):
            await message.answer("❌ У вас нет прав суперадмина.")
            return

        tutors = await Database.get_all_tutors()
        if not tutors:
            await message.answer(
                "📭 <b>В системе нет репетиторов.</b>",
                reply_markup=get_superadmin_menu_keyboard()
            )
            return

        tutors_text = "📋 <b>Список всех репетиторов:</b>\n\n"

        for tutor in tutors:
            # ИСПРАВЛЕНО: Правильное распаковывание данных репетитора
            tutor_id, name, username, subjects, cost, link = tutor

            # Получаем дополнительную информацию о пользователе
            user_info = await Database.get_user(tutor_id)
            user_username = user_info[1] if user_info else "Нет username"

            # Получаем количество учеников
            students = await Database.get_tutor_students(tutor_id)
            students_count = len([s for s in students if s[3] != 'archived'])

            tutors_text += f"👨‍🏫 <b>{name}</b>\n"
            tutors_text += f"🆔 ID: {tutor_id}\n"
            tutors_text += f"📱 @{username or user_username}\n"
            tutors_text += f"📚 Предметы: {subjects}\n"
            tutors_text += f"💰 Стоимость: {cost} руб/урок\n"
            tutors_text += f"👥 Учеников: {students_count}\n"

            if link:
                tutors_text += f"🔗 Ссылка: {link}\n"

            tutors_text += "\n" + "─" * 30 + "\n\n"

        # Разбиваем длинное сообщение на части если нужно
        if len(tutors_text) > 4000:
            parts = [tutors_text[i:i + 4000] for i in range(0, len(tutors_text), 4000)]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Последняя часть
                    await message.answer(part, reply_markup=get_superadmin_menu_keyboard())
                else:
                    await message.answer(part)
        else:
            await message.answer(tutors_text, reply_markup=get_superadmin_menu_keyboard())

    except Exception as e:
        logger.error(f"❌ Ошибка в tutors_list: {e}")
        await message.answer("❌ Произошла ошибка при получении списка репетиторов.")


# Статистика системы
@router.message(F.text == "📊 Статистика системы")
async def system_statistics(message: Message):
    """Показ статистики системы"""
    try:
        if not await check_superadmin_rights(message.from_user.id):
            return

        stats = await Database.get_system_statistics()

        stats_text = f"""📊 <b>Статистика системы</b>

👥 <b>Пользователи:</b>
• Всего пользователей: {stats.get('total_users', 0)}
• 👨‍🏫 Репетиторов: {stats.get('tutors', 0)}
• 👨‍🎓 Студентов: {stats.get('students', 0)}
• 🔧 Суперадминов: {stats.get('superadmins', 0)}
• 📁 Архивированных: {stats.get('archived', 0)}

📚 <b>Обучение:</b>
• Всего уроков: {stats.get('total_lessons', 0)}
• ✅ Проведенных: {stats.get('completed_lessons', 0)}
• 📝 Заданий выдано: {stats.get('homework_assigned', 0)}
• 📤 Заданий сдано: {stats.get('homework_submitted', 0)}

💰 <b>Финансы:</b>
• 💳 Оплаченных уроков: {stats.get('paid_lessons', 0)}
• 💵 Общий оборот: {stats.get('total_revenue', 0)} руб.

📈 <b>Активность:</b>
• 📨 Сообщений отправлено: {stats.get('total_messages', 0)}
• 📋 Активных заявок: {stats.get('pending_requests', 0)}

🕐 <b>Обновлено:</b> {stats.get('updated_at', 'Сейчас')}"""

        await message.answer(stats_text, reply_markup=get_superadmin_menu_keyboard())

    except Exception as e:
        logger.error(f"❌ Ошибка в system_statistics: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики.")


# ПОМОЩЬ
@router.message(F.text == "ℹ️ Помощь")
async def help_superadmin(message: Message):
    """Помощь для суперадмина"""
    try:
        if not await check_superadmin_rights(message.from_user.id):
            return

        help_text = """👑 <b>Помощь для суперадминистратора</b>

🛠️ <b>Управление системой:</b>
• ➕ <b>Добавить репетитора</b> - регистрация новых репетиторов
• 🗑️ <b>Удалить репетитора</b> - удаление из системы
• 👥 <b>Управление ролями</b> - изменение прав пользователей
• 📊 <b>Статистика системы</b> - общие показатели
• 📋 <b>Список репетиторов</b> - просмотр списка репетиторов
• ⚙️ <b>Настройки системы</b> - системные параметры

⚠️ <b>Внимание!</b> Все изменения влияют на всю систему.
Будьте осторожны при управлении пользователями.

🔧 <b>Доступные роли:</b>
• 👨‍🎓 Ученик - может записываться на уроки
• 👨‍🏫 Репетитор - может проводить уроки
• 👑 Суперадмин - полный доступ к системе

💡 <b>Советы:</b>
• Регулярно проверяйте статистику системы
• Следите за активностью репетиторов
• Обращайте внимание на жалобы пользователей

⏰ <b>Все время указано по Московскому времени (МСК)</b>"""

        await message.answer(help_text, reply_markup=get_superadmin_menu_keyboard())

    except Exception as e:
        logger.error(f"❌ Ошибка в help_superadmin: {e}")
        await message.answer("❌ Произошла ошибка при получении справки.")


# Обработчик всех callback'ов суперадмина
# @router.callback_query()
# async def handle_superadmin_callback(callback: CallbackQuery):
#     """Универсальный обработчик callback запросов для суперадмина"""
#     try:
#         callback_data = callback.data
#         user_id = callback.from_user.id
#
#         user = await Database.get_user(user_id)
#         if not user:
#             await callback.answer("❌ Сначала зарегистрируйтесь в системе")
#             return
#
#         # Проверяем права суперадмина
#         if not await check_superadmin_rights(user_id):
#             await callback.answer("❌ У вас нет прав суперадмина.")
#             return
#
#         # Обрабатываем различные callback данные
#         if callback_data.startswith("delete_tutor_"):
#             await confirm_delete_tutor(callback, None)
#         elif callback_data.startswith("delete_tutor_yes_"):
#             await execute_delete_tutor(callback, None)
#         elif callback_data.startswith("role_"):
#             # Создаем временное состояние для обработки роли
#             from aiogram.fsm.context import FSMContext
#             state = FSMContext()
#             await process_new_role(callback, state)
#         else:
#             await callback.answer("❓ Неизвестная команда.")
#
#     except Exception as e:
#         logger.error(f"❌ Ошибка в handle_superadmin_callback: {e}")
#         await callback.answer("❌ Произошла ошибка при обработке запроса.")
