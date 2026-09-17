"""Вспомогательные функции проекта.

Модуль содержит безопасный ввод данных с обработкой исключений,
преобразование даты и времени, а также средства интроспекции,
используемые для вывода справки о функциях проекта.
"""

import inspect
from datetime import datetime
from types import ModuleType

DATETIME_FORMAT = "%d.%m.%Y %H:%M"


def next_id(records: list[dict]) -> int:
    """Вернуть следующий свободный идентификатор записи.

    Идентификаторы не переиспользуются: берется максимальный
    существующий и увеличивается на единицу.
    """
    maximum = 0
    for record in records:
        if record.get("id", 0) > maximum:
            maximum = record["id"]
    return maximum + 1


def error_text(error: Exception) -> str:
    """Вернуть текст сообщения исключения.

    str(KeyError) добавляет кавычки вокруг сообщения, поэтому для
    вывода пользователю берется первый аргумент исключения.
    """
    if error.args:
        return str(error.args[0])
    return str(error)


def input_text(prompt: str) -> str:
    """Запросить у пользователя непустую строку."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значение не может быть пустым, повторите ввод.")


def input_int(prompt: str, minimum: int, maximum: int) -> int:
    """Запросить целое число в заданных границах.

    Некорректный ввод не прерывает программу: исключение
    ValueError перехватывается, запрос повторяется.
    """
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("Нужно ввести целое число, повторите ввод.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"Число должно быть от {minimum} до {maximum}.")


def input_choice(prompt: str, allowed: set[str]) -> str:
    """Запросить значение из множества допустимых."""
    while True:
        value = input(prompt).strip().lower()
        if value in allowed:
            return value
        print("Допустимые значения: " + ", ".join(sorted(allowed)))


def input_datetime(prompt: str) -> datetime:
    """Запросить дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ."""
    while True:
        try:
            return parse_datetime(input(prompt).strip())
        except ValueError:
            print("Формат даты и времени: 15.09.2026 14:30.")


def format_datetime(moment: datetime) -> str:
    """Представить дату и время строкой для вывода и хранения."""
    return moment.strftime(DATETIME_FORMAT)


def parse_datetime(value: str) -> datetime:
    """Разобрать дату и время из строки.

    Возбуждает ValueError, если строка не соответствует формату.
    """
    return datetime.strptime(value, DATETIME_FORMAT)


def describe_module(module: ModuleType) -> list[str]:
    """Собрать описания функций модуля средствами интроспекции.

    Для каждой функции, объявленной в самом модуле, возвращается
    строка вида «имя(параметры) - первая строка docstring».
    """
    descriptions = []
    for name in dir(module):
        attribute = getattr(module, name)
        if not inspect.isfunction(attribute):
            continue
        if attribute.__module__ != module.__name__:
            continue
        document = inspect.getdoc(attribute) or "описание отсутствует"
        signature = inspect.signature(attribute)
        descriptions.append(
            f"{name}{signature} - {document.splitlines()[0]}"
        )
    return descriptions
