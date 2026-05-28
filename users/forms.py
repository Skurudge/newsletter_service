from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from users.models import User


class StyleFormMixin:
    """Миксин для автоматической стилизации полей под Bootstrap."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class UserRegisterForm(StyleFormMixin, UserCreationForm):
    """Форма регистрации нового пользователя по email (Задача 7)."""
    class Meta:
        model = User
        fields = ("email",)


class UserLoginForm(AuthenticationForm):
    """Форма авторизации по email (Задача 7)."""
    username = forms.EmailField(
        label="Электронная почта",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "email@example.com"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class PasswordRecoveryForm(forms.Form):
    """Форма восстановления пароля (Задача 7)."""
    email = forms.EmailField(
        label="Укажите email вашей учетной записи",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@example.com"})
    )


class ManagerUserForm(StyleFormMixin, forms.ModelForm):
    """Форма менеджера для блокировки/разблокировки пользователей (Задача 9)."""
    class Meta:
        model = User
        fields = ("is_active",)
