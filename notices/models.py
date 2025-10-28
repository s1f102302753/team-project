# notices/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# ------------------------
# 自治体モデル
# ------------------------
class Municipality(models.Model):
    """自治体（市区町村）"""
    name = models.CharField(max_length=100)
    prefecture = models.CharField(max_length=50)
    api_url = models.URLField(blank=True, null=True, help_text="ニュースAPIのURL")

    class Meta:
        verbose_name = "自治体"
        verbose_name_plural = "自治体"

    def __str__(self):
        return f"{self.prefecture} {self.name}"


# ------------------------
# ユーザーモデル
# ------------------------
class CustomUser(AbstractUser):
    """拡張ユーザー"""
    ROLE_CHOICES = (
        ('resident', '住民'),
        ('staff', '自治体職員'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='resident')
    municipality = models.ForeignKey(Municipality, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def is_staff_member(self):
        return self.role == 'staff'

    @property
    def is_resident_member(self):
        return self.role == 'resident'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ------------------------
# ニュースモデル
# ------------------------
class News(models.Model):
    """自治体のお知らせ・ニュース"""
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    url = models.URLField(blank=True, null=True)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']
        verbose_name = "ニュース"
        verbose_name_plural = "ニュース"

    def __str__(self):
        return f"[{self.municipality}] {self.title}"


# ------------------------
# 掲示板投稿モデル
# ------------------------
class Post(models.Model):
    """掲示板投稿"""
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title