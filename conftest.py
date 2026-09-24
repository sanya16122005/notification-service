"""Настройка запуска тестов и общие фикстуры.

Файл размещен в корне проекта, поэтому pytest добавляет корневой
каталог в пути импорта: тесты подключают модули проекта по имени,
например `from app.models import User`. Фикстуры создают объекты
предметной области, общие для нескольких файлов тестов.
"""

import pytest

from app.models import EmailChannel, PushChannel, SmsChannel, User
from app.services.notifications import NotificationService
from app.services.repositories import (
    ChannelRepository,
    NotificationRepository,
    UserRepository,
)


@pytest.fixture
def user() -> User:
    """Пользователь с «тихими часами» 23:00-08:00."""
    return User(1, "Стерлигов Александр", "a.sterligov@example.com")


@pytest.fixture
def email() -> EmailChannel:
    """Включенный канал электронной почты с запасом лимита."""
    return EmailChannel(daily_limit=20, sent_today=17)


@pytest.fixture
def service(user: User, email: EmailChannel) -> NotificationService:
    """Сервис с двумя пользователями и тремя каналами в памяти."""
    users = UserRepository([
        user, User(2, "Иванова Мария", "+7 900 123-45-67", quiet_start=22,
                   quiet_end=7),
    ])
    channels = ChannelRepository([
        email,
        SmsChannel(daily_limit=10, sent_today=4),
        PushChannel(daily_limit=50, enabled=False),
    ])
    return NotificationService(users, channels, NotificationRepository())
