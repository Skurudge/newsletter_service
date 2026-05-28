from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class Client(models.Model):
    """Модель получателя рассылки (Задача 1)."""
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=150, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")

    # Привязка к владельцу для Задачи 9
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        related_name="clients"
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    """Модель сообщения для рассылки (Задача 2)."""
    title = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        related_name="messages"
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self):
        return self.title


class Mailing(models.Model):
    """Модель рассылки (Задача 3)."""

    STATUS_CREATED = "Создана"
    STATUS_STARTED = "Запущена"
    STATUS_FINISHED = "Завершена"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_STARTED, "Запущена"),
        (STATUS_FINISHED, "Завершена"),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время начала отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="Статус рассылки"
    )

    message = models.ForeignKey(
        Message,
        on_delete=models.PROTECT,
        verbose_name="Сообщение",
        related_name="mailings"
    )
    recipients = models.ManyToManyField(
        Client,
        verbose_name="Получатели",
        related_name="mailings"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        related_name="mailings"
    )

    # Новое поле из Задачи 9 для Менеджера (Отключение рассылки)
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        permissions = [
            ("can_deactivate_mailing", "Может отключать рассылки"),
        ]

    def __str__(self):
        return f"Рассылка #{self.pk} (Статус: {self.status})"

    def clean(self):
        """Валидация дат согласно ТЗ (Задача 3)."""
        super().clean()

        # Если объект создается впервые, проверяем, чтобы старт не был в прошлом
        if not self.pk and self.start_time and self.start_time < timezone.now():
            raise ValidationError({"start_time": "Дата начала не может быть в прошлом."})

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "Дата окончания должна быть строго позже даты начала."})

    def update_status(self):
        """Динамический пересчет статуса рассылки согласно ТЗ (Задача 3)."""
        now = timezone.now()
        new_status = self.status

        if not self.is_active:
            new_status = self.STATUS_FINISHED
        elif now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_STARTED
        elif now > self.end_time:
            new_status = self.STATUS_FINISHED

        if self.status != new_status:
            self.status = new_status
            # Используем update_fields, чтобы обновить только статус без циклической валидации
            Mailing.objects.filter(pk=self.pk).update(status=new_status)


class MailingAttempt(models.Model):
    """Модель попытки рассылки (Задача 5)."""

    STATUS_SUCCESS = "Успешно"
    STATUS_FAILED = "Не успешно"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(blank=True, null=True, verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        verbose_name="Рассылка",
        related_name="attempts"
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"

    def __str__(self):
        return f"Попытка для Рассылки #{self.mailing.pk} ({self.status}) от {self.attempt_time}"
