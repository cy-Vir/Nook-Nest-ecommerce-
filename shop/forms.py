from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("first_name", "username", "email", "password1", "password2")


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    city = forms.CharField(max_length=80)
    postal_code = forms.CharField(max_length=12)
    payment_method = forms.ChoiceField(choices=[("demo_card", "Demo Card — payment simulation"), ("cash", "Cash on delivery")])
