from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import Database
from keyboards import get_main_menu_keyboard, get_admin_homework_content_keyboard
from states import AdminStates, HomeworkStates
from constants import ROLES, has_role, get_user_role_for_menu as get_menu_role
from notifications import notification_service
import logging

logger = logging.getLogger(__name__)
router = Router()


def check_admin_rights(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(message_or_callback, *args, **kwargs):
        user_id = message_or_callback.from_user.id
        user = await Database.get_user(user_id)

        if not user:
            if hasattr(message_or_callback, 'answer'):
                await message_or_callback.answer("❌ Пользователь не найден.")
            else:
                await message_or_callback.message.answer("❌ Пользователь не найден.")
            return

        menu_role = get_menu_role(user_id, user[3])
        if menu_role not in [ROLES["ADMIN"], ROLES["SUPERADMIN"]]:
            if hasattr(message_or_callback, 'answer'):
                await message_or_callback.answer("❌ У вас нет прав администратора.")
            else:
                await message_or_callback.message.answer("❌ У вас нет прав администратора.")
            return

        return await func(message_or_callback, *args, **kwargs)
    return wrapper


@router.message(F.text == "📚 Задать ДЗ")
@check_admin_rights
async def assign_homework_start(message: Message, state: FSMContext):
    """Начало процесса задания домашнего задания"""
    try:
        tutor_id = message.from_user.id
        students = await Database.get_tutor_students(tutor_id)
        
        if not students:
            await message.answer(
                "👥 <b>Задать домашнее задание</b>\n\n"
                "❌ У вас пока нет учеников.\n\n"
                "💡 Ученики появятся после принятия заявок.",
                reply_markup=get_main_menu_keyboard(ROLES["ADMIN"])
            )
            return

        # Создаем клавиатуру со студентами
        builder = InlineKeyboardBuilder()
        
        homework_text = "📚 <b>Задать домашнее задание</b>\n\n👥 <b>Выберите ученика:</b>\n\n"
        
        for i, student in enumerate(students[:10], 1):
            student_id, username, name, role = student
            if role == 'archived':
                continue
                
            display_name = name or username or f"Ученик {student_id}"
            homework_text += f"{i}. {display_name}\n"
            
            builder.add(InlineKeyboardButton(
                text=f"👤 {display_name}",
                callback_data=f"hw_select_student_{student_id}"
            ))
        
        builder.adjust(1)
        builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="hw_cancel"))
        
        await message.answer(homework_text, reply_markup=builder.as_markup())
        await state.set_state(HomeworkStates.waiting_for_content)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в assign_homework_start: {e}")
        await message.answer("❌ Произошла ошибка при задании ДЗ.")


@router.callback_query(F.data.startswith("hw_select_student_"))
async def select_student_for_homework(callback: CallbackQuery, state: FSMContext):
    """Выбор студента для задания ДЗ"""
    try:
        student_id = int(callback.data.split("_")[3])
        await state.update_data(selected_student_id=student_id)
        
        student = await Database.get_user(student_id)
        student_name = student[2] if student else f"Ученик {student_id}"
        
        await callback.message.edit_text(
            f"📚 <b>Задать ДЗ для {student_name}</b>\n\n"
            "📝 Выберите тип задания:",
            reply_markup=get_admin_homework_content_keyboard()
        )
        await state.set_state(HomeworkStates.waiting_for_homework_content)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в select_student_for_homework: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("hw_type_"))
async def handle_homework_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа ДЗ"""
    try:
        hw_type = callback.data.replace("hw_type_", "")
        
        if hw_type == "cancel":
            await callback.message.edit_text("❌ Задание ДЗ отменено")
            await state.clear()
            await callback.answer()
            return
            
        await state.update_data(homework_type=hw_type)
        
        type_messages = {
            "text": "📝 Введите текст домашнего задания:",
            "photo": "📷 Отправьте фото с заданием:",
            "file": "📁 Отправьте файл с заданием:",
            "voice": "🎤 Отправьте голосовое сообщение:",
            "video": "🎥 Отправьте видео с заданием:"
        }
        
        message_text = type_messages.get(hw_type, "📝 Отправьте задание:")
        
        await callback.message.edit_text(message_text)
        await state.set_state(HomeworkStates.waiting_for_homework_content)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_homework_type: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.message(HomeworkStates.waiting_for_homework_content)
async def receive_homework_content(message: Message, state: FSMContext):
    """Получение содержимого ДЗ"""
    try:
        data = await state.get_data()
        student_id = data.get("selected_student_id")
        hw_type = data.get("homework_type", "text")
        tutor_id = message.from_user.id
        
        if not student_id:
            await message.answer("❌ Ошибка: студент не выбран")
            await state.clear()
            return
            
        content_data = ""
        description = ""
        
        # Обрабатываем разные типы контента
        if hw_type == "text" and message.text:
            content_data = message.text
            description = message.text[:100] + "..." if len(message.text) > 100 else message.text
        elif hw_type == "photo" and message.photo:
            content_data = message.photo[-1].file_id
            description = message.caption or "Фото задание"
        elif hw_type == "file" and message.document:
            content_data = message.document.file_id
            description = message.document.file_name or "Файл задание"
        elif hw_type == "voice" and message.voice:
            content_data = message.voice.file_id
            description = "Голосовое задание"
        elif hw_type == "video" and message.video:
            content_data = message.video.file_id
            description = message.caption or "Видео задание"
        else:
            await message.answer("❌ Неподдерживаемый тип контента. Попробуйте еще раз.")
            return
            
        # Сохраняем ДЗ в базу
        success = await Database.assign_homework(
            student_id=student_id,
            tutor_id=tutor_id,
            content_type=hw_type,
            content_data=content_data,
            description=description
        )
        
        if success:
            student = await Database.get_user(student_id)
            student_name = student[2] if student else f"Ученик {student_id}"
            tutor = await Database.get_user(tutor_id)
            tutor_name = tutor[2] if tutor else f"Репетитор {tutor_id}"
            
            await message.answer(
                f"✅ <b>Домашнее задание успешно задано!</b>\n\n"
                f"👤 <b>Ученик:</b> {student_name}\n"
                f"📝 <b>Тип:</b> {hw_type}\n"
                f"📄 <b>Описание:</b> {description}\n\n"
                f"📨 Ученик получит уведомление о новом задании.",
                reply_markup=get_main_menu_keyboard(ROLES["ADMIN"])
            )
            
            # Отправляем уведомление студенту
            try:
                if notification_service:
                    await notification_service.send_homework_notification(student_id, description, tutor_name)
                else:
                    # Прямое уведомление если сервис недоступен
                    notification_text = f"📚 <b>Новое домашнее задание!</b>\n\n👨‍🏫 <b>От репетитора:</b> {tutor_name}\n\n📝 <b>Задание:</b>\n{description}\n\n💡 Выполните задание и отправьте результат через раздел '📚 Мои ДЗ'."
                    
                    if hw_type == "text":
                        await message.bot.send_message(student_id, notification_text + f"\n\n📄 <b>Полное задание:</b>\n{content_data}")
                    elif hw_type == "voice":
                        await message.bot.send_voice(student_id, content_data, caption=notification_text)
                    elif hw_type == "photo":
                        await message.bot.send_photo(student_id, content_data, caption=notification_text)
                    elif hw_type == "file":
                        await message.bot.send_document(student_id, content_data, caption=notification_text)
                    elif hw_type == "video":
                        await message.bot.send_video(student_id, content_data, caption=notification_text)
                        
            except Exception as e:
                logger.error(f"❌ Ошибка отправки уведомления студенту: {e}")
        else:
            await message.answer("❌ Ошибка при сохранении домашнего задания.")
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в receive_homework_content: {e}")
        await message.answer("❌ Произошла ошибка при обработке ДЗ.")
        await state.clear()


@router.callback_query(F.data == "hw_cancel")
async def cancel_homework_assignment(callback: CallbackQuery, state: FSMContext):
    """Отмена задания ДЗ"""
    try:
        await callback.message.edit_text("❌ Задание домашнего задания отменено")
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Ошибка в cancel_homework_assignment: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.message(F.text == "⚙️ Настроить профиль")
@check_admin_rights
async def edit_profile_start(message: Message, state: FSMContext):
    """Начало редактирования профиля"""
    try:
        tutor_id = message.from_user.id
        tutor_info = await Database.get_tutor(tutor_id)
        
        if tutor_info:
            _, name, username, subjects, cost, link = tutor_info
            profile_text = f"""⚙️ <b>Текущий профиль репетитора:</b>

👤 <b>Имя:</b> {name}
📱 <b>Username:</b> @{username or 'не указан'}
📚 <b>Предметы:</b> {subjects}
💰 <b>Стоимость:</b> {cost} руб/урок
🔗 <b>Ссылка:</b> {link or 'не указана'}

📝 Что хотите изменить?"""
        else:
            profile_text = "⚙️ <b>Настройка профиля репетитора</b>\n\n❌ Профиль не найден. Создаем новый профиль.\n\n📝 Введите ваше имя:"
            await state.set_state(AdminStates.waiting_for_profile_name)
        
        # Создаем клавиатуру для редактирования
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="👤 Изменить имя", callback_data="edit_name"),
            InlineKeyboardButton(text="📚 Изменить предметы", callback_data="edit_subjects")
        )
        builder.row(
            InlineKeyboardButton(text="💰 Изменить стоимость", callback_data="edit_cost"),
            InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data="edit_link")
        )
        builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="edit_cancel"))
        
        await message.answer(profile_text, reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"❌ Ошибка в edit_profile_start: {e}")
        await message.answer("❌ Произошла ошибка при загрузке профиля.")


@router.callback_query(F.data.startswith("edit_"))
async def handle_profile_edit(callback: CallbackQuery, state: FSMContext):
    """Обработка редактирования профиля"""
    try:
        edit_type = callback.data.replace("edit_", "")
        
        if edit_type == "cancel":
            await callback.message.edit_text("❌ Редактирование профиля отменено")
            await state.clear()
            await callback.answer()
            return
            
        edit_messages = {
            "name": ("👤 Введите новое имя:", AdminStates.waiting_for_profile_name),
            "subjects": ("📚 Введите предметы (через запятую):", AdminStates.waiting_for_profile_subjects),
            "cost": ("💰 Введите стоимость урока в рублях:", AdminStates.waiting_for_profile_cost),
            "link": ("🔗 Введите ссылку на урок:", AdminStates.waiting_for_profile_link)
        }
        
        if edit_type in edit_messages:
            message_text, new_state = edit_messages[edit_type]
            await callback.message.edit_text(message_text)
            await state.set_state(new_state)
            await callback.answer()
        else:
            await callback.answer("❌ Неизвестная команда")
            
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_profile_edit: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.message(AdminStates.waiting_for_profile_name)
async def process_profile_name(message: Message, state: FSMContext):
    """Обработка нового имени"""
    try:
        tutor_id = message.from_user.id
        new_name = message.text.strip()
        
        success = await Database.update_tutor_profile(tutor_id, name=new_name)
        
        if success:
            await message.answer(
                f"✅ <b>Имя успешно обновлено!</b>\n\n👤 <b>Новое имя:</b> {new_name}",
                reply_markup=get_main_menu_keyboard(ROLES["ADMIN"])
            )
        else:
            await message.answer("❌ Ошибка при обновлении имени.")
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в process_profile_name: {e}")
        await message.answer("❌ Произошла ошибка.")
        await state.clear()


@router.message(AdminStates.waiting_for_profile_subjects)
async def process_profile_subjects(message: Message, state: FSMContext):
    """Обработка новых предметов"""
    try:
        tutor_id = message.from_user.id
        new_subjects = message.text.strip()
        
        success = await Database.update_tutor_profile(tutor_id, subjects=new_subjects)
        
        if success:
            await message.answer(
                f"✅ <b>Предметы успешно обновлены!</b>\n\n📚 <b>Новые предметы:</b> {new_subjects}",
                reply_markup=get_main_menu_keyboard(ROLES["ADMIN"])
            )
        else:
            await message.answer("❌ Ошибка при обновлении предметов.")
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в process_profile_subjects: {e}")
        await message.answer("❌ Произошла ошибка.")
        await state.clear()


@router.message(AdminStates.waiting_for_profile_cost)
async def process_profile_cost(message: Message, state: FSMContext):
    """Обработка новой стоимости"""
    try:
        tutor_id = message.from_user.id
        
        try:
            new_cost = float(message.text.strip())
            if new_cost < 0:
                await message.answer("❌ Стоимость не может быть отрицательной.")
                return
        except ValueError:
            await message.answer("❌ Неверный формат стоимости. Введите число:")
            return
            
        success = await Database.update_tutor_profile(tutor_id, cost=new_cost)
        
        if success:
            await message.answer(
                f"✅ <b>Стоимость успешно обновлена!</b>\n\n💰 <b>Новая стоимость:</b> {new_cost} руб/урок",
                reply_markup=get_main_menu_keyboard(ROLES["ADMIN"])
            )
        else:
            await message.answer("❌ Ошибка при обновлении стоимости.")
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в process_profile_cost: {e}")
        await message.answer("❌ Произошла ошибка.")
        await state.clear()


@router.message(AdminStates.waiting_for_profile_link)
async def process_profile_link(message: Message, state: FSMContext):
    """Обработка новой ссылки"""
    try:
        tutor_id = message.from_user.id
        new_link = message.text.strip()
        
        if new_link.lower() == "нет":
            new_link = None
            
        success = await Database.update_tutor_profile(tutor_id, link=new_link)
        
        if success:
            link_text = new_link or "не указана"
            await message.answer(
                f"✅ <b>Ссылка успешно обновлена!</b>\n\n🔗 <b>Новая ссылка:</b> {link_text}",
                reply_markup=get_main_menu_keyboard(ROLES["ADMIN"])
            )
        else:
            await message.answer("❌ Ошибка при обновлении ссылки.")
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в process_profile_link: {e}")
        await message.answer("❌ Произошла ошибка.")
        await state.clear()
