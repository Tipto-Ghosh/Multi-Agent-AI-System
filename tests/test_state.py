""" 
Validation tests for the shared state definition.

These tests are fast and deterministic, they do NOT call Ollama.
They verify that the data structures work correctly before any
agents are built on top of them.

Run: uv run pytest tests/test_state.py -v
"""

import pytest
import sys
from src.graph.state import Topic, StudyRoadmap, QuizQuestion, QuizResult
from src.utils.state_utils import initial_state, get_current_topic, get_latest_quiz_result, session_is_complete
from src.logger import logging
from src.exception import LearningAcceleratorException


class TestTopic:
    """Tests for the Topic dataclass."""

    def test_topic_defaults(self):
        """Topic should have sensible defaults for optional fields."""
        logging.info("Starting test_topic_defaults - verifying Topic dataclass default values")
        
        try:
            topic = Topic(
                title = "Closures",
                description = "Understanding Python closures",
                estimated_minutes = 60,
            )
            
            logging.info(f"Created Topic with title='{topic.title}', status='{topic.status}'")
            assert topic.status == "pending"
            assert topic.prerequisites == []
            
            logging.info("test_topic_defaults passed successfully - defaults are correct")
            
        except Exception as e:
            logging.error(f"test_topic_defaults failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_topic_serialization_round_trip(self):
        """Topic should survive a to_dict/from_dict round trip."""
        logging.info("Starting test_topic_serialization_round_trip - testing serialization integrity")
        
        try:
            original = Topic(
                title = "Decorators",
                description = "Python decorator pattern",
                estimated_minutes = 45,
                prerequisites = ["Closures"],
                status = "completed",
            )
            
            logging.info(f"Original Topic: title='{original.title}', prerequisites={original.prerequisites}, status='{original.status}'")
            
            restored = Topic.from_dict(original.to_dict())
            
            logging.info(f"Restored Topic: title='{restored.title}', prerequisites={restored.prerequisites}, status='{restored.status}'")
            
            assert restored.title == original.title
            assert restored.prerequisites == original.prerequisites
            assert restored.status == original.status
            
            logging.info("test_topic_serialization_round_trip passed - serialization preserved all fields")
            
        except AssertionError as e:
            logging.error(f"Serialization round trip failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Unexpected error in test_topic_serialization_round_trip: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_topic_status_values(self):
        """Verify expected status values can be set."""
        logging.info("Starting test_topic_status_values - testing all valid status values")
        
        try:
            topic = Topic("Test", "desc", 30)
            
            for status in ("pending", "in_progress", "completed", "needs_review"):
                logging.info(f"Testing status transition to '{status}'")
                topic.status = status
                assert topic.status == status
                logging.info(f"Status '{status}' set successfully")
            
            logging.info("test_topic_status_values passed - all status values are valid")
            
        except Exception as e:
            logging.error(f"Status value test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)


class TestStudyRoadmap:
    """Tests for the StudyRoadmap dataclass."""

    def _make_roadmap(self) -> StudyRoadmap:
        """Helper: create a test roadmap with 3 topics."""
        logging.info("Creating test roadmap with 3 topics")
        return StudyRoadmap(
            goal = "Learn Python closures",
            total_weeks = 2,
            topics = [
                Topic("Functions", "Review functions", 45),
                Topic(
                    "Closures", "Understand closures", 60, prerequisites=["Functions"]),
                Topic("Decorators", "Build decorators", 75, prerequisites=["Closures"]),
            ],
        )

    def test_completed_count_starts_at_zero(self):
        """Verify completed_count is 0 for a fresh roadmap."""
        logging.info("Testing completed_count starts at zero")
        
        try:
            roadmap = self._make_roadmap()
            count = roadmap.completed_count()
            
            logging.info(f"Initial completed count: {count}")
            assert count == 0
            
            logging.info("test_completed_count_starts_at_zero passed")
            
        except Exception as e:
            logging.error(f"Completed count test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_completed_count_increments(self):
        """Verify completed_count updates when topics are marked complete."""
        logging.info("Testing completed_count increments correctly")
        
        try:
            roadmap = self._make_roadmap()
            
            roadmap.topics[0].status = "completed"
            logging.info(f"Marked topic '{roadmap.topics[0].title}' as completed")
            
            roadmap.topics[1].status = "completed"
            logging.info(f"Marked topic '{roadmap.topics[1].title}' as completed")
            
            count = roadmap.completed_count()
            logging.info(f"Completed count after updates: {count}")
            
            assert count == 2
            logging.info("test_completed_count_increments passed")
            
        except Exception as e:
            logging.error(f"Completed count increment test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_is_complete_false_when_pending_topics(self):
        """Roadmap should not be complete when topics are still pending."""
        logging.info("Testing is_complete returns False with pending topics")
        
        try:
            roadmap = self._make_roadmap()
            complete = roadmap.is_complete()
            
            logging.info(f"Roadmap complete status: {complete}")
            assert complete is False
            
            logging.info("test_is_complete_false_when_pending_topics passed")
            
        except Exception as e:
            logging.error(f"Roadmap completion test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_is_complete_true_when_all_done(self):
        """Roadmap should be complete when all topics are done."""
        logging.info("Testing is_complete returns True when all topics completed")
        
        try:
            roadmap = self._make_roadmap()
            
            for topic in roadmap.topics:
                topic.status = "completed"
                logging.info(f"Marked topic '{topic.title}' as completed")
            
            complete = roadmap.is_complete()
            logging.info(f"Roadmap complete status after all topics completed: {complete}")
            
            assert complete is True
            logging.info("test_is_complete_true_when_all_done passed")
            
        except Exception as e:
            logging.error(f"Full roadmap completion test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_is_complete_true_with_needs_review(self):
        """needs_review also counts as done, student moved on."""
        logging.info("Testing is_complete with 'needs_review' status topics")
        
        try:
            roadmap = self._make_roadmap()
            roadmap.topics[0].status = "completed"
            roadmap.topics[1].status = "needs_review"
            roadmap.topics[2].status = "completed"
            
            for i, topic in enumerate(roadmap.topics):
                logging.info(f"Topic {i} '{topic.title}' status: '{topic.status}'")
            
            complete = roadmap.is_complete()
            logging.info(f"Roadmap complete status with needs_review topics: {complete}")
            
            assert complete is True
            logging.info("test_is_complete_true_with_needs_review passed")
            
        except Exception as e:
            logging.error(f"Needs review completion test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_serialization_round_trip(self):
        """StudyRoadmap should survive a complete serialization round trip."""
        logging.info("Testing StudyRoadmap serialization round trip")
        
        try:
            roadmap = self._make_roadmap()
            logging.info(f"Original roadmap: goal='{roadmap.goal}', topics={len(roadmap.topics)}")
            
            restored = StudyRoadmap.from_dict(roadmap.to_dict())
            logging.info(f"Restored roadmap: goal='{restored.goal}', topics={len(restored.topics)}")
            
            assert restored.goal == roadmap.goal
            assert len(restored.topics) == len(roadmap.topics)
            assert restored.topics[1].prerequisites == ["Functions"]
            
            logging.info("test_serialization_round_trip passed - roadmap serialization preserved all data")
            
        except Exception as e:
            logging.error(f"Roadmap serialization test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)


class TestQuizResult:
    """Tests for QuizResult dataclass."""

    def _make_result(self, score: float) -> QuizResult:
        """Helper: create a QuizResult with a single question."""
        logging.info(f"Creating QuizResult with score={score}")
        return QuizResult(
            topic = "Closures",
            questions = [
                QuizQuestion(
                    question = "What is a closure?",
                    expected_answer = "A nested function that captures outer variables.",
                    user_answer = "A function inside a function",
                    correct = score >= 0.5,
                    score = score,
                )
            ],
            score = score,
            weak_areas = [] if score >= 0.75 else ["late binding"],
        )

    def test_passed_threshold(self):
        """Verify passed() threshold at 0.5 exactly."""
        logging.info("Testing quiz passed threshold at 0.5")
        
        try:
            result_pass = self._make_result(0.5)
            passed = result_pass.passed()
            logging.info(f"Score 0.5 - passed: {passed}")
            assert passed is True
            
            result_fail = self._make_result(0.49)
            passed = result_fail.passed()
            logging.info(f"Score 0.49 - passed: {passed}")
            assert passed is False
            
            logging.info("test_passed_threshold passed - threshold correct at 0.5")
            
        except Exception as e:
            logging.error(f"Pass threshold test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_strong_pass_threshold(self):
        """Verify strong_pass() threshold at 0.75 exactly."""
        logging.info("Testing strong_pass threshold at 0.75")
        
        try:
            result_strong = self._make_result(0.75)
            strong = result_strong.strong_pass()
            logging.info(f"Score 0.75 - strong_pass: {strong}")
            assert strong is True
            
            result_not_strong = self._make_result(0.74)
            strong = result_not_strong.strong_pass()
            logging.info(f"Score 0.74 - strong_pass: {strong}")
            assert strong is False
            
            logging.info("test_strong_pass_threshold passed - threshold correct at 0.75")
            
        except Exception as e:
            logging.error(f"Strong pass threshold test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_serialization(self):
        """QuizResult.to_dict() should include all expected fields."""
        logging.info("Testing QuizResult serialization")
        
        try:
            result = self._make_result(0.8)
            d = result.to_dict()
            
            logging.info(f"Serialized QuizResult: topic='{d['topic']}', score={d['score']}, questions={len(d['questions'])}")
            
            assert d["topic"] == "Closures"
            assert d["score"] == 0.8
            assert len(d["questions"]) == 1
            
            logging.info("test_serialization passed - QuizResult serialization correct")
            
        except Exception as e:
            logging.error(f"QuizResult serialization test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)


class TestInitialState:
    """Tests for the initial_state factory function."""

    def test_initial_state_has_all_required_keys(self):
        """Every key in AgentState must be present in initial_state output."""
        logging.info("Testing initial_state includes all required keys")
        
        try:
            state = initial_state("Learn Python", "session-001")
            
            required_keys = [
                "messages", "session_id", "goal", "roadmap",
                "approved", "current_topic_index", "quiz_results",
                "weak_areas", "study_materials_path", "error",
            ]
            
            for key in required_keys:
                assert key in state, f"Missing key: {key}"
                logging.info(f"Key '{key}' present: {state[key] is not None if key != 'error' else True}")
            
            logging.info("test_initial_state_has_all_required_keys passed - all keys present")
            
        except AssertionError as e:
            logging.error(f"Missing required key in initial state: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Initial state key validation failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_initial_state_defaults(self):
        """Verify that initial_state sets correct default values."""
        logging.info("Testing initial_state default values")
        
        try:
            state = initial_state("Learn Python", "session-001")
            
            logging.info("Checking default values...")
            assert state["messages"] == [], "messages should be empty list"
            assert state["roadmap"] is None, "roadmap should be None"
            assert state["approved"] is False, "approved should be False"
            assert state["current_topic_index"] == 0, "current_topic_index should be 0"
            assert state["quiz_results"] == [], "quiz_results should be empty list"
            assert state["weak_areas"] == [], "weak_areas should be empty list"
            assert state["error"] is None, "error should be None"
            
            logging.info("All default values verified correctly")
            logging.info("test_initial_state_defaults passed")
            
        except AssertionError as e:
            logging.error(f"Default value assertion failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        except Exception as e:
            logging.error(f"Initial state defaults test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_initial_state_captures_goal_and_session(self):
        """Verify goal and session_id are stored correctly."""
        logging.info("Testing initial_state captures goal and session_id")
        
        try:
            state = initial_state("Learn decorators", "abc-123")
            
            logging.info(f"Goal: '{state['goal']}', Session ID: '{state['session_id']}'")
            
            assert state["goal"] == "Learn decorators"
            assert state["session_id"] == "abc-123"
            
            logging.info("test_initial_state_captures_goal_and_session passed")
            
        except Exception as e:
            logging.error(f"Goal/session capture test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_custom_study_materials_path(self):
        """Verify custom study_materials_path can be set."""
        logging.info("Testing custom study_materials_path")
        
        try:
            custom_path = "/custom/path/notes"
            state = initial_state("Learn Python", "s1", custom_path)
            
            logging.info(f"Study materials path: '{state['study_materials_path']}'")
            
            assert state["study_materials_path"] == custom_path
            
            logging.info("test_custom_study_materials_path passed")
            
        except Exception as e:
            logging.error(f"Custom study materials path test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)
        

class TestStateHelpers:
    """Tests for get_current_topic, get_latest_quiz_result, session_is_complete."""

    def _make_state_with_roadmap(self, n_topics=3, current_index=0):
        """Helper: build a state dict with a roadmap."""
        logging.info(f"Creating test state with {n_topics} topics, current_index={current_index}")
        
        topics = [
            Topic(f"Topic {i}", f"Description {i}", 30)
            for i in range(n_topics)
        ]
        roadmap = StudyRoadmap("Test goal", 1, topics)
        state = initial_state("Test goal", "test-session")
        state["roadmap"] = roadmap
        state["current_topic_index"] = current_index
        
        logging.info(f"Test state created with roadmap: goal='{roadmap.goal}', topics={len(roadmap.topics)}")
        return state

    def test_get_current_topic_returns_correct_topic(self):
        """get_current_topic should return the topic at current_topic_index."""
        logging.info("Testing get_current_topic returns correct topic")
        
        try:
            state = self._make_state_with_roadmap(n_topics=3, current_index=1)
            topic = get_current_topic(state)
            
            logging.info(f"Current topic: '{topic.title}' (expected 'Topic 1')")
            
            assert topic is not None
            assert topic.title == "Topic 1"
            
            logging.info("test_get_current_topic_returns_correct_topic passed")
            
        except Exception as e:
            logging.error(f"Get current topic test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_get_current_topic_returns_none_when_complete(self):
        """get_current_topic should return None when all topics are done."""
        logging.info("Testing get_current_topic returns None when index past end")
        
        try:
            state = self._make_state_with_roadmap(n_topics=3, current_index=3)
            topic = get_current_topic(state)
            
            logging.info(f"Current topic result: {topic} (expected None)")
            
            assert topic is None
            
            logging.info("test_get_current_topic_returns_none_when_complete passed")
            
        except Exception as e:
            logging.error(f"Get current topic None test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_get_current_topic_returns_none_without_roadmap(self):
        """get_current_topic should return None when no roadmap exists."""
        logging.info("Testing get_current_topic returns None without roadmap")
        
        try:
            state = initial_state("Test", "session-1")
            topic = get_current_topic(state)
            
            logging.info(f"Current topic result without roadmap: {topic}")
            
            assert topic is None
            
            logging.info("test_get_current_topic_returns_none_without_roadmap passed")
            
        except Exception as e:
            logging.error(f"Get current topic without roadmap test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_get_latest_quiz_result_none_when_empty(self):
        """get_latest_quiz_result should return None when no results exist."""
        logging.info("Testing get_latest_quiz_result returns None for empty results")
        
        try:
            state = initial_state("Test", "session-1")
            result = get_latest_quiz_result(state)
            
            logging.info(f"Latest quiz result: {result} (expected None)")
            
            assert result is None
            
            logging.info("test_get_latest_quiz_result_none_when_empty passed")
            
        except Exception as e:
            logging.error(f"Get latest quiz result empty test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_get_latest_quiz_result_returns_last(self):
        """get_latest_quiz_result should return the most recent result."""
        logging.info("Testing get_latest_quiz_result returns last result")
        
        try:
            state = initial_state("Test", "session-1")
            r1 = QuizResult("Topic 0", [], 0.6, [])
            r2 = QuizResult("Topic 1", [], 0.9, [])
            state["quiz_results"] = [r1, r2]
            
            logging.info(f"Added {len(state['quiz_results'])} quiz results")
            
            result = get_latest_quiz_result(state)
            
            logging.info(f"Latest result: topic='{result.topic}', score={result.score}")
            
            assert result.topic == "Topic 1"
            
            logging.info("test_get_latest_quiz_result_returns_last passed")
            
        except Exception as e:
            logging.error(f"Get latest quiz result test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_session_is_complete_false_with_pending_topics(self):
        """session_is_complete should be False when topics remain."""
        logging.info("Testing session_is_complete returns False with pending topics")
        
        try:
            state = self._make_state_with_roadmap(n_topics=3, current_index=0)
            complete = session_is_complete(state)
            
            logging.info(f"Session complete status: {complete}")
            
            assert complete is False
            
            logging.info("test_session_is_complete_false_with_pending_topics passed")
            
        except Exception as e:
            logging.error(f"Session complete false test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_session_is_complete_true_when_index_past_end(self):
        """session_is_complete should be True when current_index is past all topics."""
        logging.info("Testing session_is_complete returns True when index past end")
        
        try:
            state = self._make_state_with_roadmap(n_topics=3, current_index=3)
            complete = session_is_complete(state)
            
            logging.info(f"Session complete status (index={state['current_topic_index']}): {complete}")
            
            assert complete is True
            
            logging.info("test_session_is_complete_true_when_index_past_end passed")
            
        except Exception as e:
            logging.error(f"Session complete true test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)

    def test_session_is_complete_true_without_roadmap(self):
        """session_is_complete should be True when no roadmap exists."""
        logging.info("Testing session_is_complete returns True without roadmap")
        
        try:
            state = initial_state("Test", "session-1")
            complete = session_is_complete(state)
            
            logging.info(f"Session complete status without roadmap: {complete}")
            
            assert complete is True
            
            logging.info("test_session_is_complete_true_without_roadmap passed")
            
        except Exception as e:
            logging.error(f"Session complete without roadmap test failed: {str(e)}")
            raise LearningAcceleratorException(e, sys)


def test_quiz_result_from_dict():
    """QuizResult.from_dict() reconstructs correctly from a plain dict."""
    logging.info("Testing QuizResult.from_dict() reconstruction")
    
    try:
        data = {
            "topic": "Python Closures",
            "score": 0.75,
            "weak_areas": ["nonlocal keyword", "late binding"],
            "timestamp": "2026-04-19T10:00:00+00:00",
            "questions": [],
        }
        
        logging.info(f"Creating QuizResult from dict: topic='{data['topic']}', score={data['score']}")
        
        result = QuizResult.from_dict(data)
        
        logging.info(f"Reconstructed QuizResult: topic='{result.topic}', score={result.score}, weak_areas={result.weak_areas}")
        
        assert result.topic == "Python Closures"
        assert result.score == 0.75
        assert result.weak_areas == ["nonlocal keyword", "late binding"]
        assert result.passed() is True
        assert result.strong_pass() is True
        
        logging.info("test_quiz_result_from_dict passed - reconstruction successful")
        
    except Exception as e:
        logging.error(f"QuizResult from_dict test failed: {str(e)}")
        raise LearningAcceleratorException(e, sys)


def test_get_latest_quiz_result_handles_dict():
    """get_latest_quiz_result() returns QuizResult even when state has raw dicts."""
    logging.info("Testing get_latest_quiz_result handles raw dicts")
    
    try:
        state = {
            "quiz_results": [
                {
                    "topic": "Closures",
                    "score": 0.6,
                    "weak_areas": [],
                    "timestamp": "",
                    "questions": [],
                }
            ]
        }
        
        logging.info(f"State has {len(state['quiz_results'])} quiz result(s) as dicts")
        
        result = get_latest_quiz_result(state)
        
        logging.info(f"Retrieved result: type={type(result).__name__}, topic='{result.topic}', score={result.score}")
        
        assert result is not None
        assert isinstance(result, QuizResult)
        assert result.topic == "Closures"
        assert result.score == 0.6
        
        logging.info("test_get_latest_quiz_result_handles_dict passed - dict conversion works")
        
    except Exception as e:
        logging.error(f"Dict handling test failed: {str(e)}")
        raise LearningAcceleratorException(e, sys)