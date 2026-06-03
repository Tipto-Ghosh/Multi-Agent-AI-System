import json
import os
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from src.graph.state import QuizResult, StudyRoadmap
from src.utils.state_utils import get_latest_quiz_result
from src.mcp_servers.memory_server import memory_set
from src.constants import MODEL_NAME, OLLAMA_BASE_URL, PASS_THRESHOLD, USE_A2A_QUIZ
from src.prompts import COACHING_PROMPT
from src.logger import logging

""" 
The Progress Coach agent with A2A delegation support.

Reads quiz results, generates personalized coaching messages,
updates topic status in the roadmap, and optionally delegates
to the external Quiz A2A service or the CrewAI Study Buddy
for supplementary help. Falls back gracefully when external
services are unavailable.
"""

def get_coaching_message(topic: str, score: float, weak_areas: list[str]) -> dict:
    """Ask the LLM for a personalized coaching message."""
    llm = ChatOllama(
        model = MODEL_NAME,
        base_url = OLLAMA_BASE_URL,
        temperature = 0.4,
        format = "json"
    )
    
    context = {
        "topic": topic,
        "score_percent": f"{score:.0%}",
        "weak_areas": weak_areas if  weak_areas else ["none identified"]
    }
    
    try:
        response = llm.invoke([
            SystemMessage(content = COACHING_PROMPT),
            HumanMessage(content = json.dumps(context))
        ])
    except Exception as e:
        logging.info(f"[Progress Coach] LLM call failed: {e}")
        return {
           "summary": f"You scored {score:.0%} on {topic}. Keep going!",
            "encouragement": "Every topic builds on the last.", 
        }
    
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {
            "summary": f"You scored {score:.0%} on {topic}.",
            "encouragement": "Keep going, every topic builds on the last!",
        }
        

def try_a2a_quiz_delegation(topic: str, explaination: str, answers: list[str]) -> dict | None:
    """
    Attempt to delegate quiz grading to the A2A Quiz Service.

    Returns the grading result dict if successful, None if the
    service is unavailable or returns an error.

    The Progress Coach calls this first. If it returns None,
    the coach falls back to local quiz generation.
    """
    use_a2a = USE_A2A_QUIZ
    if not use_a2a:
        return None 
    
    try:
        from a2a_services
    