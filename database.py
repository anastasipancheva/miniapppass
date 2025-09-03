import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class Database:
    _db_path = "bot_database.db"
    _connection = None
    _lock = asyncio.Lock()

    @classmethod
    async def init_db(cls):
        """Инициализация базы данных"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT,
                        name TEXT,
                        role TEXT DEFAULT 'student',
                        tutor_id INTEGER,
                        timezone TEXT,
                        subject TEXT,
                        age INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tutor_id) REFERENCES users (id)
                    )
                ''')

                await db.execute('''
                    CREATE TABLE IF NOT EXISTS tutors (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        username TEXT,
                        subjects TEXT,
                        cost REAL DEFAULT 1000,
                        link TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы уроков
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS lessons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        tutor_id INTEGER,
                        lesson_date TEXT,
                        lesson_time TEXT,
                        subject TEXT,
                        status TEXT DEFAULT 'scheduled',
                        cost REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES users (id),
                        FOREIGN KEY (tutor_id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы домашних заданий
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS homework (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        tutor_id INTEGER,
                        content_type TEXT,
                        content_data TEXT,
                        description TEXT,
                        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        reminder_date TEXT,
                        reminder_time TEXT,
                        is_completed BOOLEAN DEFAULT 0,
                        FOREIGN KEY (student_id) REFERENCES users (id),
                        FOREIGN KEY (tutor_id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы сообщений
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_id INTEGER,
                        recipient_id INTEGER,
                        content TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_read BOOLEAN DEFAULT 0,
                        FOREIGN KEY (sender_id) REFERENCES users (id),
                        FOREIGN KEY (recipient_id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы заявок студентов
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS student_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        tutor_id INTEGER,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES users (id),
                        FOREIGN KEY (tutor_id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы групп
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tutor_id INTEGER,
                        name TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tutor_id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы участников групп
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS group_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER,
                        student_id INTEGER,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (group_id) REFERENCES groups (id),
                        FOREIGN KEY (student_id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы доступных слотов
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS available_slots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tutor_id INTEGER,
                        slot_date TEXT,
                        slot_time TEXT,
                        is_booked BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tutor_id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы стандартного расписания
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS standard_schedule (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tutor_id INTEGER,
                        student_id INTEGER,
                        day_of_week INTEGER,
                        time TEXT,
                        subject TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tutor_id) REFERENCES users (id),
                        FOREIGN KEY (student_id) REFERENCES users (id)
                    )
                ''')

                # Создание таблицы отпусков
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS vacation_periods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tutor_id INTEGER,
                        start_date TEXT,
                        end_date TEXT,
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tutor_id) REFERENCES users (id)
                    )
                ''')

                await db.commit()
                logger.info("✅ База данных успешно инициализирована")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise

    @classmethod
    async def close(cls):
        """Закрытие соединения с базой данных"""
        if cls._connection:
            await cls._connection.close()
            cls._connection = None

    # Методы для работы с пользователями
    @classmethod
    async def get_user(cls, user_id: int) -> Optional[Tuple]:
        """Получить пользователя по ID"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    "SELECT id, username, name, role, tutor_id, timezone, subject, age, created_at FROM users WHERE id = ?",
                    (user_id,)
                )
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя {user_id}: {e}")
            return None

    @classmethod
    async def add_user(cls, user_id: int, username: str, full_name: str, role: str = "student",
                       tutor_id: int = None, timezone: str = None, subject: str = None, age: int = None) -> bool:
        """Добавить нового пользователя"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO users (id, username, name, role, tutor_id, timezone, subject, age) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, username, full_name, role, tutor_id, timezone, subject, age)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления пользователя {user_id}: {e}")
            return False

    @classmethod
    async def update_user_role(cls, user_id: int, role: str) -> bool:
        """Обновить роль пользователя"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "UPDATE users SET role = ? WHERE id = ?",
                    (role, user_id)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления роли пользователя {user_id}: {e}")
            return False

    @classmethod
    async def delete_user(cls, user_id: int) -> bool:
        """Удалить пользователя"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления пользователя {user_id}: {e}")
            return False

    # Методы для работы с репетиторами
    @classmethod
    async def get_tutor(cls, tutor_id: int) -> Optional[Tuple]:
        """Получить информацию о репетиторе"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    "SELECT id, name, username, subjects, cost, link FROM tutors WHERE id = ?",
                    (tutor_id,)
                )
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка получения репетитора {tutor_id}: {e}")
            return None

    @classmethod
    async def get_all_tutors(cls) -> List[Tuple]:
        """Получить всех репетиторов"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    "SELECT id, name, username, subjects, cost, link FROM tutors"
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка репетиторов: {e}")
            return []

    @classmethod
    async def add_tutor_with_username(cls, tutor_id: int, name: str, subjects: str, cost: float, link: str = None,
                                      username: str = None) -> bool:
        """Добавить репетитора с username"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO tutors (id, name, username, subjects, cost, link) VALUES (?, ?, ?, ?, ?, ?)",
                    (tutor_id, name, username, subjects, cost, link)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления репетитора {tutor_id}: {e}")
            return False

    @classmethod
    async def update_tutor_profile(cls, tutor_id: int, name: str = None, username: str = None, subjects: str = None,
                                   cost: float = None, link: str = None) -> bool:
        """Обновить профиль репетитора"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                # Получаем текущие данные
                current = await cls.get_tutor(tutor_id)
                if not current:
                    # Создаем новый профиль
                    await db.execute(
                        "INSERT INTO tutors (id, name, username, subjects, cost, link) VALUES (?, ?, ?, ?, ?, ?)",
                        (tutor_id, name or "Репетитор", username, subjects or "Не указано", cost or 1000, link)
                    )
                else:
                    # Обновляем существующий
                    await db.execute(
                        "UPDATE tutors SET name = ?, username = ?, subjects = ?, cost = ?, link = ? WHERE id = ?",
                        (
                            name or current[1],
                            username or current[2],
                            subjects or current[3],
                            cost or current[4],
                            link or current[5],
                            tutor_id
                        )
                    )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления профиля репетитора {tutor_id}: {e}")
            return False

    @classmethod
    async def delete_tutor_info(cls, tutor_id: int) -> bool:
        """Удалить информацию о репетиторе"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute("DELETE FROM tutors WHERE id = ?", (tutor_id,))
                # Также обновляем роль пользователя
                await db.execute("UPDATE users SET role = 'archived' WHERE id = ?", (tutor_id,))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления репетитора {tutor_id}: {e}")
            return False

    # Методы для работы со студентами
    @classmethod
    async def get_tutor_students(cls, tutor_id: int, include_archived: bool = False) -> List[Tuple]:
        """Получить студентов репетитора"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                if include_archived:
                    cursor = await db.execute(
                        """SELECT DISTINCT u.id, u.username, u.name, u.role 
                           FROM users u 
                           JOIN lessons l ON u.id = l.student_id 
                           WHERE l.tutor_id = ?""",
                        (tutor_id,)
                    )
                else:
                    cursor = await db.execute(
                        """SELECT DISTINCT u.id, u.username, u.name, u.role 
                           FROM users u 
                           JOIN lessons l ON u.id = l.student_id 
                           WHERE l.tutor_id = ? AND u.role != 'archived'""",
                        (tutor_id,)
                    )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения студентов репетитора {tutor_id}: {e}")
            return []

    @classmethod
    async def get_student_tutor(cls, student_id: int) -> Optional[Tuple]:
        """Получить репетитора студента"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT DISTINCT u.id, u.username, u.name, u.role 
                       FROM users u 
                       JOIN lessons l ON u.id = l.tutor_id 
                       WHERE l.student_id = ? 
                       ORDER BY l.created_at DESC LIMIT 1""",
                    (student_id,)
                )
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка получения репетитора студента {student_id}: {e}")
            return None

    @classmethod
    async def get_tutor_students_and_groups(cls, tutor_id: int) -> Dict[str, List]:
        """Получить студентов и группы репетитора"""
        try:
            students = await cls.get_tutor_students(tutor_id)
            groups = await cls.get_tutor_groups(tutor_id)
            return {
                'students': students,
                'groups': groups
            }
        except Exception as e:
            logger.error(f"❌ Ошибка получения студентов и групп репетитора {tutor_id}: {e}")
            return {'students': [], 'groups': []}

    # Методы для работы с уроками
    @classmethod
    async def get_student_upcoming_lessons(cls, student_id: int) -> List[Tuple]:
        """Получить предстоящие уроки студента"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, student_id, tutor_id, lesson_date, lesson_time, subject, status 
                       FROM lessons 
                       WHERE student_id = ? AND status != 'cancelled' 
                       ORDER BY lesson_date, lesson_time""",
                    (student_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения уроков студента {student_id}: {e}")
            return []

    @classmethod
    async def get_tutor_upcoming_lessons(cls, tutor_id: int) -> List[Tuple]:
        """Получить предстоящие уроки репетитора"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, student_id, tutor_id, lesson_date, lesson_time, subject, status 
                       FROM lessons 
                       WHERE tutor_id = ? AND status != 'cancelled' 
                       ORDER BY lesson_date, lesson_time""",
                    (tutor_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения уроков репетитора {tutor_id}: {e}")
            return []

    @classmethod
    async def add_lesson(cls, student_id: int, tutor_id: int, lesson_date: str, lesson_time: str, subject: str = None,
                         cost: float = None) -> bool:
        """Добавить урок"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "INSERT INTO lessons (student_id, tutor_id, lesson_date, lesson_time, subject, cost) VALUES (?, ?, ?, ?, ?, ?)",
                    (student_id, tutor_id, lesson_date, lesson_time, subject, cost)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления урока: {e}")
            return False

    @classmethod
    async def get_lesson_by_id(cls, lesson_id: int) -> Optional[Tuple]:
        """Получить урок по ID"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    "SELECT id, student_id, tutor_id, lesson_date, lesson_time, subject, status, cost FROM lessons WHERE id = ?",
                    (lesson_id,)
                )
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка получения урока {lesson_id}: {e}")
            return None

    @classmethod
    async def cancel_lesson(cls, lesson_id: int) -> bool:
        """Отменить урок"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "UPDATE lessons SET status = 'cancelled' WHERE id = ?",
                    (lesson_id,)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка отмены урока {lesson_id}: {e}")
            return False

    # Методы для работы с домашними заданиями
    @classmethod
    async def get_homework_for_student(cls, student_id: int) -> List[Tuple]:
        """Получить домашние задания студента"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, student_id, tutor_id, content_type, content_data, description, 
                              assigned_at, reminder_date, reminder_time, is_completed 
                       FROM homework 
                       WHERE student_id = ? 
                       ORDER BY assigned_at DESC""",
                    (student_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения ДЗ студента {student_id}: {e}")
            return []

    @classmethod
    async def get_homework_by_id(cls, hw_id: int) -> Optional[Tuple]:
        """Получить домашнее задание по ID"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, student_id, tutor_id, content_type, content_data, description, 
                              assigned_at, reminder_date, reminder_time, is_completed 
                       FROM homework WHERE id = ?""",
                    (hw_id,)
                )
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка получения ДЗ {hw_id}: {e}")
            return None

    @classmethod
    async def submit_homework(cls, student_id: int, tutor_id: int, content_type: str, content_data: str,
                              description: str) -> bool:
        """Сдать домашнее задание"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "INSERT INTO homework (student_id, tutor_id, content_type, content_data, description, is_completed) VALUES (?, ?, ?, ?, ?, 1)",
                    (student_id, tutor_id, content_type, content_data, description)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка сдачи ДЗ: {e}")
            return False

    @classmethod
    async def assign_homework(cls, student_id: int, tutor_id: int, content_type: str, content_data: str,
                              description: str, reminder_date: str = None, reminder_time: str = None) -> bool:
        """Задать домашнее задание"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    """INSERT INTO homework (student_id, tutor_id, content_type, content_data, description, 
                                           reminder_date, reminder_time, is_completed) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
                    (student_id, tutor_id, content_type, content_data, description, reminder_date, reminder_time)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка задания ДЗ: {e}")
            return False

    @classmethod
    async def get_homework_for_tutor(cls, tutor_id: int) -> List[Tuple]:
        """Получить домашние задания репетитора"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT h.id, h.student_id, h.tutor_id, h.content_type, h.content_data, 
                              h.description, h.assigned_at, h.reminder_date, h.reminder_time, 
                              h.is_completed, u.name as student_name
                       FROM homework h
                       JOIN users u ON h.student_id = u.id
                       WHERE h.tutor_id = ? 
                       ORDER BY h.assigned_at DESC""",
                    (tutor_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения ДЗ репетитора {tutor_id}: {e}")
            return []

    # Методы для работы с сообщениями
    @classmethod
    async def send_message(cls, sender_id: int, recipient_id: int, content: str, message_type: str = "text", 
                          file_id: str = None) -> bool:
        """Отправить сообщение (только для системных уведомлений)"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)",
                    (sender_id, recipient_id, content)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            return False

    @classmethod
    async def get_messages_for_user(cls, user_id: int) -> List[Tuple]:
        """Получить сообщения для пользователя"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, sender_id, recipient_id, content, sent_at, is_read 
                       FROM messages 
                       WHERE recipient_id = ? 
                       ORDER BY sent_at DESC LIMIT 10""",
                    (user_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений пользователя {user_id}: {e}")
            return []

    @classmethod
    async def get_recent_messages_for_user(cls, user_id: int) -> List[Tuple]:
        """Получить недавние сообщения для пользователя"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, sender_id, recipient_id, 'text' as message_type, content, 
                              NULL as file_id, sent_at, is_read, NULL as reply_to_id
                       FROM messages 
                       WHERE recipient_id = ? 
                       ORDER BY sent_at DESC LIMIT 10""",
                    (user_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений пользователя {user_id}: {e}")
            return []

    @classmethod
    async def get_conversation_history(cls, tutor_id: int, student_id: int) -> List[Tuple]:
        """Получить историю переписки"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, sender_id, recipient_id, content, sent_at, is_read 
                       FROM messages 
                       WHERE (sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?)
                       ORDER BY sent_at DESC LIMIT 20""",
                    (tutor_id, student_id, student_id, tutor_id)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения истории переписки: {e}")
            return []

    # Методы для работы с заявками
    @classmethod
    async def add_student_request(cls, student_id: int, tutor_id: int) -> Optional[int]:
        """Добавить заявку студента"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    "INSERT INTO student_requests (student_id, tutor_id) VALUES (?, ?)",
                    (student_id, tutor_id)
                )
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Ошибка добавления заявки: {e}")
            return None

    @classmethod
    async def get_student_requests_for_tutor(cls, tutor_id: int) -> List[Tuple]:
        """Получить заявки студентов для репетитора"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT sr.id, sr.student_id, sr.tutor_id, sr.status, sr.created_at,
                              u.name, u.age, u.timezone, u.subject
                       FROM student_requests sr
                       JOIN users u ON sr.student_id = u.id
                       WHERE sr.tutor_id = ? AND sr.status = 'pending'
                       ORDER BY sr.created_at DESC""",
                    (tutor_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения заявок для репетитора {tutor_id}: {e}")
            return []

    @classmethod
    async def get_student_request_by_id(cls, request_id: int) -> Optional[Tuple]:
        """Получить заявку по ID"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    "SELECT id, student_id, tutor_id, status, created_at FROM student_requests WHERE id = ?",
                    (request_id,)
                )
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка получения заявки {request_id}: {e}")
            return None

    @classmethod
    async def approve_student_request(cls, request_id: int, tutor_id: int) -> bool:
        """Одобрить заявку студента"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "UPDATE student_requests SET status = 'accepted' WHERE id = ?",
                    (request_id,)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка одобрения заявки {request_id}: {e}")
            return False

    @classmethod
    async def reject_student_request(cls, request_id: int) -> bool:
        """Отклонить заявку студента"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "UPDATE student_requests SET status = 'rejected' WHERE id = ?",
                    (request_id,)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка отклонения заявки {request_id}: {e}")
            return False

    @classmethod
    async def process_student_request(cls, request_id: int, status: str) -> bool:
        """Обработать заявку студента"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "UPDATE student_requests SET status = ? WHERE id = ?",
                    (status, request_id)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка обработки заявки {request_id}: {e}")
            return False

    @classmethod
    async def get_request_by_id(cls, request_id: int) -> Optional[Tuple]:
        """Получить заявку по ID (алиас для get_student_request_by_id)"""
        return await cls.get_student_request_by_id(request_id)

    # Методы для работы с группами
    @classmethod
    async def get_tutor_groups(cls, tutor_id: int) -> List[Tuple]:
        """Получить группы репетитора"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    "SELECT id, tutor_id, name, description, created_at FROM groups WHERE tutor_id = ?",
                    (tutor_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения групп репетитора {tutor_id}: {e}")
            return []

    @classmethod
    async def get_group_by_id(cls, group_id: int) -> Optional[Tuple]:
        """Получить группу по ID"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    "SELECT id, tutor_id, name, description, created_at FROM groups WHERE id = ?",
                    (group_id,)
                )
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка получения группы {group_id}: {e}")
            return None

    @classmethod
    async def get_group_members(cls, group_id: int) -> List[Tuple]:
        """Получить участников группы"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT u.id, u.username, u.name, u.role 
                       FROM users u 
                       JOIN group_members gm ON u.id = gm.student_id 
                       WHERE gm.group_id = ?""",
                    (group_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения участников группы {group_id}: {e}")
            return []

    # Методы для работы с расписанием
    @classmethod
    async def get_student_schedule(cls, tutor_id: int, student_id: int) -> List[Tuple]:
        """Получить расписание студента"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, day_of_week, time, subject 
                       FROM standard_schedule 
                       WHERE tutor_id = ? AND student_id = ?""",
                    (tutor_id, student_id)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения расписания студента: {e}")
            return []

    @classmethod
    async def get_standard_schedule(cls, tutor_id: int, student_id: int) -> List[Tuple]:
        """Получить стандартное расписание (алиас)"""
        return await cls.get_student_schedule(tutor_id, student_id)

    @classmethod
    async def add_standard_schedule(cls, tutor_id: int, student_id: int, day_of_week: int, lesson_time: str,
                                    subject: str = None) -> bool:
        """Добавить стандартное расписание"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "INSERT INTO standard_schedule (tutor_id, student_id, day_of_week, time, subject) VALUES (?, ?, ?, ?, ?)",
                    (tutor_id, student_id, day_of_week, lesson_time, subject or "Не указан")
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления стандартного расписания: {e}")
            return False

    @classmethod
    async def generate_lessons_from_standard_schedule(cls, tutor_id: int, student_id: int, weeks: int = 4) -> bool:
        """Генерировать уроки из стандартного расписания"""
        try:
            schedule = await cls.get_standard_schedule(tutor_id, student_id)
            if not schedule:
                return False

            # Получаем стоимость урока
            tutor_info = await cls.get_tutor(tutor_id)
            cost = tutor_info[4] if tutor_info else 1000

            # Генерируем уроки на указанное количество недель
            from datetime import datetime, timedelta
            today = datetime.now()

            for week in range(weeks):
                for schedule_item in schedule:
                    _, day_of_week, time, subject = schedule_item

                    # Вычисляем дату урока
                    days_ahead = day_of_week - today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    days_ahead += week * 7

                    lesson_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

                    await cls.add_lesson(student_id, tutor_id, lesson_date, time, subject, cost)

            return True
        except Exception as e:
            logger.error(f"❌ Ошибка генерации уроков из расписания: {e}")
            return False

    @classmethod
    async def get_group_schedule(cls, tutor_id: int, group_id: int) -> List[Tuple]:
        """Получить расписание группы"""
        try:
            # Пока возвращаем пустой список, так как групповое расписание не реализовано
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка получения расписания группы: {e}")
            return []

    # Методы для работы с доступными слотами
    @classmethod
    async def get_available_slots(cls, tutor_id: int) -> List[Tuple]:
        """Получить доступные слоты репетитора"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, tutor_id, slot_date, slot_time, is_booked 
                       FROM available_slots 
                       WHERE tutor_id = ? AND is_booked = 0 
                       ORDER BY slot_date, slot_time""",
                    (tutor_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения доступных слотов репетитора {tutor_id}: {e}")
            return []

    @classmethod
    async def add_available_slot(cls, tutor_id: int, slot_date: str, slot_time: str) -> bool:
        """Добавить доступный слот"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                await db.execute(
                    "INSERT INTO available_slots (tutor_id, slot_date, slot_time) VALUES (?, ?, ?)",
                    (tutor_id, slot_date, slot_time)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления доступного слота: {e}")
            return False

    # Методы для работы с отпусками
    @classmethod
    async def get_vacation_periods(cls, tutor_id: int) -> List[Tuple]:
        """Получить периоды отпуска репетитора"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                cursor = await db.execute(
                    """SELECT id, tutor_id, start_date, end_date, reason, created_at 
                       FROM vacation_periods 
                       WHERE tutor_id = ? 
                       ORDER BY start_date""",
                    (tutor_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка получения периодов отпуска репетитора {tutor_id}: {e}")
            return []

    # Методы для статистики
    @classmethod
    async def get_system_statistics(cls) -> Dict[str, Any]:
        """Получить статистику системы"""
        try:
            async with aiosqlite.connect(cls._db_path) as db:
                stats = {}

                # Общее количество пользователей
                cursor = await db.execute("SELECT COUNT(*) FROM users")
                stats['total_users'] = (await cursor.fetchone())[0]

                # Количество по ролям
                cursor = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                stats['tutors'] = (await cursor.fetchone())[0]

                cursor = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
                stats['students'] = (await cursor.fetchone())[0]

                cursor = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")
                stats['superadmins'] = (await cursor.fetchone())[0]

                cursor = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'archived'")
                stats['archived'] = (await cursor.fetchone())[0]

                # Статистика уроков
                cursor = await db.execute("SELECT COUNT(*) FROM lessons")
                stats['total_lessons'] = (await cursor.fetchone())[0]

                cursor = await db.execute("SELECT COUNT(*) FROM lessons WHERE status = 'completed'")
                stats['completed_lessons'] = (await cursor.fetchone())[0]

                cursor = await db.execute("SELECT COUNT(*) FROM lessons WHERE status = 'scheduled'")
                stats['paid_lessons'] = (await cursor.fetchone())[0]

                # Статистика домашних заданий
                cursor = await db.execute("SELECT COUNT(*) FROM homework")
                stats['homework_assigned'] = (await cursor.fetchone())[0]

                cursor = await db.execute("SELECT COUNT(*) FROM homework WHERE is_completed = 1")
                stats['homework_submitted'] = (await cursor.fetchone())[0]

                # Статистика сообщений
                cursor = await db.execute("SELECT COUNT(*) FROM messages")
                stats['total_messages'] = (await cursor.fetchone())[0]

                # Статистика заявок
                cursor = await db.execute("SELECT COUNT(*) FROM student_requests WHERE status = 'pending'")
                stats['pending_requests'] = (await cursor.fetchone())[0]

                # Финансовая статистика
                cursor = await db.execute("SELECT SUM(cost) FROM lessons WHERE status = 'completed'")
                result = await cursor.fetchone()
                stats['total_revenue'] = result[0] if result[0] else 0

                stats['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                return stats
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики системы: {e}")
            return {}
