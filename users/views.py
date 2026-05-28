import random
import string
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, ListView, FormView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from users.models import User
from users.forms import UserRegisterForm, UserLoginForm, PasswordRecoveryForm, ManagerUserForm


class RegisterView(CreateView):
    """Регистрация пользователя с генерацией токена верификации (Задача 7)."""
    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_verified = False  # Почта изначально не подтверждена
        user.generate_verification_token()

        # Ссылка для подтверждения email
        verify_url = self.request.build_absolute_uri(
            reverse("users:verify_email", kwargs={"token": user.verification_token})
        )

        # Отправка приветственного письма с верификацией
        send_mail(
            subject="Подтверждение регистрации в сервисе рассылок",
            message=(
                f"Здравствуйте!\n\n"
                f"Для подтверждения вашей учетной записи перейдите по следующей ссылке:\n"
                f"{verify_url}\n\n"
                f"С уважением, Команда сервиса рассылок"
            ),
            from_email=getattr(settings, "EMAIL_HOST_USER", "noreply@newsletter.local"),
            recipient_list=[user.email],
            fail_silently=True,
        )

        messages.success(self.request, "Регистрация успешна! Ссылка для подтверждения отправлена на ваш email.")
        return super().form_valid(form)


class VerifyEmailView(TemplateView):
    """Контроллер верификации почты по токену из письма (Задача 7)."""
    template_name = "users/verification_result.html"

    def get(self, request, *args, **kwargs):
        token = kwargs.get("token")
        user = get_object_or_404(User, verification_token=token)

        user.is_verified = True
        user.verification_token = None  # Сбрасываем токен после использования
        user.save()

        return super().get(request, *args, **kwargs)


class UserLoginView(LoginView):
    """Авторизация по email с проверкой верификации учетной записи (Задача 7)."""
    form_class = UserLoginForm
    template_name = "users/login.html"

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_verified and not user.is_superuser:
            messages.error(self.request, "Ваша электронная почта еще не подтверждена. Проверьте ваш почтовый ящик.")
            return redirect("users:login")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    """Выход из учетной записи."""
    next_page = reverse_lazy("mailing:home")


class PasswordRecoveryView(FormView):
    """Сброс и восстановление случайного пароля (Задача 7)."""
    form_class = PasswordRecoveryForm
    template_name = "users/password_recovery.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            # Генерация случайного пароля длиной 12 символов
            characters = string.ascii_letters + string.digits
            new_password = "".join(random.choice(characters) for _ in range(12))

            user.set_password(new_password)
            user.save()

            # Отправка нового пароля на почту
            send_mail(
                subject="Восстановление доступа к сервису рассылок",
                message=(
                    f"Здравствуйте!\n\n"
                    f"Ваш пароль был успешно сброшен.\n"
                    f"Новый пароль для входа: {new_password}\n\n"
                    f"Рекомендуем изменить его сразу после успешной авторизации."
                ),
                from_email=getattr(settings, "EMAIL_HOST_USER", "noreply@newsletter.local"),
                recipient_list=[user.email],
                fail_silently=True,
            )
            messages.success(self.request, "Новый пароль успешно отправлен на вашу электронную почту.")
        else:
            messages.error(self.request, "Пользователь с таким email не найден в системе.")
            return redirect("users:password_recovery")

        return super().form_valid(form)


# ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ДЛЯ МЕНЕДЖЕРА (Задача 9) ====================

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Просмотр списка пользователей сервиса менеджером (Задача 9)."""
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users_list"

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name="Менеджер").exists() or user.has_perm(
            "users.can_view_users")


class UserToggleActiveView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Блокировка/разблокировка пользователей сервиса менеджером (Задача 9)."""
    model = User
    form_class = ManagerUserForm
    template_name = "users/user_toggle.html"
    success_url = reverse_lazy("users:user_list")

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name="Менеджер").exists() or user.has_perm(
            "users.can_block_users")

    def form_valid(self, form):
        user = self.get_object()
        # Предотвращаем самоблокировку администратора
        if user.is_superuser:
            messages.error(self.request, "Невозможно заблокировать суперпользователя системы.")
            return redirect("users:user_list")

        response = super().form_valid(form)
        status_text = "активирован" if form.instance.is_active else "заблокирован"
        messages.success(self.request, f"Пользователь {user.email} успешно {status_text}.")
        return response
