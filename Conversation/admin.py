from django.contrib import admin
from .models import Conversation, Message

# Register your models here.
class MessagesInline(admin.TabularInline):
    model = Message
    extra = 0
    autocomplete_fields = ['conversation']

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('owner', 'title', 'created_time', 'modified_time')
    list_filter = ('owner__username', 'created_time',)
    search_fields = ('owner__username', 'title')
    inlines = [MessagesInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'created_time')
    list_filter = ('role', 'created_time')
    search_fields = ('content',)
