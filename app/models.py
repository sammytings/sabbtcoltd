import random
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Native SMS Integration Fallback
try:
    from .notifications import send_native_sms
except ImportError:
    def send_native_sms(phone, text):
        print(f"[SMS Fallback Log] To {phone}: {text}")
# =========================
# 📦 SHIPMENT STATUS MESSAGES
# =========================

STATUS_MESSAGES = {
    "received": (
        "Your order has been received. "
        "Our team is working on it. "
        "Keep checking the portal for updates."
    ),

    "loading": (
        "Your shipment is now being loaded into the container. "
        "We are carefully organizing all cargo items."
    ),

    "in_transit": (
        "Good news! Your shipment is now in transit. "
        "It is currently on its way via sea freight."
    ),

    "customs": (
        "Your shipment has arrived at customs clearance. "
        "We are handling all required inspections and documentation."
    ),

    "ready": (
        "Your shipment is ready for pickup or final delivery. "
        "Please stay alert for final instructions."
    ),

    "delivered": (
        "Your shipment has been successfully delivered. "
        "Thank you for trusting our logistics service."
    ),
}
# ==========================================
# 1. SHIPMENT CONTAINER MODEL & PHOTOS
# ==========================================
class Shipment(models.Model):
    STATUS_CHOICES = [
        ('loading', 'Loading Container'),
        ('in_transit', 'In Transit / At Sea'),
        ('customs', 'Clearing Customs'),
        ('ready', 'Ready for Pickup / Delivery'),
        ('delivered', 'Delivered'),
    ]

    container_number = models.CharField(max_length=100, unique=True)
    destination = models.CharField(max_length=100)
    mode_of_delivery = models.CharField(
        max_length=20,
        choices=[
            ("air", "Air Freight"),
            ("sea", "Sea Freight"),
        ]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='loading')
    tracking_number = models.CharField(max_length=100, blank=True, null=True, help_text="Master tracking reference number")
    date_of_release = models.DateTimeField(blank=True, null=True, help_text="Timestamp when the container is dispatched")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.container_number

    def save(self, *args, **kwargs):
        is_updating = self.pk is not None
        old_status = None
        if is_updating:
            old_status = Shipment.objects.get(pk=self.pk).status
            
            if self.status == 'in_transit' and old_status != 'in_transit' and not self.date_of_release:
                self.date_of_release = timezone.now()

        super().save(*args, **kwargs)

        if is_updating and old_status != self.status:
            status_mapping = {
                'loading': 'on_hold',
                'in_transit': 'shipping',
                'customs': 'arrived',
                'ready': 'arrived',
                'delivered': 'delivered'
            }
            new_order_status = status_mapping.get(self.status, 'pending')
            bundled_orders = self.orders.all()
            bundled_orders.update(status=new_order_status)

            for order in bundled_orders:
                ClientNotification.objects.create(
                    user=order.user,
                    title=f"Order {order.order_id} Update",
                    message=f"Your package cargo container ({self.container_number}) status is now: {self.get_status_display()}."
                )

                try:
                    recipient = order.email or order.user.email
                    subject = f"SABBTCo Update: Order {order.order_id} is {self.get_status_display()}"
                    email_context = {
                        'client_name': order.full_name or order.user.username,
                        'order_id': order.order_id,
                        'container': self.container_number,
                        'status_display': self.get_status_display()
                    }
                    html_message = render_to_string('emails/status_update.html', email_context)
                    
                    send_mail(
                        subject=subject,
                        message=f"Your container update: {self.get_status_display()}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient],
                        html_message=html_message,
                        fail_silently=True
                    )
                except Exception as e:
                    print(f"Notification error for order {order.order_id}: {e}")

class ShipmentPhoto(models.Model):
    """🌟 Added for batch shipment image uploads inside the admin panel"""
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="container_photos")
    image = models.ImageField(upload_to="shipment_photos/")
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption or f"Photo for {self.shipment.container_number}"


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

import random
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Native SMS Integration Fallback
try:
    from .notifications import send_native_sms
except ImportError:
    def send_native_sms(phone, text):
        print(f"[SMS Fallback Log] To {phone}: {text}")
# =========================
# 📦 SHIPMENT STATUS MESSAGES
# =========================

STATUS_MESSAGES = {
    "received": (
        "Your order has been received. "
        "Our team is working on it. "
        "Keep checking the portal for updates."
    ),

    "loading": (
        "Your shipment is now being loaded into the container. "
        "We are carefully organizing all cargo items."
    ),

    "in_transit": (
        "Good news! Your shipment is now in transit. "
        "It is currently on its way via sea freight."
    ),

    "customs": (
        "Your shipment has arrived at customs clearance. "
        "We are handling all required inspections and documentation."
    ),

    "ready": (
        "Your shipment is ready for pickup or final delivery. "
        "Please stay alert for final instructions."
    ),

    "delivered": (
        "Your shipment has been successfully delivered. "
        "Thank you for trusting our logistics service."
    ),
}
# ==========================================
# 1. SHIPMENT CONTAINER MODEL & PHOTOS
# ==========================================

class ShipmentPhoto(models.Model):
    """🌟 Added for batch shipment image uploads inside the admin panel"""
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="container_photos")
    image = models.ImageField(upload_to="shipment_photos/")
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption or f"Photo for {self.shipment.container_number}"

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver

def generate_order_id():
    last_order = Order.objects.order_by("-id").first()

    if not last_order:
        prefix = "DMK"
    else:
        last_prefix = last_order.order_id.split("-")[0]

        prefix = "JWM" if last_prefix == "DMK" else "DMK"

    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"




from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SupplierPaymentRequest(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("approved", "Approved"),
        ("paid", "Paid"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="supplier_payment_requests"
    )

    request_id = models.CharField(max_length=20, unique=True, blank=True)

    # CLIENT DETAILS
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)

    # SUPPLIER DETAILS
    supplier_name = models.CharField(max_length=255)
    supplier_contact = models.CharField(max_length=255)

    # PAYMENT DETAILS
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")

    invoice = models.FileField(upload_to="supplier_invoices/", blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    admin_seen = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if not self.request_id:
            self.request_id = f"SPR-{timezone.now().strftime('%Y%m%d')}-{self.id or ''}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.request_id or f"SupplierRequest-{self.id}"


# ==========================================
# 3. NOTIFICATION & TIMELINE SYSTEMS
# ==========================================
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Banner(models.Model):
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="banners/")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Banner {self.id}"

class OrderTimeline(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="timeline")
    #order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="timeline")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_id} - {self.title}"

class Document(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="timeline")
    #order = models.ForeignKey(Order, related_name="documents", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PackagePhoto(models.Model):
    #order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="photos")
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="timeline")
    image = models.ImageField(upload_to="package_photos/")
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption or f"Photo for {self.order.order_id}"


# ==========================================
# 4. SUPPLIER PROFILES & SOURCING
# ==========================================
class Supplier(models.Model):
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name="supplier_profile",
    null=True,
    blank=True
)
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    country = models.CharField(max_length=100)
    address = models.TextField()
    product_category = models.CharField(max_length=255)
    business_license = models.FileField(upload_to="supplier_licenses/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name
  
class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="supplier_products/")
    created_at = models.DateTimeField(auto_now_add=True)

class SupplierShipment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="timeline")
   # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    tracking_number = models.CharField(max_length=255)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("supplier", "Supplier"),
        ("client", "Client"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class SourcingRequest(models.Model):
    SHIPPING_METHODS = [
        ('Sea Freight', 'Sea Freight'),
        ('Air Freight', 'Air Freight'),
        ('Not sure', 'Not sure — advise me'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sourcing_requests')
    customer_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=30)
    country = models.CharField(max_length=100, blank=True, null=True)
    destination = models.CharField(max_length=255, blank=True, null=True)
    product_name = models.CharField(max_length=255)
    quantity = models.CharField(max_length=100, default="1")
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_METHODS, default='Sea Freight')
    product_image = models.ImageField(upload_to='quote_attachments/', blank=True, null=True)
    product_description = models.TextField()
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.product_name}"

class ItemManifest(models.Model):
    sourcing_request = models.ForeignKey(SourcingRequest, on_delete=models.CASCADE, related_name='found_items')
    item_name = models.CharField(max_length=255)
    admin_image = models.ImageField(upload_to='verified_items/')
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    length_cm = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    width_cm = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    cbm_total = models.DecimalField(max_digits=8, decimal_places=4, default=0.0000, editable=False)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if self.length_cm and self.width_cm and self.height_cm:
            self.cbm_total = (self.length_cm * self.width_cm * self.height_cm) / 1000000
        else:
            self.cbm_total = 0.0000
        super().save(*args, **kwargs)



    
class KnowledgeBase(models.Model):
    category = models.CharField(max_length=100)
    question = models.CharField(max_length=500)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    sender = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# ==========================================
# 6. BACKEND SIGNALS ENGINE
# ========================================
@receiver(post_save, sender="app.Order")
def handle_new_order_notifications(sender, instance, created, **kwargs):
    
    if created:
        order_ref = instance.order_id
        

        client_email_body = (
    f"Dear {instance.full_name},\n\n"
    f"Your order {order_ref} for '{instance.product_name}' has been successfully logged!\n"
    f"Quantity: {instance.quantity}\n"
    f"Total Value: KES {instance.total_amount}\n\n"
    f"You can monitor live status logs by logging into your dashboard."
)
     
        send_mail(
            subject=f"SABBTCo Order Lodged: {order_ref}",
            message=client_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=True
        )
        
        client_sms_text = f"SABBTCo: Order {order_ref} received successfully. Check dashboard for tracking updates."
       # send_native_sms(instance.phone_number, client_sms_text)

        admin_email_all = getattr(settings, 'ADMIN_EMAIL', 'admin@sabbtco.com')
        admin_phone_all = getattr(settings, 'ADMIN_PHONE', '')
        
        admin_email_body = (
            f"SABBTCo Admin Alert!\n\n"
            f"A fresh booking order has been saved onto the live terminal database.\n"
            f"Order Tracking ID: {order_ref}\n"
            f"Customer Name: {instance.full_name}\n"
            f"Manifest Contents: {instance.quantity}x {instance.product_name}\n"
        )
        send_mail(
            subject=f"CRITICAL COMPLIANCE: New Order Saved ({order_ref})",
            message=admin_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email_all],
            fail_silently=True
        )
        
        if admin_phone_all:
            admin_sms_text = f"SABBTCo Admin: New order request {order_ref} made by {instance.full_name}."
            send_native_sms(admin_phone_all, admin_sms_text)

        from django.db import models
from django.conf import settings

class Feedback(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(default=5)
    message = models.TextField()

    approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role_company = models.CharField(max_length=150, help_text="e.g., IMPORTER · NAIROBI")
    message = models.TextField()
    is_approved = models.BooleanField(default=False, help_text="Check this to display it on the homepage slider.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.name} ({'Approved' if self.is_approved else 'Pending'})"
class ShipmentTimeline(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        related_name="timeline",
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shipment.container_number} - {self.status}"

from django.utils import timezone

class Banner(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()

    image = models.ImageField(upload_to="banners/")

    is_active = models.BooleanField(default=True)

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        now = timezone.now()

        if not self.is_active:
            return False

        if self.start_date and now < self.start_date:
            return False

        if self.end_date and now > self.end_date:
            return False

        return True

    def __str__(self):
        return self.title

from django.db import models
from django.contrib.auth.models import User
import uuid

class SupplierPaymentRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("paid", "Paid"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="supplier_payments"
    )

    request_id = models.CharField(max_length=20, unique=True, editable=False)

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    address = models.TextField()

    supplier_name = models.CharField(max_length=255)
    supplier_contact = models.CharField(max_length=255)
    invoice_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"SP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.request_id

# ==========================================
# 3. NOTIFICATION & TIMELINE SYSTEMS
class ClientNotification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_notifications'
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Banner(models.Model):
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="banners/")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Banner {self.id}"

class OrderTimeline(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="timeline")
    #order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="timeline")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_id} - {self.title}"

class Document(models.Model):
    order = models.ForeignKey("Order", related_name="documents", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PackagePhoto(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="package_photos/")
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption or f"Photo for {self.order.order_id}"


# ==========================================
# 4. SUPPLIER PROFILES & SOURCING
# ==========================================
class Supplier(models.Model):
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name="supplier_profile",
    null=True,
    blank=True
)
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    country = models.CharField(max_length=100)
    address = models.TextField()
    product_category = models.CharField(max_length=255)
    business_license = models.FileField(upload_to="supplier_licenses/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name
  
class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="supplier_products/")
    created_at = models.DateTimeField(auto_now_add=True)

class SupplierShipment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    tracking_number = models.CharField(max_length=255)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("supplier", "Supplier"),
        ("client", "Client"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class ItemManifest(models.Model):
    sourcing_request = models.ForeignKey(SourcingRequest, on_delete=models.CASCADE, related_name='found_items')
    item_name = models.CharField(max_length=255)
    admin_image = models.ImageField(upload_to='verified_items/')
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    length_cm = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    width_cm = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    cbm_total = models.DecimalField(max_digits=8, decimal_places=4, default=0.0000, editable=False)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if self.length_cm and self.width_cm and self.height_cm:
            self.cbm_total = (self.length_cm * self.width_cm * self.height_cm) / 1000000
        else:
            self.cbm_total = 0.0000
        super().save(*args, **kwargs)



    
class KnowledgeBase(models.Model):
    category = models.CharField(max_length=100)
    question = models.CharField(max_length=500)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    sender = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# ==========================================
# 6. BACKEND SIGNALS ENGINE
# ==========================================
@receiver(post_save, sender="app.Order")
def handle_new_order_notifications(sender, instance, created, **kwargs):
    if created:
        order_ref = instance.order_id
        client_email_body = (
    f"Dear {instance.full_name},\n\n"
    f"Your order {order_ref} for '{instance.product_name}' has been successfully logged!\n"
    f"Quantity: {instance.quantity}\n"
    f"Total Value: KES {instance.total_amount}\n\n"
    f"You can monitor live status logs by logging into your dashboard."
)
     
        send_mail(
            subject=f"SABBTCo Order Lodged: {order_ref}",
            message=client_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=True
        )
        
        client_sms_text = f"SABBTCo: Order {order_ref} received successfully. Check dashboard for tracking updates."
       # send_native_sms(instance.phone_number, client_sms_text)

        admin_email_all = getattr(settings, 'ADMIN_EMAIL', 'admin@sabbtco.com')
        admin_phone_all = getattr(settings, 'ADMIN_PHONE', '')
        
        admin_email_body = (
            f"SABBTCo Admin Alert!\n\n"
            f"A fresh booking order has been saved onto the live terminal database.\n"
            f"Order Tracking ID: {order_ref}\n"
            f"Customer Name: {instance.full_name}\n"
            f"Manifest Contents: {instance.quantity}x {instance.product_name}\n"
        )
        send_mail(
            subject=f"CRITICAL COMPLIANCE: New Order Saved ({order_ref})",
            message=admin_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email_all],
            fail_silently=True
        )
        
        if admin_phone_all:
            admin_sms_text = f"SABBTCo Admin: New order request {order_ref} made by {instance.full_name}."
            send_native_sms(admin_phone_all, admin_sms_text)

        from django.db import models
from django.conf import settings

class Feedback(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(default=5)
    message = models.TextField()

    approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role_company = models.CharField(max_length=150, help_text="e.g., IMPORTER · NAIROBI")
    message = models.TextField()
    is_approved = models.BooleanField(default=False, help_text="Check this to display it on the homepage slider.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.name} ({'Approved' if self.is_approved else 'Pending'})"
class ShipmentTimeline(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        related_name="timeline",
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shipment.container_number} - {self.status}"

from django.utils import timezone

class Banner(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()

    image = models.ImageField(upload_to="banners/")

    is_active = models.BooleanField(default=True)

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        now = timezone.now()

        if not self.is_active:
            return False

        if self.start_date and now < self.start_date:
            return False

        if self.end_date and now > self.end_date:
            return False

        return True

    def __str__(self):
        return self.title
    
import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

def some_function():
    from .models import Order

def generate_order_id():
    last_order = Order.objects.order_by("-id").first()

    if not last_order:
        prefix = "DMK"
    else:
        # extract prefix from last order
        last_prefix = last_order.order_id.split("-")[0]

        prefix = "JWM" if last_prefix == "DMK" else "DMK"

    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("paid", "Paid"),
        ("on_hold", "On Hold / At Warehouse"),
        ("shipping", "Shipping"),
        ("arrived", "Arrived"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_id = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    supplier_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="on_hold")
   
    shipment = models.ForeignKey(
        "Shipment", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_method = models.CharField(
        max_length=20,
        choices=[("air", "Air Freight"), ("sea", "Sea Freight")],
        default="sea"
    )
    sourcing_request = models.ForeignKey(
    "SourcingRequest",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="orders"
)
    links_specs = models.TextField(null=True, blank=True)
    product_image = models.ImageField(upload_to="orders/", null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)

    # ✅ MERGED INTO ONE SINGLE SAVE METHOD
    def save(self, *args, **kwargs):
        # 1. Generate unique customized order token
        if not self.order_id:
            self.order_id = generate_order_id()

        # 2. Calculate prices safely
        buying_total = Decimal(str(self.unit_price or 0)) * Decimal(str(self.quantity or 1))
        self.supplier_fee = buying_total * Decimal("0.03")
        self.service_fee = buying_total * Decimal("0.05")

        self.total_amount = (
            buying_total +
            self.supplier_fee +
            self.service_fee +
            self.fixed_fee +
            Decimal(str(self.extra_charges or 0))
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_id

# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random

class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return (timezone.now() - self.created_at).seconds > 300  # 5 min
from django.db import models
from django.utils import timezone

class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    excerpt = models.TextField()
    content = models.TextField()

    meta_description = models.CharField(max_length=160)

    keywords = models.CharField(max_length=255, blank=True)

    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db import models
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar_url = models.URLField(blank=True, null=True)
    google_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username
# ============================================================
# NEWS FEED
# ============================================================
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


# ============================================================
# NEWS FEED
# ============================================================
class NewsPost(models.Model):

    POST_TYPE_CHOICES = [
        ("photo", "Photo Only"),
        ("article", "Photo + Description"),
        ("video", "Video + Description"),
    ]

    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="News title or short caption."
    )

    slug = models.SlugField(
        max_length=280,
        unique=True,
        blank=True
    )

    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPE_CHOICES,
        default="article"
    )

    # ========================================================
    # MEDIA
    # ========================================================

    image = models.ImageField(
        upload_to="news/",
        blank=True,
        null=True,
        help_text="Main image for this news post."
    )

    video = models.FileField(
        upload_to="news/videos/",
        blank=True,
        null=True,
        help_text="Upload an MP4, WebM or compatible video file."
    )

    image_alt = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO-friendly alternative text for the main image."
    )

    # ========================================================
    # DESCRIPTION
    # ========================================================

    description = models.TextField(
        blank=True,
        help_text="News description. Supports rich text formatting."
    )

    # ========================================================
    # SEO
    # ========================================================

    focus_keyword = models.CharField(
        max_length=150,
        blank=True,
        help_text="Primary keyword you want this news post to target."
    )

    seo_keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated related SEO keywords."
    )

    meta_title = models.CharField(
        max_length=160,
        blank=True
    )

    meta_description = models.CharField(
        max_length=160,
        blank=True
    )

    seo_score = models.PositiveIntegerField(
        default=0,
        help_text="Internal SEO content score from 0 to 100."
    )

    # ========================================================
    # AI
    # ========================================================

    ai_generated = models.BooleanField(
        default=False
    )

    ai_prompt = models.TextField(
        blank=True,
        help_text="Prompt used to generate the description."
    )

    # ========================================================
    # PUBLISHING
    # ========================================================

    is_published = models.BooleanField(
        default=True
    )

    is_featured = models.BooleanField(
        default=False
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "News Post"
        verbose_name_plural = "News Posts"

    def save(self, *args, **kwargs):

        # Generate slug automatically
        if not self.slug:
            base_slug = (
                slugify(self.title)
                if self.title
                else "news-post"
            )

            slug = base_slug
            counter = 1

            while NewsPost.objects.filter(
                slug=slug
            ).exclude(pk=self.pk).exists():

                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        # Automatically set publication time
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        # Photo-only posts do not need description
        if self.post_type == "photo":
            self.description = ""

        # Video posts do not require a main image
        if self.post_type == "video":
            self.image = self.image if self.image else None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"News Post #{self.pk}"


# ============================================================
# NEWS GALLERY IMAGES
# ============================================================

class NewsPostImage(models.Model):

    news_post = models.ForeignKey(
        NewsPost,
        on_delete=models.CASCADE,
        related_name="gallery_images"
    )

    image = models.ImageField(
        upload_to="news/gallery/"
    )

    image_alt = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO-friendly alt text for this image."
    )

    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional caption displayed below the image."
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Controls the order of gallery images."
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "News Gallery Image"
        verbose_name_plural = "News Gallery Images"

    def __str__(self):
        return f"{self.news_post} - Gallery Image #{self.pk}"