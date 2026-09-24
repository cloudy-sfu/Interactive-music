from django.db import models

from Conversation.models import Conversation


# Create your models here.
class Music(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="music")
    audio = models.BinaryField()
    prompt = models.TextField(blank=False)
    created_time = models.DateTimeField(auto_now_add=True)
    lyrics = models.TextField(blank=True)
    mime_type = models.TextField(blank=True)
