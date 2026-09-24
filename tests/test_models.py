"""Тесты классов предметной области."""

from datetime import datetime

import pytest

from app.models import (
    Channel,
    EmailChannel,
    Notification,
    PushChannel,
    SmsChannel,
    User,
)
from app.models.notification import STATUS_DELAYED, STATUS_SENT


def test_quiet_time_crosses_midnight(user: User) -> None:
    """Интервал 23:00-08:00 корректно переходит через полночь."""
    assert user.is_quiet_time(23)
    assert user.is_quiet_time(2)
    assert not user.is_quiet_time(12)


def test_quiet_time_inside_day() -> None:
    """Интервал 00:00-06:00 внутри суток не захватывает день."""
    night_user = User(3, "Петров Сергей", "s.petrov@example.com",
                      quiet_start=0, quiet_end=6)
    assert night_user.is_quiet_time(3)
    assert not night_user.is_quiet_time(12)


def test_user_validates_hours_and_name() -> None:
    """Сеттеры свойств не допускают некорректных значений."""
    with pytest.raises(ValueError):
        User(1, "Тест", "test@example.com", quiet_start=25)
    with pytest.raises(ValueError):
        User(1, "   ", "test@example.com")


def test_user_subscription_is_encapsulated(user: User) -> None:
    """Подписка меняется методами, а не присваиванием."""
    user.unsubscribe()
    assert not user.can_receive
    with pytest.raises(AttributeError):
        user.subscribed = True  # type: ignore[misc]
    user.subscribe()
    assert user.can_receive


def test_user_dict_round_trip(user: User) -> None:
    """Пользователь сохраняется в словарь и восстанавливается."""
    restored = User.from_dict(user.to_dict())
    assert restored == user
    assert restored.quiet_hours_text() == "23:00-08:00"


def test_channel_is_abstract() -> None:
    """Объект абстрактного класса Channel создать нельзя."""
    with pytest.raises(TypeError):
        Channel(daily_limit=10)  # type: ignore[abstract]


def test_channels_check_contacts_differently() -> None:
    """Полиморфизм: каждый канал по-своему проверяет контакт."""
    channels = [EmailChannel(10), SmsChannel(10), PushChannel(10)]
    email_result = [ch.accepts_contact("a@example.com") for ch in channels]
    phone_result = [ch.accepts_contact("+7 900 123-45-67")
                    for ch in channels]
    assert email_result == [True, False, True]
    assert phone_result == [False, True, True]


def test_channels_format_message_differently() -> None:
    """Полиморфизм: один вызов format_message - разный результат."""
    messages = [
        channel.format_message("Код", "Код входа: 4821")
        for channel in (EmailChannel(10), SmsChannel(10), PushChannel(10))
    ]
    assert messages == [
        "Тема: Код\nКод входа: 4821",
        "Код входа: 4821",
        "Код: Код входа: 4821",
    ]


def test_channel_from_dict_creates_subclass() -> None:
    """Фабричный метод создает объект нужного наследника."""
    channel = Channel.from_dict({"code": "sms", "daily_limit": 10})
    assert isinstance(channel, SmsChannel)
    assert channel.max_length == 70
    with pytest.raises(ValueError):
        Channel.from_dict({"code": "fax", "daily_limit": 1})


def test_channel_limit_and_length() -> None:
    """Остаток лимита, длина текста и счетчик отправок."""
    sms = SmsChannel(daily_limit=5, sent_today=4)
    assert sms.limit_left() == 1
    assert sms.is_too_long(71)
    assert not sms.is_too_long(70)
    sms.register_sent()
    assert not sms.has_capacity
    with pytest.raises(ValueError):
        sms.register_sent()
    assert sms.reset_counter() == 5


def make_notification(notification_id: int, priority: int,
                      created: datetime) -> Notification:
    """Создать уведомление для тестов сортировки."""
    return Notification(notification_id, 1, "email", "Тема", "Текст",
                        priority, created, STATUS_SENT)


def test_notification_priority_is_checked() -> None:
    """Недопустимый приоритет возбуждает ValueError."""
    with pytest.raises(ValueError):
        make_notification(1, 5, datetime(2026, 9, 10, 12, 0))


def test_notifications_sort_by_priority_and_date() -> None:
    """Магический метод __lt__ задает порядок для sorted()."""
    late_urgent = make_notification(1, 1, datetime(2026, 10, 1, 9, 0))
    early_normal = make_notification(2, 2, datetime(2026, 9, 1, 9, 0))
    early_urgent = make_notification(3, 1, datetime(2026, 9, 5, 9, 0))
    ordered = sorted([late_urgent, early_normal, early_urgent])
    assert [item.id for item in ordered] == [3, 1, 2]


def test_notification_dict_round_trip() -> None:
    """Даты уведомления сохраняются строками и восстанавливаются."""
    item = Notification(7, 1, "email", "Работы", "Текст", 2,
                        datetime(2026, 9, 10, 23, 40), STATUS_DELAYED,
                        "Тихие часы", datetime(2026, 9, 11, 8, 0))
    data = item.to_dict()
    assert data["created_at"] == "10.09.2026 23:40"
    restored = Notification.from_dict(data)
    assert restored.delivery_at == datetime(2026, 9, 11, 8, 0)
    assert restored == item
