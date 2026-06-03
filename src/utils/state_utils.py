import sys
from src.exception import LearningAcceleratorException
from src.graph.state import Topic, QuizQuestion, QuizResult
from src.logger import logger

def initial_state(
    goal: str, session_id: str, 
    study_materials_path: str = "study_materials/sample_notes"
) -> dict:
    """Create the initial state for a new study session."""
    if not goal:
        raise LearningAcceleratorException("goal must not be empty", sys)

    if not session_id:
        raise LearningAcceleratorException("session_id must not be empty", sys)

    logger.info("Creating initial state for session_id=%s", session_id)
    return {
        "messages": [],
        "session_id": session_id,
        "goal": goal,
        "roadmap": None,
        "approved": False,
        "current_topic_index": 0,
        "quiz_results": [],
        "weak_areas": [],
        "study_materials_path": study_materials_path,
        "error": None,
    }

def get_current_topic(state: dict) -> Topic | None:
    """Get the topic currently being studied, or None if done."""
    roadmap = state.get("roadmap")
    if roadmap is None:
        logger.warning("No roadmap found in state for session_id=%s", state.get("session_id"))
        return None
    
    index = state.get("current_topic_index" , 0)
    if index >= len(roadmap.topics):
        logger.info("All topics completed for session_id=%s", state.get("session_id"))
        return None # all topic is completed
    
    # return the element of current studing index
    logger.info(
        "Fetching current topic index=%s for session_id=%s",
        index,
        state.get("session_id"),
    )
    return roadmap.topics[index] 


def get_latest_quiz_result(state: dict) -> QuizResult | None:
    """
    Get the most recent quiz result, or None if no quizzes have run.

    Handles dict or dataclass quiz results, after a checkpoint resume,
    LangGraph may deserialize quiz_results as a list of plain dicts.

    Usage in the progress_coach node to analyze the just-completed quiz.
    """
    results = state.get("quiz_results", [])
    if not results:
        return None

    latest = results[-1]

    # After msgpack checkpoint deserialization, quiz results may come
    # back as plain dicts. Reconstruct them using from_dict().
    if isinstance(latest, dict):
        return QuizResult.from_dict(latest)

    return latest

def session_is_complete(state: dict) -> bool:
    """True when all topics have been studied."""
    roadmap = state.get("roadmap")
    if roadmap is None:
        logger.warning("session_is_complete called without a roadmap for session_id=%s", state.get("session_id"))
        return False
    index = state.get("current_topic_index" , 0)
    is_complete = index >= len(roadmap.topics)
    logger.info("Session completion checked for session_id=%s: %s", state.get("session_id"), is_complete)
    return is_complete