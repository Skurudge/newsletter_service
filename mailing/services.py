import smtplib
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from mailing.models import Mailing, MailingAttempt


def send_mailing_requirements(mailing_id):
    """
    Функция отправки рассылки по требованию (Задача 4).
    Проверяет время действия, собирает клиентов и выполняет отправку с фиксацией истории.
    """
    # Загружаем рассылку из базы данных
    try:
        mailing = Mailing.objects.get(pk=mailing_id)
    except Mailing.DoesNotExist:
        return "Ошибка: Рассылка не найдена."

    # Обновляем динамический статус перед отправкой
    mailing.update_status()

    # Инициация. Проверяем, разрешена ли отправка согласно ТЗ
    now = timezone.now()
    if not mailing.is_active:
        return "Ошибка: Рассылка отключена менеджером или администратором."
    if not (mailing.start_time <= now <= mailing.end_time):
        return "Ошибка: Текущее время находится вне диапазона действия рассылки."

    # Определение получателей
    recipients = mailing.recipients.all()
    if not recipients.exists():
        return "Ошибка: У рассылки нет получателей."

    # Отправка писем каждому клиенту
    success_count = 0
    fail_count = 0

    for client in recipients:
        try:
            # Выполняем отправку через стандартный send_mail
            send_mail(
                subject=mailing.message.title,
                message=mailing.message.body,
                from_email=getattr(settings, "EMAIL_HOST_USER", "noreply@newsletter.local"),
                recipient_list=[client.email],
                fail_silently=False,
            )

            # В случае успеха создаем запись о попытке
            MailingAttempt.objects.create(
                status=MailingAttempt.STATUS_SUCCESS,
                server_response="Письмо успешно отправлено и принято почтовым сервером.",
                mailing=mailing
            )
            success_count += 1

        except (smtplib.SMTPException, Exception) as e:
            # При ошибке создаем запись со статусом 'Не успешно' и текстом ошибки
            MailingAttempt.objects.create(
                status=MailingAttempt.STATUS_FAILED,
                server_response=f"Ошибка отправки: {str(e)}",
                mailing=mailing
            )
            fail_count += 1

    return f"Рассылка завершена. Успешно отправлено: {success_count}, ошибок: {fail_count}."
