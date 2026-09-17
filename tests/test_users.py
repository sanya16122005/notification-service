"""Тесты функций работы с пользователями и каналами."""

from channels import channel_codes, is_too_long, limit_left
from users import add_user, find_users, get_user, subscribed_users


def make_users() -> list[dict]:
    """Подготовить список пользователей для тестов."""
    users: list[dict] = []
    add_user(users, "Стерлигов Александр", "a.sterligov@example.com")
    add_user(users, "Иванова Мария", "+7 900 123-45-67")
    return users


def test_add_user() -> None:
    """Пользователь добавляется в список и получает идентификатор."""
    users = make_users()
    assert len(users) == 2
    assert users[0]["id"] == 1
    assert users[1]["id"] == 2


def test_find_users() -> None:
    """Поиск находит пользователя по части имени без учета регистра."""
    users = make_users()
    found = find_users(users, "иванова")
    assert len(found) == 1
    assert found[0]["name"] == "Иванова Мария"


def test_get_user_raises_key_error() -> None:
    """Запрос несуществующего пользователя возбуждает KeyError."""
    users = make_users()
    try:
        get_user(users, 99)
    except KeyError:
        return
    raise AssertionError("Ожидалось исключение KeyError")


def test_subscribed_users_skips_unsubscribed() -> None:
    """Генератор отдает только активных подписанных пользователей."""
    users = make_users()
    users[1]["subscribed"] = False
    assert [user["id"] for user in subscribed_users(users)] == [1]


def test_channel_limit_and_length() -> None:
    """Остаток лимита и ограничение длины считаются верно."""
    channel = {
        "code": "sms", "title": "SMS", "enabled": True,
        "daily_limit": 10, "sent_today": 4, "max_length": 70,
    }
    assert limit_left(channel) == 6
    assert is_too_long(channel, 71)
    assert not is_too_long(channel, 70)
    assert channel_codes([channel]) == {"sms"}
