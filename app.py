# from openai import OpenAI
import requests
import trafilatura

# client = OpenAI()

# SYSTEM_PROMPT = "You are a useful chatbot."

# user_input = input("Question: ")

# response = client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     messages=[
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": user_input}
#     ]
# )

# answer = response.choices[0].message.content

# print(answer)

YOUTUBE_API_KEY='sk_d5T3bl2LoJyTCOoVNBgKiqlfiaJV91GPgJIqrXwGIKo'



def youtube_data( youtube_url):
    url = 'https://transcriptapi.com/api/v2/youtube/transcript'
    params = {'video_url': youtube_url, 'format': 'json'}
    r = requests.get(url, params=params, headers={'Authorization': 'Bearer ' + YOUTUBE_API_KEY}, timeout=30)
    r.raise_for_status()
    raw_data = r.json()
    transcript= [i['text'] for i in raw_data['transcript']]
    return transcript

youtube_url= "https://www.youtube.com/watch?v=JGO_zDWmkvk&t=79s"

# x = youtube_data(youtube_url)
# print(x)


def get_youtube_title(video_url):
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



# print(get_youtube_title(youtube_url))


# def read_webpage(url):
#     downloaded = trafilatura.fetch_url(url)
#     if downloaded is None:
#         raise Exception("Unable to fetch webpage.")
#     text = trafilatura.extract(
#         downloaded,
#         include_links=False,
#         include_tables=True,
#         include_comments=False,
#     )
#     return text


# x = read_webpage("https://www.theblogstarter.com/")
# print(x)

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

NVIDIA_API_KEY= "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"

NVIDIA_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"


SYSTEM_PROMPT ="you are a chatbot"
user_input ="hi how much is distance from earth to mooon "

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

print(answer)