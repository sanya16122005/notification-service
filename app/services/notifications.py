"""Функции работы с уведомлениями.

Модуль содержит правила доставки, реализованные в ПР1, и новые
функции ПР2: создание и отмену уведомлений, поиск, сортировку и
статистику по статусам. Уведомления хранятся списком словарей.
"""

from datetime import datetime, timedelta
from typing import Iterator

from channels import is_too_long, limit_left, register_sent
from utils import format_datetime, next_id

STATUS_SENT = "ОТПРАВЛЕНО"
STATUS_DELAYED = "ОТЛОЖЕНО"
STATUS_REJECTED = "ОТКЛОНЕНО"

# Неизменяемый перечень возможных статусов уведомления
STATUSES = (STATUS_SENT, STATUS_DELAYED, STATUS_REJECTED)

PRIORITY_URGENT = 1


def is_quiet_time(hour: int, start_hour: int, end_hour: int) -> bool:
    """Проверить, попадает ли час в «тихие часы» пользователя.

    Интервал переходит через полночь, поэтому час считается тихим,
    если он не раньше начала интервала или раньше его окончания.
    """
    return hour >= start_hour or hour < end_hour


def get_block_reason(user: dict, channel: dict, text_length: int) -> str:
    """Вернуть причину отказа в доставке.

    Если запретов нет, возвращается пустая строка.
    """
    if not user["is_active"] or not user["subscribed"]:
        return "Пользователь неактивен или отписан от рассылки"
    if not channel["enabled"]:
        return "Канал доставки отключен"
    if limit_left(channel) <= 0:
        return "Исчерпан суточный лимит отправок по каналу"
    if is_too_long(channel, text_length):
        return "Текст превышает допустимую длину для канала"
    return ""


def get_status(block_reason: str, quiet_time: bool, urgent: bool) -> str:
    """Определить статус уведомления по результатам проверок."""
    if block_reason:
        return STATUS_REJECTED
    if quiet_time and not urgent:
        return STATUS_DELAYED
    return STATUS_SENT


def get_status_comment(status: str, block_reason: str) -> str:
    """Сформировать пояснение к статусу уведомления."""
    if status == STATUS_REJECTED:
        return block_reason
    if status == STATUS_DELAYED:
        return "Отправка запрещена в «тихие часы» пользователя"
    return "Уведомление передано в канал доставки"


def get_delivery_time(
    created: datetime,
    status: str,
    start_hour: int,
    end_hour: int,
) -> datetime:
    """Вычислить время доставки уведомления.

    Отложенное уведомление отправляется сразу после окончания
    «тихих часов»: созданное вечером - утром следующего дня,
    созданное ночью - тем же утром.
    """
    if status != STATUS_DELAYED:
        return created
    morning = created.replace(hour=end_hour, minute=0)
    if created.hour >= start_hour:
        return morning + timedelta(days=1)
    return morning


def check_delivery(
    user: dict,
    channel: dict,
    text: str,
    priority: int,
    created: datetime,
) -> dict:
    """Проверить правила доставки и вернуть результат проверки.

    Возвращается словарь с ключами status, comment и delivery_at.
    Функция объединяет правила ПР1 и используется как при проверке
    возможности отправки, так и при создании уведомления.
    """
    block_reason = get_block_reason(user, channel, len(text))
    quiet_time = is_quiet_time(
        created.hour, user["quiet_start"], user["quiet_end"]
    )
    urgent = priority == PRIORITY_URGENT
    status = get_status(block_reason, quiet_time, urgent)
    delivery_at = get_delivery_time(
        created, status, user["quiet_start"], user["quiet_end"]
    )
    return {
        "status": status,
        "comment": get_status_comment(status, block_reason),
        "quiet_time": quiet_time,
        "delivery_at": delivery_at,
    }


def create_notification(
    notifications: list[dict],
    user: dict,
    channel: dict,
    subject: str,
    text: str,
    priority: int,
    created: datetime,
) -> dict:
    """Создать уведомление и добавить его в список notifications.

    Отправленное уведомление учитывается в суточном счетчике
    канала. Возбуждает ValueError при недопустимом приоритете.
    """
    if priority not in (1, 2, 3):
        raise ValueError("Приоритет должен быть числом от 1 до 3")
    result = check_delivery(user, channel, text, priority, created)
    notification = {
        "id": next_id(notifications),
        "user_id": user["id"],
        "channel": channel["code"],
        "subject": subject,
        "text": text,
        "priority": priority,
        "created_at": format_datetime(created),
        "status": result["status"],
        "comment": result["comment"],
        "delivery_at": format_datetime(result["delivery_at"]),
    }
    notifications.append(notification)
    if notification["status"] == STATUS_SENT:
        register_sent(channel)
    return notification


def cancel_notification(
    notifications: list[dict],
    notification_id: int,
) -> dict:
    """Отменить уведомление и удалить его из списка.

    Возбуждает KeyError, если уведомление не найдено, и ValueError,
    если уведомление уже отправлено.
    """
    for position, notification in enumerate(notifications):
        if notification["id"] != notification_id:
            continue
        if notification["status"] == STATUS_SENT:
            raise ValueError("Отправленное уведомление нельзя отменить")
        return notifications.pop(position)
    raise KeyError(f"Уведомление с id={notification_id} не найдено")


def find_notifications(
    notifications: list[dict],
    query: str,
) -> list[dict]:
    """Найти уведомления по подстроке темы или текста."""
    found = []
    pattern = query.strip().lower()
    for notification in notifications:
        subject = notification["subject"].lower()
        text = notification["text"].lower()
        if pattern in subject or pattern in text:
            found.append(notification)
    return found


def notifications_by_status(
    notifications: list[dict],
    status: str,
) -> Iterator[dict]:
    """Перебрать уведомления с указанным статусом.

    Функция является генератором и отдает записи по одной.
    """
    for notification in notifications:
        if notification["status"] == status:
            yield notification


def user_notifications(
    notifications: list[dict],
    user_id: int,
) -> list[dict]:
    """Отобрать уведомления одного пользователя."""
    return [
        notification
        for notification in notifications
        if notification["user_id"] == user_id
    ]


def sort_notifications(notifications: list[dict]) -> list[dict]:
    """Вернуть уведомления от срочных к обычным, затем по дате."""
    return sorted(
        notifications,
        key=lambda item: (item["priority"], item["created_at"]),
    )


def count_by_status(notifications: list[dict]) -> dict[str, int]:
    """Подсчитать количество уведомлений каждого статуса."""
    statistics = {}
    for status in STATUSES:
        statistics[status] = 0
    for notification in notifications:
        status = notification["status"]
        if status in statistics:
            statistics[status] += 1
    return statistics
