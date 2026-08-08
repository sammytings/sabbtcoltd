from django.contrib.auth import views as auth_views
from django.urls import path
from app.views import controldash
from . import views
from .views import (
    google_one_tap_callback,
    update_order_pricing,
)

urlpatterns = [
    # --- Main Marketing / Core Pages ---
    path("", views.index, name="index"),
    path("services/", views.services, name="services"),
    path("about/", views.about, name="about"),
    path("quote/", views.quote, name="quote"),
    path("faq/", views.faq, name="faq"),
    path("feedback/", views.feedback_view, name="feedback"),
    path("submit_feedback/", views.submit_feedback_view, name="submit_feedback"),
    path("tracking/", views.tracking_search, name="tracking_search"),
    path("track/<str:container_number>/", views.track_container, name="track_container"),

    # --- Authentication & Profile ---
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("change-email/", views.change_email, name="change_email"),
    path("password-change/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("google-one-tap-callback/", google_one_tap_callback, name="google_one_tap_callback"),

    # --- Customer Dashboard & Orders ---
    path("dashboard/", views.dashboard, name="dashboard"),
    path("orders/", views.orders, name="orders"),
    path("Orders-alt/", views.Orders_view, name="Orders_alt"), # Renamed to avoid confusion with lowercase orders
    path("orders/<str:order_id>/", views.order_detail, name="order_detail"),
    path("orders/<str:order_id>/update-pricing/", update_order_pricing, name="update_order_pricing"),
    path("order/<str:order_id>/upload/", views.upload_document, name="upload_document"),
    path("invoice/<str:order_id>/", views.generate_invoice, name="generate_invoice"),
    path("dashboard/order/<str:order_id>/", views.update_order, name="update_order"),

    # --- Supplier Management ---
    path("become-supplier/", views.become_supplier, name="become_supplier"),
    path("become-a-supplier/", views.supplier_signup_view, name="supplier_signup"),
    path("become-a-supplier/success/", views.supplier_signup_success, name="supplier_signup_success"),
    path("supplier/dashboard/", views.supplier_dashboard, name="supplier_dashboard"),
    path("suppliers/dashboard-alt/", views.supplier_dashboard_view, name="supplier_dashboard_view"),
    path("supplier-login/<uidb64>/<token>/", views.supplier_token_login, name="supplier_token_login"),
    path("supplier-payments/", views.supplier_payments, name="supplier_payments"),
    path("supplier-payments/read/<int:pk>/", views.supplier_payment_read, name="supplier_payment_read"),

    # --- Administration & Management Panel ---
    path("controldash/", views.controldash, name="controldash"),
    path("admin/shipments/", views.shipment_dashboard, name="shipment_dashboard"),
    path("dashboard/shipments/add/", views.add_shipment_view, name="add_shipment"),
    path("shipments/<str:container_number>/", views.shipment_detail_view, name="shipment_detail"),
    path("dashboard/customers/", views.customers_view, name="customers"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/read/", views.mark_notifications_read, name="mark_notifications_read"),
    path("add-admin/", views.add_admin, name="add_admin"),
    path("admin-logout/", views.admin_logout, name="admin_logout"),
    path("reports/", views.reports, name="reports"),
    path("chatbot/", views.logistics_ai_chat, name="chatbot"),
# --- News Feed ---
# ============================================================
# NEWS FEED
# ============================================================

path("news/", views.news_list, name="news_list"),
path(
    "news/<slug:slug>/",
    views.news_detail,
    name="news_detail"
),

# Admin News Management
path(
    "controldash/news/",
    views.news_admin_list,
    name="news_admin_list"
),

path(
    "controldash/news/create/",
    views.news_create,
    name="news_create"
),

path(
    "controldash/news/<int:pk>/edit/",
    views.news_edit,
    name="news_edit"
),

path(
    "controldash/news/<int:pk>/delete/",
    views.news_delete,
    name="news_delete"
),
    
]
