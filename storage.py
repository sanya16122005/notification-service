"""Сохранение и загрузка данных проекта в JSON-файлах.

Чтение и запись выполняются через контекстный менеджер with.
Отсутствие файла и некорректный JSON обрабатываются исключениями
и не приводят к аварийному завершению программы.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, "notifications.json")


def load_json(filename: str) -> list[dict]:
    """Прочитать список записей из JSON-файла.

    Если файл отсутствует или поврежден, выводится сообщение
    и возвращается пустой список.
    """
    try:
        with open(filename, "r", encoding="utf-8") as data_file:
            records = json.load(data_file)
    except FileNotFoundError:
        print(f"Файл {os.path.basename(filename)} не найден.")
        return []
    except json.JSONDecodeError as error:
        print(f"Файл {os.path.basename(filename)} поврежден: {error.msg}")
        return []
    if not isinstance(records, list):
        print(f"Файл {os.path.basename(filename)} должен хранить список.")
        return []
    return records


def save_json(filename: str, records: list[dict]) -> None:
    """Записать список записей в JSON-файл."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # newline="\n" - файлы данных хранятся с одинаковыми переводами
    # строк независимо от операционной системы
    with open(filename, "w", encoding="utf-8", newline="\n") as data_file:
        json.dump(records, data_file, ensure_ascii=False, indent=2)
        data_file.write("\n")


def load_users() -> list[dict]:
    """Загрузить пользователей из файла данных."""
    return load_json(USERS_FILE)


def save_users(users: list[dict]) -> None:
    """Сохранить пользователей в файл данных."""
    save_json(USERS_FILE, users)


def load_channels() -> list[dict]:
    """Загрузить каналы доставки из файла данных."""
    return load_json(CHANNELS_FILE)


def save_channels(channels: list[dict]) -> None:
    """Сохранить каналы доставки в файл данных."""
    save_json(CHANNELS_FILE, channels)


def load_notifications() -> list[dict]:
    """Загрузить уведомления из файла данных."""
    return load_json(NOTIFICATIONS_FILE)


def save_notifications(notifications: list[dict]) -> None:
    """Сохранить уведомления в файл данных."""
    save_json(NOTIFICATIONS_FILE, notifications)
