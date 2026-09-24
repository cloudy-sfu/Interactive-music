import base64

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from google import genai

from AudioGeneration.models import Music
from Conversation.models import Conversation
from UserConfig.models import UserKeyBind

with open("AudioGeneration/llm_prompts/lyria_prompt_composing") as f:
    prompts_conv_to_lyria = f.read()


# Create your views here.
@login_required(login_url='login')
@require_POST
def generate_lyria_prompt(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, owner=request.user)
    try:
        past_messages = conversation.messages.order_by('created_time')
        gemini_history = []
        for msg in past_messages:
            if msg.content:
                gemini_history.append({
                    "role": msg.get_role_display(),
                    "parts": [{"text": msg.content}]
                })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    try:
        user_key_bind = UserKeyBind.objects.get(user=request.user)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    if not user_key_bind.model_key:
        return JsonResponse({
            'error': 'No access to large language model resources. Please contact the '
                     'administrator.'
        }, status=400)
    model_key = user_key_bind.model_key

    try:
        client = genai.Client(api_key=model_key.model_api_key)
        chat = client.chats.create(
            model=model_key.model_id,
            config=genai.types.GenerateContentConfig(
                system_instruction=prompts_conv_to_lyria
            ),
            history=gemini_history
        )
    except Exception as e:
        return JsonResponse({'error': f"Failed to initialize model: {e}"}, status=500)
    try:
        response = chat.send_message("Based on the conversation above, generate the final "
                                     "Google Lyria prompt.")
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    if response.text is None:
        return JsonResponse({
            'error': f"Model {model_key.model_id} fails to generate the prompt for Google "
                     f"Lyria based on the conversation."
        }, status=500)
    return JsonResponse({"prompt": response.text})


@login_required(login_url='login')
@require_POST
def generate_music(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, owner=request.user)
    prompt = request.POST.get('prompt')
    if not prompt:
        return JsonResponse({'error': 'Google Lyria prompt is empty.'}, status=500)

    try:
        user_key_bind = UserKeyBind.objects.get(user=request.user)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    if not user_key_bind.model_key:
        return JsonResponse({
            'error': 'No access to large language model resources. Please contact the '
                     'administrator.'
        }, status=400)
    model_key = user_key_bind.model_key

    try:
        client = genai.Client(api_key=model_key.model_api_key)
        interaction = client.interactions.create(
            model=model_key.lyria_model_id, input=prompt,
            response_format={"type": "audio"},
        )
    except Exception as e:
        return JsonResponse({'error': f"Failed to initialize model: {e}"}, status=500)
    if interaction.status != "completed":
        return JsonResponse({
            'error': f'The request is {interaction.status}. Error: {interaction.errors}'
        }, status=500)
    if not (interaction.output_audio and interaction.output_audio.data):
        return JsonResponse(
            {'error': 'Google Lyria fails to generate an audio.'}, status=500)
    music = Music(
        conversation=conversation,
        audio=base64.b64decode(interaction.output_audio.data),
        prompt=prompt,
    )
    if interaction.output_audio.mime_type:
        music.mime_type = interaction.output_audio.mime_type
    if interaction.output_text:
        music.lyrics = interaction.output_text
    music.save()
    return JsonResponse({
        'status': 'success',
        'diagram': {
            'id': music.id,
            'lyrics': music.lyrics,
            'mime_type': music.mime_type,
            'prompt': prompt,
        }
    })


@login_required(login_url='login')
def view_music(request, music_id):
    music = get_object_or_404(Music, conversation__owner=request.user, id=music_id)
    return JsonResponse({
        'lyrics': music.lyrics,
        'mime_type': music.mime_type,
        'prompt': music.prompt,
    })


@login_required(login_url='login')
def view_audio(request, music_id):
    music = get_object_or_404(Music, conversation__owner=request.user, id=music_id)
    response = HttpResponse(music.audio, content_type=music.mime_type)
    response["Accept-Ranges"] = "bytes"
    return response
