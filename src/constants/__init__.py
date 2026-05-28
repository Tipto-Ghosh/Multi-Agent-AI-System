import os 
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# planner LLM related constants
PLANNER_LLM_TEMPERATURE = 0.1
PLANNER_LLM_OUTPUT_FORMAT = "json"