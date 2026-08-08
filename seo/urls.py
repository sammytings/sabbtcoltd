from django.urls import path
from .views import seo_page

urlpatterns = [
    path("<slug:slug>/", seo_page, name="seo_page"),
]