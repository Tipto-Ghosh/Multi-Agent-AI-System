from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

@dataclass
class Topic:
    """A single topic within the study roadmap.
    The Curriculum Planner creates these.
    The Explainer and Quiz Generator read them.
    The Progress Coach updates their status.
    """
    title: str 
    description: str 
    estimated_minutes: int # time need to complete the topic
    prerequisites: list[str] = field(default_factory = list)
    """ 
    Status lifecycle:
       pending -> not yet studied
       in_progress -> currently being explained
       completed -> quiz passed (score >= 0.5)
       needs_review -> quiz failed (score < 0.5)
    """
    status: str = "pending" # pending -> in_progress -> completed -> needs_review
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls , data: dict) -> "Topic":
        return cls(
            title = data["title"],
            description = data["description"],
            estimated_minutes = data["estimated_minutes"],
            prerequisites = data["prerequisites"],
            status = data["status"]
        )
        

@dataclass
class StudyRoadmap:
    """The full study plan produced by the Curriculum Planner."""
    goal: str 
    total_weeks: int 
    topics: list[Topic]
    weekly_hours: int = 5
    
    def is_complete(self) -> bool:
        """Check a study roadmap is completed or not."""
        return all(t.status in ("completed" , "needs_review") for t in self.topics)
    
    def from_dict(cls, data: dict)-> "StudyRoadmap":
        """Reconstruct from a plain dict."""
        return cls(
            goal = data["goal"],
            total_weeks = data["total_weeks"],
            weekly_hours = data.get("weekly_hours", 5),
            topics = [Topic.from_dict(t) for t in data.get("topics", [])],
        )
        
    def completed_count(self)->int:
        """How many topic have been completed."""
        return sum(
            1 for t in self.topics if t.status == "completed"
        )
        
    def is_complete(self) -> bool:
        """True when all topics are completed or needs_review."""
        return all(t.status in ("completed", "needs_review") for t in self.topics)
    
@dataclass
class QuizQuestion:
    """One question within a quiz, with the user's answer and grading.

    The Quiz Generator creates these.
    The Progress Coach reads them to identify weak areas."""
    qestion: str 
    expected_answer: str 
    user_answer: str = ""
    correct: bool = False
    feedback: str  = ""
    score: float = 0.0
    
    def to_dict(self)->dict:
        return asdict(self)

@dataclass
class QuizResult:
    """The complete result of one quiz session on a single topic.
    Stored in AgentState.quiz_results, one entry per topic per session.
    The Progress Coach reads this to decide what to do next.
    """
    topic: str 
    questions: list[QuizQuestion]
    score: float # 0.0 to 1.0 -> 0 to 100%
    weak_areas: list[str]
    timestamp: str = ""
    
    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "score": self.score,
            "weak_areas": self.weak_areas,
            "timestamp": self.timestamp,
            "questions": [q.to_dict() for q in self.questions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuizResult":
        """
        Reconstruct from a plain dict.

        Called when LangGraph deserializes quiz_results from a SQLite
        checkpoint as raw dicts (msgpack round-trip). This happens when
        resuming a crashed or interrupted session.
        """
        return cls(
            topic = data.get("topic", ""),
            questions = [], # Questions not needed for coaching logic
            score = float(data.get("score", 0.0)),
            weak_areas = data.get("weak_areas", []),
            timestamp = data.get("timestamp", ""),
        )
    def passed(self)->bool:
        """Check a quiz result is pass fail."""
        return self.score >= 50
    
    def strong_pass(self) -> bool:
        """A score of 0.75 or above, ready to move to next topic."""
        return self.score >= 0.75
    
class AgentState(TypedDict):
    """The shared state for the Learning Accelerator graph."""
    messages: Annotated[list[BaseMessage] , add_messages]
    session_id: str 
    goal: str
    roadmap: StudyRoadmap | None 
    approved: bool
    current_topic_index: int 
    quiz_results: list[QuizResult]
    weak_areas: list[str]
    study_matrials_path: str 
    error: str | None 