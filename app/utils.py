from django.core.mail import send_mail
from django.conf import settings

from .models import Notification



from .models import Notification


def create_notification(user, title, message):
    Notification.objects.create(
        user=user,
        title=title,
        message=message
    )

    # EMAIL NOTIFICATION
    if user.email:

        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )

from django.db.models import Max
from datetime import date


def get_order_prefix(user):
    return getattr(user.profile, "order_type", "JWM")
from django.db.models import Max
from datetime import date


def generate_order_id(prefix, OrderModel):
    today = date.today().strftime("%Y%m%d")

    latest = OrderModel.objects.filter(
        order_id__startswith=f"{prefix}-{today}"
    ).aggregate(Max("order_id"))["order_id__max"]

    if latest:
        try:
            last_number = int(latest.split("-")[-1])
        except:
            last_number = 0
        new_number = last_number + 1
    else:
        new_number = 1

    return f"{prefix}-{today}-{new_number:04d}"

# utils.py
import random
from django.core.mail import send_mail

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    send_mail(
        subject="SABBTCo Email Verification OTP",
        message=f"Your OTP code is: {otp}",
        from_email="no-reply@sabbtco.com",
        recipient_list=[email],
        fail_silently=False,
    )