from src.constants import OLLAMA_BASE_URL, MODEL_NAME
from langchain_ollama import ChatOllama

model = ChatOllama(
    model = MODEL_NAME,
    temperature = 0.6,
    base_url = OLLAMA_BASE_URL
)

response = model.invoke("Hello")
print(response.content)