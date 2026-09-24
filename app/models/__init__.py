"""Объектная модель предметной области (ПР3).

Подпакет содержит классы сущностей сервиса уведомлений:
- base - абстрактный базовый класс Entity;
- user - пользователь (получатель уведомлений);
- channel - каналы доставки: базовый класс Channel и наследники
  EmailChannel, SmsChannel, PushChannel;
- notification - уведомление и результат проверки доставки.
"""

from app.models.base import Entity
from app.models.channel import (
    CHANNEL_TYPES,
    Channel,
    EmailChannel,
    PushChannel,
    SmsChannel,
)
from app.models.notification import DeliveryResult, Notification
from app.models.user import User

__all__ = [
    "CHANNEL_TYPES",
    "Channel",
    "DeliveryResult",
    "EmailChannel",
    "Entity",
    "Notification",
    "PushChannel",
    "SmsChannel",
    "User",
]
