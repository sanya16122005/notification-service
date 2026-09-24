"""Хранение данных проекта в JSON-файлах.

Класс JsonStorage отвечает только за файл: читает и записывает
список словарей. Преобразование словарей в объекты выполняют
сами классы сущностей (методы from_dict и to_dict), а связывают
их хранилища-репозитории из app/services/repositories.py.
"""

import json
import os

# Каталог data/ находится в корне проекта, на уровень выше пакета app
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PACKAGE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, "notifications.json")


class JsonStorage:
    """Файловое хранилище списка записей в формате JSON.

    Чтение и запись выполняются через контекстный менеджер with.
    Отсутствие файла и некорректный JSON обрабатываются и не
    приводят к аварийному завершению программы.
    """

    def __init__(self, filename: str) -> None:
        self._filename = filename

    @property
    def filename(self) -> str:
        """Полный путь к файлу данных (только чтение)."""
        return self._filename

    @property
    def name(self) -> str:
        """Имя файла без каталога."""
        return os.path.basename(self._filename)

    def load(self) -> list[dict]:
        """Прочитать список записей из файла.

        Если файл отсутствует или поврежден, выводится сообщение
        и возвращается пустой список.
        """
        try:
            with open(self._filename, "r", encoding="utf-8") as data_file:
                records = json.load(data_file)
        except FileNotFoundError:
            print(f"Файл {self.name} не найден.")
            return []
        except json.JSONDecodeError as error:
            print(f"Файл {self.name} поврежден: {error.msg}")
            return []
        if not isinstance(records, list):
            print(f"Файл {self.name} должен хранить список.")
            return []
        return records

    def save(self, records: list[dict]) -> None:
        """Записать список записей в файл."""
        os.makedirs(os.path.dirname(self._filename), exist_ok=True)
        # newline="\n" - файлы данных хранятся с одинаковыми переводами
        # строк независимо от операционной системы
        with open(
            self._filename, "w", encoding="utf-8", newline="\n"
        ) as data_file:
            json.dump(records, data_file, ensure_ascii=False, indent=2)
            data_file.write("\n")

    def __repr__(self) -> str:
        """Вернуть техническое представление хранилища."""
        return f"JsonStorage({self.name!r})"
