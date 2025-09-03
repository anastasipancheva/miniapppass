import logging
from functools import wraps
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import get_main_menu_keyboard, get_student_homework_content_keyboard
from states import StudentStates, StudentHomeworkStates
from constants import ROLES, get_user_role_for_menu as get_menu_role

logger = logging.getLogger(__name__)

router = Router()


def check_student_rights(func):
    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        user_id = message_or_callback.from_user.id
        user = await Database.get_user(user_id)

        # Allow access for unregistered users during registration process
        if not user:
            return await func(message_or_callback, *args, **kwargs)

        # Allow access for students and unregistered users
        if user[3] not in [ROLES["STUDENT"], ROLES["UNREGISTERED"]]:
            if hasattr(message_or_callback, 'answer'):
                await message_or_callback.answer("❌ У вас нет прав ученика.")
            else:
                await message_or_callback.message.answer("❌ У вас нет прав ученика.")
            return

        return await func(message_or_callback, *args, **kwargs)

    return wrapper


@router.message(F.text == "📚 Мои ДЗ")
@check_student_rights
async def show_my_homework(message: Message):
    """Показать домашние задания ученика"""
    try:
        student_id = message.from_user.id
        homework_list = await Database.get_homework_for_student(student_id)

        if not homework_list:
            await message.answer(
                "📚 <b>У вас пока нет домашних заданий.</b>\n\n"
                "⏳ Ожидайте заданий от вашего репетитора.",
                reply_markup=get_main_menu_keyboard(ROLES["STUDENT"])
            )
            return

        # Формируем список ДЗ
        homework_text = "📚 <b>Ваши домашние задания:</b>\n\n"

        builder = InlineKeyboardBuilder()

        for i, hw in enumerate(homework_list[:10], 1):  # Показываем последние 10
            hw_id, student_id, tutor_id, content_type, content_data, description, assigned_at, reminder_date, reminder_time, is_completed = hw

            status = "✅" if is_completed else "⏳"
            short_desc = description[:50] + "..." if description and len(description) > 50 else (
                    description or "Без описания")

            homework_text += f"{i}. {status} {short_desc}\n"

            builder.add(InlineKeyboardButton(
                text=f"{status} ДЗ #{i}",
                callback_data=f"hw_view_{hw_id}"
            ))

        builder.adjust(2)

        await message.answer(
            homework_text + "\n💡 Выберите задание для просмотра:",
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        logger.error(f"❌ Ошибка в show_my_homework: {e}")
        await message.answer("❌ Произошла ошибка при загрузке домашних заданий.")


@router.callback_query(F.data.startswith("hw_view_"))
async def view_homework_details(callback: CallbackQuery):
    """Просмотр деталей домашнего задания"""
    try:
        hw_id = int(callback.data.split("_")[2])

        homework = await Database.get_homework_by_id(hw_id)
        if not homework:
            await callback.answer("❌ Задание не найдено")
            return

        hw_id, student_id, tutor_id, content_type, content_data, description, assigned_at, reminder_date, reminder_time, is_completed = homework

        # Получаем информацию о репетиторе
        tutor = await Database.get_user(tutor_id)
        tutor_name = tutor[2] if tutor else f"Репетитор {tutor_id}"

        status_text = "✅ Выполнено" if is_completed else "⏳ В процессе"

        hw_text = (
            f"📚 <b>Домашнее задание #{hw_id}</b>\n\n"
            f"👨‍🏫 <b>От:</b> {tutor_name}\n"
            f"📅 <b>Задано:</b> {assigned_at}\n"
            f"📊 <b>Статус:</b> {status_text}\n"
            f"📝 <b>Описание:</b> {description or 'Без описания'}\n"
        )

        # Создаем клавиатуру для действий
        builder = InlineKeyboardBuilder()

        if not is_completed:
            builder.add(InlineKeyboardButton(
                text="📤 Сдать ДЗ",
                callback_data=f"submit_hw_{hw_id}"
            ))

        builder.add(InlineKeyboardButton(
            text="🔙 К списку ДЗ",
            callback_data="back_to_homework_list"
        ))

        # Отправляем контент задания
        if content_type == "text":
            await callback.message.edit_text(
                hw_text + f"\n📄 <b>Задание:</b>\n{content_data}",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.edit_text(hw_text, reply_markup=builder.as_markup())

            # Отправляем медиа-контент
            try:
                if content_type == "voice":
                    await callback.message.answer_voice(content_data)
                elif content_type == "photo":
                    await callback.message.answer_photo(content_data)
                elif content_type == "file":
                    await callback.message.answer_document(content_data)
                elif content_type == "video":
                    await callback.message.answer_video(content_data)
            except Exception as e:
                logger.error(f"❌ Ошибка отправки медиа-контента: {e}")

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в view_homework_details: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("submit_hw_"))
async def start_homework_submission(callback: CallbackQuery, state: FSMContext):
    """Начало сдачи домашнего задания"""
    try:
        hw_id = int(callback.data.split("_")[2])

        await state.update_data(submitting_hw_id=hw_id)

        await callback.message.edit_text(
            "📤 <b>Сдача домашнего задания</b>\n\n"
            "📝 Выберите тип ответа:",
            reply_markup=get_student_homework_content_keyboard(include_cancel=True)
        )
        await state.set_state(StudentHomeworkStates.waiting_for_submission_type)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в start_homework_submission: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("submit_"))
async def handle_submission_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа сдачи ДЗ"""
    try:
        submission_type = callback.data.replace("submit_", "")

        if submission_type == "cancel":
            await callback.message.edit_text("❌ Сдача ДЗ отменена")
            await state.clear()
            await callback.answer()
            return

        await state.update_data(submission_type=submission_type)

        type_messages = {
            "text": "📝 Введите ваш ответ текстом:",
            "photo": "📷 Отправьте фото с решением:",
            "file": "📁 Отправьте файл с решением:",
            "voice": "🎤 Отправьте голосовое сообщение:",
            "video": "🎥 Отправьте видео с решением:"
        }

        message_text = type_messages.get(submission_type, "📝 Отправьте ваш ответ:")

        await callback.message.edit_text(message_text, reply_markup=None)
        await state.set_state(StudentHomeworkStates.waiting_for_submission_content)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_submission_type: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.message(StudentHomeworkStates.waiting_for_submission_content)
async def receive_homework_submission(message: Message, state: FSMContext):
    """Получение сдачи домашнего задания"""
    try:
        data = await state.get_data()
        hw_id = data.get("submitting_hw_id")
        submission_type = data.get("submission_type", "text")
        student_id = message.from_user.id

        if not hw_id:
            await message.answer("❌ Ошибка: задание не найдено")
            await state.clear()
            return

        # Получаем информацию о ДЗ
        homework = await Database.get_homework_by_id(hw_id)
        if not homework:
            await message.answer("❌ Задание не найдено")
            await state.clear()
            return

        tutor_id = homework[2]

        content_data = ""
        description = ""

        # Обрабатываем разные типы контента
        if submission_type == "text" and message.text:
            content_data = message.text
            description = message.text[:100] + "..." if len(message.text) > 100 else message.text
        elif submission_type == "photo" and message.photo:
            content_data = message.photo[-1].file_id
            description = message.caption or "Фото решение"
        elif submission_type == "file" and message.document:
            content_data = message.document.file_id
            description = message.document.file_name or "Файл решение"
        elif submission_type == "voice" and message.voice:
            content_data = message.voice.file_id
            description = "Голосовое решение"
        elif submission_type == "video" and message.video:
            content_data = message.video.file_id
            description = message.caption or "Видео решение"
        else:
            await message.answer("❌ Неподдерживаемый тип контента. Попробуйте еще раз.")
            return

        # Сохраняем сдачу ДЗ
        success = await Database.submit_homework(
            student_id=student_id,
            tutor_id=tutor_id,
            content_type=submission_type,
            content_data=content_data,
            description=description
        )

        if success:
            await message.answer(
                "✅ <b>Домашнее задание успешно сдано!</b>\n\n"
                "📨 Репетитор получит уведомление о вашем ответе.",
                reply_markup=get_main_menu_keyboard(ROLES["STUDENT"])
            )

            try:
                student = await Database.get_user(student_id)
                student_name = student[2] if student else f"Ученик {student_id}"

                notification_text = f"📤 <b>Новая сдача ДЗ!</b>\n\n👤 <b>От:</b> {student_name}\n📝 <b>Тип:</b> {submission_type}\n📄 <b>Описание:</b> {description}"

                if submission_type == "text":
                    await message.bot.send_message(tutor_id, notification_text + f"\n\n📄 <b>Ответ:</b>\n{content_data}")
                elif submission_type == "voice":
                    await message.bot.send_voice(tutor_id, content_data, caption=notification_text)
                elif submission_type == "photo":
                    await message.bot.send_photo(tutor_id, content_data, caption=notification_text)
                elif submission_type == "file":
                    await message.bot.send_document(tutor_id, content_data, caption=notification_text)
                elif submission_type == "video":
                    await message.bot.send_video(tutor_id, content_data, caption=notification_text)

            except Exception as e:
                logger.error(f"❌ Ошибка отправки уведомления репетитору: {e}")
        else:
            await message.answer("❌ Ошибка при сохранении сдачи ДЗ.")

        await state.clear()

    except Exception as e:
        logger.error(f"❌ Ошибка в receive_homework_submission: {e}")
        await message.answer("❌ Произошла ошибка при обработке сдачи ДЗ.")
        await state.clear()


@router.callback_query(F.data == "back_to_homework_list")
async def back_to_homework_list(callback: CallbackQuery):
    """Возврат к списку ДЗ"""
    try:
        student_id = callback.from_user.id
        homework_list = await Database.get_homework_for_student(student_id)

        if not homework_list:
            await callback.message.edit_text("📚 <b>У вас нет домашних заданий.</b>")
            await callback.answer()
            return

        # Формируем список ДЗ
        homework_text = "📚 <b>Ваши домашние задания:</b>\n\n"

        builder = InlineKeyboardBuilder()

        for i, hw in enumerate(homework_list[:10], 1):
            hw_id, student_id, tutor_id, content_type, content_data, description, assigned_at, reminder_date, reminder_time, is_completed = hw

            status = "✅" if is_completed else "⏳"
            short_desc = description[:50] + "..." if description and len(description) > 50 else (
                    description or "Без описания")

            homework_text += f"{i}. {status} {short_desc}\n"

            builder.add(InlineKeyboardButton(
                text=f"{status} ДЗ #{i}",
                callback_data=f"hw_view_{hw_id}"
            ))

        builder.adjust(2)

        await callback.message.edit_text(
            homework_text + "\n💡 Выберите задание для просмотра:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка в back_to_homework_list: {e}")
        await callback.answer("❌ Произошла ошибка")


# Обновленные обработчики для студента
@router.message(F.text == "📅 Мои уроки")
@check_student_rights
async def show_my_lessons(message: Message):
    """Показать уроки ученика"""
    try:
        student_id = message.from_user.id
        lessons = await Database.get_student_upcoming_lessons(student_id)

        if not lessons:
            await message.answer(
                "📅 <b>Мои уроки</b>\n\n"
                "📭 У вас пока нет запланированных уроков.\n\n"
                "💡 Свяжитесь с репетитором для планирования занятий.",
                reply_markup=get_main_menu_keyboard(ROLES["STUDENT"])
            )
            return

        lessons_text = "📅 <b>Ваши уроки:</b>\n\n"

        for i, lesson in enumerate(lessons[:10], 1):
            lesson_id, student_id, tutor_id, lesson_date, lesson_time, subject, status = lesson
            tutor = await Database.get_user(tutor_id)
            tutor_name = tutor[2] if tutor else f"Репетитор {tutor_id}"

            status_emoji = {
                'scheduled': '📅',
                'completed': '✅',
                'cancelled': '❌',
                'rescheduled': '🔄'
            }.get(status, '📅')

            lessons_text += f"{i}. {status_emoji} {lesson_date} в {lesson_time}\n"
            lessons_text += f"   👨‍🏫 {tutor_name}\n"
            lessons_text += f"   📚 {subject or 'Урок'}\n"
            lessons_text += f"   📊 {status}\n\n"

        await message.answer(lessons_text, reply_markup=get_main_menu_keyboard(ROLES["STUDENT"]))

    except Exception as e:
        logger.error(f"❌ Ошибка в show_my_lessons: {e}")
        await message.answer("❌ Произошла ошибка при загрузке уроков.")


@router.message(F.text == "💬 Сообщения")
@check_student_rights
async def student_messages(message: Message, state: FSMContext):
    """Сообщения для ученика с возможностью ответа"""
    try:
        student_id = message.from_user.id
        messages = await Database.get_messages_for_user(student_id)

        if not messages:
            await message.answer(
                "💬 <b>Сообщения</b>\n\n"
                "📭 У вас нет новых сообщений.\n\n"
                "💡 Здесь будут отображаться сообщения от репетитора.\n\n"
                "📝 Чтобы написать репетитору, просто отправьте текстовое сообщение.",
                reply_markup=get_main_menu_keyboard(ROLES["STUDENT"])
            )
            return

        messages_text = "💬 <b>Ваши сообщения:</b>\n\n"

        for i, msg in enumerate(messages[:5], 1):
            msg_id, sender_id, recipient_id, content, sent_at, is_read = msg
            sender = await Database.get_user(sender_id)
            sender_name = sender[2] if sender else f"Пользователь {sender_id}"

            status = "📖" if is_read else "📩"
            short_content = content[:50] + "..." if len(content) > 50 else content

            messages_text += f"{i}. {status} От {sender_name}\n"
            messages_text += f"   📝 {short_content}\n"
            messages_text += f"   📅 {sent_at}\n\n"

        messages_text += "📝 Чтобы ответить, просто отправьте текстовое сообщение."

        await message.answer(messages_text, reply_markup=get_main_menu_keyboard(ROLES["STUDENT"]))

    except Exception as e:
        logger.error(f"❌ Ошибка в student_messages: {e}")
        await message.answer("❌ Произошла ошибка при загрузке сообщений.")


@router.message(F.text == "📞 Связаться с репетитором")
@check_student_rights
async def contact_tutor(message: Message):
    """Связаться с репетитором"""
    try:
        student_id = message.from_user.id

        # Получаем репетитора ученика
        tutor = await Database.get_student_tutor(student_id)

        if not tutor:
            await message.answer(
                "📞 <b>Связаться с репетитором</b>\n\n"
                "❌ У вас пока нет назначенного репетитора.\n\n"
                "💡 Обратитесь к администратору для назначения репетитора.",
                reply_markup=get_main_menu_keyboard(ROLES["STUDENT"])
            )
            return

        tutor_id, tutor_username, tutor_name, tutor_role = tutor
        tutor_display_name = tutor_name or tutor_username or f"Репетитор {tutor_id}"

        contact_text = (
            "📞 <b>Связаться с репетитором</b>\n\n"
            f"👨‍🏫 <b>Ваш репетитор:</b> {tutor_display_name}\n\n"
            "💬 <b>Способы связи:</b>\n"
            "• Написать сообщение через бота\n"
            "• Задать вопрос о домашнем задании\n"
            "• Обсудить расписание уроков\n\n"
            "💡 Для отправки сообщения используйте кнопку 'Сообщения'."
        )

        await message.answer(contact_text, reply_markup=get_main_menu_keyboard(ROLES["STUDENT"]))

    except Exception as e:
        logger.error(f"❌ Ошибка в contact_tutor: {e}")
        await message.answer("❌ Произошла ошибка при загрузке информации о репетиторе.")


# @router.callback_query()
# async def handle_student_callback(callback: CallbackQuery, state: FSMContext):
#     """Обработчик всех callback'ов студента"""
#     try:
#         callback_data = callback.data
#
#         # Маршрутизация callback'ов студента
#         if callback_data.startswith("hw_view_"):
#             await view_homework_details(callback)
#         elif callback_data.startswith("submit_hw_"):
#             await start_homework_submission(callback, state)
#         elif callback_data.startswith("submit_"):
#             await handle_submission_type(callback, state)
#         elif callback_data == "back_to_homework_list":
#             await back_to_homework_list(callback)
#         else:
#             await callback.answer("❌ Неизвестная команда")
#
#     except Exception as e:
#         logger.error(f"❌ Ошибка в handle_student_callback: {e}")
#         await callback.answer("❌ Произошла ошибка")
