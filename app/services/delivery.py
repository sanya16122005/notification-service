"""Правила доставки уведомлений.

Сценарий ПР1 (проверка возможности отправки) оформлен классом
DeliveryRules. Отдельные правила стали методами класса, а метод
check() объединяет их и возвращает объект DeliveryResult.
"""

from datetime import datetime, timedelta

from app.models import Channel, DeliveryResult, User
from app.models.notification import (
    PRIORITY_URGENT,
    STATUS_DELAYED,
    STATUS_REJECTED,
    STATUS_SENT,
)


class DeliveryRules:
    """Проверка правил доставки уведомления.

    Порядок проверок: активность и подписка пользователя, состояние
    канала, соответствие контакта каналу, суточный лимит, длина
    текста. Если запретов нет, учитываются «тихие часы»: обычное
    уведомление откладывается до их окончания, срочное (приоритет
    urgent_priority) отправляется сразу.
    """

    COMMENT_SENT = "Уведомление передано в канал доставки"
    COMMENT_DELAYED = "Отправка запрещена в «тихие часы» пользователя"

    def __init__(self, urgent_priority: int = PRIORITY_URGENT) -> None:
        self.urgent_priority = urgent_priority

    def block_reason(self, user: User, channel: Channel, text: str) -> str:
        """Вернуть причину отказа в доставке или пустую строку."""
        if not user.can_receive:
            return "Пользователь неактивен или отписан от рассылки"
        if not channel.enabled:
            return "Канал доставки отключен"
        if not channel.accepts_contact(user.contact):
            return "Контакт пользователя не подходит для канала"
        if not channel.has_capacity:
            return "Исчерпан суточный лимит отправок по каналу"
        if channel.is_too_long(len(text)):
            return "Текст превышает допустимую длину для канала"
        return ""

    @staticmethod
    def status(block_reason: str, quiet_time: bool, urgent: bool) -> str:
        """Определить статус уведомления по результатам проверок."""
        if block_reason:
            return STATUS_REJECTED
        if quiet_time and not urgent:
            return STATUS_DELAYED
        return STATUS_SENT

    @classmethod
    def comment(cls, status: str, block_reason: str) -> str:
        """Сформировать пояснение к статусу уведомления."""
        if status == STATUS_REJECTED:
            return block_reason
        if status == STATUS_DELAYED:
            return cls.COMMENT_DELAYED
        return cls.COMMENT_SENT

    @staticmethod
    def delivery_time(created: datetime, status: str, user: User) -> datetime:
        """Вычислить время доставки уведомления.

        Отложенное уведомление отправляется сразу после окончания
        «тихих часов»: созданное вечером - утром следующего дня,
        созданное ночью - тем же утром.
        """
        if status != STATUS_DELAYED:
            return created
        morning = created.replace(
            hour=user.quiet_end, minute=0, second=0, microsecond=0
        )
        if morning <= created:
            morning += timedelta(days=1)
        return morning

    def check(
        self,
        user: User,
        channel: Channel,
        text: str,
        priority: int,
        created: datetime,
    ) -> DeliveryResult:
        """Проверить все правила и вернуть результат проверки."""
        reason = self.block_reason(user, channel, text)
        quiet_time = user.is_quiet_time(created.hour)
        urgent = priority == self.urgent_priority
        status = self.status(reason, quiet_time, urgent)
        return DeliveryResult(
            status=status,
            comment=self.comment(status, reason),
            quiet_time=quiet_time,
            delivery_at=self.delivery_time(created, status, user),
        )
