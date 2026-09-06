from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from openai import OpenAI
from dotenv import load_dotenv
from .models import Chat, UploadedFile, DataFiles, DatabaseChat,YoutbeLink,DatabaseLink,UploadedBackup, URLLink
from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
import os
from pathlib  import Path
from django.conf import settings
from langchain_core.documents import Document
from pypdf import PdfReader
import pandas as pd
import requests
from yt_dlp import YoutubeDL
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import trafilatura
import tldextract




# Create your views here.


load_dotenv()
client = OpenAI()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY",)
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "nvidia/nemotron-3-nano-30b-a3b"



def health(request):
    return JsonResponse({"status": "ok"})


def load_documents(user):
    documents = []

    directory = Path(settings.MEDIA_ROOT)/"uploads"/user.email

    if not directory.exists():
        return documents

    for file_path in directory.rglob("*"):
        if file_path.suffix.lower() not in {".txt", ".pdf", ".md", ".csv"}:
            continue

        if file_path.suffix.lower() == ".pdf":
            reader = PdfReader(file_path)
            content = "\n".join(
                (page.extract_text() or "")
                for page in reader.pages
            )

        elif file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
            content = df.to_csv(index=False)

        else:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "path": str(file_path.relative_to(directory))
                },
            )
        )

    return documents




# def load_documents(user):
#     documents = []
#     directory = Path(settings.MEDIA_ROOT) / f"uploads/{user.email}"

#     # if not directory.exists():
#     #     return documents
    
#     for file_path in directory.rglob("*"):
#         if file_path.suffix.lower() in {'.txt', '.pdf', '.md', '.csv'}:

#             if file_path.suffix.lower() == ".pdf":
#                 reader = PdfReader(file_path)
#                 content = "\n".join(
#                     (page.extract_text() or "") for page in reader.pages
#                 )

#             elif file_path.suffix.lower() == ".csv":
#                 df = pd.read_csv(file_path)
#                 content = df.to_csv(index=False)

#             else:
#                 content = file_path.read_text(encoding="utf-8", errors="ignore")

#             documents.append(
#                 Document(
#                     page_content=content,
#                     metadata={"path": str(file_path.relative_to(directory))}
#                 )
#             )
#     return documents


def get_title(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("title", "Unknown title")



def youtube_data(user, youtube_url):
    url = 'https://transcriptapi.com/api/v2/youtube/transcript'
    params = {'video_url': youtube_url, 'format': 'json'}
    r = requests.get(url, params=params, headers={'Authorization': 'Bearer ' + YOUTUBE_API_KEY}, timeout=30)
    r.raise_for_status()
    raw_data = r.json()
    transcript= [i['text'] for i in raw_data['transcript']]
    return transcript

def generate_script(user,youtube_url):
    data= youtube_data(user, youtube_url)
    title = get_title(youtube_url)
    directory = Path(settings.MEDIA_ROOT) / f"uploads/{user.email}"
    with open(f"{directory}/{title}.txt", "w", encoding="utf-8") as f:
        for line in data:
            f.write(line + "\n")



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
    # collection_name= f"documents_collection"

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



def chat_context(user, user_input):
    SYSTEM_PROMPT = f"""
    You are a helpful assistant.
    if user asks questions from dictionary response from dictionary 
    
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
    uploaded = get_object_or_404(UploadedFile, id=id)
    if uploaded.file and os.path.isfile(uploaded.file.path):
        os.remove(uploaded.file.path)
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
    return render(request, "index-2.html")



def transaction(request):
    return render(request, "pricing.html")



def index(request):
    user_data = None
    youtube_url= None

    if request.user.is_authenticated:
        user_data = User.objects.get(id=request.user.id)
        directory = Path(settings.MEDIA_ROOT) / f"uploads/{user_data.email}"
        directory.mkdir(parents=True, exist_ok=True)
    
    try:
        if request.method == "POST":
            user_input = request.POST.get("data")
            answer = chat_context(user=user_data, user_input=user_input)
            
            Chat.objects.create(
                user = request.user if request.user.is_authenticated else None,
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
    except:
        pass
    
    if request.method == "POST" and request.FILES.get("documents"):
        try:
            UploadedFile.objects.create(
                user=user_data,
                file=request.FILES["documents"]
            )
            UploadedBackup.objects.create(
                file=request.FILES["documents"]
            )
            return redirect("chat")
        except:
            pass

    if request.method == "POST" and request.POST.get("youtube"):
        try:
            youtube_url = request.POST.get("youtube")
            youtube_title = get_title(youtube_url) 
            YoutbeLink.objects.create(user=user_data, name=youtube_url, title=youtube_title)
            DatabaseLink.objects.create(name=youtube_url, title=youtube_title)
            generate_script(user=user_data,youtube_url=youtube_url)
            return redirect("chat")
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    if request.method == "POST" and request.POST.get("url"):
        url = request.POST.get("url")
        url_name = tldextract.extract(url).domain
        try:
            user = request.user
            webpage_content = read_webpage(url)
            file_name = directory / f"{url_name}.txt"
            URLLink.objects.create(
                user=user,
                name=url
            )

            with open(file_name, "w", encoding="utf-8") as f:
                f.write(webpage_content)

            UploadedFile.objects.create(
                file=f"uploads/{user.username}/{url_name}.txt"
            )
            UploadedBackup.objects.create(
                file=f"uploads/{user.username}/{url_name}.txt"
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        return redirect("chat")

    file_names = UploadedFile.objects.filter(user_id= request.user.id)
    youtube_link = YoutbeLink.objects.filter(user_id= request.user.id)
    url_link = URLLink.objects.filter(user_id= request.user.id)
    chat_data = Chat.objects.filter(user_id= request.user.id) 
    return render(
        request,
        "home.html",
        {
            "chat_data": chat_data,
            "file_names": file_names,
            "youtube_link":youtube_link,
            "url_link":url_link,
        }
    )

