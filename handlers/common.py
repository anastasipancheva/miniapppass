import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from database import Database
from keyboards import get_main_menu_keyboard, get_tutors_keyboard
from states import RegistrationStates
from constants import ROLES, SPECIAL_USERS, has_role, get_primary_role, SUPERADMIN_IDS
from notifications import notification_service
from datetime import datetime, timedelta
from constants import get_user_role_for_menu as get_menu_role

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    try:
        await state.clear()
        user_id = message.from_user.id
        user = await Database.get_user(user_id)

        if not user and user_id in SUPERADMIN_IDS:
            # Регистрируем суперадмина автоматически
            success = await Database.add_user(
                user_id=user_id,
                username=message.from_user.username,
                full_name=message.from_user.full_name or "Суперадмин",
                role=ROLES["SUPERADMIN"]
            )
            if success:
                # Создаем профиль репетитора для суперадмина
                await Database.add_tutor_with_username(
                    tutor_id=user_id,
                    name=message.from_user.full_name or "Суперадмин",
                    subjects="Все предметы",
                    cost=1000,
                    username=message.from_user.username
                )
                user = await Database.get_user(user_id)
                logger.info(f"👑 Автоматически зарегистрирован суперадмин {user_id} с профилем репетитора")

        if user:
            role = user[3]
            menu_role = get_menu_role(user_id, role)

            logger.info(
                f"👤 Пользователь {user_id} ({message.from_user.full_name}) вернулся. DB роль: {role}, Меню роль: {menu_role}")

            welcome_messages = {
                ROLES[
                    "STUDENT"]: f"🎓 С возвращением, {message.from_user.first_name}!\n\n📚 Добро пожаловать в систему обучения!",
                ROLES["ADMIN"]: f"👨‍🏫 С возвращением, {message.from_user.first_name}!\n\n🔧 Панель репетитора активна!",
                ROLES[
                    "SUPERADMIN"]: f"👑 С возвращением, {message.from_user.first_name}!\n\n🛠️ Панель суперадминистратора активна!"
            }

            welcome_text = welcome_messages.get(menu_role, f"👋 С возвращением, {message.from_user.first_name}!")

            if user_id in SPECIAL_USERS:
                available_roles = ", ".join(SPECIAL_USERS[user_id]["roles"])
                welcome_text += f"\n\n🔧 <b>Доступные роли:</b> {available_roles}"
                welcome_text += f"\n💡 Используйте команды /admin, /superadmin, /student для переключения"

            await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(menu_role))
        else:
            logger.info(f"🆕 Новый пользователь {user_id} ({message.from_user.full_name}) начал диалог.")
            await message.answer(
                "🎉 <b>Добро пожаловать в систему обучения!</b>\n\n"
                "👨‍🎓 Выберите своего репетитора из списка ниже:",
                reply_markup=await get_tutors_keyboard()
            )
            await state.set_state(RegistrationStates.waiting_for_tutor_choice)

    except Exception as e:
        logger.error(f"❌ Ошибка в cmd_start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(RegistrationStates.waiting_for_tutor_choice, F.data.startswith("select_tutor_"))
async def register_student_with_tutor(callback: CallbackQuery, state: FSMContext):
    """Регистрация ученика с выбранным репетитором"""
    try:
        tutor_id = int(callback.data.split("_")[2])
        student_id = callback.from_user.id

        logger.info(f"🎓 Начинается регистрация студента {student_id} с репетитором {tutor_id}")

        existing_user = await Database.get_user(student_id)
        if existing_user:
            role = existing_user[3]
            menu_role = get_menu_role(student_id, role)
            await callback.message.edit_text(
                f"✅ Вы уже зарегистрированы как <b>{role}</b>",
                reply_markup=get_main_menu_keyboard(menu_role)
            )
            await callback.answer()
            await state.clear()
            return

        await state.update_data(selected_tutor_id=tutor_id)
        await callback.message.edit_text(
            "📝 <b>Регистрация ученика</b>\n\n"
            "👤 Введите ваше полное имя:"
        )
        await state.set_state(RegistrationStates.waiting_for_name)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при регистрации ученика: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.message(RegistrationStates.waiting_for_name)
async def process_student_name(message: Message, state: FSMContext):
    """Process student name input"""
    try:
        student_name = message.text.strip()
        if len(student_name) < 2:
            await message.answer("❌ Имя должно содержать минимум 2 символа")
            return

        await state.update_data(student_name=student_name)
        await message.answer(
            "🎂 Введите ваш возраст:"
        )
        await state.set_state(RegistrationStates.waiting_for_age)
    except Exception as e:
        logger.error(f"❌ Ошибка в process_student_name: {e}")
        await message.answer("❌ Произошла ошибка")


@router.message(RegistrationStates.waiting_for_age)
async def process_student_age(message: Message, state: FSMContext):
    """Process student age input"""
    try:
        try:
            age = int(message.text.strip())
            if age < 5 or age > 100:
                await message.answer("❌ Возраст должен быть от 5 до 100 лет")
                return
        except ValueError:
            await message.answer("❌ Введите возраст числом (например: 16)")
            return

        await state.update_data(student_age=age)
        await message.answer(
            "🌍 Введите ваш часовой пояс в формате МСК+N (например: МСК+3, МСК-2):"
        )
        await state.set_state(RegistrationStates.waiting_for_timezone)
    except Exception as e:
        logger.error(f"❌ Ошибка в process_student_age: {e}")
        await message.answer("❌ Произошла ошибка")


@router.message(RegistrationStates.waiting_for_timezone)
async def process_student_timezone(message: Message, state: FSMContext):
    """Process student timezone input"""
    try:
        timezone = message.text.strip().upper()
        if not timezone.startswith("МСК"):
            await message.answer("❌ Часовой пояс должен быть в формате МСК+N или МСК-N")
            return

        await state.update_data(student_timezone=timezone)
        await message.answer(
            "📚 Введите предмет, который хотите изучать:"
        )
        await state.set_state(RegistrationStates.waiting_for_subject)
    except Exception as e:
        logger.error(f"❌ Ошибка в process_student_timezone: {e}")
        await message.answer("❌ Произошла ошибка")


@router.message(RegistrationStates.waiting_for_subject)
async def process_student_subject(message: Message, state: FSMContext):
    """Process student subject input"""
    try:
        subject = message.text.strip()
        data = await state.get_data()

        student_id = message.from_user.id
        tutor_id = data.get('selected_tutor_id')
        student_name = data.get('student_name')
        student_age = data.get('student_age')
        timezone = data.get('student_timezone')

        # Register student with age
        success = await Database.add_user(
            user_id=student_id,
            username=message.from_user.username,
            full_name=student_name,
            role=ROLES["STUDENT"],
            tutor_id=tutor_id,
            timezone=timezone,
            subject=subject,
            age=student_age
        )

        if success:
            # Send request to tutor
            request_id = await Database.add_student_request(student_id, tutor_id)

            # ИСПРАВЛЕНО: Отправляем НЕМЕДЛЕННОЕ уведомление репетитору о новой заявке
            if request_id:
                try:
                    tutor = await Database.get_user(tutor_id)
                    tutor_name = tutor[2] if tutor else f"Репетитор {tutor_id}"

                    # Отправляем уведомление репетитору
                    await message.bot.send_message(
                        tutor_id,
                        f"🔔 <b>НОВАЯ ЗАЯВКА НА РЕГИСТРАЦИЮ!</b>\n\n"
                        f"👤 <b>Студент:</b> {student_name}\n"
                        f"🎂 <b>Возраст:</b> {student_age} лет\n"
                        f"🌍 <b>Часовой пояс:</b> {timezone}\n"
                        f"📚 <b>Предмет:</b> {subject}\n\n"
                        f"📋 Перейдите в раздел 'Заявки учеников' для принятия решения."
                    )
                    logger.info(f"✅ Отправлено уведомление репетитору {tutor_id} о новой заявке от {student_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки уведомления репетитору: {e}")

            await message.answer(
                f"✅ <b>Регистрация завершена!</b>\n\n"
                f"👤 <b>Имя:</b> {student_name}\n"
                f"🎂 <b>Возраст:</b> {student_age} лет\n"
                f"🌍 <b>Часовой пояс:</b> {timezone}\n"
                f"📚 <b>Предмет:</b> {subject}\n\n"
                "📝 Ваша заявка отправлена репетитору на рассмотрение.\n"
                "⏳ Ожидайте ответа от репетитора.",
                reply_markup=get_main_menu_keyboard(ROLES["STUDENT"])
            )
        else:
            await message.answer("❌ Ошибка при регистрации")

        await state.clear()
    except Exception as e:
        logger.error(f"❌ Ошибка в process_student_subject: {e}")
        await message.answer("❌ Произошла ошибка")
        await state.clear()


@router.message(Command("admin"))
async def switch_to_admin(message: Message, state: FSMContext):
    """Переключение на роль админа для специальных пользователей"""
    try:
        user_id = message.from_user.id
        if user_id not in SPECIAL_USERS or "admin" not in SPECIAL_USERS[user_id]["roles"]:
            await message.answer("❌ У вас нет доступа к роли администратора.")
            return

        await state.clear()
        await message.answer(
            "👨‍🏫 <b>Переключено на роль репетитора</b>\n\n"
            "🔧 Панель репетитора активна!",
            reply_markup=get_main_menu_keyboard(ROLES["ADMIN"])
        )

    except Exception as e:
        logger.error(f"❌ Ошибка в switch_to_admin: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(Command("superadmin"))
async def switch_to_superadmin(message: Message, state: FSMContext):
    """Переключение на роль суперадмина для специальных пользователей"""
    try:
        user_id = message.from_user.id
        if user_id not in SPECIAL_USERS or "superadmin" not in SPECIAL_USERS[user_id]["roles"]:
            await message.answer("❌ У вас нет доступа к роли суперадминистратора.")
            return

        await state.clear()
        await message.answer(
            "👑 <b>Переключено на роль суперадминистратора</b>\n\n"
            "🛠️ Панель суперадминистратора активна!",
            reply_markup=get_main_menu_keyboard(ROLES["SUPERADMIN"])
        )

    except Exception as e:
        logger.error(f"❌ Ошибка в switch_to_superadmin: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(Command("student"))
async def switch_to_student(message: Message, state: FSMContext):
    """Переключение на роль студента для специальных пользователей"""
    try:
        user_id = message.from_user.id
        if user_id not in SPECIAL_USERS or "student" not in SPECIAL_USERS[user_id]["roles"]:
            await message.answer("❌ У вас нет доступа к роли студента.")
            return

        await state.clear()
        await message.answer(
            "🎓 <b>Переключено на роль студента</b>\n\n"
            "📚 Добро пожаловать в систему обучения!",
            reply_markup=get_main_menu_keyboard(ROLES["STUDENT"])
        )

    except Exception as e:
        logger.error(f"❌ Ошибка в switch_to_student: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message, state: FSMContext):
    """Команда помощи"""
    try:
        await state.clear()
        user = await Database.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Зарегистрируйтесь командой /start")
            return

        role = user[3]
        menu_role = get_menu_role(message.from_user.id, role)

        help_texts = {
            ROLES["STUDENT"]: (
                "🎓 <b>Помощь для ученика:</b>\n\n"
                "🗓️ <b>Мои уроки</b> - просмотр расписания\n"
                "📚 <b>Мои ДЗ</b> - домашние задания\n"
                "💬 <b>Сообщения</b> - переписка с репетитором\n"
                "📞 <b>Связаться с репетитором</b> - прямая связь"
            ),
            ROLES["ADMIN"]: (
                "👨‍🏫 <b>Помощь для репетитора:</b>\n\n"
                "⚙️ <b>Настроить профиль</b> - настройки профиля\n"
                "👥 <b>Мои ученики</b> - управление учениками\n"
                "📚 <b>Задать ДЗ</b> - домашние задания\n"
                "📊 <b>Управление расписанием</b> - просмотр расписания\n"
                "🕐 <b>Свободные окна</b> - управление слотами\n"
                "📈 <b>Статистика</b> - отчеты и аналитика"
            ),
            ROLES["SUPERADMIN"]: (
                "👑 <b>Помощь для суперадминистратора:</b>\n\n"
                "👥 <b>Управление ролями</b> - назначение ролей пользователям\n"
                "📋 <b>Список репетиторов</b> - просмотр всех репетиторов\n"
                "📊 <b>Статистика системы</b> - просмотр общей статистики\n"
                "⚙️ <b>Настройки системы</b> - конфигурация системы\n\n"
                "💡 Также доступны все функции репетитора"
            )
        }

        help_text = help_texts.get(menu_role, "❓ Неизвестная роль пользователя")
        await message.answer(help_text, reply_markup=get_main_menu_keyboard(menu_role))

    except Exception as e:
        logger.error(f"❌ Ошибка в help_command: {e}")
        await message.answer("❌ Произошла ошибка при получении справки.")


@router.message(Command("menu"))
@router.message(F.text == "🏠 Главное меню")
async def cmd_menu(message: Message, state: FSMContext):
    """Обработчик команды /menu и кнопки главного меню"""
    try:
        await state.clear()
        user_id = message.from_user.id
        user = await Database.get_user(user_id)
        if user:
            db_role = user[3]
            role = get_menu_role(user_id, db_role)
        else:
            role = ROLES["STUDENT"]

        keyboard = get_main_menu_keyboard(role)
        await message.answer("📋 <b>Главное меню:</b>", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"❌ Ошибка в cmd_menu: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.message(F.text == "❌ Отмена")
async def handle_cancel(message: Message, state: FSMContext):
    """Обработчик кнопки отмены"""
    try:
        current_state = await state.get_state()
        if current_state:
            await state.clear()
            user = await Database.get_user(message.from_user.id)
            if user:
                role = user[3]
                menu_role = get_menu_role(message.from_user.id, role)
            else:
                menu_role = ROLES["STUDENT"]

            await message.answer(
                "🚫 <b>Действие отменено.</b>",
                reply_markup=get_main_menu_keyboard(menu_role)
            )
        else:
            await message.answer("ℹ️ Нет активных действий для отмены.")
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_cancel: {e}")
        await message.answer("❌ Произошла ошибка.")


@router.callback_query(F.data == "my_schedule")
async def handle_my_schedule_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Мое расписание'"""
    try:
        user_id = callback.from_user.id
        user = await Database.get_user(user_id)

        if not user:
            await callback.answer("❌ Пользователь не найден")
            return

        role = user[3]
        menu_role = get_menu_role(user_id, role)

        if menu_role == ROLES["STUDENT"]:
            lessons = await Database.get_student_upcoming_lessons(user_id)

            if not lessons:
                schedule_text = (
                    "📅 <b>Мое расписание</b>\n\n"
                    "📭 У вас пока нет запланированных уроков.\n\n"
                    "💡 Свяжитесь с репетитором для планирования занятий."
                )
            else:
                schedule_text = "📅 <b>Ваше расписание:</b>\n\n"

                for i, lesson in enumerate(lessons[:5], 1):
                    lesson_id, student_id, tutor_id, lesson_date, lesson_time, subject, status = lesson
                    tutor = await Database.get_user(tutor_id)
                    tutor_name = tutor[2] if tutor else f"Репетитор {tutor_id}"

                    status_emoji = {
                        'scheduled': '📅',
                        'completed': '✅',
                        'cancelled': '❌'
                    }.get(status, '📅')

                    schedule_text += f"{i}. {status_emoji} {lesson_date} в {lesson_time}\n"
                    schedule_text += f"   👨‍🏫 {tutor_name} - {subject or 'Урок'}\n\n"
        else:
            lessons = await Database.get_tutor_upcoming_lessons(user_id)

            if not lessons:
                schedule_text = (
                    "📊 <b>Управление расписанием</b>\n\n"
                    "📅 У вас пока нет запланированных уроков.\n\n"
                    "💡 Уроки появятся здесь после записи учеников."
                )
            else:
                schedule_text = "📊 <b>Ваше расписание:</b>\n\n"

                for i, lesson in enumerate(lessons[:5], 1):
                    lesson_id, student_id, tutor_id, lesson_date, lesson_time, subject, status = lesson
                    student = await Database.get_user(student_id)
                    student_name = student[2] if student else f"Ученик {student_id}"

                    schedule_text += f"{i}. 📅 {lesson_date} в {lesson_time}\n"
                    schedule_text += f"   👤 {student_name} - {subject or 'Урок'}\n\n"

        await callback.message.edit_text(schedule_text, reply_markup=get_main_menu_keyboard(menu_role))
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_my_schedule_callback: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "my_homework")
async def handle_my_homework_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Мои ДЗ'"""
    try:
        user_id = callback.from_user.id
        user = await Database.get_user(user_id)

        if not user:
            await callback.answer("❌ Пользователь не найден")
            return

        homework_list = await Database.get_homework_for_student(user_id)

        if not homework_list:
            homework_text = (
                "📚 <b>Мои домашние задания</b>\n\n"
                "📭 У вас пока нет домашних заданий.\n\n"
                "⏳ Ожидайте заданий от вашего репетитора."
            )
        else:
            homework_text = "📚 <b>Ваши домашние задания:</b>\n\n"

            for i, hw in enumerate(homework_list[:5], 1):
                hw_id, student_id, tutor_id, content_type, content_data, description, assigned_at, reminder_date, reminder_time, is_completed = hw

                status = "✅" if is_completed else "⏳"
                short_desc = description[:40] + "..." if description and len(description) > 40 else (
                        description or "Без описания")

                homework_text += f"{i}. {status} {short_desc}\n"
                homework_text += f"   📅 Задано: {assigned_at}\n\n"

        await callback.message.edit_text(homework_text, reply_markup=get_main_menu_keyboard(ROLES["STUDENT"]))
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_my_homework_callback: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "write_to_tutor")
async def handle_write_to_tutor_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Написать репетитору' - функция отключена"""
    try:
        await callback.message.edit_text(
            "💬 <b>Связаться с репетитором</b>\n\n"
            "❌ Функция переписки временно отключена.\n\n"
            "💡 Для связи с репетитором используйте другие способы связи:\n"
            "• Телефон\n"
            "• Email\n"
            "• Внешние мессенджеры\n\n"
            "🔧 Обратитесь к администратору для получения контактов.",
            reply_markup=get_main_menu_keyboard(ROLES["STUDENT"])
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_write_to_tutor_callback: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "open_messages")
async def handle_open_messages_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Открыть сообщения' - функция отключена"""
    try:
        user_id = callback.from_user.id
        user = await Database.get_user(user_id)
        menu_role = get_menu_role(user_id, user[3]) if user else ROLES["STUDENT"]

        await callback.message.edit_text(
            "💬 <b>Сообщения</b>\n\n"
            "❌ Функция сообщений временно отключена.\n\n"
            "💡 Все важные уведомления будут приходить автоматически:\n"
            "• Уведомления о новых уроках\n"
            "• Напоминания о домашних заданиях\n"
            "• Системные сообщения\n\n"
            "🔧 Для прямой связи обратитесь к администратору.",
            reply_markup=get_main_menu_keyboard(menu_role)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_open_messages_callback: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("reply_to_user_"))
async def handle_reply_to_user_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Ответить пользователю'"""
    try:
        sender_id = int(callback.data.split("_")[3])
        sender = await Database.get_user(sender_id)
        sender_name = sender[2] if sender else f"Пользователь {sender_id}"

        reply_text = (
            f"💬 <b>Ответ пользователю</b>\n\n"
            f"👤 <b>Получатель:</b> {sender_name}\n\n"
            "📝 Напишите ваше сообщение в следующем сообщении для отправки пользователю."
        )

        await callback.message.edit_text(reply_text)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_reply_to_user_callback: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.message(F.text == "📋 Заявки учеников")
async def handle_student_requests(message: Message, state: FSMContext):
    """Обработчик кнопки 'Заявки учеников'"""
    try:
        await state.clear()
        tutor_id = message.from_user.id
        user = await Database.get_user(tutor_id)

        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        role = user[3]
        menu_role = get_menu_role(tutor_id, role)

        # Проверяем, что пользователь - репетитор
        if menu_role not in [ROLES["ADMIN"], ROLES["SUPERADMIN"]]:
            await message.answer("❌ У вас нет доступа к заявкам учеников")
            return

        # Получаем заявки от студентов
        requests = await Database.get_student_requests_for_tutor(tutor_id)

        if not requests:
            await message.answer(
                "📋 <b>Заявки учеников</b>\n\n"
                "📭 У вас пока нет новых заявок от учеников.\n\n"
                "💡 Заявки появятся здесь, когда студенты выберут вас как репетитора.",
                reply_markup=get_main_menu_keyboard(menu_role)
            )
            return

        # Формируем список заявок
        requests_text = "📋 <b>Заявки от учеников:</b>\n\n"

        # Создаем inline клавиатуру для действий с заявками
        keyboard = InlineKeyboardBuilder()

        for i, request in enumerate(requests[:5], 1):
            request_id, student_id, tutor_id_req, status, created_at, student_name, student_age, timezone, subject = request

            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }.get(status, '⏳')

            requests_text += f"{i}. {status_emoji} <b>{student_name}</b>\n"
            requests_text += f"   🎂 Возраст: {student_age} лет\n"
            requests_text += f"   🌍 Часовой пояс: {timezone}\n"
            requests_text += f"   📚 Предмет: {subject}\n"
            requests_text += f"   📅 Подано: {created_at}\n"

            if status == 'pending':
                # Добавляем кнопки для принятия/отклонения заявки
                keyboard.row(
                    InlineKeyboardButton(
                        text=f"✅ Принять #{i}",
                        callback_data=f"approve_request_{request_id}"
                    ),
                    InlineKeyboardButton(
                        text=f"❌ Отклонить #{i}",
                        callback_data=f"reject_request_{request_id}"
                    )
                )

            requests_text += "\n"

        # Добавляем кнопку обновления списка
        keyboard.row(
            InlineKeyboardButton(
                text="🔄 Обновить список",
                callback_data="refresh_requests"
            )
        )

        await message.answer(requests_text, reply_markup=keyboard.as_markup())

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_student_requests: {e}")
        await message.answer("❌ Произошла ошибка при загрузке заявок")


@router.callback_query(F.data.startswith("approve_request_"))
async def handle_approve_request(callback: CallbackQuery):
    """Обработчик принятия заявки студента"""
    try:
        request_id = int(callback.data.split("_")[2])
        tutor_id = callback.from_user.id

        # Получаем информацию о заявке
        request_info = await Database.get_student_request_by_id(request_id)
        if not request_info:
            await callback.answer("❌ Заявка не найдена")
            return

        student_id = request_info[1]  # student_id из заявки

        # Принимаем заявку
        success = await Database.approve_student_request(request_id, tutor_id)

        if success:
            # Уведомляем студента о принятии
            if notification_service:
                await notification_service.notify_student_request_approved(callback.bot, student_id, tutor_id)

            await callback.answer("✅ Заявка принята!")

            # Обновляем список заявок
            await refresh_requests_list(callback)
        else:
            await callback.answer("❌ Ошибка при принятии заявки")

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_approve_request: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("reject_request_"))
async def handle_reject_request(callback: CallbackQuery):
    """Обработчик отклонения заявки студента"""
    try:
        request_id = int(callback.data.split("_")[2])
        tutor_id = callback.from_user.id

        # Получаем информацию о заявке
        request_info = await Database.get_student_request_by_id(request_id)
        if not request_info:
            await callback.answer("❌ Заявка не найдена")
            return

        student_id = request_info[1]  # student_id из заявки

        # ИСПРАВЛЕНО: Отклоняем заявку И удаляем студента из системы
        success = await Database.reject_student_request(request_id)

        if success:
            # Удаляем студента из базы данных, так как заявка отклонена
            await Database.delete_user(student_id)

            # Уведомляем студента об отклонении
            if notification_service:
                await notification_service.notify_student_request_rejected(callback.bot, student_id, tutor_id)

            await callback.answer("❌ Заявка отклонена, студент удален из системы")

            # Обновляем список заявок
            await refresh_requests_list(callback)
        else:
            await callback.answer("❌ Ошибка при отклонении заявки")

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_reject_request: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "refresh_requests")
async def handle_refresh_requests(callback: CallbackQuery):
    """Обработчик обновления списка заявок"""
    try:
        await refresh_requests_list(callback)
        await callback.answer("🔄 Список обновлен")
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_refresh_requests: {e}")
        await callback.answer("❌ Произошла ошибка")


async def refresh_requests_list(callback: CallbackQuery):
    """Функция обновления списка заявок"""
    try:
        tutor_id = callback.from_user.id
        user = await Database.get_user(tutor_id)
        menu_role = get_menu_role(tutor_id, user[3])

        # Получаем заявки от студентов
        requests = await Database.get_student_requests_for_tutor(tutor_id)

        if not requests:
            await callback.message.edit_text(
                "📋 <b>Заявки учеников</b>\n\n"
                "📭 У вас пока нет новых заявок от учеников.\n\n"
                "💡 Заявки появятся здесь, когда студенты выберут вас как репетитора.",
                reply_markup=get_main_menu_keyboard(menu_role)
            )
            return

        # Формируем обновленный список заявок
        requests_text = "📋 <b>Заявки от учеников:</b>\n\n"
        keyboard = InlineKeyboardBuilder()

        for i, request in enumerate(requests[:5], 1):
            request_id, student_id, tutor_id_req, status, created_at, student_name, student_age, timezone, subject = request

            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }.get(status, '⏳')

            requests_text += f"{i}. {status_emoji} <b>{student_name}</b>\n"
            requests_text += f"   🎂 Возраст: {student_age} лет\n"
            requests_text += f"   🌍 Часовой пояс: {timezone}\n"
            requests_text += f"   📚 Предмет: {subject}\n"
            requests_text += f"   📅 Подано: {created_at}\n"

            if status == 'pending':
                keyboard.row(
                    InlineKeyboardButton(
                        text=f"✅ Принять #{i}",
                        callback_data=f"approve_request_{request_id}"
                    ),
                    InlineKeyboardButton(
                        text=f"❌ Отклонить #{i}",
                        callback_data=f"reject_request_{request_id}"
                    )
                )

            requests_text += "\n"

        keyboard.row(
            InlineKeyboardButton(
                text="🔄 Обновить список",
                callback_data="refresh_requests"
            )
        )

        await callback.message.edit_text(requests_text, reply_markup=keyboard.as_markup())

    except Exception as e:
        logger.error(f"❌ Ошибка в refresh_requests_list: {e}")


@router.message(F.text & ~F.text.startswith('/') & ~F.text.in_([
    "📅 Мои уроки", "📚 Мои ДЗ", "ℹ️ Помощь",
    "⚙️ Настроить профиль", "📊 Управление расписанием", "🕐 Свободные окна", "👥 Мои ученики",
    "📚 Задать ДЗ", "📋 Заявки учеников", "💰 Управление оплатой", "📈 Статистика",
    "🏖️ Мои отпуска", "👥 Групповые уроки", "🔔 Настройки напоминаний",
    "➕ Добавить репетитора", "🗑️ Удалить репетитора", "👥 Управление ролями",
    "📊 Статистика системы", "📋 Список репетиторов", "⚙️ Настройки системы",
    "👑 Суперадмин-меню", "🏠 Главное меню", "❌ Отмена"
]))
async def handle_text_message(message: Message, state: FSMContext):
    """Обработчик текстовых сообщений - переписка отключена"""
    try:
        current_state = await state.get_state()
        if current_state:
            # Если есть активное состояние, не обрабатываем как сообщение
            return

        user_id = message.from_user.id
        user = await Database.get_user(user_id)

        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        role = user[3]
        menu_role = get_menu_role(user_id, role)

        await message.answer(
            "💡 <b>Информация</b>\n\n"
            "📝 Функция переписки отключена.\n"
            "🔧 Используйте кнопки меню для навигации.\n\n"
            "💬 Для связи с администрацией обратитесь к суперадминистратору.",
            reply_markup=get_main_menu_keyboard(menu_role)
        )

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_text_message: {e}")
        await message.answer("❌ Произошла ошибка при обработке сообщения")


# Универсальный обработчик callback запросов
@router.callback_query()
async def handle_callback_query(callback: CallbackQuery, state: FSMContext):
    """Универсальный обработчик callback запросов"""
    try:
        data = callback.data
        user_id = callback.from_user.id

        if data.startswith("select_tutor_"):
            await register_student_with_tutor(callback, state)
            return

        user = await Database.get_user(user_id)

        if not user:
            if data.startswith("select_tutor_"):
                await register_student_with_tutor(callback, state)
                return
            else:
                await callback.answer("❌ Пользователь не найден")
                return

        role = user[3]
        menu_role = get_menu_role(user_id, role)

        # Обработка различных callback данных
        if data == "my_schedule":
            await handle_my_schedule_callback(callback)
        elif data == "my_homework":
            await handle_my_homework_callback(callback)
        elif data == "write_to_tutor":
            await handle_write_to_tutor_callback(callback)
        elif data == "open_messages":
            await handle_open_messages_callback(callback)
        elif data.startswith("reply_to_user_"):
            await handle_reply_to_user_callback(callback)
        elif data.startswith("approve_request_"):
            await handle_approve_request(callback)
        elif data.startswith("reject_request_"):
            await handle_reject_request(callback)
        elif data == "refresh_requests":
            await handle_refresh_requests(callback)
        else:
            await callback.answer("❓ Команда не распознана")

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_callback_query: {e}")
        await callback.answer("❌ Произошла ошибка")
