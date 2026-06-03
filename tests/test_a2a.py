import json
import pytest
from unittest.mock import patch, MagicMock

class TestAgentCard:
    """Verify the Quiz Agent Card is correctly structured."""

    def test_agent_card_has_required_fields(self):
        """Agent Card must have name, url, version, skills."""
        from src.a2a_services.quiz_service import QUIZ_AGENT_CARD

        assert QUIZ_AGENT_CARD.name
        assert QUIZ_AGENT_CARD.url
        assert QUIZ_AGENT_CARD.version
        assert QUIZ_AGENT_CARD.skills
        assert len(QUIZ_AGENT_CARD.skills) > 0

    def test_agent_card_url_is_localhost(self):
        """For local development, URL should point to localhost:9001."""
        from src.a2a_services.quiz_service import QUIZ_AGENT_CARD
        assert "9001" in QUIZ_AGENT_CARD.url

    def test_skill_has_required_fields(self):
        """Each skill must have id, name, description."""
        from src.a2a_services.quiz_service import QUIZ_AGENT_CARD
        skill = QUIZ_AGENT_CARD.skills[0]
        assert skill.id
        assert skill.name
        assert skill.description
        assert len(skill.description) > 20

    def test_skill_has_examples(self):
        """Skills should have examples to guide callers."""
        from src.a2a_services.quiz_service import QUIZ_AGENT_CARD
        skill = QUIZ_AGENT_CARD.skills[0]
        assert skill.examples
        assert len(skill.examples) >= 1

    def test_skill_id_is_correct(self):
        """Skill ID should match the documented value."""
        from src.a2a_services.quiz_service import QUIZ_AGENT_CARD
        assert QUIZ_AGENT_CARD.skills[0].id == "generate_and_grade_quiz"
