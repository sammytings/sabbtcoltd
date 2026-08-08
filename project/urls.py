from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from django.contrib.sitemaps.views import sitemap   # ✅ ADD THIS
from app.sitemaps import StaticViewSitemap
from app import views
from django.contrib.auth import views as auth_views

# ==========================================================
# SITEMAP CONFIG (DEFINE FIRST)
# ==========================================================
sitemaps = {
    "static": StaticViewSitemap,
}

# ==========================================================
# NON-TRANSLATED URLS
# ==========================================================
urlpatterns = [
    path('admin/', admin.site.urls),
     path(
        "accounts/password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="account/password_change.html"
        ),
        name="account_change_password",
    ),

    path(
        "accounts/password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="account/password_change_done.html"
        ),
        name="password_change_done",
    ),

    path("accounts/", include("allauth.urls")),
    path("chatbot/", views.logistics_ai_chat, name="chatbot"),
   

    path('i18n/', include('django.conf.urls.i18n')),
    path("seo/", include("seo.urls")),
    


    # ✅ FIXED SITEMAP
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}),
]

# ==========================================================
# TRANSLATED URLS
# ==========================================================
urlpatterns += i18n_patterns(
    path('', include('app.urls')),
    
)
handler404 = 'app.views.custom_404'
# ==========================================================
# MEDIA FILES
# ==========================================================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )