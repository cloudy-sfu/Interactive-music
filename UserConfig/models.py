from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class ModelKey(models.Model):
    name = models.CharField(max_length=128, unique=True)
    model_provider = models.CharField(max_length=32, default="gemini", editable=False)
    model_id = models.CharField(max_length=64, blank=False)
    quick_model_id = models.CharField(max_length=64, blank=False)
    lyria_model_id = models.CharField(max_length=64, blank=False)
    model_api_key = models.TextField(blank=False)

    def __str__(self):
        return self.name


class UserKeyBind(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, auto_created=True)
    model_key = models.ForeignKey(ModelKey, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.user.username
