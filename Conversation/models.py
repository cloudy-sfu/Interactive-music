from django.contrib.auth.models import User
from django.db import models


class Conversation(models.Model):
    created_time = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return self.title

    def modified_time(self):
        last_message = self.messages.order_by('created_time').last()
        if last_message:
            return last_message.created_time
        else:
            return None


class Message(models.Model):
    class RoleChoices(models.TextChoices):
        SYSTEM = 'S', 'system'
        USER = 'U', 'user'
        MODEL = 'M', 'model'
        TOOL = 'T', 'tool'

    conversation = models.ForeignKey(
        Conversation, related_name='messages', on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=1, choices=RoleChoices.choices)
    content = models.TextField(blank=True)

    def __str__(self):
        return f"Message {self.created_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"


class Image(models.Model):
    image = models.ImageField()
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="images")
