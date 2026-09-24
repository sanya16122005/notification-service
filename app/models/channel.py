"""Каналы доставки уведомлений: базовый класс и его наследники."""

import re
from abc import abstractmethod

from app.models.base import Entity

UNLIMITED_LENGTH = 0


class Channel(Entity):
    """Абстрактный канал доставки уведомлений.

    Общая логика всех каналов - суточный лимит, счетчик отправок и
    ограничение длины текста - реализована в базовом классе.
    Проверка контакта получателя и оформление сообщения у каждого
    канала свои, поэтому объявлены абстрактными методами и
    переопределяются в наследниках (полиморфизм). Создать объект
    самого класса Channel нельзя - только объект наследника.
    """

    code = ""
    default_title = ""
    default_max_length = UNLIMITED_LENGTH

    def __init__(
        self,
        daily_limit: int,
        enabled: bool = True,
        sent_today: int = 0,
        max_length: int | None = None,
        title: str | None = None,
    ) -> None:
        self.title = title or self.default_title
        self._enabled = enabled
        self.daily_limit = daily_limit
        if sent_today < 0:
            raise ValueError("Счетчик отправок не может быть меньше нуля")
        self._sent_today = sent_today
        if max_length is None:
            max_length = self.default_max_length
        self._max_length = max_length

    @property
    def key(self) -> str:
        """Ключ сущности - код канала."""
        return self.code

    @property
    def enabled(self) -> bool:
        """Признак включенного канала (только чтение)."""
        return self._enabled

    @property
    def daily_limit(self) -> int:
        """Суточный лимит отправок."""
        return self._daily_limit

    @daily_limit.setter
    def daily_limit(self, value: int) -> None:
        if value < 0:
            raise ValueError("Суточный лимит не может быть меньше нуля")
        self._daily_limit = value

    @property
    def sent_today(self) -> int:
        """Количество отправок за сутки (только чтение)."""
        return self._sent_today

    @property
    def max_length(self) -> int:
        """Ограничение длины текста, 0 - без ограничения."""
        return self._max_length

    @property
    def load(self) -> float:
        """Загрузка канала - доля израсходованного лимита."""
        return self._sent_today / max(self._daily_limit, 1)

    @property
    def has_capacity(self) -> bool:
        """Остался ли у канала лимит отправок на сегодня."""
        return self.limit_left() > 0

    def enable(self) -> None:
        """Включить канал."""
        self._enabled = True

    def disable(self) -> None:
        """Отключить канал."""
        self._enabled = False

    def limit_left(self) -> int:
        """Вычислить остаток суточного лимита отправок."""
        return self._daily_limit - self._sent_today

    def is_too_long(self, text_length: int) -> bool:
        """Проверить превышение ограничения длины текста."""
        maximum = self._max_length
        return maximum != UNLIMITED_LENGTH and text_length > maximum

    def register_sent(self) -> None:
        """Учесть одну отправку в суточном счетчике канала.

        Возбуждает ValueError, если лимит уже исчерпан.
        """
        if not self.has_capacity:
            raise ValueError("Исчерпан суточный лимит отправок по каналу")
        self._sent_today += 1

    def reset_counter(self) -> int:
        """Обнулить счетчик и вернуть число учтенных отправок."""
        sent, self._sent_today = self._sent_today, 0
        return sent

    @abstractmethod
    def accepts_contact(self, contact: str) -> bool:
        """Проверить, подходит ли контакт получателя для канала."""

    @abstractmethod
    def format_message(self, subject: str, text: str) -> str:
        """Оформить сообщение так, как его увидит получатель."""

    def __str__(self) -> str:
        """Вернуть представление канала для вывода."""
        return f"{self.code} - {self.title}"

    def to_dict(self) -> dict:
        """Представить канал словарем для JSON."""
        return {
            "code": self.code,
            "title": self.title,
            "enabled": self._enabled,
            "daily_limit": self._daily_limit,
            "sent_today": self._sent_today,
            "max_length": self._max_length,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Channel":
        """Создать объект нужного класса-наследника по коду канала.

        Фабричный метод: по значению поля code выбирается класс из
        словаря CHANNEL_TYPES. Для неизвестного кода возбуждается
        ValueError.
        """
        channel_class = CHANNEL_TYPES.get(data["code"])
        if channel_class is None:
            raise ValueError(f"Неизвестный тип канала «{data['code']}»")
        return channel_class(
            daily_limit=data["daily_limit"],
            enabled=data.get("enabled", True),
            sent_today=data.get("sent_today", 0),
            max_length=data.get("max_length"),
            title=data.get("title"),
        )


class EmailChannel(Channel):
    """Канал электронной почты: письмо с темой, без ограничения длины."""

    code = "email"
    default_title = "Электронная почта"
    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def accepts_contact(self, contact: str) -> bool:
        """Письмо можно отправить только на адрес электронной почты."""
        return bool(self.EMAIL_PATTERN.match(contact))

    def format_message(self, subject: str, text: str) -> str:
        """Письмо содержит строку темы и текст."""
        return f"Тема: {subject}\n{text}"


class SmsChannel(Channel):
    """SMS-канал: короткий текст на номер телефона, без темы."""

    code = "sms"
    default_title = "SMS-сообщения"
    default_max_length = 70
    PHONE_PATTERN = re.compile(r"^\+?[\d\s()-]+$")

    def accepts_contact(self, contact: str) -> bool:
        """SMS отправляется на номер телефона из 10-15 цифр."""
        digits = sum(symbol.isdigit() for symbol in contact)
        return bool(self.PHONE_PATTERN.match(contact)) and 10 <= digits <= 15

    def format_message(self, subject: str, text: str) -> str:
        """В SMS тема не передается - только текст."""
        return text


class PushChannel(Channel):
    """Push-канал: уведомление в приложении пользователя."""

    code = "push"
    default_title = "Push-уведомления"
    default_max_length = 120

    def accepts_contact(self, contact: str) -> bool:
        """Push доставляется по учетной записи, контакт не важен."""
        return True

    def format_message(self, subject: str, text: str) -> str:
        """Push-уведомление выводится одной строкой «тема: текст»."""
        return f"{subject}: {text}"


# Реестр классов-наследников: код канала -> класс
CHANNEL_TYPES: dict[str, type[Channel]] = {
    channel_class.code: channel_class
    for channel_class in (EmailChannel, SmsChannel, PushChannel)
}
