from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import PermissionDenied

from mailing.models import Client, Message, Mailing, MailingAttempt
from mailing.forms import ClientForm, MessageForm, MailingForm, ManagerMailingForm
from mailing.services import send_mailing_requirements


class MailingHomeView(TemplateView):
    """Главная страница приложения со статистикой и кэшированием (Задачи 6, 8, 10)."""
    template_name = "mailing/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Задача 10: Кэшируем общую статистику в Redis на 15 минут (900 секунд)
        cache_key = "mailing_home_statistics"
        stats = cache.get(cache_key)

        if stats is None:
            mailings_count = Mailing.objects.count()
            active_mailings_count = Mailing.objects.filter(status=Mailing.STATUS_STARTED, is_active=True).count()
            unique_clients_count = Client.objects.count()

            stats = {
                "mailings_count": mailings_count,
                "active_mailings_count": active_mailings_count,
                "unique_clients_count": unique_clients_count,
            }
            cache.set(cache_key, stats, timeout=900)

        context.update(stats)
        return context


# ==================== CRUD ДЛЯ КЛИЕНТОВ (Задача 1) ====================

class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "mailing/client_list.html"
    context_object_name = "clients"

    def get_queryset(self):
        """Пользователи видят своих клиентов, Менеджеры — всех (Задача 9)."""
        user = self.request.user
        if user.is_superuser or user.groups.filter(name="Менеджер").exists() or user.has_perm("mailing.view_client"):
            return Client.objects.all()
        return Client.objects.filter(owner=user)


class ClientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Client
    template_name = "mailing/client_detail.html"

    def test_func(self):
        user = self.request.user
        client = self.get_object()
        return client.owner == user or user.is_superuser or user.groups.filter(name="Менеджер").exists()


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def test_func(self):
        """Менеджер не может редактировать чужие данные (Задача 9)."""
        return self.get_object().owner == self.request.user or self.request.user.is_superuser


class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Client
    template_name = "mailing/client_confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")

    def test_func(self):
        return self.get_object().owner == self.request.user or self.request.user.is_superuser


# ==================== CRUD ДЛЯ СООБЩЕНИЙ (Задача 2) ====================

class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name="Менеджер").exists():
            return Message.objects.all()
        return Message.objects.filter(owner=user)


class MessageDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Message
    template_name = "mailing/message_detail.html"

    def test_func(self):
        user = self.request.user
        return self.get_object().owner == user or user.is_superuser or user.groups.filter(name="Менеджер").exists()


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def test_func(self):
        return self.get_object().owner == self.request.user or self.request.user.is_superuser


class MessageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")

    def test_func(self):
        return self.get_object().owner == self.request.user or self.request.user.is_superuser


# ==================== CRUD ДЛЯ РАССЫЛОК (Задача 3, 9) ====================

class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name="Менеджер").exists() or user.has_perm("mailing.view_mailing"):
            return Mailing.objects.all()
        return Mailing.objects.filter(owner=user)


class MailingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"

    def get_object(self, queryset=None):
        """Динамический пересчет статуса рассылки при просмотре карточки (Задача 3)."""
        obj = super().get_object(queryset)
        obj.update_status()
        return obj

    def test_func(self):
        user = self.request.user
        return self.get_object().owner == user or user.is_superuser or user.groups.filter(name="Менеджер").exists()


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Mailing
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_class(self):
        """Менеджер использует форму отключения, Владелец — полную форму (Задача 9)."""
        user = self.request.user
        if user.groups.filter(name="Менеджер").exists() and not user.is_superuser:
            return ManagerMailingForm
        return MailingForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.get_form_class() == MailingForm:
            kwargs["user"] = self.request.user
        return kwargs

    def test_func(self):
        user = self.request.user
        mailing = self.get_object()
        # Менеджер может отключать рассылки (редактировать поле is_active) (Задача 9)
        if user.has_perm("mailing.can_deactivate_mailing") or user.groups.filter(name="Менеджер").exists():
            return True
        return mailing.owner == user or user.is_superuser


class MailingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def test_func(self):
        """Менеджеры не имеют права удалять чужие рассылки (Задача 9)."""
        return self.get_object().owner == self.request.user or self.request.user.is_superuser


# ==================== ЗАПУСК РАССЫЛКИ ПО ТРЕБОВАНИЮ (Задача 4) ====================

class MailingRunView(LoginRequiredMixin, View):
    """Контроллер ручного запуска отправки писем через интерфейс."""

    def post(self, request, pk, *args, **kwargs):
        mailing = get_object_or_404(Mailing, pk=pk)

        # Проверка владения перед запуском
        if mailing.owner != request.user and not request.user.is_superuser:
            raise PermissionDenied("Вы не можете запускать чужую рассылку.")

        # Вызываем сервисную логику отправки
        result_message = send_mailing_requirements(mailing.pk)

        if "Ошибка" in result_message:
            messages.error(request, result_message)
        else:
            messages.success(request, result_message)

        return redirect("mailing:mailing_detail", pk=mailing.pk)


# ==================== СТАТИСТИКА ПОПЫТОК (Задача 5, 8) ====================

class MailingAttemptListView(LoginRequiredMixin, ListView):
    """Отображение истории и статистики попыток отправки сообщений."""
    model = MailingAttempt
    template_name = "mailing/attempt_list.html"
    context_object_name = "attempts"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name="Менеджер").exists():
            return MailingAttempt.objects.all().order_by("-attempt_time")
        return MailingAttempt.objects.filter(mailing__owner=user).order_by("-attempt_time")
