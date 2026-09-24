"""Сервис уведомлений - точка входа в логику предметной области.

Класс NotificationService объединяет хранилища пользователей,
каналов и уведомлений с правилами доставки. Консольный интерфейс
работает только с этим классом и не обращается к данным напрямую.
"""

from datetime import datetime

from app import storage
from app.models import DeliveryResult, Notification
from app.services.delivery import DeliveryRules
from app.services.repositories import (
    ChannelRepository,
    NotificationRepository,
    UserRepository,
)
from app.storage import JsonStorage


class NotificationService:
    """Управление уведомлениями: проверка, создание, отмена, статистика.

    Объект сервиса получает хранилища и правила доставки через
    конструктор (композиция), поэтому в тестах вместо файловых
    хранилищ можно передать хранилища с подготовленными объектами.
    """

    def __init__(
        self,
        users: UserRepository,
        channels: ChannelRepository,
        notifications: NotificationRepository,
        rules: DeliveryRules | None = None,
    ) -> None:
        self.users = users
        self.channels = channels
        self.notifications = notifications
        self.rules = rules or DeliveryRules()

    @classmethod
    def from_files(cls) -> "NotificationService":
        """Создать сервис с данными из JSON-файлов каталога data/."""
        users = UserRepository(storage=JsonStorage(storage.USERS_FILE))
        channels = ChannelRepository(
            storage=JsonStorage(storage.CHANNELS_FILE)
        )
        notifications = NotificationRepository(
            storage=JsonStorage(storage.NOTIFICATIONS_FILE)
        )
        for repository in (users, channels, notifications):
            repository.load()
        return cls(users, channels, notifications)

    def check_delivery(
        self,
        user_id: int,
        channel_code: str,
        text: str,
        priority: int,
        created: datetime,
    ) -> DeliveryResult:
        """Проверить возможность доставки без создания уведомления.

        Сценарий ПР1. Возбуждает KeyError для несуществующего
        пользователя или канала и ValueError при неверном приоритете.
        """
        user = self.users.get(user_id)
        channel = self.channels.get(channel_code)
        Notification.check_priority(priority)
        return self.rules.check(user, channel, text, priority, created)

    def create_notification(
        self,
        user_id: int,
        channel_code: str,
        subject: str,
        text: str,
        priority: int,
        created: datetime,
    ) -> Notification:
        """Создать уведомление и определить его статус.

        Отправленное уведомление учитывается в суточном счетчике
        канала.
        """
        result = self.check_delivery(
            user_id, channel_code, text, priority, created
        )
        notification = Notification.create(
            self.notifications.next_id(), user_id, channel_code,
            subject, text, priority, created, result,
        )
        self.notifications.add(notification)
        if notification.is_sent:
            self.channels.get(channel_code).register_sent()
        return notification

    def cancel_notification(self, notification_id: int) -> Notification:
        """Отменить уведомление и удалить его из хранилища.

        Возбуждает KeyError, если уведомление не найдено, и
        ValueError, если оно уже отправлено.
        """
        notification = self.notifications.get(notification_id)
        if not notification.can_cancel:
            raise ValueError("Отправленное уведомление нельзя отменить")
        return self.notifications.remove(notification_id)

    def preview(self, notification: Notification) -> str:
        """Показать сообщение так, как его оформит канал доставки."""
        channel = self.channels.get(notification.channel_code)
        return channel.format_message(notification.subject, notification.text)

    def toggle_subscription(self, user_id: int) -> bool:
        """Переключить подписку пользователя, вернуть новое значение."""
        user = self.users.get(user_id)
        if user.subscribed:
            user.unsubscribe()
        else:
            user.subscribe()
        return user.subscribed

    def statistics(self) -> dict[str, int]:
        """Статистика «статус - количество уведомлений»."""
        return self.notifications.count_by_status()

    def save(self) -> None:
        """Сохранить все данные сервиса."""
        for repository in (self.users, self.channels, self.notifications):
            repository.save()
