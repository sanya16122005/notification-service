"""Сервис управления уведомлениями.

Практическая работа № 1. Начальный сценарий проекта:
проверка возможности доставки одного уведомления пользователю
по выбранному каналу связи и определение его статуса.

Используются конструкции ПР1: простые типы данных, операции,
преобразование типов, ветвления, импорт модулей. Проверки правил
доставки вынесены в отдельные функции.
"""

from datetime import datetime, timedelta

# Статусы уведомления
STATUS_SENT = "ОТПРАВЛЕНО"
STATUS_DELAYED = "ОТЛОЖЕНО"
STATUS_REJECTED = "ОТКЛОНЕНО"

# Ограничение длины одного SMS для кириллицы
SMS_MAX_LENGTH = 70


def is_quiet_time(hour, start_hour, end_hour):
    """Проверить, попадает ли час в «тихие часы» пользователя.

    Интервал переходит через полночь, поэтому час считается тихим,
    если он не раньше начала интервала или раньше его окончания.
    """
    return hour >= start_hour or hour < end_hour


def is_too_long_for_channel(channel, text_length):
    """Проверить, превышает ли текст ограничение длины для канала."""
    return channel == "sms" and text_length > SMS_MAX_LENGTH


def get_block_reason(is_active, is_subscribed, channel_enabled,
                     limit_left, too_long):
    """Вернуть причину отказа в доставке.

    Если запретов нет, возвращается пустая строка.
    """
    if not is_active or not is_subscribed:
        return "Пользователь неактивен или отписан от рассылки"
    if not channel_enabled:
        return "Канал доставки отключен"
    if limit_left <= 0:
        return "Исчерпан суточный лимит отправок по каналу"
    if too_long:
        return "Текст превышает допустимую длину SMS"
    return ""


def get_status(block_reason, quiet_time, urgent):
    """Определить статус уведомления по результатам проверок."""
    if block_reason:
        return STATUS_REJECTED
    if quiet_time and not urgent:
        return STATUS_DELAYED
    return STATUS_SENT


def get_status_comment(status, block_reason):
    """Сформировать пояснение к статусу уведомления."""
    if status == STATUS_REJECTED:
        return block_reason
    if status == STATUS_DELAYED:
        return "Отправка запрещена в «тихие часы» пользователя"
    return "Уведомление передано в канал доставки"


def get_delivery_time(created, status, start_hour, end_hour):
    """Вычислить время доставки уведомления.

    Отложенное уведомление отправляется сразу после окончания
    «тихих часов»: созданное вечером - утром следующего дня,
    созданное ночью - тем же утром.
    """
    if status != STATUS_DELAYED:
        return created
    morning = created.replace(hour=end_hour, minute=0)
    if created.hour >= start_hour:
        return morning + timedelta(days=1)
    return morning


# --- Сущность «Пользователь» ---------------------------------------
user_id = 1042
user_name = "Стерлигов Александр"
user_contact = "a.sterligov@example.com"
user_is_active = True
user_subscribed = True
quiet_hours_start = 23  # начало «тихих часов» пользователя
quiet_hours_end = 8     # конец «тихих часов» пользователя

# --- Сущность «Канал» ----------------------------------------------
channel_code = "email"        # email / sms / push
channel_is_enabled = True
channel_daily_limit = 20
channel_sent_today_raw = "17"  # из внешней системы приходит строкой

# --- Сущность «Уведомление» ----------------------------------------
notification_id = 5573
notification_subject = "Плановые технические работы"
notification_text = (
    "Сервис будет недоступен 12.09.2026 с 02:00 до 04:00 по МСК."
)
notification_priority = 2  # 1 - высокий, 2 - обычный, 3 - низкий
created_at = datetime(2026, 9, 10, 23, 40)

# --- Преобразование типов и операции над данными --------------------
sent_today = int(channel_sent_today_raw)
limit_left = channel_daily_limit - sent_today
text_length = len(notification_text)
limit_used_percent = round(sent_today / channel_daily_limit * 100, 1)
current_hour = created_at.hour

# --- Проверка правил доставки ---------------------------------------
quiet_time = is_quiet_time(current_hour, quiet_hours_start, quiet_hours_end)
urgent = notification_priority == 1
too_long = is_too_long_for_channel(channel_code, text_length)

block_reason = get_block_reason(user_is_active, user_subscribed,
                                channel_is_enabled, limit_left, too_long)
notification_status = get_status(block_reason, quiet_time, urgent)
status_comment = get_status_comment(notification_status, block_reason)
delivery_at = get_delivery_time(created_at, notification_status,
                                quiet_hours_start, quiet_hours_end)

# --- Вывод результата ----------------------------------------------
print("=" * 52)
print("СЕРВИС УПРАВЛЕНИЯ УВЕДОМЛЕНИЯМИ")
print("=" * 52)
print("Уведомление №" + str(notification_id) + ": " + notification_subject)
print(f"Получатель: {user_name} (id={user_id}, {user_contact})")
print(f"Канал: {channel_code}, отправлено сегодня: {sent_today}"
      f" из {channel_daily_limit} ({limit_used_percent}%)")
print(f"Остаток лимита: {limit_left}")
print(f"Приоритет: {notification_priority}, длина текста: {text_length}")
print(f"Создано: {created_at:%d.%m.%Y %H:%M}")
print(f"«Тихие часы»: {quiet_hours_start}:00-{quiet_hours_end}:00,"
      f" сейчас тихое время: {quiet_time}")
print("-" * 52)
print(f"Статус: {notification_status}")
print(f"Комментарий: {status_comment}")

if notification_status == STATUS_SENT:
    print(f"Время доставки: {delivery_at:%d.%m.%Y %H:%M}")
elif notification_status == STATUS_DELAYED:
    print(f"Повторная попытка: {delivery_at:%d.%m.%Y %H:%M}")
else:
    print("Доставка не запланирована")
print("=" * 52)
