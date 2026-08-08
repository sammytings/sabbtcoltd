from django import forms
from .models import Supplier, Order


# =========================================
# ORDER FORM
# =========================================
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        # Explicitly declare fields instead of __all__ to bypass automatic calculations
        fields = [
            'full_name', 'email', 'phone_number', 'address', 
            'product_name', 'quantity', 'unit_price', 'extra_charges'
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Product Name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Quantity'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Address', 'rows': 3}),
        }


# =========================================
# SUPPLIER REGISTER FORM
# =========================================

class SupplierRegisterForm(forms.ModelForm):

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'Enter Password'
            }
        )
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'Confirm Password'
            }
        )
    )

    class Meta:
        model = Supplier

        fields = [
            'company_name',
            'email',
            'phone',
            'country',
            'address',
        ]

        widgets = {

            'company_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Company Name'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Business Email'
            }),

            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Phone Number'
            }),

            'country': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Country'
            }),

            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Business Address',
                'rows': 3
            }),
        }

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:

            if password1 != password2:
                raise forms.ValidationError(
                    "Passwords do not match."
                )

        return cleaned_data

# app/forms.py
from django import forms
from .models import Supplier

class SupplierRegistrationForm(forms.ModelForm):
    class Meta:
        model = Supplier
        # 🌟 FIX: Change 'supply_category' to 'product_category'
        fields = [
            'company_name', 
            'contact_person', 
            'email', 
            'phone', 
            'country', 
            'address', 
            'product_category' # 
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Shanghai Electronics Ltd'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'business@company.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +86... or +254...'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., China, Turkey, UAE'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Office/Warehouse physical location'}),
            # 🌟 FIX: Update this key name here as well
            'product_category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Electronics, Fashion, Spare Parts'}),
        }
from django import forms
from .models import Testimonial

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'role_company', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., J. Mwangi', 'class': 'form-control'}),
            'role_company': forms.TextInput(attrs={'placeholder': 'e.g., Importer · Nairobi', 'class': 'form-control'}),
            'message': forms.Textarea(attrs={'placeholder': 'Write your feedback here...', 'rows': 4, 'class': 'form-control'}),
        }

from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):

    class Meta:
        model = Feedback

        fields = [
            "name",
            "rating",
            "message",
        ]

from django import forms
from django.contrib.auth.models import User


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput())
    new_password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())


class AddAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ["username", "email", "password"]