from django.db import models

# Create your models here.

from django.db import models
from users.models import Municipality, CustomUser



class Notice(models.Model):
    """行政・自治体からのお知らせ（回覧板の記事など）"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    municipality = models.ForeignKey(
        Municipality,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    posted_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"[{self.municipality}] {self.title}"
