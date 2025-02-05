from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["shopee_id", "first_name", "last_name", "telefone", "email", "password1", "password2"]
