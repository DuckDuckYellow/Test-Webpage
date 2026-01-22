"""
Role Evaluator - Evaluates players against role profiles

Calculates how well a player's metrics match each of the 12 defined roles.
Provides scoring, tier classification, and role recommendations.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from models.squad_audit import Player
from models.role_definitions import RoleProfile, ROLES


@dataclass
class RoleScore:
    """
    Evaluation result for a player against a specific role.

    Attributes:
        role: Role name (e.g., "CB-STOPPER")
        overall_score: 0-100 score (higher = better fit)
        tier: ELITE/GOOD/AVERAGE/POOR
        metric_scores: Dict of {metric: {value, tier, score, thresholds}}
        strengths: List of metrics where player is elite
        weaknesses: List of metrics where player is poor
    """
    role: str
    overall_score: float
    tier: str
    metric_scores: Dict[str, Dict]
    strengths: List[str]
    weaknesses: List[str]


class RoleEvaluator:
    """Evaluates how well a player matches each role."""

    def __init__(self):
        """Initialize the role evaluator."""
        pass

    def evaluate_player_for_role(self, player: Player, role: RoleProfile) -> RoleScore:
        """
        Calculate how well player fits a specific role.

        Args:
            player: Player object with metrics
            role: RoleProfile to evaluate against

        Returns:
            RoleScore object with detailed evaluation
        """
        # Get normalized metrics from player
        player_metrics = player.get_normalized_metrics()

        role_score = 0.0
        metric_scores = {}
        strengths = []
        weaknesses = []
        metric_count = 0

        for metric in role.metrics:
            if metric not in player_metrics:
                continue

            player_value = player_metrics[metric]
            thresholds = role.thresholds[metric]

            # Calculate score for this metric (0-100+ scale)
            tier, score = self._score_metric(player_value, thresholds)

            metric_scores[metric] = {
                'value': player_value,
                'tier': tier,
                'score': score,
                'threshold_good': thresholds['good'],
                'threshold_ok': thresholds['ok'],
                'threshold_poor': thresholds['poor']
            }

            # Track strengths and weaknesses
            if tier == 'ELITE':
                strengths.append(metric)
            elif tier == 'CRITICAL':
                weaknesses.append(metric)

            role_score += score
            metric_count += 1

        # Overall role score = average of all metric scores
        if metric_count > 0:
            overall_score = role_score / metric_count
        else:
            overall_score = 0.0

        # Determine overall tier
        overall_tier = self._score_to_tier(overall_score)

        return RoleScore(
            role=role.name,
            overall_score=overall_score,
            tier=overall_tier,
            metric_scores=metric_scores,
            strengths=strengths,
            weaknesses=weaknesses
        )

    def _score_metric(self, value: float, thresholds: Dict[str, float]) -> tuple[str, float]:
        """
        Score a single metric value against thresholds.

        Args:
            value: Player's metric value
            thresholds: Dict with 'good', 'ok', 'poor' thresholds

        Returns:
            Tuple of (tier, score)
            - tier: ELITE/GOOD/AVERAGE/POOR/CRITICAL
            - score: 0-120 (rewards excellence above 'good' threshold)
        """
        good = thresholds['good']
        ok = thresholds['ok']
        poor = thresholds['poor']

        if value >= good:
            # ELITE: Above "good" threshold
            # Score = 100 + bonus for excellence
            bonus = min(20, (value - good) / good * 10)
            return 'ELITE', 100 + bonus

        elif value >= ok:
            # GOOD: Between "ok" and "good"
            # Score = 70-100 based on position in range
            if good > ok:
                pct = (value - ok) / (good - ok)
                score = 70 + (pct * 30)
            else:
                score = 85  # Fallback
            return 'GOOD', score

        elif value >= poor:
            # AVERAGE: Between "poor" and "ok"
            # Score = 40-70 based on position in range
            if ok > poor:
                pct = (value - poor) / (ok - poor)
                score = 40 + (pct * 30)
            else:
                score = 55  # Fallback
            return 'AVERAGE', score

        else:
            # CRITICAL: Below "poor" threshold
            # Score = 0-40 based on how far below
            if poor > 0:
                pct = value / poor
                score = pct * 40
            else:
                score = 20
            return 'CRITICAL', score

    def _score_to_tier(self, score: float) -> str:
        """
        Convert 0-100+ score to tier classification.

        Args:
            score: Overall role score

        Returns:
            Tier string (ELITE/GOOD/AVERAGE/POOR)
        """
        if score >= 85:
            return 'ELITE'
        elif score >= 70:
            return 'GOOD'
        elif score >= 50:
            return 'AVERAGE'
        else:
            return 'POOR'

    def evaluate_all_roles(self, player: Player) -> List[RoleScore]:
        """
        Evaluate player against all 12 roles.

        Args:
            player: Player to evaluate

        Returns:
            List of RoleScore objects, sorted by score (best to worst)
        """
        role_scores = []

        for role_name, role_profile in ROLES.items():
            score = self.evaluate_player_for_role(player, role_profile)
            role_scores.append(score)

        # Sort by overall_score descending
        return sorted(role_scores, key=lambda s: s.overall_score, reverse=True)

    def get_best_role(self, player: Player) -> RoleScore:
        """
        Returns the top-scoring role for player.

        Args:
            player: Player to evaluate

        Returns:
            RoleScore for best-fitting role
        """
        all_roles = self.evaluate_all_roles(player)
        return all_roles[0]

    def get_role_recommendations(self, player: Player, min_score: float = 65.0,
                                 score_improvement: float = 10.0) -> List[RoleScore]:
        """
        Get alternative role recommendations for a player.

        Only recommends roles that:
        1. Score >= min_score (confident in the recommendation)
        2. Score improvement >= score_improvement vs current best
        3. Are interchangeable with player's natural position

        Args:
            player: Player to evaluate
            min_score: Minimum score to recommend (default 65)
            score_improvement: Minimum improvement needed (default 10 points)

        Returns:
            List of recommended RoleScore objects
        """
        all_roles = self.evaluate_all_roles(player)
        best_role = all_roles[0]

        recommendations = []

        for role_score in all_roles[1:]:  # Skip best role
            # Check minimum score threshold
            if role_score.overall_score < min_score:
                continue

            # Check score improvement
            improvement = role_score.overall_score - best_role.overall_score
            if improvement < score_improvement:
                continue

            # Check if roles are interchangeable
            role_profile = ROLES[role_score.role]
            if best_role.role not in role_profile.interchangeable_with:
                # Also check reverse (if best role allows this role)
                best_profile = ROLES[best_role.role]
                if role_score.role not in best_profile.interchangeable_with:
                    continue

            recommendations.append(role_score)

        return recommendations

    def generate_role_recommendation_text(self, role_score: RoleScore,
                                         best_role: RoleScore) -> str:
        """
        Generate human-readable recommendation text.

        Args:
            role_score: The recommended role
            best_role: The player's current best role

        Returns:
            Recommendation text string
        """
        improvement = role_score.overall_score - best_role.overall_score

        # Format top 3 strengths
        strengths = role_score.strengths[:3]
        strength_str = ", ".join([s.replace('_', ' ').title() for s in strengths])

        return f"Try as {role_score.role} (+{improvement:.0f} points) - Elite {strength_str}"
