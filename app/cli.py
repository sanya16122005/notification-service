"""Консольный интерфейс сервиса управления уведомлениями.

Практическая работа № 3. Приложение построено на объектной модели:
класс ConsoleApp хранит ссылку на сервис NotificationService и
вызывает его методы из пунктов меню. Каждый пункт меню - метод,
обернутый декоратором menu_action, а выбор пункта выполняется по
словарю «номер - (название, метод)».

Сценарий ПР1 сохранен: проверка возможности доставки выполняется
пунктом меню 4 методом DeliveryRules.check().
"""

from collections.abc import Callable
from datetime import datetime

from app import models, utils
from app.decorators import menu_action
from app.models.notification import STATUS_DELAYED
from app.services import delivery, repositories
from app.services.notifications import NotificationService

LINE_WIDTH = utils.LINE_WIDTH


class ConsoleApp:
    """Консольное приложение: меню и вывод результатов."""

    def __init__(self, service: NotificationService) -> None:
        self.service = service
        self._actions: dict[str, tuple[str, Callable[[], bool]]] = {
            "1": ("Показать пользователей", self.show_users),
            "2": ("Показать каналы доставки", self.show_channels),
            "3": ("Показать уведомления", self.show_notifications),
            "4": ("Проверить возможность отправки", self.check_delivery),
            "5": ("Создать уведомление", self.add_notification),
            "6": ("Отменить уведомление", self.remove_notification),
            "7": ("Найти уведомление по тексту", self.search),
            "8": ("Статистика по статусам", self.show_statistics),
            "9": ("Справка о классах проекта", self.show_reference),
            "10": ("Добавить пользователя", self.add_user),
            "11": ("Изменить подписку пользователя",
                   self.toggle_subscription),
        }

    def menu_text(self) -> str:
        """Сформировать текст меню из словаря действий."""
        lines = [f"{number}. {title}"
                 for number, (title, _) in self._actions.items()]
        lines.append("0. Выход")
        return "\n" + "\n".join(lines) + "\n"

    def run(self) -> None:
        """Цикл меню: выбор пункта и вызов соответствующего метода."""
        utils.print_title("СЕРВИС УПРАВЛЕНИЯ УВЕДОМЛЕНИЯМИ")
        choices = set(self._actions) | {"0"}
        while True:
            print(self.menu_text())
            choice = utils.input_choice("Выберите действие: ", choices)
            if choice == "0":
                print("Завершение работы.")
                break
            _, action = self._actions[choice]
            if action():
                self.service.save()

    def _input_user_and_channel(self) -> tuple[int, str]:
        """Запросить идентификатор пользователя и код канала."""
        user_id = utils.input_int("Идентификатор пользователя: ", 1, 999)
        self.service.users.get(user_id)
        channel_code = utils.input_choice(
            "Канал доставки: ", self.service.channels.codes()
        )
        return user_id, channel_code

    @menu_action("ПОЛЬЗОВАТЕЛИ")
    def show_users(self) -> None:
        """Вывести список пользователей."""
        users = self.service.users
        if not len(users):
            print("Список пользователей пуст.")
            return
        for user in users.sorted_by_name():
            subscription = "подписан" if user.subscribed else "отписан"
            state = "активен" if user.is_active else "неактивен"
            print(f"{user.id:>3}. {user}")
            print(f"     {state}, {subscription}, "
                  f"тихие часы {user.quiet_hours_text()}")
        receivers = list(users.receivers())
        print(f"Получают уведомления: {len(receivers)} из {len(users)}")

    @menu_action("КАНАЛЫ ДОСТАВКИ")
    def show_channels(self) -> None:
        """Вывести список каналов доставки."""
        channels = self.service.channels
        if not len(channels):
            print("Список каналов пуст.")
            return
        for channel in channels.sorted_by_load():
            state = "включен" if channel.enabled else "отключен"
            length = channel.max_length
            limit = f"{length} символов" if length else "без ограничения"
            print(f"  {channel} - {state} "
                  f"(класс {type(channel).__name__})")
            print(f"         отправлено {channel.sent_today} из "
                  f"{channel.daily_limit}, остаток "
                  f"{channel.limit_left()}, длина: {limit}")

    @menu_action("УВЕДОМЛЕНИЯ")
    def show_notifications(self) -> None:
        """Вывести уведомления от срочных к обычным."""
        notifications = self.service.notifications
        if not len(notifications):
            print("Уведомлений пока нет.")
            return
        for item in notifications.ordered():
            print(f"{item.id:>3}. {item}")
            print(f"     канал {item.channel_code}, приоритет "
                  f"{item.priority}, создано "
                  f"{utils.format_datetime(item.created_at)}")
            print(f"     {item.comment}")

    @menu_action("ПРОВЕРКА ВОЗМОЖНОСТИ ОТПРАВКИ")
    def check_delivery(self) -> None:
        """Проверить возможность доставки (сценарий ПР1)."""
        user_id, channel_code = self._input_user_and_channel()
        subject = utils.input_text("Тема: ")
        text = utils.input_text("Текст уведомления: ")
        priority = utils.input_int("Приоритет (1-3): ", 1, 3)
        created = utils.input_datetime("Дата и время (ДД.ММ.ГГГГ ЧЧ:ММ): ")

        result = self.service.check_delivery(
            user_id, channel_code, text, priority, created
        )
        user = self.service.users.get(user_id)
        channel = self.service.channels.get(channel_code)
        print("-" * LINE_WIDTH)
        print(f"Получатель: {user}")
        print(f"Канал: {channel}, остаток лимита: {channel.limit_left()}")
        print(f"Длина текста: {len(text)}, приоритет: {priority}")
        print(f"Тихое время: {result.quiet_time}")
        print(f"Статус: {result.status}")
        print(f"Комментарий: {result.comment}")
        if result.is_rejected:
            print("Доставка не запланирована")
            return
        moment = utils.format_datetime(result.delivery_at)
        print(f"Время доставки: {moment}")
        print("Сообщение в канале:")
        print(channel.format_message(subject, text))

    @menu_action("СОЗДАНИЕ УВЕДОМЛЕНИЯ")
    def add_notification(self) -> bool:
        """Создать уведомление по введенным данным."""
        user_id, channel_code = self._input_user_and_channel()
        subject = utils.input_text("Тема: ")
        text = utils.input_text("Текст: ")
        priority = utils.input_int("Приоритет (1-3): ", 1, 3)
        notification = self.service.create_notification(
            user_id, channel_code, subject, text, priority, datetime.now()
        )
        print(f"Создано уведомление №{notification.id}: "
              f"{notification.status} - {notification.comment}")
        if not notification.is_sent:
            return True
        print("Сообщение в канале:")
        print(self.service.preview(notification))
        return True

    @menu_action("ОТМЕНА УВЕДОМЛЕНИЯ")
    def remove_notification(self) -> bool:
        """Отменить уведомление по идентификатору."""
        if not len(self.service.notifications):
            print("Отменять нечего: список уведомлений пуст.")
            return False
        notification = self.service.cancel_notification(
            utils.input_int("Идентификатор уведомления: ", 1, 9999)
        )
        print(f"Уведомление №{notification.id} отменено.")
        return True

    @menu_action("ПОИСК УВЕДОМЛЕНИЙ")
    def search(self) -> None:
        """Найти уведомления по подстроке темы или текста."""
        query = utils.input_text("Строка поиска: ")
        found = self.service.notifications.find(query)
        if not found:
            print("Ничего не найдено.")
            return
        for item in found:
            print(f"{item.id:>3}. {item}")

    @menu_action("СТАТИСТИКА")
    def show_statistics(self) -> None:
        """Вывести статистику по статусам уведомлений."""
        total = len(self.service.notifications)
        if not total:
            print("Данных для статистики пока нет.")
            return
        for status, count in self.service.statistics().items():
            share = round(count / total * 100, 1)
            print(f"  {status:<12} {count:>3} ({share}%)")
        delayed = list(self.service.notifications.by_status(STATUS_DELAYED))
        print(f"Всего уведомлений: {total}, ожидают отправки: {len(delayed)}")

    @menu_action("КЛАССЫ ПРОЕКТА")
    def show_reference(self) -> None:
        """Вывести справку о классах проекта (интроспекция)."""
        classes = (
            models.User, models.Channel, models.EmailChannel,
            models.SmsChannel, models.PushChannel, models.Notification,
            repositories.UserRepository, delivery.DeliveryRules,
            NotificationService,
        )
        for cls in classes:
            print(f"--- {utils.class_hierarchy(cls)} ---")
            for description in utils.describe_class(cls):
                print(f"  {description}")

    @menu_action("НОВЫЙ ПОЛЬЗОВАТЕЛЬ")
    def add_user(self) -> bool:
        """Добавить пользователя."""
        name = utils.input_text("Имя: ")
        contact = utils.input_text("Контакт (e-mail или телефон): ")
        quiet_start = utils.input_int("Начало тихих часов (0-23): ", 0, 23)
        quiet_end = utils.input_int("Конец тихих часов (0-23): ", 0, 23)
        user = self.service.users.create(name, contact, quiet_start,
                                         quiet_end)
        print(f"Добавлен пользователь №{user.id}: {user}")
        return True

    @menu_action("ПОДПИСКА ПОЛЬЗОВАТЕЛЯ")
    def toggle_subscription(self) -> bool:
        """Включить или отключить подписку пользователя."""
        user_id = utils.input_int("Идентификатор пользователя: ", 1, 999)
        subscribed = self.service.toggle_subscription(user_id)
        state = "подписан на рассылку" if subscribed else "отписан"
        print(f"Пользователь №{user_id} {state}.")
        return True


def main() -> None:
    """Точка запуска: загрузка данных и запуск меню."""
    app = ConsoleApp(NotificationService.from_files())
    app.run()
