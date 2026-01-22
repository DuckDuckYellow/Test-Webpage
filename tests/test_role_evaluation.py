"""
Updated Unit Tests for Role Evaluation System
"""

import pytest
from services.fm_parser_v2 import FMHTMLParserV2
from services.player_evaluator_service import PlayerEvaluatorService
from models.constants import PositionCategory


class TestParserV2:
    """Test the new format parser."""

    def test_parse_new_format(self):
        """Test parsing the new 32-column FM export."""
        with open('tests/fixtures/Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)

        assert squad is not None
        assert len(squad.players) > 0

        player = squad.players[0]
        assert player.name is not None
        assert player.age > 0
        assert player.wage > 0
        assert player.expires is not None

class TestRoleEvaluator:
    """Test the role evaluation service."""

    @pytest.fixture
    def evaluator(self):
        return PlayerEvaluatorService()

    @pytest.fixture
    def squad(self):
        with open('tests/fixtures/Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        parser = FMHTMLParserV2()
        return parser.parse_html(html_content)

    def test_evaluate_player(self, evaluator, squad):
        """Test basic player evaluation."""
        player = squad.players[0]
        evaluator.evaluate_roles(player)
        
        assert player.best_role is not None
        assert hasattr(player.best_role, 'overall_score')
        assert hasattr(player.best_role, 'tier')

    def test_goalkeeper_best_role(self, evaluator, squad):
        """Test that a goalkeeper gets a GK role."""
        gk = next((p for p in squad.players if 'GK' in p.position), None)
        assert gk is not None
        
        evaluator.evaluate_roles(gk)
        assert gk.best_role.role == 'GK'

class TestRoleRecommendations:
    """Test role recommendation logic."""

    @pytest.fixture
    def evaluator(self):
        return PlayerEvaluatorService()

    def test_recommendation_logic(self, evaluator):
        """Test that recommendations are generated when appropriate."""
        # This would require a mock player with specific stats
        pass
