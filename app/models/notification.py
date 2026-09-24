"""Уведомление и результат проверки правил доставки."""

from dataclasses import dataclass
from datetime import datetime

from app.models.base import Entity
from app.utils import format_datetime, parse_datetime

STATUS_SENT = "ОТПРАВЛЕНО"
STATUS_DELAYED = "ОТЛОЖЕНО"
STATUS_REJECTED = "ОТКЛОНЕНО"

# Неизменяемый перечень возможных статусов уведомления
STATUSES = (STATUS_SENT, STATUS_DELAYED, STATUS_REJECTED)

PRIORITY_URGENT = 1
PRIORITIES = {1: "срочный", 2: "обычный", 3: "низкий"}


@dataclass(frozen=True)
class DeliveryResult:
    """Результат проверки правил доставки.

    Класс данных (dataclass): методы __init__, __repr__ и __eq__
    создаются автоматически, а frozen=True делает объект
    неизменяемым после создания.
    """

    status: str
    comment: str
    quiet_time: bool
    delivery_at: datetime

    @property
    def is_rejected(self) -> bool:
        """Отклонено ли уведомление."""
        return self.status == STATUS_REJECTED


class Notification(Entity):
    """Уведомление, адресованное пользователю через канал доставки.

    Статус, комментарий и время доставки определяются правилами
    доставки и доступны только для чтения. Приоритет проверяется в
    сеттере свойства. Метод __lt__ задает естественный порядок
    уведомлений: сначала срочные, затем по дате создания, поэтому
    список уведомлений можно упорядочить функцией sorted().
    """

    def __init__(
        self,
        notification_id: int,
        user_id: int,
        channel_code: str,
        subject: str,
        text: str,
        priority: int,
        created_at: datetime,
        status: str,
        comment: str = "",
        delivery_at: datetime | None = None,
    ) -> None:
        if status not in STATUSES:
            raise ValueError(f"Неизвестный статус уведомления «{status}»")
        self._id = notification_id
        self._user_id = user_id
        self._channel_code = channel_code
        self.subject = subject
        self.text = text
        self.priority = priority
        self._created_at = created_at
        self._status = status
        self._comment = comment
        self._delivery_at = delivery_at or created_at

    @property
    def id(self) -> int:
        """Идентификатор уведомления (только чтение)."""
        return self._id

    @property
    def key(self) -> int:
        """Ключ сущности - идентификатор уведомления."""
        return self._id

    @property
    def user_id(self) -> int:
        """Идентификатор получателя."""
        return self._user_id

    @property
    def channel_code(self) -> str:
        """Код канала доставки."""
        return self._channel_code

    @property
    def priority(self) -> int:
        """Приоритет: 1 - срочный, 2 - обычный, 3 - низкий."""
        return self._priority

    @priority.setter
    def priority(self, value: int) -> None:
        self._priority = self.check_priority(value)

    @property
    def created_at(self) -> datetime:
        """Дата и время создания."""
        return self._created_at

    @property
    def status(self) -> str:
        """Статус уведомления (только чтение)."""
        return self._status

    @property
    def comment(self) -> str:
        """Пояснение к статусу."""
        return self._comment

    @property
    def delivery_at(self) -> datetime:
        """Запланированное время доставки."""
        return self._delivery_at

    @property
    def is_sent(self) -> bool:
        """Отправлено ли уведомление."""
        return self._status == STATUS_SENT

    @property
    def is_urgent(self) -> bool:
        """Является ли уведомление срочным."""
        return self._priority == PRIORITY_URGENT

    @property
    def can_cancel(self) -> bool:
        """Можно ли отменить уведомление (отправленное - нельзя)."""
        return not self.is_sent

    @staticmethod
    def check_priority(value: int) -> int:
        """Проверить приоритет, при ошибке возбудить ValueError."""
        if value not in PRIORITIES:
            raise ValueError("Приоритет должен быть числом от 1 до 3")
        return value

    @classmethod
    def create(
        cls,
        notification_id: int,
        user_id: int,
        channel_code: str,
        subject: str,
        text: str,
        priority: int,
        created_at: datetime,
        result: DeliveryResult,
    ) -> "Notification":
        """Создать уведомление по результату проверки доставки."""
        return cls(
            notification_id, user_id, channel_code, subject, text,
            priority, created_at, result.status, result.comment,
            result.delivery_at,
        )

    def matches(self, query: str) -> bool:
        """Проверить вхождение подстроки в тему или текст."""
        pattern = query.strip().lower()
        return (pattern in self.subject.lower()
                or pattern in self.text.lower())

    def __lt__(self, other: "Notification") -> bool:
        """Сравнить уведомления: срочные раньше, затем по дате."""
        return ((self._priority, self._created_at, self._id)
                < (other.priority, other.created_at, other.id))

    def __str__(self) -> str:
        """Вернуть краткое представление уведомления для вывода."""
        return f"[{self._status}] {self.subject}"

    def to_dict(self) -> dict:
        """Представить уведомление словарем для JSON."""
        return {
            "id": self._id,
            "user_id": self._user_id,
            "channel": self._channel_code,
            "subject": self.subject,
            "text": self.text,
            "priority": self._priority,
            "created_at": format_datetime(self._created_at),
            "status": self._status,
            "comment": self._comment,
            "delivery_at": format_datetime(self._delivery_at),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Notification":
        """Создать уведомление из словаря, даты разбираются из строк."""
        created_at = parse_datetime(data["created_at"])
        delivery_at = data.get("delivery_at")
        return cls(
            notification_id=data["id"],
            user_id=data["user_id"],
            channel_code=data["channel"],
            subject=data["subject"],
            text=data["text"],
            priority=data["priority"],
            created_at=created_at,
            status=data["status"],
            comment=data.get("comment", ""),
            delivery_at=(parse_datetime(delivery_at)
                         if delivery_at else created_at),
        )
