"""Вспомогательные функции проекта.

Модуль содержит безопасный ввод данных с обработкой исключений,
преобразование даты и времени, вывод заголовков, а также средства
интроспекции, используемые для справки о классах проекта.
"""

import inspect
from datetime import datetime

DATETIME_FORMAT = "%d.%m.%Y %H:%M"
LINE_WIDTH = 60


def print_title(title: str) -> None:
    """Вывести заголовок раздела."""
    print("=" * LINE_WIDTH)
    print(title)
    print("=" * LINE_WIDTH)


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


def class_hierarchy(cls: type) -> str:
    """Вернуть цепочку наследования класса (порядок MRO)."""
    names = [item.__name__ for item in cls.__mro__ if item is not object]
    return " -> ".join(names)


def describe_class(cls: type) -> list[str]:
    """Собрать описания открытых методов и свойств класса.

    Средствами интроспекции перебираются атрибуты, объявленные в
    самом классе. Для каждого метода или свойства возвращается
    строка «имя(параметры) [вид] - первая строка docstring».
    """
    descriptions = []
    for name, member in vars(cls).items():
        if name.startswith("_"):
            continue
        if isinstance(member, property):
            kind, function = "свойство", member.fget
        elif isinstance(member, classmethod):
            kind, function = "метод класса", member.__func__
        elif isinstance(member, staticmethod):
            kind, function = "статический метод", member.__func__
        elif inspect.isfunction(member):
            kind, function = "метод", member
        else:
            continue
        if function is None:
            continue
        document = inspect.getdoc(function) or "описание отсутствует"
        signature = ""
        if kind != "свойство":
            signature = str(inspect.signature(function))
        descriptions.append(
            f"{name}{signature} [{kind}] - {document.splitlines()[0]}"
        )
    return descriptions
