# middleware.py
from django.shortcuts import redirect

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            if request.path not in ['/accounts/login/', '/accounts/google/login/']:
                return redirect('account_login')
        return self.get_response(request)
    

