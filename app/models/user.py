"""Пользователь - получатель уведомлений."""

from app.models.base import Entity

QUIET_START_DEFAULT = 23
QUIET_END_DEFAULT = 8


class User(Entity):
    """Получатель уведомлений.

    Атрибуты объекта защищены (инкапсуляция): идентификатор доступен
    только для чтения, имя, контакт и границы «тихих часов»
    проверяются в сеттерах свойств, а признаки активности и подписки
    изменяются только методами activate(), deactivate(), subscribe()
    и unsubscribe().
    """

    def __init__(
        self,
        user_id: int,
        name: str,
        contact: str,
        is_active: bool = True,
        subscribed: bool = True,
        quiet_start: int = QUIET_START_DEFAULT,
        quiet_end: int = QUIET_END_DEFAULT,
    ) -> None:
        self._id = user_id
        self.name = name
        self.contact = contact
        self._is_active = is_active
        self._subscribed = subscribed
        self.quiet_start = quiet_start
        self.quiet_end = quiet_end

    @property
    def id(self) -> int:
        """Идентификатор пользователя (только чтение)."""
        return self._id

    @property
    def key(self) -> int:
        """Ключ сущности - идентификатор пользователя."""
        return self._id

    @property
    def name(self) -> str:
        """Имя пользователя."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Имя пользователя не может быть пустым")
        self._name = value

    @property
    def contact(self) -> str:
        """Контакт пользователя: адрес почты или номер телефона."""
        return self._contact

    @contact.setter
    def contact(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Контакт пользователя не может быть пустым")
        self._contact = value

    @property
    def is_active(self) -> bool:
        """Признак активной учетной записи (только чтение)."""
        return self._is_active

    @property
    def subscribed(self) -> bool:
        """Признак подписки на рассылку (только чтение)."""
        return self._subscribed

    @property
    def can_receive(self) -> bool:
        """Может ли пользователь получать уведомления."""
        return self._is_active and self._subscribed

    @property
    def quiet_start(self) -> int:
        """Час начала «тихих часов»."""
        return self._quiet_start

    @quiet_start.setter
    def quiet_start(self, hour: int) -> None:
        self._quiet_start = self._check_hour(hour)

    @property
    def quiet_end(self) -> int:
        """Час окончания «тихих часов»."""
        return self._quiet_end

    @quiet_end.setter
    def quiet_end(self, hour: int) -> None:
        self._quiet_end = self._check_hour(hour)

    @staticmethod
    def _check_hour(hour: int) -> int:
        """Проверить, что час лежит в диапазоне 0-23."""
        if not isinstance(hour, int) or not 0 <= hour <= 23:
            raise ValueError("Час должен быть целым числом от 0 до 23")
        return hour

    def activate(self) -> None:
        """Активировать учетную запись."""
        self._is_active = True

    def deactivate(self) -> None:
        """Заблокировать учетную запись."""
        self._is_active = False

    def subscribe(self) -> None:
        """Подписать пользователя на рассылку."""
        self._subscribed = True

    def unsubscribe(self) -> None:
        """Отписать пользователя от рассылки."""
        self._subscribed = False

    def is_quiet_time(self, hour: int) -> bool:
        """Проверить, попадает ли час в «тихие часы» пользователя.

        Интервал может переходить через полночь (23:00-08:00) или
        лежать внутри суток (00:00-06:00). Совпадение границ
        означает, что «тихих часов» нет.
        """
        start, end = self._quiet_start, self._quiet_end
        if start == end:
            return False
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end

    def quiet_hours_text(self) -> str:
        """Вернуть «тихие часы» строкой вида 23:00-08:00."""
        return f"{self._quiet_start:02d}:00-{self._quiet_end:02d}:00"

    def matches(self, query: str) -> bool:
        """Проверить вхождение подстроки в имя или контакт."""
        pattern = query.strip().lower()
        return (pattern in self._name.lower()
                or pattern in self._contact.lower())

    def __str__(self) -> str:
        """Вернуть представление пользователя для вывода."""
        return f"{self._name} ({self._contact})"

    def to_dict(self) -> dict:
        """Представить пользователя словарем для JSON."""
        return {
            "id": self._id,
            "name": self._name,
            "contact": self._contact,
            "is_active": self._is_active,
            "subscribed": self._subscribed,
            "quiet_start": self._quiet_start,
            "quiet_end": self._quiet_end,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Создать пользователя из словаря."""
        return cls(
            user_id=data["id"],
            name=data["name"],
            contact=data["contact"],
            is_active=data.get("is_active", True),
            subscribed=data.get("subscribed", True),
            quiet_start=data.get("quiet_start", QUIET_START_DEFAULT),
            quiet_end=data.get("quiet_end", QUIET_END_DEFAULT),
        )
