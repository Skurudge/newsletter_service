from django.urls import path
from mailing.apps import MailingConfig
from mailing.views import (
    MailingHomeView,
    ClientListView, ClientDetailView, ClientCreateView, ClientUpdateView, ClientDeleteView,
    MessageListView, MessageDetailView, MessageCreateView, MessageUpdateView, MessageDeleteView,
    MailingListView, MailingDetailView, MailingCreateView, MailingUpdateView, MailingDeleteView,
    MailingRunView, MailingAttemptListView
)

app_name = MailingConfig.name

urlpatterns = [
    # Главная страница (Задачи 6, 8, 10)
    path("", MailingHomeView.as_view(), name="home"),

    # Получатели (Задача 1)
    path("clients/", ClientListView.as_view(), name="client_list"),
    path("clients/<int:pk>/", ClientDetailView.as_view(), name="client_detail"),
    path("clients/create/", ClientCreateView.as_view(), name="client_create"),
    path("clients/<int:pk>/update/", ClientUpdateView.as_view(), name="client_update"),
    path("clients/<int:pk>/delete/", ClientDeleteView.as_view(), name="client_delete"),

    # Сообщения (Задача 2)
    path("messages/", MessageListView.as_view(), name="message_list"),
    path("messages/<int:pk>/", MessageDetailView.as_view(), name="message_detail"),
    path("messages/create/", MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/update/", MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="message_delete"),

    # Рассылки (Задачи 3, 9)
    path("mailings/", MailingListView.as_view(), name="mailing_list"),
    path("mailings/<int:pk>/", MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/create/", MailingCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/update/", MailingUpdateView.as_view(), name="mailing_update"),
    path("mailings/<int:pk>/delete/", MailingDeleteView.as_view(), name="mailing_delete"),

    # Ручной запуск (Задача 4)
    path("mailings/<int:pk>/run/", MailingRunView.as_view(), name="mailing_run"),

    # История попыток (Задачи 5, 8)
    path("attempts/", MailingAttemptListView.as_view(), name="attempt_list"),
]
