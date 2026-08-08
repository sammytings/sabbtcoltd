from django.core.mail import send_mail
from django.conf import settings
from app.models import Notification, ClientNotification


def notify_user(user, title, message):
    ClientNotification.objects.create(
        user=user,
        title=title,
        message=message
    )

    # EMAIL (user)
    if user.email:
        send_mail(
            title,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=True
        )


def notify_admins(title, message):
    from django.contrib.auth.models import User

    admins = User.objects.filter(is_staff=True)

    for admin in admins:
        Notification.objects.create(
            user=admin,
            title=title,
            message=message
        )

        if admin.email:
            send_mail(
                title,
                message,
                settings.EMAIL_HOST_USER,
                [admin.email],
                fail_silently=True
            )