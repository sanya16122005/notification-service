"""Функции работы с пользователями сервиса уведомлений.

Пользователи хранятся списком словарей. Каждый словарь описывает
получателя: идентификатор, имя, контакт, признаки активности и
подписки, а также границы «тихих часов».
"""

from typing import Iterator

from utils import next_id

QUIET_START_DEFAULT = 23
QUIET_END_DEFAULT = 8


def add_user(
    users: list[dict],
    name: str,
    contact: str,
    quiet_start: int = QUIET_START_DEFAULT,
    quiet_end: int = QUIET_END_DEFAULT,
) -> dict:
    """Добавить пользователя в список users и вернуть его запись."""
    user = {
        "id": next_id(users),
        "name": name,
        "contact": contact,
        "is_active": True,
        "subscribed": True,
        "quiet_start": quiet_start,
        "quiet_end": quiet_end,
    }
    users.append(user)
    return user


def get_user(users: list[dict], user_id: int) -> dict:
    """Найти пользователя по идентификатору.

    Возбуждает KeyError, если пользователь не найден.
    """
    for user in users:
        if user["id"] == user_id:
            return user
    raise KeyError(f"Пользователь с id={user_id} не найден")


def find_users(users: list[dict], query: str) -> list[dict]:
    """Найти пользователей по подстроке имени или контакта."""
    found = []
    pattern = query.strip().lower()
    for user in users:
        name = user["name"].lower()
        contact = user["contact"].lower()
        if pattern in name or pattern in contact:
            found.append(user)
    return found


def subscribed_users(users: list[dict]) -> Iterator[dict]:
    """Перебрать активных подписанных пользователей.

    Функция является генератором: записи отдаются по мере
    необходимости, промежуточный список не создается.
    """
    for user in users:
        if user["is_active"] and user["subscribed"]:
            yield user


def sort_users(users: list[dict]) -> list[dict]:
    """Вернуть пользователей, упорядоченных по имени."""
    return sorted(users, key=lambda user: user["name"].lower())


def set_subscription(
    users: list[dict],
    user_id: int,
    subscribed: bool,
) -> dict:
    """Включить или отключить подписку пользователя."""
    user = get_user(users, user_id)
    user["subscribed"] = subscribed
    return user
