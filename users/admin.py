from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Municipality, CustomUser

admin.site.register(Municipality)
admin.site.register(CustomUser)