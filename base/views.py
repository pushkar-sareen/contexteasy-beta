from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from openai import OpenAI
from dotenv import load_dotenv
from .models import Chat, UploadedFile, DatabaseChat,YoutbeLink,DatabaseLink,UploadedBackup, URLLink
from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
import os
from django.core.files.base import ContentFile
from django.utils.text import slugify
from pathlib  import Path
from django.conf import settings
from langchain_core.documents import Document
from pypdf import PdfReader
import pandas as pd
import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import trafilatura
import tldextract
import re
import string
import traceback




# Create your views here.

load_dotenv()
client = OpenAI()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY",)
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"



def health(request):
    return JsonResponse({"status": "ok"})


def load_documents(user):
    documents = []

    uploaded_files = UploadedFile.objects.filter(user=user)

    for uploaded in uploaded_files:
        file = uploaded.file

        extension = file.name.lower().rsplit(".", 1)[-1]

        if extension not in {"txt", "pdf", "md", "csv"}:
            continue

        if extension == "pdf":
            with file.open("rb") as f:
                reader = PdfReader(f)

                content = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

        elif extension == "csv":
            with file.open("rb") as f:
                data = f.read()

            df = pd.read_csv(io.BytesIO(data))
            content = df.to_csv(index=False)

        else:
            with file.open("rb") as f:
                content = f.read().decode(
                    "utf-8",
                    errors="ignore"
                )

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "path": file.name,
                },
            )
        )

    return documents



def get_title(video_url):
    endpoint = "https://www.youtube.com/oembed"
    response = requests.get(
        endpoint,
        params={
            "url": video_url,
            "format": "json"
        },
        timeout=10
    )
    response.raise_for_status()

    return response.json()["title"]



def youtube_data(user, youtube_url):
    url = 'https://transcriptapi.com/api/v2/youtube/transcript'
    params = {'video_url': youtube_url, 'format': 'json'}
    r = requests.get(url, params=params, headers={'Authorization': 'Bearer ' + YOUTUBE_API_KEY}, timeout=30)
    r.raise_for_status()
    raw_data = r.json()
    transcript= [i['text'] for i in raw_data['transcript']]
    return transcript



def generate_script(user, youtube_url):
    data = youtube_data(user, youtube_url)
    title = get_title(youtube_url)

    content = "\n".join(data)

    filename = f"{slugify(title) or 'youtube-transcript'}.txt"

    uploaded = UploadedFile(user=user)

    uploaded.file.save(
        filename,
        ContentFile(content.encode("utf-8")),
        save=True,
    )

    return uploaded



def read_webpage(url):
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        raise Exception("Unable to fetch webpage.")
    text = trafilatura.extract(
        downloaded,
        include_links=False,
        include_tables=True,
        include_comments=False,
    )
    return text



def get_indexing(user):
    docs = load_documents(user=user)
    collection_name = f"{user}_documents_collection"

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=400
    )
    chunks = text_splitter.split_documents(docs)

    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-large"
    )

    vector_store = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_model,
        url="http://localhost:6333/",
        collection_name= collection_name,
        force_recreate=True
    )

    return vector_store, collection_name




def get_context(user, query):
    get_indexing(user)
    collection_name = f"{user}_documents_collection"
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    vector_db = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url="http://localhost:6333/",
        collection_name=collection_name
    )

    results = vector_db.similarity_search(query, k=5)

    context = "\n\n".join([
        f"""
    CONTENT:
    {r.page_content}

    SOURCE FILE:
    {r.metadata.get('file_name', 'unknown')}
    PATH:
    {r.metadata.get('path', 'unknown')}
    """
        for r in results
    ])
    return context


BOT_NAME = "ContextEasy"         
MODEL_NAME = "ContextEasy"

GENERIC_QA = {
    # Greetings
    "hi": "Hi there! How can I help you today?",
    "hello": "Hello! What can I do for you?",
    "hey": "Hey! How can I help?",
    "good morning": "Good morning! How can I help you today?",
    "good afternoon": "Good afternoon! What can I do for you?",
    "good evening": "Good evening! How can I help?",
    "namaste": "Namaste! How can I help you today?",

    # Small talk
    "how are you": "I'm doing well, thanks for asking! How can I help you?",
    "how are you doing": "I'm doing great! What can I help you with?",
    "whats up": "Not much, just ready to help. What do you need?",
    "how is it going": "All good here! How can I help?",

    # Identity
    "who are you": f"I'm {BOT_NAME}, an AI assistant here to answer questions and help with tasks.",
    "what is your name": f"My name is {BOT_NAME}.",
    "whats your name": f"My name is {BOT_NAME}.",
    "are you a bot": "Yes, I'm an AI assistant, not a human.",
    "are you human": "No, I'm an AI assistant.",
    "are you real": "I'm a real AI assistant, though not a person.",

    # Model questions
    "which model are you using": f"I'm powered by {MODEL_NAME}.",
    "which model are you": f"I'm powered by {MODEL_NAME}.",
    "what model are you": f"I'm powered by {MODEL_NAME}.",
    "what model do you use": f"I'm powered by {MODEL_NAME}.",
    "which llm are you": f"I'm powered by {MODEL_NAME}.",
    "who made you": "I was built by Pingaksha Labs and set up by my developers for this app.",
    "who created you": "I was built by Pingaksha Labs and set up by my developers for this app.",

    # Capabilities
    "what can you do": "I can answer questions, explain topics, write and edit text, help with code, summarize content, and more.",
    "how can you help me": "Tell me what you're working on and I'll help, whether it's writing, coding, learning, or brainstorming.",
    "help": "Sure! Tell me what you need help with.",
    "can you help me": "Of course! What do you need help with?",

    # Politeness
    "thanks": "You're welcome!",
    "thank you": "You're welcome! Let me know if you need anything else.",
    "ok": "Great! Let me know if you need anything else.",
    "okay": "Great! Let me know if you need anything else.",
    "bye": "Goodbye! Have a great day!",
    "goodbye": "Goodbye! Take care!",
    "see you": "See you later!",
    "good night": "Good night! Sleep well!",
}


def normalize(text: str) -> str:
    """Lowercase, strip punctuation and extra spaces so 'Hi!!' matches 'hi'."""
    text = text.lower().strip()
    text = text.replace("'", "")  # what's -> whats
    text = text.translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", text)


def get_generic_answer(user_input: str):
    """Return a canned answer, or None so you can fall back to the LLM."""
    return GENERIC_QA.get(normalize(user_input))





def chat_context(user, user_input):
    SYSTEM_PROMPT = f"""
    You are a helpful assistant.
    if user asks questions from dictionary response from {GENERIC_QA} 
    otherwise Answer ONLY using the provided context.
    If multiple files are present, use them equally.

    Context:
    {
        get_context(user, user_input)}
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







def delete_chat(request):
    chat = Chat.objects.filter(user_id = request.user.id)
    database = DatabaseChat.objects.all()
    chat.delete()
    return redirect("chat")





def delete_files(request, id):
    uploaded = get_object_or_404(
        UploadedFile,
        id=id,
        user=request.user,
    )

    uploaded.file.delete(save=False)
    uploaded.delete()

    return redirect("chat")


def delete_all_files(request):
    files = UploadedFile.objects.filter(
        user=request.user
    )

    for uploaded in files:
        if uploaded.file:
            uploaded.file.delete(save=False)
        uploaded.delete()

    return redirect("chat")


def delete_link(request, id):
    link = get_object_or_404(YoutbeLink, id=id)
    link.delete()
    return redirect("chat")

def delete_url(request, id):
    link = get_object_or_404(URLLink, id=id)
    link.delete()
    return redirect("chat")


def homepage(request):
    return render(request, "message.html")



def transaction(request):
    return render(request, "pricing.html")


def _index(request):
    user_data = None
    youtube_url = None
    answer = None

def index(request):

    try:
        return _index(request)

    except Exception as e:
        traceback.print_exc()

        return JsonResponse({
            "answer": (
                f"VIEW ERROR: {type(e).__name__}: {str(e)}\n\n"
                f"{traceback.format_exc()}"
            )
        }, status=500)

    
    user_data = None
    youtube_url = None
    answer = None

    if request.user.is_authenticated:
        user_data = User.objects.get(id=request.user.id)

        directory = (
            Path(settings.MEDIA_ROOT)
            / f"uploads/{user_data.email}"
        )
        directory.mkdir(parents=True, exist_ok=True)



    if request.method == "POST" and "data" in request.POST:
        user_input = request.POST.get("data", "").strip()

        if not user_input:
            return JsonResponse(
                {"error": "Message cannot be empty"},
                status=400
            )

        if user_data is None:
            return JsonResponse(
                {"error": "User must be authenticated"},
                status=401
            )

        try:
            
            answer = get_generic_answer(user_input)

            
            if answer is None:
                answer = chat_context(
                    user=user_data,
                    user_input=user_input
                )

        
            Chat.objects.create(
                user=request.user,
                user_input=user_input,
                response=answer
            )

            DatabaseChat.objects.create(
                user_input=user_input,
                response=answer
            )

            return JsonResponse({
                "answer": answer
            })

        # except Exception as e:
        #     print("UPLOAD ERROR:", repr(e))

        #     return JsonResponse(
        #         {
        #             "error": str(e),
        #             "error_type": type(e).__name__,
        #         },
        #         status=500
        #     )
        except Exception as e:
            return JsonResponse({
                "answer": f"{type(e).__name__}: {str(e)}"
            })



    if request.method == "POST" and request.FILES.get("documents"):
        uploaded_file = request.FILES["documents"]

        try:
            uploaded = UploadedFile.objects.create(
                user=user_data,
                file=uploaded_file,
            )

            print("Uploaded:", uploaded.file.name)
            print("URL:", uploaded.file.url)

            documents = load_documents(user=user_data)

            print("Documents:", documents)

            return redirect("chat")

        except Exception as e:
            print("UPLOAD ERROR:", repr(e))
            raise


    if request.method == "POST" and request.POST.get("youtube"):
        try:
            youtube_url = request.POST.get("youtube")

            youtube_title = get_title(youtube_url)

            YoutbeLink.objects.create(
                user=user_data,
                name=youtube_url,
                title=youtube_title
            )

            DatabaseLink.objects.create(
                name=youtube_url,
                title=youtube_title
            )

            generate_script(
                user=user_data,
                youtube_url=youtube_url
            )

            return redirect("chat")

        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=400
            )

    if request.method == "POST" and request.POST.get("url"):
        url = request.POST.get("url")

        try:
            user = request.user

            extracted = tldextract.extract(url)
            url_name = extracted.domain or "webpage"

            webpage_content = read_webpage(url)

            URLLink.objects.create(
                user=user,
                name=url
            )

            filename = (
                f"{slugify(url_name) or 'webpage'}.txt"
            )

            uploaded = UploadedFile(user=user)

            uploaded.file.save(
                filename,
                ContentFile(
                    webpage_content.encode("utf-8")
                ),
                save=True,
            )

            return redirect("chat")

        except Exception as e:
            print("URL ERROR:", repr(e))

            return JsonResponse(
                {"error": str(e)},
                status=400
            )



    file_names = UploadedFile.objects.filter(
        user_id=request.user.id
    )

    chat_data = Chat.objects.filter(
        user_id=request.user.id
    )

    return render(
        request,
        "home.html",
        {
            "chat_data": chat_data,
            "file_names": file_names,
            "answer": answer,
        }
    )