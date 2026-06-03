import os 
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# planner LLM related constants
PLANNER_LLM_TEMPERATURE = 0.1
PLANNER_LLM_OUTPUT_FORMAT = "json"

NOTES_BASE = Path("study_materials/sample_notes")
PASS_THRESHOLD = 0.5 # pass mark thresold
USE_A2A_QUIZ = True
QUIZ_SERVICE_URL = "http://localhost:9001"

# How long to wait for the quiz service to respond.
# Quiz generation + grading takes 15-60s depending on model size.
DEFAULT_TIMEOUT = 120.0

QUIZ_SERVICE_URL = "http://localhost:9001"
STUDY_BUDDY_URL = "http://localhost:9002"