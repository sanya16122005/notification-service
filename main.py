"""Сервис управления уведомлениями.

Практическая работа № 1. Начальный сценарий проекта:
проверка возможности доставки одного уведомления пользователю
по выбранному каналу связи и определение его статуса.

Используются только конструкции ПР1: простые типы данных,
операции, преобразование типов, ветвления, импорт модулей.
"""

from datetime import datetime, timedelta

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
is_quiet_time = (current_hour >= quiet_hours_start
                 or current_hour < quiet_hours_end)
is_urgent = notification_priority == 1
is_too_long_for_sms = channel_code == "sms" and text_length > 70

# --- Ветвления: определение статуса уведомления ---------------------
if not user_is_active or not user_subscribed:
    notification_status = "ОТКЛОНЕНО"
    status_comment = "Пользователь неактивен или отписан от рассылки"
elif not channel_is_enabled:
    notification_status = "ОТКЛОНЕНО"
    status_comment = "Канал доставки отключен"
elif limit_left <= 0:
    notification_status = "ОТКЛОНЕНО"
    status_comment = "Исчерпан суточный лимит отправок по каналу"
elif is_too_long_for_sms:
    notification_status = "ОТКЛОНЕНО"
    status_comment = "Текст превышает допустимую длину SMS"
elif is_quiet_time and not is_urgent:
    notification_status = "ОТЛОЖЕНО"
    status_comment = "Отправка запрещена в «тихие часы» пользователя"
else:
    notification_status = "ОТПРАВЛЕНО"
    status_comment = "Уведомление передано в канал доставки"

# --- Расчет времени доставки ---------------------------------------
# Отложенное уведомление отправляется, как только закончатся
# «тихие часы»: вечером - утром следующего дня, ночью - тем же утром.
morning = created_at.replace(hour=quiet_hours_end, minute=0)
if notification_status != "ОТЛОЖЕНО":
    delivery_at = created_at
elif current_hour >= quiet_hours_start:
    delivery_at = morning + timedelta(days=1)
else:
    delivery_at = morning

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
      f" сейчас тихое время: {is_quiet_time}")
print("-" * 52)
print(f"Статус: {notification_status}")
print(f"Комментарий: {status_comment}")

if notification_status == "ОТПРАВЛЕНО":
    print(f"Время доставки: {delivery_at:%d.%m.%Y %H:%M}")
elif notification_status == "ОТЛОЖЕНО":
    print(f"Повторная попытка: {delivery_at:%d.%m.%Y %H:%M}")
else:
    print("Доставка не запланирована")
print("=" * 52)
