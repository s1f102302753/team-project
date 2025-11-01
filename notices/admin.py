from django.contrib import admin

# Register your models here.

# notices/admin.py
from django.contrib import admin
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'municipality', 'published_at')
    search_fields = ('title', 'content')
    list_filter = ('municipality',)

# 他のモデルも同様に登録可能

