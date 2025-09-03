import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_lesson_added(self, student_id: int, lesson_datetime: str, tutor_name: str):
        """Уведомление о добавлении урока"""
        try:
            message = f"""📅 <b>Новый урок запланирован!</b>

👨‍🏫 <b>Репетитор:</b> {tutor_name}
📅 <b>Дата и время:</b> {lesson_datetime}

💡 Урок добавлен в ваше расписание. Не забудьте подготовиться!"""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📅 Мое расписание", callback_data="my_schedule"),
                InlineKeyboardButton(text="💬 Написать репетитору", callback_data="write_to_tutor")
            ]])

            return await send_notification_to_user(self.bot, student_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления о новом уроке: {e}")
            return False

    async def notify_lesson_cancelled(self, student_id: int, lesson_datetime: str, tutor_name: str):
        """Уведомление об отмене урока"""
        try:
            message = f"""❌ <b>Урок отменен</b>

👨‍🏫 <b>Репетитор:</b> {tutor_name}
📅 <b>Дата и время:</b> {lesson_datetime}

💡 Урок был отменен. Свяжитесь с репетитором для переноса."""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="��� Написать репетитору", callback_data="write_to_tutor")
            ]])

            return await send_notification_to_user(self.bot, student_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления об отмене урока: {e}")
            return False

    async def notify_lesson_rescheduled(self, student_id: int, old_datetime: str, new_datetime: str, tutor_name: str):
        """Уведомление о переносе урока"""
        try:
            message = f"""🔄 <b>Урок перенесен</b>

👨‍🏫 <b>Репетитор:</b> {tutor_name}
📅 <b>Было:</b> {old_datetime}
📅 <b>Стало:</b> {new_datetime}

💡 Урок перенесен на новое время. Проверьте свое расписание!"""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📅 Мое расписание", callback_data="my_schedule"),
                InlineKeyboardButton(text="💬 Написать репетитору", callback_data="write_to_tutor")
            ]])

            return await send_notification_to_user(self.bot, student_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления о переносе урока: {e}")
            return False

    async def notify_tutor_of_student_request(self, bot: Bot, tutor_id: int, student_id: int):
        """Уведомление репетитора о новой заявке ученика"""
        try:
            student = await Database.get_user(student_id)
            student_name = student[2] if student else f"Ученик {student_id}"

            message = f"""📋 <b>Новая заявка от ученика!</b>

👤 <b>Ученик:</b> {student_name}
🆔 <b>ID:</b> {student_id}

💡 Рассмотрите заявку и примите решение."""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{student_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{student_id}")
            ]])

            return await send_notification_to_user(bot, tutor_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления о заявке: {e}")
            return False

    async def send_direct_message(self, sender_id: int, recipient_id: int, content: str,
                                  message_type: str = "text", file_id: str = None):
        """Отправка прямого сообщения между пользователями"""
        try:
            # Получаем информацию об отправителе
            sender = await Database.get_user(sender_id)
            if not sender:
                logger.error(f"Отправитель с ID {sender_id} не найден")
                return False

            sender_name = sender[2] or sender[1] or f"Пользователь {sender_id}"

            # Формируем сообщение с указанием отправителя
            message_text = f"💬 <b>Сообщение от {sender_name}:</b>\n\n{content}"

            # Отправляем сообщение получателю
            success = await send_message_to_user(self.bot, recipient_id, message_text, message_type, file_id, sender_id)

            if success:
                # Сохраняем сообщение в базу данных
                await Database.send_message(sender_id, recipient_id, content, message_type, file_id)
                logger.info(f"✅ Прямое сообщение отправлено от {sender_id} к {recipient_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Ошибка отправки прямого сообщения: {e}")
            return False

    async def send_homework_notification(self, student_id: int, homework_text: str, tutor_name: str):
        """Отправка уведомления о домашнем задании"""
        try:
            message = f"""📚 <b>Новое домашнее задание!</b>

👨‍🏫 <b>От репетитора:</b> {tutor_name}

📝 <b>Задание:</b>
{homework_text}

💡 Выполните задание и отправьте результат через раздел "📚 Мои ДЗ"."""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📚 Открыть ДЗ", callback_data="my_homework"),
                InlineKeyboardButton(text="💬 Написать репетитору", callback_data="write_to_tutor")
            ]])

            success = await send_notification_to_user(self.bot, student_id, message, reply_markup)

            if success:
                logger.info(f"✅ Уведомление о ДЗ отправлено ученику {student_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о ДЗ: {e}")
            return False

    async def notify_request_approved(self, bot: Bot, student_id: int, tutor_name: str):
        """Уведомление о принятии заявки"""
        try:
            message = f"""✅ <b>Ваша заявка принята!</b>

👨‍🏫 <b>Репетитор:</b> {tutor_name}

🎉 Поздравляем! Репетитор принял вашу заявку на обучение.
Теперь вы можете записываться на уроки и получать домашние задания.

💡 Используйте главное меню для управления расписанием и обще��ия с репетитором."""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📅 Мои уроки", callback_data="my_schedule"),
                InlineKeyboardButton(text="💬 Написать репетитору", callback_data="write_to_tutor")
            ]])

            return await send_notification_to_user(bot, student_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления о принятии заявки: {e}")
            return False

    async def notify_request_rejected(self, student_id: int, tutor_name: str):
        """Уведомление об отклонении заявки"""
        try:
            message = f"""❌ <b>Заявка отклонена</b>

👨‍🏫 <b>Репетитор:</b> {tutor_name}

К сожалению, репетитор не может принять вас на обучение в данный момент.

💡 Вы можете подать заявку к другим репетиторам через главное меню."""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="👨‍🏫 Найти репетитора", callback_data="find_tutor")
            ]])

            return await send_notification_to_user(self.bot, student_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления об отклонении заявки: {e}")
            return False

    async def notify_homework_assigned(self, student_id: int, homework_preview: str, tutor_name: str):
        """Уведомление о назначении ДЗ"""
        try:
            message = f"""📚 <b>Новое домашнее задание!</b>

👨‍🏫 <b>От репетитора:</b> {tutor_name}

📝 <b>Задание:</b>
{homework_preview}

💡 Выполните задание и отправьте результат через раздел "📚 Мои ДЗ"."""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📚 Открыть ДЗ", callback_data="my_homework"),
                InlineKeyboardButton(text="💬 Написать репетитору", callback_data="write_to_tutor")
            ]])

            return await send_notification_to_user(self.bot, student_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления о ДЗ: {e}")
            return False

    async def notify_message_received(self, recipient_id: int, sender_name: str, message_preview: str):
        """Уведомление о получении сообщения"""
        try:
            message = f"""💬 <b>Новое сообщение!</b>

👤 <b>От:</b> {sender_name}

📝 <b>Сообщение:</b>
{message_preview}

💡 Откройте раздел "💬 Сообщения" для ответа."""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💬 Открыть сообщения", callback_data="open_messages"),
                InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_to_sender")
            ]])

            return await send_notification_to_user(self.bot, recipient_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления о сообщении: {e}")
            return False

    async def notify_group_lesson_created(self, student_id: int, group_name: str, lesson_datetime: str,
                                          tutor_name: str):
        """Уведомление о создании группового урока"""
        try:
            message = f"""👥 <b>Вы добавлены в группу!</b>

👨‍🏫 <b>Репетитор:</b> {tutor_name}
👥 <b>Группа:</b> {group_name}
📅 <b>Первое занятие:</b> {lesson_datetime}

🎉 Поздравляем! Вы стали участником новой группы.
Все групповые уроки будут отображаться в вашем расписании."""

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📅 Мое расписание", callback_data="my_schedule"),
                InlineKeyboardButton(text="💬 Написать репетитору", callback_data="write_to_tutor")
            ]])

            return await send_notification_to_user(self.bot, student_id, message, reply_markup)
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления о групповом уроке: {e}")
            return False


notification_service = None


def init_notification_service(bot: Bot):
    """Инициализация сервиса уведомлений"""
    global notification_service
    notification_service = NotificationService(bot)
    return notification_service


async def send_notification_to_user(bot: Bot, user_id: int, text: str, reply_markup: InlineKeyboardMarkup = None):
    """Отправка уведомления пользователю"""
    try:
        await bot.send_message(user_id, text, reply_markup=reply_markup, parse_mode="HTML")
        logger.info(f"✅ Уведомление отправлено пользователю {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
        return False


async def send_message_to_user(bot: Bot, recipient_id: int, content: str, message_type: str = "text",
                               file_id: str = None, sender_id: int = None):
    """Отправка сообщения пользователю"""
    try:
        if message_type == "text":
            await bot.send_message(recipient_id, content, parse_mode="HTML")
        elif message_type == "voice" and file_id:
            await bot.send_voice(recipient_id, file_id, caption=content)
        elif message_type == "photo" and file_id:
            await bot.send_photo(recipient_id, file_id, caption=content)
        elif message_type == "video" and file_id:
            await bot.send_video(recipient_id, file_id, caption=content)
        elif message_type == "file" and file_id:
            await bot.send_document(recipient_id, file_id, caption=content)

        # Добавляем кнопку ответа если есть отправитель
        if sender_id:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_to_user_{sender_id}")
            ]])
            await bot.send_message(recipient_id, "👆 Сообщение от вашего репетитора", reply_markup=reply_markup)

        logger.info(f"✅ Сообщение отправлено пользователю {recipient_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения пользователю {recipient_id}: {e}")
        return False
