"""Тесты правил доставки, сервиса уведомлений и декоратора меню."""

from datetime import datetime

import pytest

from app.decorators import menu_action
from app.models.notification import (
    STATUS_DELAYED,
    STATUS_REJECTED,
    STATUS_SENT,
)
from app.services.notifications import NotificationService

EVENING = datetime(2026, 9, 10, 23, 40)
NOON = datetime(2026, 9, 10, 12, 0)


def test_evening_notification_is_delayed(
    service: NotificationService,
) -> None:
    """Обычное уведомление вечером откладывается до утра."""
    result = service.check_delivery(1, "email", "Плановые работы", 2,
                                    EVENING)
    assert result.status == STATUS_DELAYED
    assert result.delivery_at == datetime(2026, 9, 11, 8, 0)


def test_night_notification_delivered_same_morning(
    service: NotificationService,
) -> None:
    """Созданное ночью уведомление уходит тем же утром."""
    result = service.check_delivery(1, "email", "Сводка", 2,
                                    datetime(2026, 9, 10, 2, 40))
    assert result.delivery_at == datetime(2026, 9, 10, 8, 0)


def test_urgent_notification_ignores_quiet_hours(
    service: NotificationService,
) -> None:
    """Срочное уведомление отправляется в «тихие часы»."""
    result = service.check_delivery(1, "email", "Код: 4821", 1, EVENING)
    assert result.status == STATUS_SENT


def test_unsubscribed_user_is_rejected(
    service: NotificationService,
) -> None:
    """Отписанному пользователю уведомление не доставляется."""
    service.users.get(1).unsubscribe()
    result = service.check_delivery(1, "email", "Сводка", 2, NOON)
    assert result.status == STATUS_REJECTED
    assert result.comment == "Пользователь неактивен или отписан от рассылки"


def test_contact_must_match_channel(service: NotificationService) -> None:
    """SMS нельзя отправить пользователю с адресом почты."""
    result = service.check_delivery(1, "sms", "Код: 4821", 1, NOON)
    assert result.comment == "Контакт пользователя не подходит для канала"


def test_disabled_channel_is_rejected(service: NotificationService) -> None:
    """Через отключенный канал уведомление не отправляется."""
    result = service.check_delivery(1, "push", "Новости", 2, NOON)
    assert result.comment == "Канал доставки отключен"


def test_create_notification_updates_channel_counter(
    service: NotificationService,
) -> None:
    """Отправленное уведомление увеличивает счетчик канала."""
    notification = service.create_notification(
        1, "email", "Код", "Код входа: 4821", 1, NOON
    )
    assert notification.id == 1
    assert len(service.notifications) == 1
    assert service.channels.get("email").sent_today == 18


def test_sent_notification_cannot_be_cancelled(
    service: NotificationService,
) -> None:
    """Отправленное уведомление отменить нельзя, отложенное - можно."""
    service.create_notification(1, "email", "Код", "Код: 4821", 1, NOON)
    service.create_notification(1, "email", "Работы", "Текст", 2, EVENING)
    with pytest.raises(ValueError):
        service.cancel_notification(1)
    assert service.cancel_notification(2).status == STATUS_DELAYED
    assert len(service.notifications) == 1


def test_statistics(service: NotificationService) -> None:
    """Статистика считает уведомления каждого статуса."""
    service.create_notification(1, "email", "Код", "Код: 4821", 1, NOON)
    service.create_notification(1, "email", "Работы", "Текст", 2, EVENING)
    service.create_notification(1, "sms", "Код", "Код: 4821", 1, NOON)
    assert service.statistics() == {
        STATUS_SENT: 1, STATUS_DELAYED: 1, STATUS_REJECTED: 1,
    }


def test_unknown_ids_raise_key_error(service: NotificationService) -> None:
    """Несуществующие пользователь и канал возбуждают KeyError."""
    with pytest.raises(KeyError):
        service.check_delivery(99, "email", "Текст", 2, NOON)
    with pytest.raises(KeyError):
        service.check_delivery(1, "fax", "Текст", 2, NOON)


def test_menu_action_decorator(capsys: pytest.CaptureFixture) -> None:
    """Декоратор выводит заголовок и перехватывает ошибки."""

    @menu_action("ТЕСТ")
    def failing_action() -> bool:
        """Пункт меню с ошибкой."""
        raise KeyError("Запись не найдена")

    assert failing_action() is False
    output = capsys.readouterr().out
    assert "ТЕСТ" in output
    assert "Операция не выполнена: Запись не найдена" in output
    assert failing_action.__name__ == "failing_action"
    assert failing_action.__doc__ == "Пункт меню с ошибкой."
