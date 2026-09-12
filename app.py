# from openai import OpenAI
import requests

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



print(get_youtube_title(youtube_url))