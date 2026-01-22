"""
Unit Tests for Role Evaluation System

Tests the complete role evaluation pipeline:
1. Parser V2 (new format)
2. Player model with new metrics
3. Role definitions
4. Role evaluator and scoring
"""

import pytest
from services.fm_parser_v2 import FMHTMLParserV2
from analyzers.role_evaluator import RoleEvaluator
from models.role_definitions import ROLES


class TestParserV2:
    """Test the new format parser."""

    def test_parse_new_format(self):
        """Test parsing the new 32-column FM export."""
        # Read the new format file
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)

        # Verify squad parsed
        assert squad is not None
        assert len(squad.players) > 0

        # Verify first player has all fields
        player = squad.players[0]
        assert player.name is not None
        assert player.age > 0
        assert player.wage > 0
        assert player.expires is not None

    def test_player_metrics_extracted(self):
        """Test that all metrics are extracted correctly."""
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)

        # Find a non-GK player
        player = next((p for p in squad.players if p.position != 'GK'), None)
        assert player is not None

        # Verify new format metrics are present
        assert player.tck_90 is not None or player.tck_90 == 0
        assert player.pr_passes_90 is not None or player.pr_passes_90 == 0
        assert player.drb_90 is not None or player.drb_90 == 0

    def test_normalized_metrics(self):
        """Test that get_normalized_metrics works."""
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)
        player = squad.players[0]

        metrics = player.get_normalized_metrics()
        assert isinstance(metrics, dict)
        assert 'tackles_90' in metrics
        assert 'pass_pct' in metrics
        assert 'dribbles_90' in metrics


class TestRoleDefinitions:
    """Test role definitions are valid."""

    def test_all_roles_defined(self):
        """Test that all 12 roles are defined."""
        assert len(ROLES) == 12

        expected_roles = [
            'GK', 'CB-STOPPER', 'BCB', 'FB', 'WB',
            'MD', 'MC', 'AM(C)', 'WAP', 'WAS',
            'ST-PROVIDER', 'ST-GS'
        ]

        for role_name in expected_roles:
            assert role_name in ROLES

    def test_role_has_required_fields(self):
        """Test each role has all required fields."""
        for role_name, role in ROLES.items():
            assert role.name is not None
            assert role.primary_position is not None
            assert len(role.metrics) > 0
            assert len(role.thresholds) > 0

            # Each metric should have thresholds
            for metric in role.metrics:
                assert metric in role.thresholds
                thresholds = role.thresholds[metric]
                assert 'good' in thresholds
                assert 'ok' in thresholds
                assert 'poor' in thresholds


class TestRoleEvaluator:
    """Test role evaluation logic."""

    def test_evaluate_player_for_role(self):
        """Test evaluating a player against a specific role."""
        # Parse squad
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)

        # Get a defender
        player = next((p for p in squad.players if 'CB' in p.position or 'D' in p.position), None)
        assert player is not None

        # Evaluate against CB-STOPPER role
        evaluator = RoleEvaluator()
        role = ROLES['CB-STOPPER']
        score = evaluator.evaluate_player_for_role(player, role)

        # Verify score structure
        assert score.role == 'CB-STOPPER'
        assert 0 <= score.overall_score <= 120
        assert score.tier in ['ELITE', 'GOOD', 'AVERAGE', 'POOR']
        assert isinstance(score.metric_scores, dict)
        assert isinstance(score.strengths, list)
        assert isinstance(score.weaknesses, list)

    def test_evaluate_all_roles(self):
        """Test evaluating a player against all roles."""
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)
        player = squad.players[0]

        evaluator = RoleEvaluator()
        all_scores = evaluator.evaluate_all_roles(player)

        # Should have 12 role scores
        assert len(all_scores) == 12

        # Should be sorted by score (best first)
        for i in range(len(all_scores) - 1):
            assert all_scores[i].overall_score >= all_scores[i + 1].overall_score

    def test_get_best_role(self):
        """Test getting the best role for a player."""
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)
        player = squad.players[0]

        evaluator = RoleEvaluator()
        best_role = evaluator.get_best_role(player)

        assert best_role is not None
        assert best_role.role in ROLES.keys()
        assert best_role.overall_score >= 0

    def test_goalkeeper_best_role(self):
        """Test that a goalkeeper is correctly identified as GK role."""
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)

        # Find a goalkeeper
        gk = next((p for p in squad.players if p.position == 'GK'), None)
        assert gk is not None

        evaluator = RoleEvaluator()
        best_role = evaluator.get_best_role(gk)

        # Best role should be GK (or very close)
        assert best_role.role == 'GK' or 'GK' in [r.role for r in evaluator.evaluate_all_roles(gk)[:2]]

    def test_evaluate_all_roles_with_filtering(self):
        """Test that evaluate_all_roles filters roles by primary_position."""
        # Parse squad
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)
        player = squad.players[0]

        evaluator = RoleEvaluator()
        
        # 1. No filtering (default)
        all_roles = evaluator.evaluate_all_roles(player)
        assert len(all_roles) == 12

        # 2. Filter for GK only
        gk_roles = evaluator.evaluate_all_roles(player, allowed_positions=['GK'])
        assert len(gk_roles) == 1
        assert gk_roles[0].role == 'GK'

        # 3. Filter for CB only
        cb_roles = evaluator.evaluate_all_roles(player, allowed_positions=['CB'])
        assert len(cb_roles) == 2
        assert all(r.role in ['CB-STOPPER', 'BCB'] for r in cb_roles)

        # 4. Filter for Multiple (CB and ST)
        multi_roles = evaluator.evaluate_all_roles(player, allowed_positions=['CB', 'ST'])
        assert len(multi_roles) == 4
        assert any(r.role == 'CB-STOPPER' for r in multi_roles)
        assert any(r.role == 'ST-GS' for r in multi_roles)
        assert not any(r.role == 'GK' for r in multi_roles)


class TestRoleRecommendations:
    """Test role recommendation logic."""

    def test_get_role_recommendations(self):
        """Test getting role recommendations."""
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)

        # Test with several players
        evaluator = RoleEvaluator()

        for player in squad.players[:5]:
            recommendations = evaluator.get_role_recommendations(player)

            # Recommendations should be list (may be empty)
            assert isinstance(recommendations, list)

            # If recommendations exist, they should meet criteria
            if recommendations:
                for rec in recommendations:
                    assert rec.overall_score >= 65  # Minimum score
                    assert rec.role != evaluator.get_best_role(player).role  # Not the best role

    def test_recommendation_text_generation(self):
        """Test generating recommendation text."""
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParserV2()
        squad = parser.parse_html(html_content)
        player = squad.players[0]

        evaluator = RoleEvaluator()
        best_role = evaluator.get_best_role(player)
        all_roles = evaluator.evaluate_all_roles(player)

        # Generate text for second-best role
        if len(all_roles) > 1:
            alt_role = all_roles[1]
            text = evaluator.generate_role_recommendation_text(alt_role, best_role)

            assert isinstance(text, str)
            assert len(text) > 0
            assert alt_role.role in text


def test_integration_full_pipeline():
    """Test the complete pipeline from HTML to role recommendations."""
    # 1. Parse HTML
    with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    parser = FMHTMLParserV2()
    squad = parser.parse_html(html_content)

    assert len(squad.players) > 0

    # 2. Evaluate all players
    evaluator = RoleEvaluator()

    for player in squad.players:
        # Get best role
        best_role = evaluator.get_best_role(player)
        assert best_role is not None

        # Get all roles (filtered by default if player.evaluate_roles was used,
        # but here we might be calling evaluator.evaluate_all_roles(player) directly)
        all_roles = evaluator.evaluate_all_roles(player)
        assert len(all_roles) >= 1

        # Get recommendations
        recommendations = evaluator.get_role_recommendations(player)
        assert isinstance(recommendations, list)

        print(f"\n{player.name} ({player.position}):")
        print(f"  Best Role: {best_role.role} (Score: {best_role.overall_score:.1f}, Tier: {best_role.tier})")

        if recommendations:
            for rec in recommendations[:1]:  # Show top recommendation
                text = evaluator.generate_role_recommendation_text(rec, best_role)
                print(f"  Recommendation: {text}")


if __name__ == '__main__':
    # Run the integration test
    test_integration_full_pipeline()
