"""Сервис управления уведомлениями. Точка запуска приложения.

Практическая работа № 2. Консольное приложение ведет учет
пользователей, каналов доставки и уведомлений: проверяет правила
отправки, создает и отменяет уведомления, ищет их и считает
статистику. Данные хранятся в JSON-файлах каталога data/.

Начальный сценарий ПР1 сохранен: проверка возможности доставки
выполняется пунктом меню 4 функциями модуля notifications.
"""

from datetime import datetime

import channels
import notifications as notify
import storage
import users
import utils

LINE_WIDTH = 60
MENU_CHOICES = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}

MENU_TEXT = """
1. Показать пользователей
2. Показать каналы доставки
3. Показать уведомления
4. Проверить возможность отправки
5. Создать уведомление
6. Отменить уведомление
7. Найти уведомление по тексту
8. Статистика по статусам
9. Справка о функциях проекта
0. Выход
"""


def print_title(title: str) -> None:
    """Вывести заголовок раздела."""
    print("=" * LINE_WIDTH)
    print(title)
    print("=" * LINE_WIDTH)


def show_users(user_list: list[dict]) -> None:
    """Вывести список пользователей таблицей."""
    print_title("ПОЛЬЗОВАТЕЛИ")
    if not user_list:
        print("Список пользователей пуст.")
        return
    for user in users.sort_users(user_list):
        subscription = "подписан" if user["subscribed"] else "отписан"
        state = "активен" if user["is_active"] else "неактивен"
        print(f"{user['id']:>3}. {user['name']} ({user['contact']})")
        print(f"     {state}, {subscription}, тихие часы "
              f"{user['quiet_start']}:00-{user['quiet_end']}:00")
    subscribed = list(users.subscribed_users(user_list))
    print(f"Получают уведомления: {len(subscribed)} из {len(user_list)}")


def show_channels(channel_list: list[dict]) -> None:
    """Вывести список каналов доставки таблицей."""
    print_title("КАНАЛЫ ДОСТАВКИ")
    if not channel_list:
        print("Список каналов пуст.")
        return
    for channel in channels.sort_channels_by_load(channel_list):
        state = "включен" if channel["enabled"] else "отключен"
        length = channel["max_length"]
        limit = "без ограничения" if not length else f"{length} символов"
        print(f"  {channel['code']:<6} {channel['title']} - {state}")
        print(f"         отправлено {channel['sent_today']} из "
              f"{channel['daily_limit']}, остаток "
              f"{channels.limit_left(channel)}, длина: {limit}")


def show_notifications(notification_list: list[dict]) -> None:
    """Вывести список уведомлений с указанием статуса."""
    print_title("УВЕДОМЛЕНИЯ")
    if not notification_list:
        print("Уведомлений пока нет.")
        return
    for item in notify.sort_notifications(notification_list):
        print(f"{item['id']:>3}. [{item['status']}] {item['subject']}")
        print(f"     канал {item['channel']}, приоритет "
              f"{item['priority']}, создано {item['created_at']}")
        print(f"     {item['comment']}")


def show_delivery_check(
    user_list: list[dict],
    channel_list: list[dict],
) -> None:
    """Проверить возможность доставки уведомления.

    Сценарий из ПР1: по выбранному пользователю, каналу и тексту
    определяется статус уведомления без его сохранения.
    """
    print_title("ПРОВЕРКА ВОЗМОЖНОСТИ ОТПРАВКИ")
    try:
        user = users.get_user(
            user_list, utils.input_int("Идентификатор пользователя: ", 1, 999)
        )
        channel = channels.get_channel(
            channel_list,
            utils.input_choice(
                "Канал доставки: ", channels.channel_codes(channel_list)
            ),
        )
    except KeyError as error:
        print(f"Ошибка: {utils.error_text(error)}")
        return
    text = utils.input_text("Текст уведомления: ")
    priority = utils.input_int("Приоритет (1-3): ", 1, 3)
    created = utils.input_datetime("Дата и время (ДД.ММ.ГГГГ ЧЧ:ММ): ")

    result = notify.check_delivery(user, channel, text, priority, created)
    print("-" * LINE_WIDTH)
    print(f"Получатель: {user['name']} ({user['contact']})")
    print(f"Канал: {channel['code']}, остаток лимита: "
          f"{channels.limit_left(channel)}")
    print(f"Длина текста: {len(text)}, приоритет: {priority}")
    print(f"Тихое время: {result['quiet_time']}")
    print(f"Статус: {result['status']}")
    print(f"Комментарий: {result['comment']}")
    if result["status"] != notify.STATUS_REJECTED:
        moment = utils.format_datetime(result["delivery_at"])
        print(f"Время доставки: {moment}")
    else:
        print("Доставка не запланирована")


def add_notification(
    notification_list: list[dict],
    user_list: list[dict],
    channel_list: list[dict],
) -> bool:
    """Создать уведомление по данным, введенным пользователем.

    Возвращает True, если уведомление создано и данные нужно
    сохранить.
    """
    print_title("СОЗДАНИЕ УВЕДОМЛЕНИЯ")
    try:
        user = users.get_user(
            user_list, utils.input_int("Идентификатор пользователя: ", 1, 999)
        )
        channel = channels.get_channel(
            channel_list,
            utils.input_choice(
                "Канал доставки: ", channels.channel_codes(channel_list)
            ),
        )
        subject = utils.input_text("Тема: ")
        text = utils.input_text("Текст: ")
        priority = utils.input_int("Приоритет (1-3): ", 1, 3)
        notification = notify.create_notification(
            notification_list, user, channel, subject, text,
            priority, datetime.now(),
        )
    except (KeyError, ValueError) as error:
        print(f"Уведомление не создано: {utils.error_text(error)}")
        return False
    print(f"Создано уведомление №{notification['id']}: "
          f"{notification['status']} - {notification['comment']}")
    return True


def remove_notification(notification_list: list[dict]) -> bool:
    """Отменить уведомление по идентификатору."""
    print_title("ОТМЕНА УВЕДОМЛЕНИЯ")
    if not notification_list:
        print("Отменять нечего: список уведомлений пуст.")
        return False
    try:
        notification = notify.cancel_notification(
            notification_list,
            utils.input_int("Идентификатор уведомления: ", 1, 9999),
        )
    except (KeyError, ValueError) as error:
        print(f"Отмена не выполнена: {utils.error_text(error)}")
        return False
    print(f"Уведомление №{notification['id']} отменено.")
    return True


def search_notifications(notification_list: list[dict]) -> None:
    """Найти уведомления по подстроке темы или текста."""
    print_title("ПОИСК УВЕДОМЛЕНИЙ")
    query = utils.input_text("Строка поиска: ")
    found = notify.find_notifications(notification_list, query)
    if not found:
        print("Ничего не найдено.")
        return
    for item in found:
        print(f"{item['id']:>3}. [{item['status']}] {item['subject']}")


def show_statistics(notification_list: list[dict]) -> None:
    """Вывести статистику по статусам уведомлений."""
    print_title("СТАТИСТИКА")
    total = len(notification_list)
    if not total:
        print("Данных для статистики пока нет.")
        return
    statistics = notify.count_by_status(notification_list)
    for status, count in statistics.items():
        share = round(count / total * 100, 1)
        print(f"  {status:<12} {count:>3} ({share}%)")
    delayed = list(
        notify.notifications_by_status(
            notification_list, notify.STATUS_DELAYED
        )
    )
    print(f"Всего уведомлений: {total}, ожидают отправки: {len(delayed)}")


def show_reference() -> None:
    """Вывести справку о функциях проекта (интроспекция)."""
    print_title("ФУНКЦИИ ПРОЕКТА")
    for module in (users, channels, notify, storage, utils):
        print(f"--- {module.__name__}.py ---")
        for description in utils.describe_module(module):
            print(f"  {description}")


def main() -> None:
    """Точка запуска приложения: цикл меню и вызов функций."""
    user_list = storage.load_users()
    channel_list = storage.load_channels()
    notification_list = storage.load_notifications()

    print_title("СЕРВИС УПРАВЛЕНИЯ УВЕДОМЛЕНИЯМИ")
    while True:
        print(MENU_TEXT)
        choice = utils.input_choice("Выберите действие: ", MENU_CHOICES)
        if choice == "0":
            print("Завершение работы.")
            break
        if choice == "1":
            show_users(user_list)
        elif choice == "2":
            show_channels(channel_list)
        elif choice == "3":
            show_notifications(notification_list)
        elif choice == "4":
            show_delivery_check(user_list, channel_list)
        elif choice == "5":
            if add_notification(notification_list, user_list, channel_list):
                storage.save_notifications(notification_list)
                storage.save_channels(channel_list)
        elif choice == "6":
            if remove_notification(notification_list):
                storage.save_notifications(notification_list)
        elif choice == "7":
            search_notifications(notification_list)
        elif choice == "8":
            show_statistics(notification_list)
        elif choice == "9":
            show_reference()


if __name__ == "__main__":
    main()
