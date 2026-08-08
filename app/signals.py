from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User

from .models import Order, Shipment, SupplierPaymentRequest, ClientNotification, Notification
from .notifications import send_native_sms


# ========================================================
# TRACK STATUS CHANGES BEFORE WRITING TO THE DATABASE
# ========================================================
@receiver(pre_save, sender=Order)
def track_order_status_before_save(sender, instance, **kwargs):
    """
    Caches the status value currently stored on disk right before 
    the model updates, allowing us to compare if it actually changed.
    """
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# ========================================================
# 1. UNIFIED ORDER SIGNAL (HANDLES CREATION & ADMIN UPDATES)
# ========================================================
@receiver(post_save, sender=Order)
def order_changed_signal(sender, instance, created, **kwargs):
    order_ref = instance.order_id or f"SBT-{instance.id}"
    
    if created:
        # ----------------------------------------------------
        # ACTION A: NEW ORDER PLACED BY CLIENT
        # ----------------------------------------------------
        try:
            subject = f"SABBTCo Order Confirmed: {order_ref}"
            context = {
                "name": instance.full_name,
                "order_id": order_ref,
                "product": instance.product_name,
                "quantity": instance.quantity,
                "total": instance.total_amount,
            }
            
            try:
                html_message = render_to_string("emails/order_confirmation.html", context)
            except Exception:
                html_message = None

            # Email to Customer
            send_mail(
                subject=subject,
                message=f"Hi {instance.full_name}, your order {order_ref} has been received successfully.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                html_message=html_message,
                fail_silently=False
            )
        except Exception as e:
            print(f"❌ CRITICAL: Client Registration Email Failed: {e}")

        try:
            # Email to Admin Engine
            admin_emails = list(User.objects.filter(is_staff=True).values_list("email", flat=True))
            if not admin_emails:
                fallback_admin = getattr(settings, 'ADMIN_EMAIL', 'admin@sabbtco.com')
                admin_emails = [fallback_admin]

            send_mail(
                subject=f"🚨 CRITICAL COMPLIANCE: New Order Lodged ({order_ref})",
                message=f"SABBTCo Admin Alert!\n\nNew booking saved.\nTracking ID: {order_ref}\nCustomer: {instance.full_name}\nManifest: {instance.quantity}x {instance.product_name}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )
        except Exception as e:
            print(f"❌ CRITICAL: Admin Alert Email Failed: {e}")

        # SMS & Internal DB Updates
        try:
            send_native_sms(instance.phone_number, f"SABBTCo: Order {order_ref} received successfully.")
            ClientNotification.objects.create(
                user=instance.user,
                title="Order Created Successfully",
                message=f"Your order {order_ref} has been created."
            )
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    user=admin,
                    title="New Order Received",
                    message=f"Order {order_ref} from {instance.full_name}"
                )
        except Exception as e:
            print(f"Internal log notification tracking error: {e}")

    else:
        # ----------------------------------------------------
        # ACTION B: EXISTING ORDER DISPATCHED / UPDATED BY ADMIN
        # ----------------------------------------------------
        old_status = getattr(instance, '_old_status', None)
        current_status = instance.status

        # 🚨 ONLY trigger emails if the status field actually modified
        if old_status is not None and old_status != current_status:
            try:
                send_mail(
                    subject=f"📦 SABBTCo Order Status Update: {order_ref}",
                    message=f"Dear {instance.full_name},\n\nYour order {order_ref} status has been updated to: {instance.get_status_display()}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=False
                )
                
                # ✅ FIXED: Swapped out get_or_create for clean fresh row entry insertion
                ClientNotification.objects.create(
                    user=instance.user,
                    title="Order Status Updated",
                    message=f"Your order {order_ref} status is now: {instance.get_status_display()}"
                )
                print(f"✅ Dispatched updated email notification for order {order_ref} ({old_status} -> {current_status})")
            except Exception as e:
                print(f"❌ CRITICAL: Admin Order Update Notification Failed: {e}")


# ========================================================
# 2. SHIPMENT UPDATE SIGNAL
# ========================================================
@receiver(post_save, sender=Shipment)
def shipment_update_signal(sender, instance, created, **kwargs):
    if created:
        return

    try:
        status_map = {
            "loading": "on_hold",
            "in_transit": "shipping",
            "customs": "arrived",
            "ready": "arrived",
            "delivered": "delivered",
        }

        new_status = status_map.get(instance.status)
        if not new_status:
            return

        orders = instance.orders.all()
        for order in orders:
            order.status = new_status
            order.save()

    except Exception as e:
        print("SHIPMENT SIGNAL ERROR:", e)


# ========================================================
# 3. SUPPLIER PAYMENT REQUEST SIGNAL
# ========================================================
@receiver(post_save, sender=SupplierPaymentRequest)
def supplier_payment_signal(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        send_mail(
            subject="Supplier Payment Request Received",
            message=f"Hi {instance.full_name}, your request {instance.request_id} has been received.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False
        )

        ClientNotification.objects.create(
            user=instance.user,
            title="Payment Request Submitted",
            message=f"Request {instance.request_id} is being processed."
        )

        for admin in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=admin,
                title="Supplier Payment Request",
                message=f"Request {instance.request_id} from {instance.full_name}"
            )
    except Exception as e:
        print("PAYMENT SIGNAL ERROR:", e)