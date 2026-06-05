import sys 
import json
from src.logger import logging
from src.exception import LearningAcceleratorException
from src.graph.state import Topic, StudyRoadmap

def parse_roadmap_json(json_string: str) -> StudyRoadmap:
    """Parse the LLM's JSON output into a StudyRoadmap dataclass.

    Args:
        json_string (str): String output from the llm

    Returns:
        StudyRoadmap: an object of StudyRoadmap class
    """
    try:
        data = json.loads(json_string)
    except Exception as e:
        logging.info(
            f"LLM returned invalid JSON.\n"
            f"Raw output (first 300 chars): {json_string[:300]}"
        )
        raise LearningAcceleratorException(e, sys)
    
    required_fields = ["goal", "total_weeks", "topics"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"LLM JSON missing required field: '{field}'")
    
    if not isinstance(data["topics"], list) or len(data["topics"]) == 0:
        raise ValueError("LLM JSON 'topics' must be a non-empty list")
    
    topics = []
    for i, topic in enumerate(data["topics"]):
        for field in ["title", "description", "estimated_minutes"]:
            if field not in topic:
                raise ValueError(f"Topic {i} missing required field: '{field}'")
        
        # FIX: Check the topic first, then check root 'data', default to empty list if missing.
        # Also removed the accidental trailing comma that forced it into a tuple.
        topic_prereqs = topic.get("prerequisites") or data.get("prerequisites") or []

        topics.append(
            Topic(
                title = topic["title"],
                description = topic["description"],
                estimated_minutes = topic["estimated_minutes"],
                prerequisites = topic_prereqs,
                status = topic.get("status", "pending")
            )
        )
    
    return StudyRoadmap(
        goal = data["goal"],
        total_weeks = int(data["total_weeks"]),
        weekly_hours = int(data.get("weekly_hours", 5)),
        topics = topics
    )            