"""Декораторы проекта."""

import functools
from collections.abc import Callable
from typing import Any

from app.utils import error_text, print_title


def menu_action(
    title: str,
) -> Callable[[Callable[..., Any]], Callable[..., bool]]:
    """Декоратор с параметром для пунктов меню.

    Оборачивает метод консольного приложения: перед вызовом
    выводит заголовок раздела, перехватывает ошибки предметной
    области (KeyError, ValueError) и выводит понятное сообщение.
    Обернутая функция возвращает True, если данные изменились и
    их нужно сохранить. functools.wraps сохраняет имя и docstring
    исходной функции.
    """

    def decorator(function: Callable[..., Any]) -> Callable[..., bool]:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> bool:
            print_title(title)
            try:
                return bool(function(*args, **kwargs))
            except (KeyError, ValueError) as error:
                print(f"Операция не выполнена: {error_text(error)}")
                return False

        return wrapper

    return decorator
