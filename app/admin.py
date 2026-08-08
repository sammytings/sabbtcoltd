from django.contrib import admin
from .models import (
    Shipment, ShipmentPhoto, Order, OrderTimeline, Document, PackagePhoto,
    Notification, ClientNotification, Banner, Supplier, SupplierProduct,
    SupplierShipment, UserProfile, SourcingRequest, ItemManifest, Feedback,
    KnowledgeBase, ChatSession, ChatMessage, Testimonial, ShipmentTimeline
)

# ==========================================================
# SAFELY UNREGISTER (prevents double registration conflicts)
# ==========================================================
for model in [Shipment, Order]:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass


# ==========================================================
# INLINE LAYOUT DEFINITIONS
# ==========================================================
class ShipmentPhotoInline(admin.TabularInline):
    model = ShipmentPhoto
    extra = 3


class OrderTimelineInline(admin.TabularInline):
    model = OrderTimeline
    extra = 1


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1


class PackagePhotoInline(admin.TabularInline):
    model = PackagePhoto
    extra = 2


class ItemManifestInline(admin.TabularInline):
    model = ItemManifest
    extra = 1


# ==========================================================
# 🔥 ADMIN ACTION (NEW: BULK STATUS UPDATE)
# ==========================================================



def mark_in_transit(modeladmin, request, queryset):
    for shipment in queryset:
        shipment.status = "in_transit"
        shipment.save()

        # Timeline entry
        ShipmentTimeline.objects.create(
            shipment=shipment,
            status="in_transit",
            message=STATUS_MESSAGES["in_transit"]
        )

mark_in_transit.short_description = "Mark selected shipments as In Transit"


# ==========================================================
# MODEL ADMIN OVERRIDES
# ==========================================================
@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'container_number',
        'status',
        'mode_of_delivery',
        'tracking_number',
        'updated_at'
    )

    list_filter = ('status', 'mode_of_delivery')
    search_fields = ('container_number', 'tracking_number', 'destination')
    ordering = ('-updated_at',)
    inlines = [ShipmentPhotoInline]

    # ✅ ADDED ACTIONS (DO NOT REMOVE EXISTING FUNCTIONALITY)
    actions = [mark_in_transit]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id',
        'full_name',
        'product_name',
        'quantity',
        'shipping_method',
        'status',
        'created_at',
        'product_image'
    )

    list_filter = ('status', 'shipping_method', 'created_at')
    search_fields = (
        'order_id',
        'full_name',
        'email',
        'phone_number',
        'product_name'
    )

    ordering = ('-created_at',)
    inlines = [OrderTimelineInline, DocumentInline, PackagePhotoInline]


@admin.register(SourcingRequest)
class SourcingRequestAdmin(admin.ModelAdmin):
    list_display = (
        'customer_name',
        'product_name',
        'quantity',
        'shipping_method',
        'is_processed',
        'created_at'
    )

    list_filter = ('is_processed', 'shipping_method')
    search_fields = ('customer_name', 'product_name', 'email')
    inlines = [ItemManifestInline]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_company', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'message')
    list_editable = ('is_approved',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'approved', 'created_at')
    list_filter = ('approved', 'created_at')
    search_fields = ('name', 'comment')
    list_editable = ('approved',)


# ==========================================================
# CORE SYSTEM REGISTRATIONS (UNCHANGED)
# ==========================================================
admin.site.register(Notification)
admin.site.register(ClientNotification)

admin.site.register(Supplier)
admin.site.register(SupplierProduct)
admin.site.register(SupplierShipment)
admin.site.register(UserProfile)
admin.site.register(KnowledgeBase)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)

from django.contrib import admin
from .models import Banner

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "start_date", "end_date")
    list_filter = ("is_active",)
    search_fields = ("title",)

from django.contrib import admin
from .models import SupplierPaymentRequest


@admin.register(SupplierPaymentRequest)
class SupplierPaymentRequestAdmin(admin.ModelAdmin):

    list_display = (
        "request_id",
        "full_name",
        "supplier_name",
        "currency",
        "status",
        "created_at",
    )

    list_filter = ("status", "currency")

    search_fields = ("request_id", "full_name", "supplier_name")

    readonly_fields = ("request_id", "created_at")


from django.contrib import admin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'published', 'created_at')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'keywords')
    list_filter = ('published',)