from django.contrib import admin

# Register your models here.

from django.contrib.auth.admin import UserAdmin
from .models import Municipality, CustomUser

admin.site.register(Municipality)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('User Type', {'fields': ('is_official', 'is_resident', 'municipality')}),
    )
