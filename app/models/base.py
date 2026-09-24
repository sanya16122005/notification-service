"""Абстрактный базовый класс сущностей предметной области."""

from abc import ABC, abstractmethod
from typing import Any


class Entity(ABC):
    """Общий предок всех сущностей проекта.

    Задает единый интерфейс сущности: ключ записи, преобразование
    в словарь для сохранения в JSON и обратное создание объекта из
    словаря. Объекты сравниваются по типу и ключу, поэтому два
    объекта одного пользователя считаются равными.
    """

    @property
    @abstractmethod
    def key(self) -> Any:
        """Уникальный ключ сущности (идентификатор или код)."""

    @abstractmethod
    def to_dict(self) -> dict:
        """Представить объект словарем для сохранения в JSON."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "Entity":
        """Создать объект из словаря, прочитанного из JSON."""

    def __eq__(self, other: object) -> bool:
        """Сравнить сущности по типу и ключу."""
        if not isinstance(other, Entity):
            return NotImplemented
        return type(self) is type(other) and self.key == other.key

    def __hash__(self) -> int:
        """Вычислить хеш по имени класса и ключу."""
        return hash((type(self).__name__, self.key))

    def __repr__(self) -> str:
        """Вернуть техническое представление объекта для отладки."""
        return f"{type(self).__name__}(key={self.key!r})"
