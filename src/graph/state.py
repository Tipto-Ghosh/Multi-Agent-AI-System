from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

@dataclass
class Topic:
    """A single topic within the study roadmap."""
    title: str 
    description: str 
    estimated_minutes: int # time need to complete the topic
    prerequisites: list[str] = field(default_factory = list)
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

@dataclass
class QuizResult:
    """The complete result of one quiz session on a single topic."""
    topic: str 
    questions: list
    score: float # 0.0 to 1.0 -> 0 to 100%
    weak_areas: list[str]
    timestamp: str = ""
    
    def passed(self)->bool:
        """Check a quiz result is pass fail."""
        return self.score >= 50
    
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