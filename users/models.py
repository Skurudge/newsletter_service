import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя для сервиса рассылок (Задача 7)."""

    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Имя пользователя"
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта"
    )

    # Поля для верификации почты (Задача 7)
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Почта верифицирована"
    )
    verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Токен верификации"
    )

    # Меняем основное поле авторизации на email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        # Права доступа для Менеджера создадутся автоматически,
        # но мы можем добавить кастомное право для блокировки, если потребуется.
        permissions = [
            ("can_view_users", "Может просматривать список пользователей"),
            ("can_block_users", "Может блокировать пользователей"),
        ]

    def __str__(self):
        return self.email

    def generate_verification_token(self):
        """Генерация уникального токена для подтверждения email."""
        self.verification_token = str(uuid.uuid4())
        self.save()
        return self.verification_token
