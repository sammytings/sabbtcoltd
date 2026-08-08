from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
import uuid

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if not user.username:
            base = user.email.split("@")[0] if user.email else "user"
            user.username = f"{base}_{uuid.uuid4().hex[:6]}"

        return user