from django.contrib import admin
from .models import ModelKey, UserKeyBind

# Register your models here.
class UserKeyBindInline(admin.TabularInline):
    model = UserKeyBind
    extra = 0
    autocomplete_fields = ['user']

@admin.register(ModelKey)
class ModelKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_id', 'quick_model_id', 'lyria_model_id')
    search_fields = ('name', )
    inlines = [UserKeyBindInline]
