# app/notifications.py
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
from django.conf import settings

def send_native_sms(phone_number, message_text):
    """Sends a standard SMS using Africa's Talking API without external dependencies."""
    username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
    api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')
    url = "https://api.africastalking.com/version1/messaging" 
    if username == "sandbox":
        url = "https://api.sandbox.africastalking.com/version1/messaging"


    data = urllib.parse.urlencode({
        'username': username,
        'to': phone_number,
        'message': message_text
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apiKey': api_key
        },
        method='POST'
    )

    try:
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=15, context=ssl_context) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"SMS Gateway Send Failed: {str(e)}")
        return None
    
# app/notifications.py
import requests
import logging
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_whatsapp_alert(phone_number, client_name, order_id, status_display, container_number, tracking_number):
    """
    Sends an automated, rich WhatsApp notification using Twilio's WhatsApp Business API gateway.
    """
    # Fallback/Safety Check for missing environment credentials
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_whatsapp = getattr(settings, 'TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886') # Twilio Sandbox Number
    
    if not account_sid or not auth_token:
        logger.warning(f"[WhatsApp Mock Log] Credentials missing. Target: {phone_number} | Order: {order_id} is {status_display}")
        return False

    try:
        client = Client(account_sid, auth_token)
        
        # Crafting a clean, scannable customer update template
        message_body = (
            f"🔔 *SABBTCo Shipment Update* 🔔\n\n"
            f"Hello {client_name},\n"
            f"The status of your order *#{order_id}* has been updated!\n\n"
            f"📦 *Current Status:* {status_display}\n"
            f"🚢 *Container Ref:* {container_number}\n"
            f"📑 *Waybill / Tracking:* {tracking_number if tracking_number else 'Pending'}\n\n"
            f"Track your parcel live anytime in your Client Portal. Thank you for choosing Shenzhen Autumn Breeze!"
        )

        message = client.messages.create(
            body=message_body,
            from_=from_whatsapp,
            to=f"whatsapp:{phone_number}"
        )
        logger.info(f"WhatsApp notification dispatched to {phone_number}. SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch WhatsApp message: {str(e)}")
        return False


def send_bulk_sms_alert(phone_number, message_text):
    """
    Dispatches a lightning-fast bulk SMS text message via standard HTTP REST API endpoints.
    Compatible with local gateways (Africa's Talking, Advanta, Mobitech, etc.)
    """
    api_url = getattr(settings, 'SMS_GATEWAY_URL', None)
    api_key = getattr(settings, 'SMS_API_KEY', None)
    sender_id = getattr(settings, 'SMS_SENDER_ID', 'SABBTCo')

    if not api_url or not api_key:
        # Standard local print log fallback if keys aren't active yet
        print(f"[SMS Bulk Fallback Log] To {phone_number}: {message_text}")
        return True

    # Example payload configuration typical of local bulk SMS aggregators
    payload = {
        'api_key': api_key,
        'username': getattr(settings, 'SMS_USERNAME', 'sabbtco'),
        'sender_id': sender_id,
        'message': message_text,
        'phone': phone_number
    }

    try:
        response = requests.post(api_url, json=payload, timeout=10)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Bulk SMS network dispatch error: {str(e)}")
        return False