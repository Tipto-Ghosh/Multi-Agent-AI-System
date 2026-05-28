from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from src.logger import logging
from src.exception import LearningAcceleratorException
from src.constants import MODEL_NAME, OLLAMA_BASE_URL, PLANNER_LLM_OUTPUT_FORMAT, PLANNER_LLM_TEMPERATURE
from src.prompts import PLANNER_SYSTEM_PROMPT
from src.graph.state import AgentState
from src.utils.curriculum_agent_utils import parse_roadmap_json

def build_planner_llm() -> ChatOllama:
    """Create a ChatOllama model object with given model name.
    
    Model name, base url, temperature, output_format are specified in the contants.
    """
    logging.info(f"""Created a planner LLM from build_planner_llm with model = {MODEL_NAME},
        base_url = {OLLAMA_BASE_URL},
        temperature = {PLANNER_LLM_TEMPERATURE},
        format = {PLANNER_LLM_OUTPUT_FORMAT}"""
    )
    return ChatOllama(
        model = MODEL_NAME,
        base_url = OLLAMA_BASE_URL,
        temperature = PLANNER_LLM_TEMPERATURE,
        format = PLANNER_LLM_OUTPUT_FORMAT
    )

def curriculum_planner_node(state: AgentState) -> dict:
    """LangGraph node: Curriculum Planner

    Args:
        state (AgentState): _description_
    
    Reads: state["goal"]
    Writes: state["roadmap"], state["messages"], state["error"]
    Returns:
        dict: a dict with key roadmap, messages, error.
    """
    goal = state.get("goal" , "").strip()
    logging.info(f"Reads the goal = {goal} from curriculum_planner_node.")
    
    if not goal:
        return {
            "error": "No learning goal provided."
        }
        
    logging.info(f"\n[Curriculum Planner] Building roadmap for: '{goal}'")
    
    llm = build_planner_llm()
    messages = [
        SystemMessage(content = PLANNER_SYSTEM_PROMPT),
        HumanMessage(content = f"Create a study roadmap for: {goal}")
    ]
    logging.info(f"[Curriculum Planner] Calling {MODEL_NAME}...")
    response = llm.invoke(messages)
    
    try:
        logging.info("Calling parse_roadmap_json to build the roadmap from planner model's response.")
        roadmap = parse_roadmap_json(response)
    except Exception as e:
        logging.info(
            f"[Curriculum Planner] Parse error: {e}"
        )
        return {
            "error": str(e),
            "messages": messages + [response]
        }
    
    logging.info(f"[Curriculum Planner] Created {len(roadmap.topics)} topics")
    
    return {
        "roadmap": roadmap,
        "messages": messages + [response],
        "error": None 
    }    