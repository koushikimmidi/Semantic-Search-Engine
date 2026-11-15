import requests


url = "http://127.0.0.1:8000/search"

payload = {
    "query": "What is Artificial Intelligence?"
}

response = requests.post(
    url,
    json=payload
)

print(response.json())