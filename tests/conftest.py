""" 
Shared pytest configuration, fixtures, and markers.

Defines two test markers:
  @pytest.mark.unit , fast, no external deps (default)
  @pytest.mark.eval , slow, requires Ollama, LLM-as-judge

Run only unit tests (fast, development):
  pytest tests/ -m "not eval" -v

Run only eval tests (slow, before releases):
  pytest tests/test_eval.py -m eval -v -s

Run everything:
  uv run pytest tests/ -v
"""

import sys 
from pathlib import Path
import pytest
from src.logger import logging
from src.exception import LearningAcceleratorException

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
logging.info(f"Added src directory to Python path: {Path(__file__).parent.parent / 'src'}")


def pytest_configure(config):
    """Register custom markers so pytest doesn't warn about unknown marks."""
    logging.info("Configuring pytest with custom markers")
    
    try:
        config.addinivalue_line(
            "markers",
            "eval: marks tests as evaluation tests requiring Ollama (deselect with -m 'not eval')"
        )
        logging.info("Registered 'eval' marker for Ollama-dependent tests")
        
        config.addinivalue_line(
            "markers",
            "unit: marks tests as fast unit tests with no external dependencies"
        )
        logging.info("Registered 'unit' marker for fast unit tests")
        
        logging.info("Pytest configuration completed successfully")
        
    except Exception as e:
        logging.error(f"Failed to configure pytest markers: {str(e)}")
        raise LearningAcceleratorException(e, sys)


@pytest.fixture
def sample_roadmap():
    """
    A minimal StudyRoadmap for use in tests.
    Avoids repeating roadmap construction across test files.
    """
    logging.info("Creating sample_roadmap fixture")
    
    try:
        from graph.state import StudyRoadmap, Topic
        
        logging.info("Successfully imported StudyRoadmap and Topic from graph.state")
        
        roadmap = StudyRoadmap(
            goal="Learn Python closures",
            total_weeks=2,
            topics=[
                Topic(
                    title="Closures Explained",
                    description="Understand how closures capture enclosing scope variables",
                    estimated_minutes=60,
                ),
                Topic(
                    title="Practical Closure Patterns",
                    description="Apply closures to real problems: factories, memoisation",
                    estimated_minutes=45,
                    prerequisites=["Closures Explained"],
                ),
            ],
        )
        
        logging.info(
            f"Created sample_roadmap: goal='{roadmap.goal}', "
            f"topics={len(roadmap.topics)}, total_weeks={roadmap.total_weeks}"
        )
        
        return roadmap
        
    except ImportError as e:
        logging.error(f"Failed to import required modules for sample_roadmap: {str(e)}")
        raise LearningAcceleratorException(
            f"Import error in sample_roadmap fixture: {str(e)}", 
            sys
        )
    except Exception as e:
        logging.error(f"Unexpected error creating sample_roadmap fixture: {str(e)}")
        raise LearningAcceleratorException(
            f"Failed to create sample_roadmap fixture: {str(e)}", 
            sys
        )


@pytest.fixture
def sample_state(sample_roadmap):
    """
    A minimal AgentState dict for use in tests.
    Has a roadmap, session ID, and all required fields populated.
    """
    logging.info("Creating sample_state fixture")
    
    try:
        from graph.state import initial_state
        
        logging.info("Successfully imported initial_state from graph.state")
        
        state = initial_state("Learn Python closures", "test-session-001")
        logging.info(
            f"Created initial state: goal='{state['goal']}', "
            f"session_id='{state['session_id']}'"
        )
        
        state["roadmap"] = sample_roadmap
        logging.info(f"Assigned sample_roadmap to state['roadmap']")
        
        state["current_topic_index"] = 0
        logging.info(f"Set current_topic_index to {state['current_topic_index']}")
        
        # Verify state has all required keys
        required_keys = [
            "messages", "session_id", "goal", "roadmap",
            "approved", "current_topic_index", "quiz_results",
            "weak_areas", "study_materials_path", "error",
        ]
        
        for key in required_keys:
            if key not in state:
                logging.error(f"Required key '{key}' missing from sample_state")
                raise LearningAcceleratorException(
                    f"Required key '{key}' missing from sample_state fixture", 
                    sys
                )
        
        logging.info(
            f"sample_state fixture created successfully: "
            f"has_roadmap={state['roadmap'] is not None}, "
            f"current_topic_index={state['current_topic_index']}, "
            f"quiz_results_count={len(state['quiz_results'])}"
        )
        
        return state
        
    except ImportError as e:
        logging.error(f"Failed to import required modules for sample_state: {str(e)}")
        raise LearningAcceleratorException(
            f"Import error in sample_state fixture: {str(e)}", 
            sys
        )
    except Exception as e:
        logging.error(f"Unexpected error creating sample_state fixture: {str(e)}")
        raise LearningAcceleratorException(
            f"Failed to create sample_state fixture: {str(e)}", 
            sys
        )


@pytest.fixture
def closures_note_content():
    """
    The content of the closures.md sample note.
    Used as retrieval context in faithfulness tests.
    """
    logging.info("Creating closures_note_content fixture")
    
    try:
        notes_path = Path(__file__).parent.parent / "study_materials/sample_notes/closures.md"
        logging.info(f"Looking for closures.md at: {notes_path}")
        
        if notes_path.exists():
            logging.info(f"Found closures.md, reading content (size: {notes_path.stat().st_size} bytes)")
            
            content = notes_path.read_text(encoding="utf-8")
            
            logging.info(
                f"Successfully read closures.md: "
                f"length={len(content)} chars, "
                f"lines={content.count(chr(10)) + 1}"
            )
            
            return content
        else:
            logging.warning(f"closures.md not found at {notes_path}, using fallback content")
            
            # Fallback if file doesn't exist
            fallback_content = """
# Python Closures

A closure is a nested function that remembers variables from its enclosing scope.

Three requirements:
1. A nested (inner) function
2. The inner function refers to a variable from the enclosing scope
3. The enclosing function returns the inner function

Example:
def make_counter(start=0):
    count = start
    def increment():
        nonlocal count
        count += 1
        return count
    return increment
"""
            logging.info(
                f"Using fallback content for closures_note_content: "
                f"length={len(fallback_content)} chars"
            )
            
            return fallback_content
            
    except PermissionError as e:
        logging.error(f"Permission denied reading closures.md at {notes_path}: {str(e)}")
        raise LearningAcceleratorException(
            f"Permission error accessing study materials in closures_note_content fixture: {str(e)}", 
            sys
        )
    except FileNotFoundError as e:
        logging.warning(f"Study materials directory not found: {str(e)}")
        # Return fallback content instead of failing
        fallback_content = """
# Python Closures
A closure is a nested function that remembers variables from its enclosing scope.
"""
        logging.info(f"Returning minimal fallback content due to missing file")
        return fallback_content
    except UnicodeDecodeError as e:
        logging.error(f"Encoding error reading closures.md: {str(e)}")
        raise LearningAcceleratorException(
            f"Encoding error in study materials file: {str(e)}", 
            sys
        )
    except Exception as e:
        logging.error(f"Unexpected error in closures_note_content fixture: {str(e)}")
        raise LearningAcceleratorException(
            f"Failed to create closures_note_content fixture: {str(e)}", 
            sys
        )


# Pytest hook: called before each test
@pytest.fixture(autouse=True)
def log_test_execution(request):
    """
    Automatically log the start and end of each test.
    Provides traceability for test execution flow.
    """
    test_name = request.node.name
    test_nodeid = request.node.nodeid
    
    logging.info(f"=== Starting test: {test_name} ({test_nodeid}) ===")
    
    yield  # Test runs here
    
    logging.info(f"=== Completed test: {test_name} ({test_nodeid}) ===")


# Pytest hook: configure logging for tests
def pytest_runtest_setup(item):
    """Setup before each test - configure test-specific logging if needed."""
    logging.debug(f"Setting up test environment for: {item.nodeid}")


def pytest_runtest_teardown(item):
    """Teardown after each test - cleanup logging if needed."""
    logging.debug(f"Tearing down test environment for: {item.nodeid}")


# Session-level hooks for overall test run logging
def pytest_sessionstart(session):
    """Called after the Session object has been created and before any tests."""
    logging.info("=" * 20)
    logging.info(f"Test session started")
    logging.info(f"Python path: {sys.path}")
    logging.info("=" * 20)


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished."""
    logging.info("=" * 20)
    logging.info(f"Test session finished with exit status: {exitstatus}")
    
    # Log test summary
    if hasattr(session, 'testsfailed') and hasattr(session, 'testscollected'):
        logging.info(f"Tests collected: {session.testscollected}")
        logging.info(f"Tests failed: {session.testsfailed}")
        logging.info(f"Tests passed: {session.testscollected - session.testsfailed}")
    
    logging.info("=" * 20)