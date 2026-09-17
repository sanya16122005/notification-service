"""Функции работы с каналами доставки уведомлений.

Канал описывается словарем: код, название, признак включения,
суточный лимит отправок, счетчик отправленных за сутки сообщений
и ограничение длины текста (0 - ограничения нет).
"""

from typing import Iterator

UNLIMITED_LENGTH = 0


def get_channel(channels: list[dict], code: str) -> dict:
    """Найти канал по коду.

    Возбуждает KeyError, если канал не найден.
    """
    for channel in channels:
        if channel["code"] == code:
            return channel
    raise KeyError(f"Канал «{code}» не найден")


def channel_codes(channels: list[dict]) -> set[str]:
    """Вернуть множество кодов доступных каналов."""
    codes = set()
    for channel in channels:
        codes.add(channel["code"])
    return codes


def limit_left(channel: dict) -> int:
    """Вычислить остаток суточного лимита отправок по каналу."""
    return channel["daily_limit"] - channel["sent_today"]


def is_too_long(channel: dict, text_length: int) -> bool:
    """Проверить превышение ограничения длины текста для канала."""
    maximum = channel["max_length"]
    return maximum != UNLIMITED_LENGTH and text_length > maximum


def register_sent(channel: dict) -> None:
    """Учесть одну отправку в суточном счетчике канала."""
    channel["sent_today"] += 1


def reset_counters(channels: list[dict]) -> int:
    """Обнулить суточные счетчики всех каналов.

    Возвращает количество отправок, учтенных до обнуления.
    """
    total = 0
    for channel in channels:
        total += channel["sent_today"]
        channel["sent_today"] = 0
    return total


def enabled_channels(channels: list[dict]) -> Iterator[dict]:
    """Перебрать включенные каналы с непустым остатком лимита."""
    for channel in channels:
        if channel["enabled"] and limit_left(channel) > 0:
            yield channel


def sort_channels_by_load(channels: list[dict]) -> list[dict]:
    """Вернуть каналы, упорядоченные по убыванию загрузки."""
    return sorted(
        channels,
        key=lambda channel: (channel["sent_today"]
                             / max(channel["daily_limit"], 1)),
        reverse=True,
    )
