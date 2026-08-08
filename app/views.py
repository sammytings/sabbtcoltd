# ================= IMPORTS (CLEANED + UNIQUE ONLY) =================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
from .models import ShipmentTimeline 
from .utils import get_order_prefix, generate_order_id
from .models import Order
from decimal import Decimal
from .models import (
    Order, OrderTimeline, Banner, Notification, Shipment,
    Supplier, Feedback, KnowledgeBase, Document, PackagePhoto
)

from .forms import OrderForm, SupplierRegisterForm
from .utils import create_notification
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib.auth.decorators import login_required

STATUS_MESSAGES = {
    "received": "Your order has been received. Our team is working on it.",
    "loading": "Your shipment is being loaded.",
    "in_transit": "Your shipment is in transit.",
    "customs": "Shipment is in customs clearance.",
    "ready": "Shipment is ready.",
    "delivered": "Shipment delivered successfully."
}
#from .models import Banner, Feedback
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Q

from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from .models import Banner, Feedback


def index(request):
    # OPTIONAL: allow public access (recommended for homepage)
    # If you really want login required, use @login_required instead

    now = timezone.now()

    banners = Banner.objects.filter(
        is_active=True
    ).filter(
        Q(end_date__isnull=True) |
        Q(end_date__gte=now)
    ).order_by("-start_date")

    feedbacks = Feedback.objects.filter(
        approved=True
    ).order_by("-created_at")

    return render(
        request,
        "index.html",
        {
            "banners": banners,
            "feedbacks": feedbacks,
            "GOOGLE_CLIENT_ID": getattr(settings, "GOOGLE_CLIENT_ID", ""),
        }
    )
def services(request):
    return render(request, "services.html")


def about(request):
    return render(request, "about.html")


# ================= AUTH =================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password!")
            return redirect("login")

    return render(request, "login.html")

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Ensure your models and notification functions are imported here

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order
def orders(request):

    # ================= POST =================
    if request.method == "POST":

        if not request.user.is_authenticated:
            return redirect("login")

        service_type = request.POST.get("service_type")

        country_code = request.POST.get("country_code", "")
        raw_phone = request.POST.get("phone", "")
        full_phone_number = f"{country_code} {raw_phone}".strip()

        address = request.POST.get("address", "No Address Specified").strip()

        # Conditional logic
        if service_type == "pay_supplier":
            product_name = f"Supplier Pay: {request.POST.get('supplier_name', 'Unknown')}"
            quantity = 1
            unit_price = Decimal(request.POST.get("invoice_amount") or 0)
        else:
            product_name = request.POST.get("product") or "General Sourcing Request"
            quantity = int(request.POST.get("qty") or 1)
            unit_price = Decimal("0")

        try:
            prefix = get_order_prefix(request.user)
            order_id = generate_order_id(prefix, Order)

            order = Order.objects.create(
                user=request.user,
                order_id=order_id,

                full_name=request.POST.get("name"),
                email=request.POST.get("email"),
                phone_number=full_phone_number,
                address=address,

                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,

                extra_charges=0,
                status="on_hold",
                shipping_method=request.POST.get("shipping", "sea"),

                links_specs=request.POST.get("links_specs", ""),
                photo=request.FILES.get("product_image")
            )

            messages.success(request, f"Order {order.order_id} created successfully!")
            return redirect("orders")

        except Exception as e:
            messages.error(request, f"Database Error: {str(e)}")
            return redirect("orders")

    # ================= GET =================
    user_orders = Order.objects.none()

    if request.user.is_authenticated:
        user_orders = Order.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "orders.html", {"orders": user_orders})
    # --- GET SYSTEM ---
@login_required
def my_orders(request):
    # Prefetch the shipment and its associated photos in a single clean query loop
    orders = Order.objects.filter(user=request.user)\
                          .select_related('shipment')\
                          .prefetch_related('shipment__container_photos')\
                          .order_by("-created_at")
    
    # Fetch client-specific notifications
    client_notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    unread_count = client_notifications.filter(is_read=False).count()

    return render(request, "orders/my_orders.html", {
        "orders": orders,
        "notifications": client_notifications,
        "unread_count": unread_count
    })

def track_order(request):
    order = None
    query = request.GET.get("order_id")

    if query:
        order = Order.objects.filter(order_id=query).first()

    return render(request, "orders/track.html", {"order": order})


# app/views.p
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order

@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order.objects.select_related('shipment')
        .prefetch_related(
            'photos',
            'timeline',
            'shipment__container_photos'
        ),
        order_id=order_id,
        user=request.user
    )
  
    unit_price = order.unit_price
    quantity = order.quantity
    buying_total = unit_price * quantity

    shipment_photos = order.shipment.container_photos.all() if order.shipment else []

    # ==========================
    # 💰 PRICING CALCULATION FIX
    # ==========================
    from decimal import Decimal

    unit_price = order.unit_price or Decimal("0.00")
    quantity = order.quantity or 0

    buying_total = unit_price * quantity

    supplier_fee = buying_total * Decimal("0.03")
    service_fee = buying_total * Decimal("0.05")

    shipping_fee = Decimal("50.00")

    grand_total = (
        buying_total +
        supplier_fee +
        service_fee +
        shipping_fee
)
    exchange_rate = 129  # USD → KES

    total_kes = grand_total * Decimal(str(exchange_rate))

    return render(request, "order_detail.html", {
        "order": order,
        "photos": order.photos.all(),
        "shipment_photos": shipment_photos,
        "timeline": order.timeline.all(),

        # ✅ ADD THESE
        "buying_total": buying_total,
        "supplier_fee": supplier_fee,
        "service_fee": service_fee,
        "shipping_fee": shipping_fee,
        "grand_total": grand_total,
        "exchange_rate":exchange_rate,
        "total_kes":total_kes,
    })
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import (
    SupplierPaymentRequest,
    SourcingRequest,
    Order,
    Notification,
    ClientNotification
)


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Order,
    SourcingRequest,
    SupplierPaymentRequest,
    ClientNotification,
    Notification
)


@login_required(login_url='/login/')
def quote(request):
    if request.method == "POST":
        try:

            # ========================
            # SERVICE TYPE
            # ========================
            service_type = request.POST.get("service_type", "source_ship")

            # ========================
            # BASIC INFO
            # ========================
            name = request.POST.get("name")
            email = request.POST.get("email")
            country = request.POST.get("country")
            address = request.POST.get("address")

            phone_prefix = request.POST.get("country_code", "").strip()
            phone_main = request.POST.get("phone", "").strip()
            full_phone = f"{phone_prefix} {phone_main}".strip()

            # ========================
            # SUPPLIER PAYMENT FLOW
            # ========================
            if service_type == "pay_supplier":
                SupplierPaymentRequest.objects.create(
                    user=request.user,
                    full_name=name,
                    email=email,
                    phone_number=full_phone,
                    address=address,
                    supplier_name=request.POST.get("supplier_name"),
                    supplier_contact=request.POST.get("supplier_contact"),
                    invoice_amount=request.POST.get("invoice_amount"),
                    currency=request.POST.get("currency"),
                )

                ClientNotification.objects.create(
                    user=request.user,
                    title="Supplier Payment Request Submitted 💰",
                    message=f"Hi {name}, your supplier payment request has been received."
                )

                send_mail(
                    subject="Supplier Payment Request Received 💰",
                    message=f"Hi {name}, we received your supplier payment request.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )

                messages.success(request, "Supplier payment request submitted successfully!")
                return redirect("orders")

            # ========================
            # PRODUCT ORDER FLOW
            # ========================
            product = request.POST.get("product")
            qty = request.POST.get("qty", "1")
            shipping = request.POST.get("shipping", "sea")
            notes = request.POST.get("notes")
            product_image = request.FILES.get("product_image")

            if not product:
                messages.error(request, "Product name is required.")
                return render(request, "quote.html")

            quantity = int(qty) if str(qty).isdigit() else 1

            # ========================
            # SAVE SOURCING REQUEST
            # ========================
            SourcingRequest.objects.create(
                client=request.user,
                customer_name=name,
                email=email,
                phone_number=full_phone,
                country=country,
                destination=country,
                product_name=product,
                quantity=quantity,
                shipping_method=shipping,
                product_description=notes,
                product_image=product_image
            )

            # ========================
            # CREATE ORDER
            # ========================
            new_order = Order.objects.create(
                user=request.user,
                full_name=name,
                email=email,
                phone_number=full_phone,
                address=address,
                product_name=product,
                quantity=quantity,
                unit_price=0,
                extra_charges=0,
                status="on_hold",
                shipping_method=shipping,
                links_specs=notes,
                product_image=product_image,
                destination=country
            )

            # ========================
            # CLIENT DB NOTIFICATION
            # ========================
            ClientNotification.objects.create(
                user=request.user,
                title="Order Received 📦",
                message=f"Your order #{new_order.order_id} for '{product}' has been received."
            )

            # ========================
            # CLIENT EMAIL
            # ========================
            send_mail(
                subject="📦 Order Received",
                message=f"""
Hi {name},

Your order for "{product}" has been received.

Tracking ID: {new_order.order_id}

We will update you shortly.
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            # ========================
            # ADMIN DB NOTIFICATIONS
            # ========================
            admins = User.objects.filter(is_staff=True)

            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title="🆕 New Order",
                    message=f"{request.user.username} ordered {quantity}x {product}"
                )

            # ========================
            # ADMIN EMAIL NOTIFICATION
            # ========================
            admin_emails = list(
                User.objects.filter(is_staff=True)
                .values_list("email", flat=True)
            )

            send_mail(
                subject="🆕 New Order Received",
                message=f"""
New order placed:

User: {request.user.username}
Product: {product}
Quantity: {quantity}
Order ID: {new_order.order_id}
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )

            messages.success(
                request,
                f"Request submitted successfully! Tracking ID: {new_order.order_id}"
            )

            return redirect("orders")

        except Exception as e:
            print("QUOTE ERROR:", e)
            messages.error(request, f"System Error: {e}")
            return render(request, "quote.html")

    return render(request, "quote.html")
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Count, Sum, Prefetch
from django.contrib.auth.models import User

from .models import (
    Order,
    Shipment,
    SourcingRequest,
    SupplierPaymentRequest
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import NewsPost
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
# ============================================================
# NEWS FEED
# ============================================================
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import NewsPost


# ============================================================
# PUBLIC NEWS FEED
# ============================================================

def news_list(request):
    """
    Public News Feed.

    Only published posts are displayed.
    Newest posts appear first.
    """

    news_posts = (
        NewsPost.objects
        .filter(is_published=True)
        .order_by("-published_at", "-created_at")
    )

    return render(
        request,
        "news/news_list.html",
        {
            "news_posts": news_posts,
        }
    )


# ============================================================
# PUBLIC NEWS DETAIL
# ============================================================

def news_detail(request, slug):
    """
    Public individual News Feed post.
    Only published posts can be viewed publicly.
    """

    news_post = get_object_or_404(
        NewsPost,
        slug=slug,
        is_published=True
    )

    return render(
        request,
        "news/news_detail.html",
        {
            "news_post": news_post,
        }
    )


# ============================================================
# ADMIN NEWS LIST
# ============================================================

@login_required
def news_admin_list(request):
    """
    Admin News Feed management page.

    Displays all posts, including unpublished posts.
    """

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to access the News Feed."
        )
        return redirect("dashboard")

    news_posts = (
        NewsPost.objects
        .all()
        .order_by("-created_at")
    )

    return render(
        request,
        "news/admin_news_list.html",
        {
            "news_posts": news_posts,
        }
    )


# ============================================================
# CREATE NEWS POST
# ============================================================

@login_required
def news_create(request):
    """
    Create a new News Feed post.

    Supported post types:

    1. photo
       - Image only
       - Description is optional/not required

    2. article
       - Image
       - Description
       - SEO information
    """

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to create news posts."
        )
        return redirect("dashboard")

    if request.method == "POST":

        # ----------------------------------------------------
        # Basic information
        # ----------------------------------------------------

        title = request.POST.get(
            "title",
            ""
        ).strip()

        post_type = request.POST.get(
            "post_type",
            "article"
        ).strip().lower()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        image = request.FILES.get("image")

        image_alt = request.POST.get(
            "image_alt",
            ""
        ).strip()

        # ----------------------------------------------------
        # SEO information
        # ----------------------------------------------------

        focus_keyword = request.POST.get(
            "focus_keyword",
            ""
        ).strip()

        seo_keywords = request.POST.get(
            "seo_keywords",
            ""
        ).strip()

        meta_title = request.POST.get(
            "meta_title",
            ""
        ).strip()

        meta_description = request.POST.get(
            "meta_description",
            ""
        ).strip()

        # ----------------------------------------------------
        # SEO score
        # ----------------------------------------------------

        seo_score_raw = request.POST.get(
            "seo_score",
            "0"
        ).strip()

        try:
            seo_score = int(seo_score_raw)
            seo_score = max(
                0,
                min(100, seo_score)
            )
        except (TypeError, ValueError):
            seo_score = 0

        # ----------------------------------------------------
        # Publishing options
        # ----------------------------------------------------

        is_published = (
            request.POST.get("is_published") == "on"
        )

        is_featured = (
            request.POST.get("is_featured") == "on"
        )

        # ----------------------------------------------------
        # Validate post type
        # ----------------------------------------------------

        allowed_post_types = {
            "photo",
            "article",
        }

        if post_type not in allowed_post_types:
            post_type = "article"

        # ----------------------------------------------------
        # Image is required
        # ----------------------------------------------------

        if not image:
            messages.error(
                request,
                "Please upload an image for the news post."
            )

            return render(
                request,
                "news/news_form.html",
                {
                    "title": title,
                    "post_type": post_type,
                    "description": description,
                    "image_alt": image_alt,
                    "focus_keyword": focus_keyword,
                    "seo_keywords": seo_keywords,
                    "meta_title": meta_title,
                    "meta_description": meta_description,
                    "seo_score": seo_score,
                    "is_published": is_published,
                    "is_featured": is_featured,
                }
            )

        # ----------------------------------------------------
        # Article requires description
        # ----------------------------------------------------

        if post_type == "article" and not description:

            messages.error(
                request,
                "Please enter a description for a Photo + Description post."
            )

            return render(
                request,
                "news/news_form.html",
                {
                    "title": title,
                    "post_type": post_type,
                    "description": description,
                    "image_alt": image_alt,
                    "focus_keyword": focus_keyword,
                    "seo_keywords": seo_keywords,
                    "meta_title": meta_title,
                    "meta_description": meta_description,
                    "seo_score": seo_score,
                    "is_published": is_published,
                    "is_featured": is_featured,
                }
            )

        # ----------------------------------------------------
        # Photo-only post should not contain description
        # ----------------------------------------------------

        if post_type == "photo":
            description = ""

        # ----------------------------------------------------
        # Create post
        # ----------------------------------------------------

        news_post = NewsPost.objects.create(
            title=title,
            post_type=post_type,
            image=image,
            image_alt=image_alt,
            description=description,
            focus_keyword=focus_keyword,
            seo_keywords=seo_keywords,
            meta_title=meta_title,
            meta_description=meta_description,
            is_published=is_published,
            is_featured=is_featured,
            seo_score=seo_score,
        )

        messages.success(
            request,
            "News post created successfully."
        )

        return redirect(
            "news_admin_list"
        )

    # --------------------------------------------------------
    # GET request
    # --------------------------------------------------------

    return render(
        request,
        "news/news_form.html"
    )


# ============================================================
# EDIT NEWS POST
# ============================================================

@login_required
def news_edit(request, pk):
    """
    Edit an existing News Feed post.
    """

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to edit news posts."
        )
        return redirect("dashboard")

    news_post = get_object_or_404(
        NewsPost,
        pk=pk
    )

    if request.method == "POST":

        # ----------------------------------------------------
        # Basic information
        # ----------------------------------------------------

        news_post.title = request.POST.get(
            "title",
            ""
        ).strip()

        post_type = request.POST.get(
            "post_type",
            "article"
        ).strip().lower()

        if post_type not in {
            "photo",
            "article",
        }:
            post_type = "article"

        news_post.post_type = post_type

        news_post.description = request.POST.get(
            "description",
            ""
        ).strip()

        news_post.image_alt = request.POST.get(
            "image_alt",
            ""
        ).strip()

        # ----------------------------------------------------
        # SEO information
        # ----------------------------------------------------

        news_post.focus_keyword = request.POST.get(
            "focus_keyword",
            ""
        ).strip()

        news_post.seo_keywords = request.POST.get(
            "seo_keywords",
            ""
        ).strip()

        news_post.meta_title = request.POST.get(
            "meta_title",
            ""
        ).strip()

        news_post.meta_description = request.POST.get(
            "meta_description",
            ""
        ).strip()

        # ----------------------------------------------------
        # SEO score
        # ----------------------------------------------------

        seo_score_raw = request.POST.get(
            "seo_score",
            "0"
        ).strip()

        try:
            seo_score = int(seo_score_raw)
            seo_score = max(
                0,
                min(100, seo_score)
            )
        except (TypeError, ValueError):
            seo_score = 0

        news_post.seo_score = seo_score

        # ----------------------------------------------------
        # Publishing options
        # ----------------------------------------------------

        news_post.is_published = (
            request.POST.get("is_published") == "on"
        )

        news_post.is_featured = (
            request.POST.get("is_featured") == "on"
        )

        # ----------------------------------------------------
        # Replace image only when a new image is uploaded
        # ----------------------------------------------------

        new_image = request.FILES.get("image")

        if new_image:
            news_post.image = new_image

        # ----------------------------------------------------
        # Photo-only post
        # ----------------------------------------------------

        if news_post.post_type == "photo":
            news_post.description = ""

        # ----------------------------------------------------
        # Article must have a description
        # ----------------------------------------------------

        if (
            news_post.post_type == "article"
            and not news_post.description
        ):
            messages.error(
                request,
                "Please enter a description for a Photo + Description post."
            )

            return render(
                request,
                "news/news_form.html",
                {
                    "news_post": news_post,
                    "editing": True,
                }
            )

        # ----------------------------------------------------
        # Save changes
        # ----------------------------------------------------

        news_post.save()

        messages.success(
            request,
            "News post updated successfully."
        )

        return redirect(
            "news_admin_list"
        )

    # --------------------------------------------------------
    # GET request
    # --------------------------------------------------------

    return render(
        request,
        "news/news_form.html",
        {
            "news_post": news_post,
            "editing": True,
        }
    )


# ============================================================
# DELETE NEWS POST
# ============================================================

@login_required
def news_delete(request, pk):
    """
    Delete a News Feed post.
    """

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to delete news posts."
        )
        return redirect("dashboard")

    news_post = get_object_or_404(
        NewsPost,
        pk=pk
    )

    if request.method == "POST":

        news_post.delete()

        messages.success(
            request,
            "News post deleted successfully."
        )

        return redirect(
            "news_admin_list"
        )

    return render(
        request,
        "news/news_delete.html",
        {
            "news_post": news_post,
        }
    )

def controldash(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard")  # change if needed

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect("/controldash/")   # or your custom admin dashboard
        else:
            messages.error(request, "Invalid admin credentials.")

    return render(request, "controldash.html")

from django.contrib.auth.decorators import login_required, user_passes_test

#@login_required
def dashboard(request):
    status = request.GET.get("status")

    # Base queryset
    orders = Order.objects.select_related('user').prefetch_related(
        Prefetch(
            'user__sourcing_requests',
            queryset=SourcingRequest.objects.all().order_by('-created_at'),
            to_attr='cached_quotes'
        )
    ).order_by("-created_at")

    # Filter by status
    if status and status != "all":
        orders = orders.filter(status=status)

    # Latest 20 orders only for dashboard
    latest_orders = orders[:20]

    # Real dashboard statistics
    total_orders = Order.objects.count()
    total_shipments = Shipment.objects.count()
    total_customers = User.objects.count()

    revenue = Order.objects.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    # Supplier payment stats (optional)
    supplier_requests = SupplierPaymentRequest.objects.count()
    pending_supplier_requests = SupplierPaymentRequest.objects.filter(
        status="pending"
    ).count()

    context = {
        "orders": latest_orders,
        "status": status or "all",

        "total_orders": total_orders,
        "total_shipments": total_shipments,
        "total_customers": total_customers,
        "revenue": revenue,

        "supplier_requests": supplier_requests,
        "pending_supplier_requests": pending_supplier_requests,
    }

    return render(request, "dashboard/dashboard_base.html", context)

def mark_notifications_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect("dashboard")
from .models import Notification, ClientNotification
@staff_member_required(login_url='controldash')
def update_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    
    # Cast to string safely or fetch the clean data attribute
    old_status = str(order.status) 

    if request.method == "POST":
        new_status = request.POST.get("status")

        if old_status != new_status:
            order.status = new_status
            order.save()

            # Fix layout injection text by forcing string evaluation
            Notification.objects.create(
                user=request.user,
                title="Shipment Status Updated",
                message=f"Order #{str(order.order_id)} changed from {str(old_status)} to {str(new_status)}"
            )

        messages.success(request, "Order updated successfully.")
        return redirect("dashboard")

    return render(request, "dashboard/update_order.html", {"order": order})
# ================= CUSTOMERS =================
@staff_member_required(login_url='controldash')
def customers_view(request):
    customers = User.objects.all().order_by("-date_joined")

    return render(request, "dashboard/customers.html", {
        "customers": customers
    })


# ================= UPLOAD DOCUMENT =================
def upload_document(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.method == "POST":
        title = request.POST.get("title")
        file = request.FILES.get("file")

        if title and file:
            Document.objects.create(order=order, title=title, file=file)

    return redirect("order_detail", order_id=order.order_id)


# ================= NOTIFICATIONS =================
from django.contrib.auth import get_user_model
from .models import ClientNotification

def notifications(request):
    user = request.user if request.user.is_authenticated else None

    notifications = (
        ClientNotification.objects.filter(user=user).order_by("-created_at")
        if user else []
    )

    return render(request, "notifications.html", {
        "notifications": notifications
    })

@login_required
def supplier_dashboard(request):

    supplier = get_object_or_404(Supplier, user=request.user)

    return render(request, "supplier/dashboard.html", {
        "supplier": supplier
    })


# ================= FEEDBACK =================
def feedback_view(request):

    if request.method == "POST":

        if request.user.is_authenticated:
            Feedback.objects.create(
                user=request.user,
                name=request.user.username,
                email=request.user.email,
                rating=request.POST.get("rating"),
                message=request.POST.get("message")
            )
        else:
            Feedback.objects.create(
                name=request.POST.get("name"),
                email=request.POST.get("email"),
                rating=request.POST.get("rating"),
                message=request.POST.get("message")
            )

        messages.success(request, "Thank you for your feedback!")
        return redirect("feedback")

    return render(request, "feedback.html")


# ================= SHIPMENTS =================
@staff_member_required(login_url='controldash')
def shipment_dashboard(request):

    shipments = Shipment.objects.all().order_by("-updated_at")

    return render(request, "dashboard/shipment_dashboard.html", {
        "shipments": shipments,
        "total": shipments.count(),
        "in_transit": shipments.filter(status="in_transit").count(),
        "delivered": shipments.filter(status="delivered").count(),
        "pending": shipments.filter(status="pending").count(),
    })
# views.py
import json
import urllib.request
import urllib.error
import ssl
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

# Import your custom rulebook file
from .logistics_knowledge import SABBTCO_KNOWLEDGE_BASE

@csrf_exempt
def logistics_ai_chat(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            
            if not user_message:
                return JsonResponse({"error": "Empty message"}, status=400)

            # 1. Free Groq API configuration details
            api_url = os.getenv("api_url")
            api_key = os.getenv("api_key")
            # 2. Build the payload using a fast, completely free open-source model
            # 2. Build the payload using an ACTIVE, completely free open-source model string
            payload = {
                "model": "llama-3.1-8b-instant",  # Updated to the current active Groq free tier standard
                "messages": [
                    {
                        "role": "system", 
                        "content": (
                            "You are the official SABBTCo Logistics AI Assistant. "
                            "Your purpose is to assist clients navigating our portal. "
                            "Use the following official company knowledge base to answer questions. "
                            "If a customer asks about pricing or data missing from this knowledge base, "
                            "politely ask them to submit a 'Request Quote' form or contact support directly.\n\n"
                            f"OFFICIAL SABBTCO DATA:\n{SABBTCO_KNOWLEDGE_BASE}"
                        )
                    },
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.2
            }

            json_data = json.dumps(payload).encode("utf-8")
            ssl_context = ssl._create_unverified_context()

            # 3. Request execution over secure native channels
            # ... payload and json_data configuration remain exactly the same ...

            # Construct the request, adding a real User-Agent identity to bypass Cloudflare's 1010 wall
            req = urllib.request.Request(
                api_url,
                data=json_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    # This tells the Cloudflare shield that the request is coming from a trusted web framework
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                # ... response parsing code remains exactly the same ...
            
                response_body = response.read().decode("utf-8")
                result = json.loads(response_body)
                
                ai_reply = result["choices"][0]["message"]["content"]
                return JsonResponse({"reply": ai_reply})

        except urllib.error.HTTPError as http_err:
            error_details = http_err.read().decode("utf-8")
            print(f"Free API HTTP Error: {error_details}")
            return JsonResponse({"error": f"API Error: {http_err.code}"}, status=500)
            
        except Exception as e:
            print(f"Global View Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Invalid request"}, status=400)

# app/views.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.mail import send_mail
from .notifications import send_native_sms
from .models import Order  # Ensure your Order model is imported

def place_order_view(request):
    if request.method == "POST":
        # 1. Extract your form details from the POST request
        client_phone = request.POST.get('phone')  # e.g., +2547XXXXXXXX
        client_email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        product_name = request.POST.get('product_name')
        quantity = request.POST.get('quantity', 1)
        address = request.POST.get('address')
        
        # 2. Save the order directly into the database as 'on_hold'
        order = Order.objects.create(
            client=full_name,            # Maps to your custom template 'order.client' field
            product=product_name,        # Maps to your custom template 'order.product' field
            qty=quantity,
            dest_address=address,
            phone=client_phone,
            email=client_email,
            status='on_hold'             # 👈 CRITICAL: Starts as 'on_hold' so it appears on the warehouse registry list
        )
        
        order_id = generate_order_id()

        # ================= 1. CLIENT NOTIFICATIONS =================
        # Send Email
        client_email_body = f"Hello,\n\nYour SABBTCo order {order_id} has been received successfully! It is currently safe in our warehouse pending container assignment. You can track its live progress on your user dashboard panel.\n\nThank you for choosing SABBTCo."
        send_mail(
            subject=f"SABBTCo Order Confirmed: {order_id}",
            message=client_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[client_email],
            fail_silently=True
        )
        # Send SMS
        client_sms_text = f"SABBTCo Alert: Order {order_id} has been successfully received. Track progress on your portal dashboard."
        send_native_sms(client_phone, client_sms_text)


        # ================= 2. ADMIN NOTIFICATIONS =================
        # Send Email to Admin
        admin_email_body = f"Alert!\n\nA new shipment order ({order_id}) has been registered on the portal. Please log into the admin panel to build a container shipment manifest and approve documentation paths."
        send_mail(
            subject=f"URGENT: New Order Placed ({order_id})",
            message=admin_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True
        )
        # Send SMS to Admin
        admin_sms_text = f"SABBTCo Admin: New order {order_id} placed on portal. Check admin dash."
        send_native_sms("+254790644050", admin_sms_text)

        return redirect('order_success')
        
    return render(request, "place_order.html")
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Shipment, Order

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Shipment, Order
@staff_member_required(login_url='controldash')
def add_shipment_view(request):
    if request.method == "POST":
        container_number = request.POST.get("container_number")
        destination = request.POST.get("destination")
        assigned_orders = request.POST.getlist("assigned_orders")
        
        if not assigned_orders:
            messages.error(request, "Please select at least one order to build a manifest.")
            return redirect(request.path)
        
        # 1. Initialize the Master Shipment Container Row
        shipment = Shipment.objects.create(
            container_number=container_number,
            destination=destination,
            status='loading'
        )
        
        # 2. Extract selected orders via their primary keys
        orders = Order.objects.filter(id__in=assigned_orders)
        
        # 3. Process status progression and client email dispatches
        for order in orders:
            order.shipment = shipment
            order.status = 'pending'  # 👈 Shifts status from on_hold to pending upon packaging assignment
            order.save()
            
            # 4. Trigger Beautiful HTML Notification Email Flow
            try:
                recipient = order.email or order.user.email
                subject = f"SABBTCo Update: Order {order.order_id} is Pending Dispatch"
                
                email_context = {
                    'client_name': order.full_name or order.user.username,
                    'order_id': order.order_id,
                    'container': container_number,
                    'status_display': "Pending Dispatch"
                }
                html_message = render_to_string('emails/status_update.html', email_context)
                
                send_mail(
                    subject=subject,
                    message=f"Your container assignment update: Pending Dispatch",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    html_message=html_message,
                    fail_silently=True
                )
            except Exception as mail_err:
                print(f"Notification error for order {order.order_id}: {mail_err}")

        messages.success(
            request, 
            f"Container {container_number} built successfully! {orders.count()} orders updated to Pending and clients notified."
        )
        return redirect('shipment_dashboard') 

    # === GET REQUEST LOGIC ===
    # Filter exclusively for unassigned orders sitting at the warehouse ('on_hold')
    orders_on_hold = Order.objects.filter(
        status__iexact='on_hold',
        shipment__isnull=True
    )
    
    return render(request, 'dashboard/add_shipment.html', {'orders_on_hold': orders_on_hold})
    # === GET REQUEST LOGIC ===
    # Case-insensitive check to guarantee matching regardless of minor database variations.
  

@staff_member_required(login_url='controldash')
def shipment_dashboard(request):
    # 💡 THE CRASH FIX: Changed from '-created_at' to '-updated_at' 
    shipments = Shipment.objects.all().order_by("-updated_at")
    return render(request, 'dashboard/shipment_list.html', {'shipments': shipments})
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Order

@login_required
@staff_member_required(login_url='controldash')
def Orders_view(request):
    orders = Order.objects.all().order_by('-created_at')
    
    # Updated to match your actual model fields
    metrics = Order.objects.aggregate(
        total_orders=Count('id'),
        # Assuming 'status' tracks both payment/fulfillment states (e.g., 'Pending', 'In Transit')
        pending_orders=Count('id', filter=Q(status__iexact='Pending')),
        in_transit=Count('id', filter=Q(status__iexact='In Transit')),
        completed=Count('id', filter=Q(status__iexact='Completed') | Q(status__iexact='Delivered'))
    )
    
    context = {
        'orders': orders,
        'total_orders_count': metrics['total_orders'],
        'pending_orders_count': metrics['pending_orders'], # Changed name
        'in_transit_count': metrics['in_transit'],
        'completed_count': metrics['completed'],
    }
    
    return render(request, 'dashboard/Orders.html', context)
@staff_member_required(login_url='controldash')
def update_shipment_status(request, shipment_id):

    shipment = get_object_or_404(
        Shipment,
        id=shipment_id
    )

    if request.method == "POST":

        shipment.status = request.POST.get("status")

        shipment.save()  # THIS triggers all order updates

        messages.success(
            request,
            "Shipment updated successfully."
        )

    return redirect("shipment_dashboard")

# app/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Shipment
# Import our new communication tasks safely
from .notifications import send_whatsapp_alert, send_bulk_sms_alert 

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import SourcingRequest, ItemManifest

import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import Shipment, ShipmentPhoto, SourcingRequest, ItemManifest, Order

# =====================================================================
# 1. ADMIN MANIFEST PROCESS ENGINE
# =====================================================================

@staff_member_required
def admin_upload_verified_item(request, request_id):
    sourcing_req = get_object_or_404(SourcingRequest, id=request_id)
    
    if request.method == "POST":
        item_name = request.POST.get('item_name')
        admin_file = request.FILES.get('admin_image')
        
        # Helper function to safely cast empty strings or missing fields to 0
        def safe_decimal(value):
            if value is None or str(value).strip() == "":
                return 0
            return value

        weight = safe_decimal(request.POST.get('weight_kg'))
        length = safe_decimal(request.POST.get('length_cm'))
        width = safe_decimal(request.POST.get('width_cm'))
        height = safe_decimal(request.POST.get('height_cm'))
        cost = safe_decimal(request.POST.get('unit_cost'))
        
        # Save into the Item Manifest dataset link
        ItemManifest.objects.create(
            sourcing_request=sourcing_req,
            item_name=item_name,
            admin_image=admin_file,
            weight_kg=weight,
            length_cm=length,
            width_cm=width,
            height_cm=height,
            unit_cost=cost
        )
        
        # Mark the root request as processed so user gets notified
        sourcing_req.is_processed = True
        sourcing_req.save()
        
        messages.success(request, f"Successfully uploaded verified product tracking data for Request #{sourcing_req.id}!")
        return redirect('admin_sourcing_dashboard')
        
    return render(request, 'admin/process_request.html', {'sourcing_req': sourcing_req})


# =====================================================================
#
# app/views.py
# =====================================================================
# 2. LOGISTICS LOG STREAM DETAIL VIEW (UPGRADED)
# =====================================================================

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.mail import send_mail

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
@staff_member_required(login_url='controldash')
def shipment_detail_view(request, container_number):
    shipment = get_object_or_404(Shipment, container_number=container_number)
    photos = shipment.container_photos.all()

    if request.method == "POST":

        # =========================
        # 📸 IMAGE UPLOAD
        # =========================
        if request.FILES.get("shipment_image"):
            ShipmentPhoto.objects.create(
                shipment=shipment,
                image=request.FILES["shipment_image"]
            )
            messages.success(request, "Shipment image uploaded successfully!")

        # =========================
        # STATUS UPDATE
        # =========================
        new_status = request.POST.get('status')
        new_tracking = request.POST.get('tracking_number')

        old_status = shipment.status

        if new_status:
            shipment.status = new_status

        if new_tracking:
            shipment.tracking_number = new_tracking

        shipment.save()

        # =========================
        # TIMELINE + NOTIFICATIONS ENGINE
        # =========================
        if new_status and new_status != old_status:

            message = STATUS_MESSAGES.get(
                new_status,
                "Shipment status has been updated."
            )

            # 1. Shipment timeline entry
            ShipmentTimeline.objects.create(
                shipment=shipment,
                status=new_status,
                message=message
            )

            # 2. Loop orders safely
            for order in shipment.orders.all():

                OrderTimeline.objects.create(
                    order=order,
                    title=shipment.get_status_display(),
                    description=message
                )

                Notification.objects.create(
                    user=order.user,
                    title="Shipment Update",
                    message=message
                )

                # Email
                if order.user.email:
                    send_mail(
                        subject=f"Shipment Update - {shipment.container_number}",
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[order.user.email],
                        fail_silently=True
                    )

        messages.success(request, "Shipment records updated successfully.")
        return redirect('shipment_detail', container_number=shipment.container_number)

    # GET request
    orders = shipment.orders.all()

    return render(request, 'dashboard/shipment_detail.html', {
        'shipment': shipment,
        'orders': orders,
        'shipment_images': photos
    })
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SupplierRegistrationForm

def supplier_signup_view(request):
    if request.method == "POST":
        form = SupplierRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.is_verified = False  # Requires admin approval
            supplier.save()
            
            messages.success(
                request, 
                "Your supplier application has been submitted successfully! Our vetting team will review your details and get in touch."
            )
            return redirect('supplier_signup_success')
    else:
        form = SupplierRegistrationForm()
        
    return render(request, 'main/supplier_signup.html', {'form': form})

def supplier_signup_success(request):
    return render(request, 'main/supplier_signup_success.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Feedback

def submit_feedback(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        feedback = Feedback(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        if request.user.is_authenticated:
            feedback.user = request.user
            
        feedback.save()
        messages.success(request, "Thank you for your feedback!")
        return redirect('feedback_success') # Replace with your URL name
        
    return render(request, 'feedback_form.html')

from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.shortcuts import redirect
from django.contrib import messages

User = get_user_model()

def supplier_token_login(request, uidb64, token):
    try:
        # Decode the user id from the URL
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Verify the token is valid for this specific user
    if user is not None and default_token_generator.check_token(user, token):
        # Dynamically specify backend to bypass password prompt
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Welcome to your dashboard!")
        return redirect('supplier_dashboard') # URL pattern for supplier dashboard
    else:
        messages.error(request, "This verification link is invalid or has expired.")
        return redirect('login') # Fallback to standard login page

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def supplier_dashboard_view(request):
    # Ensure user has a supplier profile and is verified
    if not hasattr(request.user, 'supplier_profile') or not request.user.supplier_profile.is_verified:
        raise PermissionDenied("You do not have permission to access this dashboard.")
        
    return render(request, 'supplier/dashboard.html')
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

@staff_member_required
def approve_supplier(request, supplier_id):

    supplier = get_object_or_404(Supplier, id=supplier_id)

    if supplier.is_verified:
        messages.warning(request, "Supplier already approved.")
        return redirect("admin_supplier_list")

    # Create user account if missing
    if not supplier.user:

        username = supplier.email

        user = User.objects.create_user(
            username=username,
            email=supplier.email
        )

        supplier.user = user

    supplier.is_verified = True
    supplier.save()

    user = supplier.user

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    login_url = (
        f"{request.scheme}://{request.get_host()}"
        f"/supplier-login/{uid}/{token}/"
    )

    html_message = render_to_string(
        "emails/supplier_approved.html",
        {
            "supplier": supplier,
            "login_url": login_url
        }
    )

    send_mail(
        subject="Supplier Account Approved",
        message=f"Login here: {login_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[supplier.email],
        html_message=html_message,
        fail_silently=False
    )

    messages.success(
        request,
        f"{supplier.company_name} approved successfully."
    )

    return redirect("admin_supplier_list")

def become_supplier(request):
    return render(request, "supplier/temporary_notice.html")
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import TestimonialForm
from .forms import FeedbackForm
from django.contrib import messages

def submit_feedback_view(request):

    if request.method == "POST":

        form = FeedbackForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Thank you. Your feedback has been submitted."
            )

            return redirect("index")

    else:
        form = FeedbackForm()

    return render(
        request,
        "submit_feedback.html",
        {"form": form}
    )
def orders_dashboard(request):
    status = request.GET.get("status", "all")

    if status == "all":
        orders = Order.objects.all()
    else:
        orders = Order.objects.filter(status=status)

    return render(request, "dashboard/orders.html", {
        "orders": orders,
        "status": status
    })

from django.shortcuts import render, get_object_or_404
from .models import Shipment
def tracking_search(request):

    if request.method == "POST":
        container = request.POST.get("container_number")

        return redirect(
            "track_container",
            container_number=container
        )

    return render(
        request,
        "tracking/search.html"
    )


def track_container(request, container_number):

    shipment = get_object_or_404(
        Shipment,
        container_number=container_number
    )

    orders = shipment.orders.all()

    photos = shipment.container_photos.all()

    timeline = shipment.timeline.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "tracking/tracking.html",
        {
            "shipment": shipment,
            "orders": orders,
            "photos": photos,
            "timeline": timeline,
        }
    )

from django.shortcuts import get_object_or_404, render, redirect
from .models import Order

def update_order_pricing(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == "POST":
        order.unit_price = request.POST.get("unit_price") or 0
        order.quantity = request.POST.get("quantity") or 1
        order.extra_charges = request.POST.get("extra_charges") or 0

        order.save()  # IMPORTANT: triggers calculation in model

        return redirect("orders")

    return render(request, "admin/update_order_pricing.html", {
        "order": order
    })

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Order

def generate_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    return HttpResponse(f"Invoice for {order.order_id}")
def supplier_payments_view(request):
    if not request.user.is_authenticated:
        supplier_payments = []
    else:
        supplier_payments = SupplierPaymentRequest.objects.filter(
            user=request.user
        ).order_by("-created_at")

    return render(request, "supplier_payments.html", {
        "supplier_payments": supplier_payments
    })

def supplier_payment_read(request, pk):
    payment = get_object_or_404(SupplierPaymentRequest, pk=pk)

    payment.is_read = True
    payment.status = "processing"
    payment.save()

    return redirect("supplier_payments")


    
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def profile_view(request):
    return render(request, "profile.html")

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect("index")  # or login page

# views.py
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .models import EmailOTP
from .utils import generate_otp, send_otp_email

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            is_active=False  # IMPORTANT
        )

        otp = generate_otp()
        EmailOTP.objects.create(user=user, otp=otp)

        send_otp_email(email, otp)

        request.session["pending_user_id"] = user.id

        return redirect("verify_otp")

    return render(request, "register.html")

from django.contrib.auth import login
from django.shortcuts import render, redirect
from .models import EmailOTP
from .utils import generate_otp, send_otp_email
from django.contrib.auth.models import User

def verify_otp(request):
    user_id = request.session.get("pending_user_id")

    if not user_id:
        return redirect("register")

    user = User.objects.get(id=user_id)
    otp_obj, _ = EmailOTP.objects.get_or_create(user=user)

    error = None
    message = None

    # RESEND OTP
    if request.method == "POST" and "resend" in request.POST:
        new_otp = generate_otp()
        otp_obj.otp = new_otp
        otp_obj.save()

        send_otp_email(user.email, new_otp)
        message = "New OTP sent to your email."

    # VERIFY OTP
    elif request.method == "POST":
        entered_otp = request.POST.get("otp")

        if otp_obj.otp == entered_otp and not otp_obj.is_expired():
            user.is_active = True
            user.save()

            otp_obj.delete()
            request.session.pop("pending_user_id", None)

            return redirect("login")

        error = "Wrong OTP or expired code"

    return render(request, "verify_otp.html", {
        "error": error,
        "message": message,
        "email": user.email
    })

from django.shortcuts import render, get_object_or_404
from .models import BlogPost


def blog_list(request):
    posts = BlogPost.objects.filter(published=True)
    return render(request, 'blog/list.html', {'posts': posts})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    return render(request, 'blog/detail.html', {'post': post})

@staff_member_required
def reports(request):
    context = {
        "total_orders": Order.objects.count(),
        "total_shipments": Shipment.objects.count(),
        "total_customers": User.objects.count(),
        "revenue": Order.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    }
    return render(request, "dashboard/reports.html", context)

from . import views
def change_email(request):
    user_id = request.session.get("pending_user_id")

    if not user_id:
        return redirect("register")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        new_email = request.POST.get("email")

        user.email = new_email
        user.save()

        otp_obj, _ = EmailOTP.objects.get_or_create(user=user)
        new_otp = generate_otp()
        otp_obj.otp = new_otp
        otp_obj.save()

        send_otp_email(new_email, new_otp)

        return redirect("verify_otp")

from django.contrib.auth import logout
from django.shortcuts import redirect

def admin_logout(request):
    logout(request)
    return redirect("controldash")   # sends user back to admin login page
import json

from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.conf import settings

from google.oauth2 import id_token
from google.auth.transport import requests

from .models import Profile


@csrf_exempt
def google_one_tap_callback(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "POST required"},
            status=405
        )

    try:
        # =========================
        # GET TOKEN
        # =========================
        token = request.POST.get("credential")

        if not token:
            try:
                data = json.loads(request.body.decode("utf-8"))
                token = data.get("credential")
            except Exception:
                token = None

        if not token:
            return JsonResponse(
                {"success": False, "message": "No credential received"},
                status=400
            )

        # =========================
        # VERIFY GOOGLE TOKEN
        # =========================
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID   # ✅ FIXED HERE
        )

        email = idinfo.get("email")
        name = idinfo.get("name", "")
        picture = idinfo.get("picture", "")
        google_id = idinfo.get("sub", "")

        if not email:
            return JsonResponse(
                {"success": False, "message": "Email not provided"},
                status=400
            )

        # =========================
        # CREATE OR GET USER
        # =========================
        user = User.objects.filter(email=email).first()

        if not user:
            base_username = slugify(email.split("@")[0]) or "user"
            username = base_username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=name
            )
        else:
            if name and user.first_name != name:
                user.first_name = name
                user.save()

        # =========================
        # PROFILE UPDATE
        # =========================
        # =========================
# PROFILE UPDATE
# =========================
        profile, _ = Profile.objects.get_or_create(user=user)

# Always update google id
        profile.google_id = google_id

# Only update avatar if provided
        if picture:
            profile.avatar_url = picture

        profile.save()
     
        # =========================
        # LOGIN USER
        # =========================
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        return JsonResponse({
            "success": True,
            "message": "Login successful",
            "avatar": picture
        })

    except ValueError as e:
        return JsonResponse({
            "success": False,
            "message": f"Google token verification failed: {str(e)}"
        }, status=401)

    except Exception as e:
        import traceback
        traceback.print_exc()

        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import ChangePasswordForm, AddAdminForm
@login_required
def change_password(request):
    form = ChangePasswordForm()

    if request.method == "POST":
        form = ChangePasswordForm(request.POST)

        if form.is_valid():
            old = form.cleaned_data["old_password"]
            new = form.cleaned_data["new_password"]
            confirm = form.cleaned_data["confirm_password"]

            if not request.user.check_password(old):
                messages.error(request, "Old password incorrect")
            elif new != confirm:
                messages.error(request, "Passwords do not match")
            else:
                request.user.set_password(new)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password changed successfully")
                return redirect("dashboard")

    return render(request, "admin/change_password.html", {"form": form})

@login_required
def add_admin(request):
    form = AddAdminForm()

    if request.method == "POST":
        form = AddAdminForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.is_staff = True
            user.is_superuser = True
            user.save()

            messages.success(request, "Admin added successfully")
            return redirect("dashboard")

    return render(request, "admin/add_admin.html", {"form": form})

from django.shortcuts import render
from django.shortcuts import render

def supplier_payments(request):
    return render(request, "supplier_payments.html")


def faq(request):
    return render(request, "faq.html")
from django.shortcuts import render

def custom_404(request, exception):
    return render(request, "404.html", status=404)
from decimal import Decimal

from django.http import HttpResponse
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from django.templatetags.static import static
import os
from django.conf import settings

from .models import Order


def generate_invoice(request, order_id):
    order = Order.objects.get(order_id=order_id)
    from decimal import Decimal

    buying_total = Decimal(order.unit_price) * Decimal(order.quantity)
    supplier_fee = buying_total * Decimal("0.03")
    service_fee = buying_total * Decimal("0.05")
    shipping_fee = Decimal("50.00")
    exchange_rate = Decimal("130.00")

    grand_total = (
        buying_total
        + supplier_fee
        + service_fee
        + shipping_fee
)

    total_kes = grand_total * exchange_rate

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{order.order_id}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    elements = []

    # Logo
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=140, height=60)
        elements.append(logo)

    elements.append(Spacer(1, 15))

    # Company Title
    elements.append(Paragraph("SABBTCo Logistics Invoice", title_style))
    elements.append(Spacer(1, 20))

    # Customer + Order Info
    info = [
        ["Invoice No:", order.order_id],
        ["Customer:", order.user.username],
        ["Product:", order.product_name],
        ["Quantity:", str(order.quantity)],
        ["Shipping Method:", order.shipping_method],
        ["Status:", order.status],
    ]

    info_table = Table(info, colWidths=[150, 350])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1F3AA8")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("BACKGROUND", (1, 0), (1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 25))

    # Pricing Table
    pricing = [
        ["Description", "Amount (USD)"],
        ["Buying Total", f"{buying_total:.2f}"],
        ["Supplier Fee (3%)", f"{supplier_fee:.2f}"],
        ["Service Fee (5%)", f"{service_fee:.2f}"],
        ["Shipping Fee", f"{shipping_fee:.2f}"],
        ["Grand Total", f"{grand_total:.2f}"],
        ["Total in KES", f"{total_kes:.2f}"],
    ]

    pricing_table = Table(pricing, colWidths=[320, 180])
    pricing_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F41E2D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("BACKGROUND", (0, 1), (-1, -2), colors.whitesmoke),

        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#1F3AA8")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))

    elements.append(pricing_table)
    elements.append(Spacer(1, 25))

    # Footer
    footer = """
    Thank you for choosing SABBTCo.<br/>
    Shenzhen to the World 🌍<br/><br/>
    Email: support@sabbtco.com<br/>
    Phone: +254727698319
    """

    elements.append(Paragraph(footer, styles["BodyText"]))

    doc.build(elements)

    return response