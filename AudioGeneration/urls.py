from django.urls import path
from . import views

urlpatterns = [
    path('generate_lyria_prompt/<int:conversation_id>/', views.generate_lyria_prompt, name='generate_lyria_prompt'),
    path('generate_music/<int:conversation_id>', views.generate_music, name='generate_music'),
    path('music/<int:music_id>', views.view_music),
    path('audio/<int:music_id>', views.view_audio),
]
