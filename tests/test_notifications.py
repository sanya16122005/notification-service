"""Тесты правил доставки и функций работы с уведомлениями."""

from datetime import datetime

from app.services.notifications import (
    STATUS_DELAYED,
    STATUS_REJECTED,
    STATUS_SENT,
    cancel_notification,
    check_delivery,
    count_by_status,
    create_notification,
    get_delivery_time,
    is_quiet_time,
)


def make_user() -> dict:
    """Подготовить пользователя с «тихими часами» 23:00-08:00."""
    return {
        "id": 1, "name": "Стерлигов Александр",
        "contact": "a.sterligov@example.com", "is_active": True,
        "subscribed": True, "quiet_start": 23, "quiet_end": 8,
    }


def make_channel() -> dict:
    """Подготовить включенный канал с запасом суточного лимита."""
    return {
        "code": "email", "title": "Электронная почта", "enabled": True,
        "daily_limit": 20, "sent_today": 17, "max_length": 0,
    }


def test_is_quiet_time_crosses_midnight() -> None:
    """Интервал «тихих часов» корректно переходит через полночь."""
    assert is_quiet_time(23, 23, 8)
    assert is_quiet_time(2, 23, 8)
    assert not is_quiet_time(12, 23, 8)


def test_evening_notification_is_delayed() -> None:
    """Обычное уведомление ночью откладывается до утра."""
    result = check_delivery(
        make_user(), make_channel(), "Плановые работы", 2,
        datetime(2026, 9, 10, 23, 40),
    )
    assert result["status"] == STATUS_DELAYED
    assert result["delivery_at"] == datetime(2026, 9, 11, 8, 0)


def test_urgent_notification_ignores_quiet_hours() -> None:
    """Срочное уведомление отправляется в «тихие часы»."""
    result = check_delivery(
        make_user(), make_channel(), "Код подтверждения: 4821", 1,
        datetime(2026, 9, 10, 23, 40),
    )
    assert result["status"] == STATUS_SENT


def test_unsubscribed_user_is_rejected() -> None:
    """Отписанному пользователю уведомление не доставляется."""
    user = make_user()
    user["subscribed"] = False
    result = check_delivery(
        user, make_channel(), "Сводка за неделю", 2,
        datetime(2026, 9, 10, 12, 0),
    )
    assert result["status"] == STATUS_REJECTED
    assert result["comment"] == (
        "Пользователь неактивен или отписан от рассылки"
    )


def test_night_notification_delivered_same_morning() -> None:
    """Созданное ночью уведомление уходит тем же утром."""
    delivery = get_delivery_time(
        datetime(2026, 9, 10, 2, 40), STATUS_DELAYED, 23, 8
    )
    assert delivery == datetime(2026, 9, 10, 8, 0)


def test_create_notification_updates_channel_counter() -> None:
    """Отправленное уведомление увеличивает счетчик канала."""
    notifications: list[dict] = []
    channel = make_channel()
    create_notification(
        notifications, make_user(), channel, "Код", "Код входа: 4821", 1,
        datetime(2026, 9, 10, 12, 0),
    )
    assert len(notifications) == 1
    assert channel["sent_today"] == 18


def test_sent_notification_cannot_be_cancelled() -> None:
    """Отправленное уведомление отменить нельзя."""
    notifications: list[dict] = []
    create_notification(
        notifications, make_user(), make_channel(), "Код", "Код: 4821", 1,
        datetime(2026, 9, 10, 12, 0),
    )
    try:
        cancel_notification(notifications, 1)
    except ValueError:
        assert len(notifications) == 1
        return
    raise AssertionError("Ожидалось исключение ValueError")


def test_count_by_status() -> None:
    """Статистика считает уведомления каждого статуса."""
    notifications = [
        {"status": STATUS_SENT}, {"status": STATUS_SENT},
        {"status": STATUS_DELAYED},
    ]
    statistics = count_by_status(notifications)
    assert statistics[STATUS_SENT] == 2
    assert statistics[STATUS_DELAYED] == 1
    assert statistics[STATUS_REJECTED] == 0
