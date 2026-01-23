"""
Unit tests for 70/30 weighted scoring algorithm.

Tests the migration from equal-weight KPI scoring to Primary (70%) / Secondary (30%) weighted scoring.
Ensures that players with strong primary metrics score higher than those with strong secondary metrics.
"""

import pytest
from models.squad_audit import Player
from models.role_definitions import CB_STOPPER, BCB, GK, WAP, ST_GS
from analyzers.role_evaluator import RoleEvaluator


class TestWeightedScoringAlgorithm:
    """Test 70/30 weighted scoring calculation."""

    @pytest.fixture
    def evaluator(self):
        return RoleEvaluator()

    @pytest.fixture
    def base_player_data(self):
        """Base player data template."""
        return {
            'name': 'Test Player',
            'position_selected': 'DC',
            'position': 'D (C)',
            'age': 25,
            'wage': 10000,
            'apps': 30,
            'subs': 0,
            'gls': 0,
            'ast': 0,
            'av_rat': 7.5,
            'expires': '01/06/2025',
            'inf': '',
            'mins': 2700  # Qualifies for analysis (>500 mins)
        }

    def test_elite_primary_outscores_elite_secondary(self, evaluator, base_player_data):
        """
        Player with elite primary metrics should score higher than player with elite secondary.

        This is the core principle of 70/30 weighting.
        """
        # Player A: Elite primary, poor secondary (CB-STOPPER)
        player_a_data = {
            **base_player_data,
            'name': 'Elite Primary Player',
            # CB-STOPPER Primary (70%): header_win_pct, tackles_90, interceptions_90
            'hdr_pct': 90,  # ELITE (good = 82)
            'tck_90': 3.0,  # ELITE (good = 2.38)
            'int_90': 4.0,  # ELITE (good = 3.18)
            # CB-STOPPER Secondary (30%): blocks_90, clearances_90
            'shts_blckd_90': 0.1,  # CRITICAL (poor = 0.19)
            'clr_90': 0.3   # CRITICAL (poor = 0.44)
        }
        player_a = Player(**player_a_data)

        # Player B: Poor primary, elite secondary (CB-STOPPER)
        player_b_data = {
            **base_player_data,
            'name': 'Elite Secondary Player',
            # CB-STOPPER Primary (70%): header_win_pct, tackles_90, interceptions_90
            'hdr_pct': 50,  # CRITICAL (poor = 59)
            'tck_90': 0.5,  # CRITICAL (poor = 0.8)
            'int_90': 0.8,  # CRITICAL (poor = 1.36)
            # CB-STOPPER Secondary (30%): blocks_90, clearances_90
            'shts_blckd_90': 0.9,  # ELITE (good = 0.72)
            'clr_90': 2.0   # ELITE (good = 1.64)
        }
        player_b = Player(**player_b_data)

        score_a = evaluator.evaluate_player_for_role(player_a, CB_STOPPER)
        score_b = evaluator.evaluate_player_for_role(player_b, CB_STOPPER)

        # Player A (elite primary) should score significantly higher
        assert score_a.overall_score > score_b.overall_score, \
            f"Elite primary ({score_a.overall_score:.1f}) should outscore elite secondary ({score_b.overall_score:.1f})"

        # Verify substantial difference (at least 20 points)
        difference = score_a.overall_score - score_b.overall_score
        assert difference >= 20, \
            f"Expected difference >= 20 points, got {difference:.1f}"

    def test_weighted_calculation_correctness(self, evaluator, base_player_data):
        """
        Verify exact weighted calculation: (primary_avg * 0.7) + (secondary_avg * 0.3).

        Uses metrics at exact threshold values for predictable scoring.
        """
        # Player with all metrics at 'good' threshold (should score ~100 each)
        player_data = {
            **base_player_data,
            'name': 'Threshold Player',
            # CB-STOPPER Primary (good thresholds)
            'hdr_pct': 82,    # Exactly 'good' threshold
            'tck_90': 2.38,   # Exactly 'good' threshold
            'int_90': 3.18,   # Exactly 'good' threshold
            # CB-STOPPER Secondary (good thresholds)
            'shts_blckd_90': 0.72,  # Exactly 'good' threshold
            'clr_90': 1.64    # Exactly 'good' threshold
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, CB_STOPPER)

        # All metrics at 'good' threshold should score ~100
        # Expected: (100 * 0.7) + (100 * 0.3) = 70 + 30 = 100
        assert 98 <= score.overall_score <= 102, \
            f"Expected score ~100 (all metrics at 'good' threshold), got {score.overall_score:.1f}"

    def test_metric_weight_tagging(self, evaluator, base_player_data):
        """Verify that each metric is correctly tagged as PRIMARY or SECONDARY."""
        player_data = {
            **base_player_data,
            'hdr_pct': 75,
            'tck_90': 2.0,
            'int_90': 2.5,
            'shts_blckd_90': 0.5,
            'clr_90': 1.2
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, CB_STOPPER)

        # Check primary metrics are tagged
        for metric in CB_STOPPER.primary_metrics:
            if metric in score.metric_scores:
                assert score.metric_scores[metric]['weight'] == 'PRIMARY', \
                    f"Metric '{metric}' should be tagged as PRIMARY"

        # Check secondary metrics are tagged
        for metric in CB_STOPPER.secondary_metrics:
            if metric in score.metric_scores:
                assert score.metric_scores[metric]['weight'] == 'SECONDARY', \
                    f"Metric '{metric}' should be tagged as SECONDARY"

    def test_goalkeeper_weighted_scoring(self, evaluator, base_player_data):
        """Test weighted scoring for Goalkeeper (2P + 2S metrics)."""
        player_data = {
            **base_player_data,
            'name': 'Test Keeper',
            'position_selected': 'GK',
            'position': 'GK',
            # GK Primary (70%): xgp_90, conceded_90
            'xgp_90': 0.3,   # ELITE (good = 0.25)
            'con_90': 0.5,   # ELITE (good = 0.75, lower is better for conceded)
            # GK Secondary (30%): pass_pct, interceptions_90
            'pas_pct': 98,   # ELITE (good = 97)
            'int_90': 0.25   # ELITE (good = 0.22)
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, GK)

        # All elite metrics should score high
        assert score.tier == 'ELITE', \
            f"All elite metrics should result in ELITE tier, got {score.tier}"
        assert score.overall_score >= 100, \
            f"All elite metrics should score >= 100, got {score.overall_score:.1f}"

    def test_bcb_primary_secondary_split(self, evaluator, base_player_data):
        """
        Test BCB role (2 primary + 3 secondary metrics).

        BCB Primary: prog_passes_90, interceptions_90
        BCB Secondary: tackles_90, clearances_90, blocks_90
        """
        player_data = {
            **base_player_data,
            'name': 'Ball-Playing CB',
            # BCB Primary (70%) - Distribution focus
            'pr_passes_90': 8.0,  # ELITE (good = 6.9)
            'int_90': 3.5,        # ELITE (good = 3)
            # BCB Secondary (30%) - Defensive fundamentals
            'tck_90': 1.0,        # CRITICAL (poor = 0.88)
            'clr_90': 0.3,        # CRITICAL (poor = 0.39)
            'shts_blckd_90': 0.1  # CRITICAL (poor = 0.16)
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, BCB)

        # Elite primary (70%) should dominate despite poor secondary (30%)
        # Expected: (~110 * 0.7) + (~30 * 0.3) = 77 + 9 = 86 (ELITE tier)
        assert score.tier in ['ELITE', 'GOOD'], \
            f"Elite primary metrics should result in GOOD or ELITE tier, got {score.tier}"
        assert score.overall_score >= 70, \
            f"Elite primary should keep score >= 70, got {score.overall_score:.1f}"

    def test_missing_secondary_metrics_handled(self, evaluator, base_player_data):
        """Test edge case: player missing all secondary metrics."""
        player_data = {
            **base_player_data,
            # Only CB-STOPPER primary metrics
            'hdr_pct': 80,
            'tck_90': 2.5,
            'int_90': 3.0,
            # Missing: shts_blckd_90, clr_90
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, CB_STOPPER)

        # Should fall back to primary-only scoring (no crash)
        assert score.overall_score > 0, \
            "Should calculate score even with missing secondary metrics"
        assert score.tier in ['ELITE', 'GOOD', 'AVERAGE', 'POOR'], \
            "Should assign valid tier even with missing secondary metrics"

    def test_mixed_performance_weighted_correctly(self, evaluator, base_player_data):
        """
        Test realistic scenario: good primary, average secondary.

        This represents a typical "role specialist" who excels at core duties
        but is average at supporting attributes.
        """
        player_data = {
            **base_player_data,
            'name': 'Role Specialist',
            # WAP Primary (70%): dribbles_90, crosses_90, sprints_90
            'drb_90': 5.0,         # ELITE (good = 4.69)
            'op_crs_c_90': 0.7,    # ELITE (good = 0.66)
            'sprints_90': 19.0,    # ELITE (good = 18.03)
            # WAP Secondary (30%): key_passes_90, xassists_90
            'op_kp_90': 0.8,       # AVERAGE (ok = 1.15, poor = 0.59)
            'xa_90': 0.12          # AVERAGE (ok = 0.19, poor = 0.1)
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, WAP)

        # Elite primary (70%) + average secondary (30%) should be GOOD or ELITE
        # Expected: (~110 * 0.7) + (~55 * 0.3) = 77 + 16.5 = 93.5 (ELITE tier)
        assert score.tier in ['ELITE', 'GOOD'], \
            f"Elite primary + average secondary should be GOOD or ELITE, got {score.tier}"
        assert score.overall_score >= 75, \
            f"Should score >= 75, got {score.overall_score:.1f}"


class TestBackwardCompatibility:
    """Ensure migration doesn't break existing interfaces."""

    @pytest.fixture
    def evaluator(self):
        return RoleEvaluator()

    def test_role_score_structure_unchanged(self, evaluator):
        """RoleScore output should maintain all expected attributes."""
        player = Player(
            name='Test', position_selected='DC', position='D (C)',
            age=25, wage=10000, apps=30, subs=0, gls=0, ast=0,
            av_rat=7.5, expires='01/06/2025', inf='', mins=2700,
            hdr_pct=75, tck_90=2.0, int_90=2.5, shts_blckd_90=0.5, clr_90=1.2
        )

        score = evaluator.evaluate_player_for_role(player, CB_STOPPER)

        # Check all expected attributes exist
        assert hasattr(score, 'role'), "Missing 'role' attribute"
        assert hasattr(score, 'display_name'), "Missing 'display_name' attribute"
        assert hasattr(score, 'overall_score'), "Missing 'overall_score' attribute"
        assert hasattr(score, 'tier'), "Missing 'tier' attribute"
        assert hasattr(score, 'metric_scores'), "Missing 'metric_scores' attribute"
        assert hasattr(score, 'strengths'), "Missing 'strengths' attribute"
        assert hasattr(score, 'weaknesses'), "Missing 'weaknesses' attribute"

    def test_metric_scores_structure(self, evaluator):
        """Each metric score should contain expected fields plus new 'weight' field."""
        player = Player(
            name='Test', position_selected='DC', position='D (C)',
            age=25, wage=10000, apps=30, subs=0, gls=0, ast=0,
            av_rat=7.5, expires='01/06/2025', inf='', mins=2700,
            hdr_pct=75, tck_90=2.0, int_90=2.5, shts_blckd_90=0.5, clr_90=1.2
        )

        score = evaluator.evaluate_player_for_role(player, CB_STOPPER)

        for metric, data in score.metric_scores.items():
            # Check existing fields (backward compatibility)
            assert 'value' in data, f"Missing 'value' in {metric}"
            assert 'tier' in data, f"Missing 'tier' in {metric}"
            assert 'score' in data, f"Missing 'score' in {metric}"
            assert 'threshold_good' in data, f"Missing 'threshold_good' in {metric}"
            assert 'threshold_ok' in data, f"Missing 'threshold_ok' in {metric}"
            assert 'threshold_poor' in data, f"Missing 'threshold_poor' in {metric}"
            # Check new field
            assert 'weight' in data, f"Missing 'weight' tag in {metric}"
            assert data['weight'] in ['PRIMARY', 'SECONDARY'], \
                f"Invalid weight tag: {data['weight']}"


class TestTierBoundaries:
    """Test tier classification boundaries with weighted scoring."""

    @pytest.fixture
    def evaluator(self):
        return RoleEvaluator()

    @pytest.fixture
    def base_player_data(self):
        return {
            'name': 'Test Player',
            'position_selected': 'ST',
            'position': 'ST',
            'age': 25,
            'wage': 10000,
            'apps': 30,
            'subs': 0,
            'gls': 0,
            'ast': 0,
            'av_rat': 7.5,
            'expires': '01/06/2025',
            'inf': '',
            'mins': 2700
        }

    def test_elite_tier_threshold(self, evaluator, base_player_data):
        """Score >= 85 should be ELITE tier."""
        # Create player that scores exactly at ELITE boundary
        # All metrics just above 'good' threshold
        player_data = {
            **base_player_data,
            # ST-GS Primary: headers_won_90, dribbles_90, xg_90
            'hdrs_w_90': 5.3,  # Slightly above good (5.08)
            'drb_90': 3.2,     # Slightly above good (3.05)
            'np_xg_90': 0.52,  # Slightly above good (0.5)
            # ST-GS Secondary: shots_on_target_90, conversion_pct
            'sht_90': 1.6,     # Slightly above good (1.57)
            'conv_pct': 31     # Slightly above good (30)
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, ST_GS)

        if score.overall_score >= 85:
            assert score.tier == 'ELITE', \
                f"Score {score.overall_score:.1f} >= 85 should be ELITE, got {score.tier}"

    def test_good_tier_range(self, evaluator, base_player_data):
        """Score 70-84 should be GOOD tier."""
        # Create player with metrics in 'good' range
        player_data = {
            **base_player_data,
            # ST-GS Primary: at 'ok' thresholds (will score ~70-85)
            'hdrs_w_90': 2.9,  # Between ok (2.76) and good (5.08)
            'drb_90': 1.3,     # Between ok (1.17) and good (3.05)
            'np_xg_90': 0.38,  # Between ok (0.35) and good (0.5)
            # ST-GS Secondary: at 'ok' thresholds
            'sht_90': 1.2,     # Between ok (1.09) and good (1.57)
            'conv_pct': 23     # Between ok (21) and good (30)
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, ST_GS)

        if 70 <= score.overall_score < 85:
            assert score.tier == 'GOOD', \
                f"Score {score.overall_score:.1f} (70-84 range) should be GOOD, got {score.tier}"

    def test_average_tier_range(self, evaluator, base_player_data):
        """Score 50-69 should be AVERAGE tier."""
        # Create player with metrics in 'average' range
        player_data = {
            **base_player_data,
            # ST-GS Primary: at 'poor' thresholds (will score ~40-70)
            'hdrs_w_90': 1.2,  # Between poor (1.03) and ok (2.76)
            'drb_90': 0.85,    # Between poor (0.69) and ok (1.17)
            'np_xg_90': 0.28,  # Between poor (0.22) and ok (0.35)
            # ST-GS Secondary: at 'poor' thresholds
            'sht_90': 0.85,    # Between poor (0.73) and ok (1.09)
            'conv_pct': 18     # Between poor (15) and ok (21)
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, ST_GS)

        if 50 <= score.overall_score < 70:
            assert score.tier == 'AVERAGE', \
                f"Score {score.overall_score:.1f} (50-69 range) should be AVERAGE, got {score.tier}"

    def test_poor_tier_below_50(self, evaluator, base_player_data):
        """Score < 50 should be POOR tier."""
        # Create player with metrics below 'poor' thresholds
        player_data = {
            **base_player_data,
            # ST-GS Primary: below 'poor' thresholds (CRITICAL)
            'hdrs_w_90': 0.5,  # Below poor (1.03)
            'drb_90': 0.3,     # Below poor (0.69)
            'np_xg_90': 0.1,   # Below poor (0.22)
            # ST-GS Secondary: below 'poor' thresholds
            'sht_90': 0.4,     # Below poor (0.73)
            'conv_pct': 8      # Below poor (15)
        }
        player = Player(**player_data)

        score = evaluator.evaluate_player_for_role(player, ST_GS)

        if score.overall_score < 50:
            assert score.tier == 'POOR', \
                f"Score {score.overall_score:.1f} < 50 should be POOR, got {score.tier}"
