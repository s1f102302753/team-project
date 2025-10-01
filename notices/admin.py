from django.contrib import admin

# Register your models here.

# notices/admin.py
from django.contrib import admin
from .models import Notice

admin.site.register(Notice)
