from django import forms
from django.contrib.auth.forms import AuthenticationForm

class CustomLoginForm(AuthenticationForm):
    municipality_id = forms.CharField(label="自治体ID", max_length=100)
