from django.shortcuts import render
from django.http import JsonResponse
from .models import ChatData
from openai import OpenAI
from dotenv import load_dotenv
import os, requests

# Create your views here.



load_dotenv()
client = OpenAI()


NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY",)
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "nvidia/nemotron-3-nano-30b-a3b"

def chat_context(user_input):
    SYSTEM_PROMPT = f"""
    you are a chatbot
    
    """
    resp = requests.post(
                        NVIDIA_API_URL,
                        headers={
                            "Authorization": f"Bearer {NVIDIA_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": NVIDIA_MODEL,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_input},
                            ],
                            "max_tokens": 4096,
                        },
                        timeout=120,
                    )
    data = resp.json()
    answer = data['choices'][0]['message']['content'] 
    return answer



def chat_index(request):
    chat_data = ChatData.objects.all()

    if request.method == "POST":
        name = request.POST.get("data")
        print("User input:", name)

        answer = chat_context(name)
        print(answer)

        ChatData.objects.create(
            user_chat=name,
            response_chat=answer
        )

        return JsonResponse({
            "answer": answer
        })

    return render(request, "home.html", {
        "chat_data": chat_data
    })