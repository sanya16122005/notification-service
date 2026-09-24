"""Хранилища сущностей (репозитории).

Базовый класс Repository реализует общие операции с набором
объектов одного типа, а наследники UserRepository,
ChannelRepository и NotificationRepository добавляют запросы,
специфичные для своей сущности. Примесь AutoIdMixin выдает
числовые идентификаторы новым записям.
"""

from collections.abc import Callable, Iterable, Iterator
from typing import Any, Generic, TypeVar

from app.models import Channel, Entity, Notification, User
from app.models.notification import STATUSES
from app.models.user import QUIET_END_DEFAULT, QUIET_START_DEFAULT
from app.storage import JsonStorage

EntityType = TypeVar("EntityType", bound=Entity)


class Repository(Generic[EntityType]):
    """Базовое хранилище сущностей одного типа.

    Объекты хранятся в защищенном списке _items. Магические методы
    __len__, __iter__ и __contains__ позволяют работать с
    хранилищем как с обычной коллекцией: len(users),
    for user in users, 1 in users. Загрузка и сохранение
    выполняются через объект JsonStorage.
    """

    # Any: базовый класс Entity абстрактный, конкретный класс
    # сущности задают наследники хранилища.
    entity_class: Any = Entity
    not_found_text = "Запись «{key}» не найдена"

    def __init__(
        self,
        items: Iterable[EntityType] = (),
        storage: JsonStorage | None = None,
    ) -> None:
        self._items: list[EntityType] = list(items)
        self._storage = storage

    def __len__(self) -> int:
        """Количество записей в хранилище."""
        return len(self._items)

    def __iter__(self) -> Iterator[EntityType]:
        """Перебор записей хранилища."""
        return iter(self._items)

    def __contains__(self, key: object) -> bool:
        """Проверить наличие записи с указанным ключом."""
        return any(item.key == key for item in self._items)

    def __repr__(self) -> str:
        """Вернуть техническое представление хранилища."""
        return f"{type(self).__name__}(records={len(self)})"

    def get(self, key: Any) -> EntityType:
        """Найти запись по ключу.

        Возбуждает KeyError, если запись не найдена.
        """
        for item in self._items:
            if item.key == key:
                return item
        raise KeyError(self.not_found_text.format(key=key))

    def add(self, item: EntityType) -> EntityType:
        """Добавить запись, ключ должен быть уникальным."""
        if item.key in self:
            raise ValueError(f"Запись с ключом {item.key} уже существует")
        self._items.append(item)
        return item

    def remove(self, key: Any) -> EntityType:
        """Удалить запись по ключу и вернуть ее."""
        item = self.get(key)
        self._items.remove(item)
        return item

    def filter(
        self, condition: Callable[[EntityType], bool]
    ) -> Iterator[EntityType]:
        """Перебрать записи, удовлетворяющие условию (генератор)."""
        for item in self._items:
            if condition(item):
                yield item

    def load(self) -> None:
        """Загрузить записи из хранилища и создать объекты.

        Некорректная запись пропускается с сообщением и не мешает
        загрузке остальных.
        """
        if self._storage is None:
            return
        self._items = []
        for record in self._storage.load():
            try:
                self._items.append(self.entity_class.from_dict(record))
            except (KeyError, TypeError, ValueError) as error:
                print(f"Пропущена запись в {self._storage.name}: {error}")

    def save(self) -> None:
        """Сохранить записи в хранилище."""
        if self._storage is not None:
            self._storage.save([item.to_dict() for item in self._items])


class AutoIdMixin:
    """Примесь: выдает следующий свободный числовой идентификатор.

    Используется при множественном наследовании вместе с
    Repository. Идентификаторы не переиспользуются: берется
    максимальный существующий и увеличивается на единицу.
    """

    _items: list

    def next_id(self) -> int:
        """Вернуть следующий свободный идентификатор."""
        return max((item.key for item in self._items), default=0) + 1


class UserRepository(AutoIdMixin, Repository[User]):
    """Хранилище пользователей."""

    entity_class = User
    not_found_text = "Пользователь с id={key} не найден"

    def create(
        self,
        name: str,
        contact: str,
        quiet_start: int = QUIET_START_DEFAULT,
        quiet_end: int = QUIET_END_DEFAULT,
    ) -> User:
        """Создать пользователя с новым идентификатором."""
        user = User(self.next_id(), name, contact,
                    quiet_start=quiet_start, quiet_end=quiet_end)
        return self.add(user)

    def find(self, query: str) -> list[User]:
        """Найти пользователей по подстроке имени или контакта."""
        return [user for user in self._items if user.matches(query)]

    def receivers(self) -> Iterator[User]:
        """Перебрать пользователей, которые получают уведомления."""
        return self.filter(lambda user: user.can_receive)

    def sorted_by_name(self) -> list[User]:
        """Вернуть пользователей, упорядоченных по имени."""
        return sorted(self._items, key=lambda user: user.name.lower())


class ChannelRepository(Repository[Channel]):
    """Хранилище каналов доставки."""

    entity_class = Channel
    not_found_text = "Канал «{key}» не найден"

    def codes(self) -> set[str]:
        """Вернуть множество кодов каналов."""
        return {channel.code for channel in self._items}

    def available(self) -> Iterator[Channel]:
        """Перебрать включенные каналы с остатком лимита."""
        return self.filter(
            lambda channel: channel.enabled and channel.has_capacity
        )

    def sorted_by_load(self) -> list[Channel]:
        """Вернуть каналы по убыванию загрузки."""
        return sorted(
            self._items, key=lambda channel: channel.load, reverse=True
        )

    def reset_counters(self) -> int:
        """Обнулить счетчики всех каналов, вернуть сумму отправок."""
        return sum(channel.reset_counter() for channel in self._items)


class NotificationRepository(AutoIdMixin, Repository[Notification]):
    """Хранилище уведомлений."""

    entity_class = Notification
    not_found_text = "Уведомление с id={key} не найдено"

    def find(self, query: str) -> list[Notification]:
        """Найти уведомления по подстроке темы или текста."""
        return [item for item in self._items if item.matches(query)]

    def by_status(self, status: str) -> Iterator[Notification]:
        """Перебрать уведомления с указанным статусом."""
        return self.filter(lambda item: item.status == status)

    def of_user(self, user_id: int) -> list[Notification]:
        """Отобрать уведомления одного пользователя."""
        return list(self.filter(lambda item: item.user_id == user_id))

    def ordered(self) -> list[Notification]:
        """Вернуть уведомления в естественном порядке (__lt__)."""
        return sorted(self._items)

    def count_by_status(self) -> dict[str, int]:
        """Подсчитать количество уведомлений каждого статуса."""
        statistics = dict.fromkeys(STATUSES, 0)
        for item in self._items:
            statistics[item.status] += 1
        return statistics
