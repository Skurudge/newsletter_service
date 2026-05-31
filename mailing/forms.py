from django import forms
from mailing.models import Client, Message, Mailing


class StyleFormMixin:
    """Миксин для автоматической стилизации полей под Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class ClientForm(StyleFormMixin, forms.ModelForm):
    """Форма управления получателями (Задача 1)."""

    class Meta:
        model = Client
        fields = ('email', 'full_name', 'comment')


class MessageForm(StyleFormMixin, forms.ModelForm):
    """Форма управления сообщениями (Задача 2)."""

    class Meta:
        model = Message
        fields = ('title', 'body')


class MailingForm(StyleFormMixin, forms.ModelForm):
    """Форма управления рассылками для обычного пользователя (Задача 3)."""

    class Meta:
        model = Mailing
        fields = ('start_time', 'end_time', 'message', 'recipients')
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'recipients': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Безопасное получение полей, чтобы убрать жёлтый цвет в PyCharm
        if user and not user.is_superuser:
            message_field = self.fields.get('message')
            if message_field:
                message_field.queryset = Message.objects.filter(owner=user)

            recipients_field = self.fields.get('recipients')
            if recipients_field:
                recipients_field.queryset = Client.objects.filter(owner=user)


class ManagerMailingForm(StyleFormMixin, forms.ModelForm):
    """Форма для Менеджера, позволяющая только отключать рассылку (Задача 9)."""

    class Meta:
        model = Mailing
        fields = ('is_active',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                field.disabled = True
