import os
from typing import Dict, List

# Константы для бота
ROLES = {
    "STUDENT": "student",
    "ADMIN": "admin",
    "SUPERADMIN": "superadmin",
    "ARCHIVED": "archived",
    "UNREGISTERED": "unregistered"  # Добавили недостающую роль
}

LESSON_STATUSES = {
    "SCHEDULED": "scheduled",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled",
    "RESCHEDULED": "rescheduled"
}

PAYMENT_STATUSES = {
    "PENDING": "pending",
    "PAID": "paid",
    "UNPAID": "unpaid"
}

HOMEWORK_STATUSES = {
    "ASSIGNED": "assigned",
    "SUBMITTED": "submitted",
    "CHECKED": "checked",
    "COMPLETED": "completed"
}

REQUEST_STATUSES = {
    "PENDING": "pending",
    "ACCEPTED": "accepted",
    "REJECTED": "rejected"
}

WEEKDAYS = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
}

CONTENT_TYPES = {
    "TEXT": "text",
    "VOICE": "voice",
    "PHOTO": "photo",
    "VIDEO": "video",
    "FILE": "file"
}

# Список ID суперадминов
SUPERADMIN_IDS = [982741411]  # Замените на реальные ID

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "мой токен")  # Замените на токен вашего бота

# Обновленная структура SPECIAL_USERS
SPECIAL_USERS: Dict[int, Dict[str, List[str] | str]] = {
    982741411: {
        "roles": ["admin", "superadmin", "student"],
        "primary_role": "superadmin"
    }
    # Добавьте других специальных пользователей
}

def get_primary_role(user_id: int) -> str:
    """Получение основной роли пользователя"""
    if user_id in SPECIAL_USERS:
        return SPECIAL_USERS[user_id].get("primary_role", ROLES["STUDENT"])
    return ROLES["STUDENT"]  # По умолчанию студент


def has_role(user_id: int, role: str) -> bool:
    """Проверка роли пользователя"""
    if role == ROLES["SUPERADMIN"]:
        return user_id in SUPERADMIN_IDS

    if user_id in SPECIAL_USERS:
        return role in SPECIAL_USERS[user_id].get("roles", [])

    return False


def get_user_role_for_menu(user_id: int, db_role: str) -> str:
    """Определение роли для меню с учетом специальных пользователей"""
    if user_id in SPECIAL_USERS:
        return SPECIAL_USERS[user_id].get("primary_role", db_role)
    return db_role
