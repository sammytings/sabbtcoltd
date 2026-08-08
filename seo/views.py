from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import SEOPage

def seo_page(request, slug):
    page = get_object_or_404(SEOPage, slug=slug)
    return render(request, "seo/page.html", {"page": page})