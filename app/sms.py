import africastalking

from django.conf import settings


# INITIALIZE SDK
africastalking.initialize(
    settings.AFRICASTALKING_USERNAME,
    settings.AFRICASTALKING_API_KEY
)

sms = africastalking.SMS


def send_sms(phone, message):

    try:

        response = sms.send(

            message,

            [phone],

            sender_id=settings.AFRICASTALKING_SENDER_ID
        )

        print("SMS SENT:", response)

        return response

    except Exception as e:

        print("SMS ERROR:", e)

        return None