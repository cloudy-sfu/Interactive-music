import importlib
import json
import os

from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from google import genai
from google.genai import types

from UserConfig.models import UserKeyBind
from .models import Conversation, Message

with open("Conversation/llm_prompts/conversation_title") as f:
    prompts_conv_title = f.read()
with open("Conversation/llm_prompts/conversation") as f:
    prompts_conv = f.read()



@login_required(login_url='login')
def create_conversation(request):
    conversation = Conversation.objects.create(owner=request.user)
    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required(login_url='login')
def conversation_list(request):
    conversations = Conversation.objects.filter(owner=request.user).order_by(
        '-created_time')
    return render(request, 'Conversation/conversation_list.html',
                  {'conversations': conversations})


@login_required(login_url='login')
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, owner=request.user)
    musics = conversation.music.only('id', 'created_time').order_by('created_time')
    messages = conversation.messages.all().order_by('created_time')
    return render(request, 'Conversation/conversation_detail.html', {
        'conversation': conversation,
        'diagrams': musics,
        'messages': messages,
        # 'syntax_choices': Diagram.SyntaxChoice.choices,
    })


@login_required(login_url='login')
def delete_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, owner=request.user)
    if request.method == 'POST':
        conversation.delete()
    return redirect('conversation_list')


@login_required(login_url='login')
@require_POST
def chat_stream(request, conversation_id):
    try:
        data = json.loads(request.body)
        raw_message = data.get('message')
        if not raw_message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        user_message_content = raw_message.strip()
        conversation = get_object_or_404(
            Conversation, id=conversation_id, owner=request.user)

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
        if not user_key_bind.model_key:
            raise ValueError("No model key bound.")
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    if not user_key_bind.model_key:
        return JsonResponse({
            'error': 'No access to large language model resources. Please contact the '
                     'administrator.'
        }, status=400)
    model_key = user_key_bind.model_key
    client = genai.Client(api_key=model_key.model_api_key)

    try:
        chat = client.chats.create(
            model=model_key.model_id,
            config=types.GenerateContentConfig(
                system_instruction=prompts_conv
            ),
            history=gemini_history
        )
    except Exception as e:
        return JsonResponse({'error': f"Failed to initialize model: {e}"}, status=500)

    # Title generation
    if not conversation.title:
        try:
            title_chat = client.chats.create(
                model=model_key.quick_model_id,
                config=types.GenerateContentConfig(
                    system_instruction=prompts_conv_title),
                history=[]
            )
            title_response = title_chat.send_message(user_message_content)
            if title_response.text:
                conversation.title = title_response.text.strip()
                conversation.save()
        except Exception:
            pass

    def event_stream():
        _ = client  # hold reference to prevent client being closed
        full_response = ""
        try:
            response = chat.send_message_stream(user_message_content)
        except Exception as e1:
            yield str(e1)
            return

        for chunk in response:
            try:
                text = chunk.text
                if text:
                    full_response += text
                    yield text
            except ValueError:
                yield "Content filtered."

        if full_response:
            Message.objects.create(conversation=conversation,
                                   role=Message.RoleChoices.USER,
                                   content=user_message_content)
            Message.objects.create(conversation=conversation,
                                   role=Message.RoleChoices.MODEL,
                                   content=full_response.strip())

    return StreamingHttpResponse(event_stream(), content_type='text/plain')
