from django.urls import path
from users.apps import UsersConfig
from users.views import (
    RegisterView, VerifyEmailView, UserLoginView, UserLogoutView,
    PasswordRecoveryView, UserListView, UserToggleActiveView
)

app_name = UsersConfig.name

urlpatterns = [
    # Аутентификация и профиль (Задача 7)
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify/<str:token>/", VerifyEmailView.as_view(), name="verify_email"),
    path("recovery/", PasswordRecoveryView.as_view(), name="password_recovery"),

    # Модерация пользователей менеджером (Задача 9)
    path("list/", UserListView.as_view(), name="user_list"),
    path("<int:pk>/toggle/", UserToggleActiveView.as_view(), name="user_toggle"),
]
