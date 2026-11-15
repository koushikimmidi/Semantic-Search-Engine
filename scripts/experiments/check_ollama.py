import ollama

client = ollama.Client(
    host="http://localhost:11434"
)

response = client.chat(
    model="gemma4:latest",
    messages=[
        {
            "role": "user",
            "content": "Say Hello"
        }
    ]
)

print(response["message"]["content"])