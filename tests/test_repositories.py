"""Тесты хранилищ сущностей и файлового хранилища JSON."""

from pathlib import Path

import pytest

from app.models import User
from app.services.repositories import UserRepository
from app.storage import JsonStorage


def make_users() -> UserRepository:
    """Подготовить хранилище с двумя пользователями."""
    users = UserRepository()
    users.create("Стерлигов Александр", "a.sterligov@example.com")
    users.create("Иванова Мария", "+7 900 123-45-67")
    return users


def test_create_assigns_ids() -> None:
    """Новые пользователи получают последовательные идентификаторы."""
    users = make_users()
    assert [user.id for user in users] == [1, 2]
    assert users.next_id() == 3


def test_repository_behaves_like_collection() -> None:
    """Магические методы: len(), in, перебор в цикле."""
    users = make_users()
    assert len(users) == 2
    assert 2 in users
    assert 5 not in users


def test_get_missing_user_raises_key_error() -> None:
    """Запрос несуществующего пользователя возбуждает KeyError."""
    with pytest.raises(KeyError, match="id=99"):
        make_users().get(99)


def test_duplicate_key_is_rejected() -> None:
    """Запись с существующим ключом не добавляется."""
    users = make_users()
    with pytest.raises(ValueError):
        users.add(User(1, "Дубликат", "copy@example.com"))


def test_find_and_receivers() -> None:
    """Поиск по подстроке и генератор получателей."""
    users = make_users()
    assert users.find("иванова")[0].id == 2
    users.get(2).unsubscribe()
    assert [user.id for user in users.receivers()] == [1]


def test_json_storage_round_trip(tmp_path: Path) -> None:
    """Хранилище сохраняет объекты в JSON и загружает обратно."""
    storage = JsonStorage(str(tmp_path / "users.json"))
    users = UserRepository(make_users(), storage=storage)
    users.save()
    loaded = UserRepository(storage=storage)
    loaded.load()
    assert [user.name for user in loaded] == [
        "Стерлигов Александр", "Иванова Мария"
    ]


def test_missing_file_gives_empty_repository(tmp_path: Path) -> None:
    """Отсутствующий файл не прерывает работу программы."""
    users = UserRepository(
        storage=JsonStorage(str(tmp_path / "absent.json"))
    )
    users.load()
    assert len(users) == 0


def test_invalid_record_is_skipped(tmp_path: Path) -> None:
    """Некорректная запись пропускается, остальные загружаются."""
    storage = JsonStorage(str(tmp_path / "users.json"))
    storage.save([
        {"id": 1, "name": "Стерлигов Александр", "contact": "a@b.ru"},
        {"id": 2, "name": "Без контакта"},
    ])
    users = UserRepository(storage=storage)
    users.load()
    assert len(users) == 1
