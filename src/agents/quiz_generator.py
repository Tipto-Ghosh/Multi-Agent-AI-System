import os 
import json
from datetime import datetime, timezone
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from src.graph.state import QuizResult, QuizQuestion 
from src.utils.state_utils import get_current_topic
from src.constants import MODEL_NAME, OLLAMA_BASE_URL
from src.prompts import GENERATION_PROMPT, GRADING_PROMPT


def generate_questions(topic: str, explanation: str, n: int = 3) -> list[dict]:
    """Generate n quiz questions from the Explainer's output."""
    llm = ChatOllama(
        model = MODEL_NAME,
        base_url = OLLAMA_BASE_URL,
        temperature = 0.4,
        format = "json"
    )

    prompt = GENERATION_PROMPT.format(n = n)
    try:
        response = llm.invoke([
            SystemMessage(content = prompt),
            HumanMessage(content = f"Topic: {topic}\n\nExplanation:\n{explanation}"),
        ])
        
        data = json.loads(response.content)
        questions = data.get("questions", [])
        if questions and isinstance(questions, list):
            return questions
    except Exception as e:
        print(f"[Quiz Generator] LLM call failed during question generation: {e}")

    # Fallback: one generic question
    return [{
        "question": f"In your own words, explain the key concept of {topic} and why it matters.",
        "expected_answer": "A clear explanation demonstrating conceptual understanding.",
        "difficulty": "medium",
    }]

def grade_answer(question: str, expected: str, student_answer: str) -> dict:
    """Grade a student's answer using the LLM as judge."""
    llm = ChatOllama(
        model = MODEL_NAME,
        base_url = OLLAMA_BASE_URL,
        temperature = 0.1,   # Analytical: grading must be consistent
        format = "json",
    )

    prompt = GRADING_PROMPT.format(
        question = question,
        expected_answer = expected,
        student_answer = student_answer
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return json.loads(response.content)
    except Exception as e:
        print(f"[Quiz Generator] LLM call failed during grading: {e}")
        return {
            "correct": False,
            "score": 0.5,
            "feedback": "Could not grade automatically. Please review manually.",
            "missing_concept": "",
        }

def run_quiz(topic: str, explanation: str) -> QuizResult:
    """Run an interactive quiz session in the terminal."""
    
    print(f"\n{'='*60}")
    print(f"Quiz: {topic}")
    print(f"{'='*20}")
    print("Answer each question in your own words. Press Enter to submit.\n")
    
    questions_data = generate_questions(topic, explanation, n = 3)
    graded_questions = []
    total_score = 0.0
    weak_areas = []
    
    for i, q_data in enumerate(questions_data, 1):
        question_text = q_data["question"]
        expected = q_data["expected_answer"]
        difficulty = q_data.get("difficulty", "medium")

        print(f"Question {i} [{difficulty}]: {question_text}")
        
        user_answer = input("Your answer: ").strip()
        if not user_answer:
            user_answer = "(no answer provided)"

        print("Grading...")
        grade = grade_answer(question_text, expected, user_answer)

        score = float(grade.get("score", 0.0))
        correct = bool(grade.get("correct", False))
        feedback = grade.get("feedback", "")
        missing = grade.get("missing_concept", "")

        total_score += score
        status = "✓" if correct else "✗"
        print(f"{status} Score: {score:.0%}. {feedback}\n")

        if missing:
            weak_areas.append(missing)

        graded_questions.append(QuizQuestion(
            question = question_text,
            expected_answer = expected,
            user_answer = user_answer,
            correct = correct,
            feedback = feedback,
            score = score
        ))

    avg_score = total_score / len(questions_data) if questions_data else 0.0
    correct_count = sum(1 for q in graded_questions if q.correct)

    print(f"{'='*20}")
    print(f"Quiz complete! Score: {avg_score:.0%} ({correct_count}/{len(graded_questions)} correct)")
    if weak_areas:
        print(f"Areas to review: {', '.join(set(weak_areas))}")
    print(f"{'='*60}\n")

    return QuizResult(
        topic = topic,
        questions = graded_questions,
        score = avg_score,
        weak_areas = list(set(weak_areas)),
        timestamp = datetime.now(timezone.utc).isoformat(),
    )


def quiz_generator_node(state: dict) -> dict:
    """
    LangGraph node: Quiz Generator

    Reads:  state["roadmap"], state["current_topic_index"], state["messages"]
    Writes: state["quiz_results"], state["weak_areas"], state["error"]
    """
    topic = get_current_topic(state)
    if topic is None:
        return {"error": "No current topic. Curriculum Planner must run first"}

    """Extract the Explainer's final response from message history.
    The Explainer's output is the last AIMessage that has no tool_calls.
    Tool-calling responses have content too, but they also have tool_calls set.
    """
    messages = state.get("messages", [])
    explanation = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
            explanation = msg.content
            break

    if not explanation:
        print("[Quiz Generator] Warning: no explanation found, generating generic quiz")
        explanation = f"Topic: {topic.title}. {topic.description}"

    print(f"\n[Quiz Generator] Generating quiz for: '{topic.title}'")
    quiz_result = run_quiz(topic.title, explanation)

    existing_results = state.get("quiz_results", [])
    all_weak_areas = list(set(
        state.get("weak_areas", []) + quiz_result.weak_areas
    ))

    return {
        "quiz_results": existing_results + [quiz_result],
        "weak_areas": all_weak_areas,
        "error": None,
        # Pass state forward explicitly to preserve it across interrupt/resume
        "roadmap": state.get("roadmap"),
        "current_topic_index": state.get("current_topic_index", 0),
        "session_id": state.get("session_id", ""),
    }