from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

# Create your models here.

class Municipality(models.Model):
    """自治体（市区町村など）の情報"""
    name = models.CharField(max_length=100)
    prefecture = models.CharField(max_length=50)
    api_url = models.URLField(default='https://example.com/dummy')  # 自治体のAPIエンドポイントURL

    def __str__(self):
        return f"{self.prefecture} {self.name}"
    
class CustomUser(AbstractUser):
    """拡張ユーザー"""
    municipality = models.ForeignKey(
        Municipality,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    is_official = models.BooleanField(default=False)   # 自治体職員
    is_resident = models.BooleanField(default=True)    # 住民

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # 衝突回避
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # 衝突回避
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username
