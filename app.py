from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = "You are a useful chatbot."

user_input = input("Question: ")

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]
)

answer = response.choices[0].message.content

print(answer)