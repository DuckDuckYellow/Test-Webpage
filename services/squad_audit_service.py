"""
Squad Audit Analysis Service - Refactored.
"""

from typing import Dict, List, Optional
from datetime import datetime
from models.squad_audit import (
    Player,
    Squad,
    PlayerAnalysis,
    SquadAnalysisResult,
    StatusFlag,
    PerformanceVerdict
)
from models.constants import PositionCategory, POSITION_METRICS, METRIC_NAMES
from services.player_evaluator_service import PlayerEvaluatorService

class SquadAuditService:
    """Service for analyzing squad performance and value."""

    def __init__(self):
        self.player_evaluator = PlayerEvaluatorService()

    def analyze_squad(self, squad: Squad) -> SquadAnalysisResult:
        """Perform complete squad analysis."""
        benchmarks = self._calculate_position_benchmarks(squad)
        squad_avg_wage = squad.get_average_wage()

        player_analyses = []
        for player in squad.players:
            analysis = self._analyze_player(player, benchmarks, squad_avg_wage)
            player_analyses.append(analysis)

        return SquadAnalysisResult(
            squad=squad,
            player_analyses=player_analyses,
            position_benchmarks=benchmarks,
            squad_avg_wage=squad_avg_wage,
            total_players=len(squad.players)
        )

    def _analyze_player(
        self,
        player: Player,
        benchmarks: Dict[str, Dict[str, float]],
        squad_avg_wage: float,
        position_override: Optional[PositionCategory] = None
    ) -> PlayerAnalysis:
        """
        Analyze a single player with minutes-based reliability thresholds.

        Minutes Thresholds:
        - < 200 mins: Hard Floor - Insufficient data, bypass performance calculation
        - 200-500 mins: Soft Floor - Apply Bayesian Average to prevent one-game outliers
        - > 500 mins: Normal calculation with full player stats
        """
        mins = player.mins if player.mins is not None else 0

        # Store all possible positions for filtering (always set this)
        player.all_possible_positions = self.player_evaluator.get_all_possible_positions(player)

        # HARD FLOOR: < 200 minutes
        if mins < 200:
            # Bypass performance calculation entirely
            # Still need to evaluate roles to set best_role for display
            if not player.best_role:
                self.player_evaluator.evaluate_roles(player)

            return PlayerAnalysis(
                player=player,
                performance_index=0.0,  # Not calculated
                value_score=0.0,        # Not calculated
                verdict=PerformanceVerdict.POOR,  # Default tier
                recommendation="INSUFFICIENT DATA - Less than 200 minutes played",
                top_metrics=["N/A - Insufficient Data"],
                contract_warning=self._check_contract_warning(player.expires)
            )

        # SOFT FLOOR: 200-500 minutes - Apply Bayesian Average
        if 200 <= mins < 500:
            self._apply_bayesian_average(player, benchmarks, mins)

        # Evaluate roles (uses adjusted stats if Bayesian Average was applied)
        if not player.best_role:
            self.player_evaluator.evaluate_roles(player)

        performance_index = player.best_role.overall_score
        value_score = self._calculate_value_score(performance_index, player.wage, squad_avg_wage)
        verdict = PerformanceVerdict(player.best_role.tier)

        # Add "Projected" prefix for Soft Floor players
        if 200 <= mins < 500:
            recommendation = f"PROJECTED - {self._generate_role_recommendation(player, value_score)}"
            top_metrics = self._format_all_metrics(player.best_role.metric_scores, projected=True)
        else:
            recommendation = self._generate_role_recommendation(player, value_score)
            top_metrics = self._format_all_metrics(player.best_role.metric_scores)

        contract_warning = self._check_contract_warning(player.expires)

        return PlayerAnalysis(
            player=player,
            performance_index=performance_index,
            value_score=value_score,
            verdict=verdict,
            recommendation=recommendation,
            top_metrics=top_metrics,
            contract_warning=contract_warning
        )

    def _apply_bayesian_average(self, player: Player, benchmarks: Dict[str, Dict[str, float]], mins: int):
        """
        Apply Bayesian Average to pull player stats toward squad average.

        This prevents one-game outliers from skewing analysis for players with 200-500 minutes.
        The weight transitions linearly:
        - 200 mins: 0% player stats, 100% squad average (full regression to mean)
        - 350 mins: 50% player stats, 50% squad average (balanced blend)
        - 500 mins: 100% player stats, 0% squad average (no regression)

        Formula: adjusted_stat = (player_stat × weight) + (squad_avg × (1 - weight))

        Args:
            player: Player to adjust (modified in-place)
            benchmarks: Squad averages by position
            mins: Minutes played (must be 200-500)
        """
        # Calculate player weight (0.0 at 200 mins → 1.0 at 500 mins)
        player_weight = (mins - 200) / 300.0

        # Get position benchmarks for this player's position
        position = self.player_evaluator.get_position_category(player)
        position_benchmarks = benchmarks.get(position.value, {})

        if not position_benchmarks:
            return  # No adjustment if no benchmarks available for this position

        # Apply weighted average to each metric in the position's benchmark
        for metric_attr, squad_avg in position_benchmarks.items():
            player_value = getattr(player, metric_attr, None)

            # Only adjust if player has a valid value for this metric
            if player_value is not None:
                # Apply Bayesian weighted average
                adjusted_value = (player_value * player_weight) + (squad_avg * (1 - player_weight))
                setattr(player, metric_attr, adjusted_value)

    def _calculate_position_benchmarks(self, squad: Squad) -> Dict[str, Dict[str, float]]:
        """Calculate average metrics for each position."""
        benchmarks = {}

        for position in PositionCategory:
            # Group players by position using the evaluator
            position_players = [p for p in squad.players if self.player_evaluator.get_position_category(p) == position]

            if not position_players:
                continue

            metrics = POSITION_METRICS.get(position, [])
            position_benchmarks = {}
            for metric in metrics:
                values = [getattr(p, metric, 0.0) for p in position_players if getattr(p, metric, None) is not None]
                position_benchmarks[metric] = sum(values) / len(values) if values else 0.0

            benchmarks[position.value] = position_benchmarks

        return benchmarks

    def _calculate_value_score(self, performance_index: float, player_wage: float, squad_avg_wage: float) -> float:
        if squad_avg_wage == 0.0 or player_wage == 0.0:
            return 100.0
        wage_index = max(0.1, player_wage / squad_avg_wage)
        return performance_index / wage_index

    def _generate_role_recommendation(self, player: Player, value_score: float) -> str:
        """
        Generate contract-related recommendations only.
        Retraining suggestions are not included in this column.
        """
        if player.mins is not None and player.mins < 500:
            return "USE OR SELL - Insufficient data to judge (Sub 500 mins)"

        # Check for low value score (poor value for money)
        if value_score < 50:
            if player.best_role and player.best_role.tier == 'ELITE':
                return "CONSIDER WAGE REDUCTION - Elite performance but overpaid"
            else:
                return "CONSIDER SALE - Poor value for wage cost"

        # Contract-related recommendations based on performance tier
        role = player.best_role
        status = player.get_status_flag()

        if role.tier == 'ELITE':
            if status == StatusFlag.TRANSFER_LISTED: return "KEEP & PLAY - Elite ratings despite transfer list"
            elif status == StatusFlag.U21: return "PROMOTE - Elite young talent"
            elif player.apps < 10: return "INCREASE MINUTES - Elite output per 90"
            else: return "CORE STARTER - Elite performance"

        elif role.tier == 'GOOD':
            if status == StatusFlag.TRANSFER_LISTED: return "EVALUATE - Good depth option"
            return "ROTATION/STARTER - Solid performance"

        elif role.tier == 'POOR':
            if status == StatusFlag.U21: return "DEVELOPMENT REQUIRED - Not ready"
            return "SELL/REPLACE - Below standard"

        return "BACKUP - Average performance"

    def _format_all_metrics(self, metric_scores: Dict[str, Dict], projected: bool = False) -> List[str]:
        """
        Format all metrics with their tier ratings for display.

        Shows all PRIMARY and SECONDARY metrics evaluated, organized by tier.
        Includes metrics that are good/average/poor to give full picture.
        """
        from models.constants import METRIC_NAMES

        if not metric_scores:
            return ["N/A - No metrics"]

        # Group metrics by tier
        elite_metrics = []
        good_metrics = []
        average_metrics = []
        poor_metrics = []

        for metric_name, metric_data in metric_scores.items():
            tier = metric_data.get('tier', 'UNKNOWN')
            display_name = METRIC_NAMES.get(metric_name, metric_name.replace('_', ' ').title())

            if tier == 'ELITE':
                elite_metrics.append(display_name)
            elif tier == 'GOOD':
                good_metrics.append(display_name)
            elif tier == 'AVERAGE':
                average_metrics.append(display_name)
            else:  # CRITICAL or POOR
                poor_metrics.append(display_name)

        # Format output
        result = []
        prefix = "Projected: " if projected else ""

        if elite_metrics:
            result.append(f"{prefix}Elite: {', '.join(elite_metrics)}")
        if good_metrics:
            result.append(f"{prefix}Good: {', '.join(good_metrics)}")
        if average_metrics:
            result.append(f"{prefix}Average: {', '.join(average_metrics)}")
        if poor_metrics:
            result.append(f"{prefix}Poor: {', '.join(poor_metrics)}")

        return result if result else ["N/A"]

    def _check_contract_warning(self, expires: str) -> bool:
        if not expires or expires == "-": return False
        try:
            expiry_date = datetime.strptime(expires, "%d/%m/%Y")
            today = datetime.now()
            months_remaining = (expiry_date.year - today.year) * 12 + (expiry_date.month - today.month)
            return months_remaining <= 12
        except: return False

    def export_to_csv_data(self, result: SquadAnalysisResult) -> List[Dict[str, str]]:
        csv_data = []
        for analysis in result.player_analyses:
            row = {
                "Name": analysis.player.name,
                "Position": self.player_evaluator.get_position_category(analysis.player).value,
                "Age": str(analysis.player.age),
                "Value Score": f"{analysis.value_score:.1f}",
                "Performance": analysis.verdict.value,
                "Status": analysis.player.inf or "-",
                "Recommendation": analysis.recommendation,
                "Contract Expires": analysis.player.expires,
                "Wage": analysis.player.get_wage_formatted(),
                "Top Metric 1": analysis.top_metrics[0] if len(analysis.top_metrics) > 0 else "-",
                "Top Metric 2": analysis.top_metrics[1] if len(analysis.top_metrics) > 1 else "-"
            }
            csv_data.append(row)
        return csv_data

    def suggest_formations(self, result: SquadAnalysisResult, top_n: int = 3) -> List[Dict]:
        FORMATIONS = [
            {"name": "4-2-3-1 DM AM Wide", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 2, PositionCategory.FB: 2, PositionCategory.DM: 2, PositionCategory.AM: 1, PositionCategory.W: 2, PositionCategory.ST: 1}},
            {"name": "4-3-3 DM Wide", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 2, PositionCategory.FB: 2, PositionCategory.DM: 1, PositionCategory.CM: 2, PositionCategory.W: 2, PositionCategory.ST: 1}},
            {"name": "4-3-2-1 DM AM Narrow", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 2, PositionCategory.FB: 2, PositionCategory.DM: 1, PositionCategory.CM: 2, PositionCategory.AM: 2, PositionCategory.ST: 1}},
            {"name": "5-2-2-1 DM AM", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 3, PositionCategory.FB: 2, PositionCategory.DM: 2, PositionCategory.AM: 2, PositionCategory.ST: 1}},
            {"name": "5-2-3 DM Wide", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 3, PositionCategory.FB: 2, PositionCategory.DM: 2, PositionCategory.W: 2, PositionCategory.ST: 1}},
            {"name": "4-4-2", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 2, PositionCategory.FB: 2, PositionCategory.CM: 2, PositionCategory.W: 2, PositionCategory.ST: 2}},
            {"name": "4-2-4 DM Wide", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 2, PositionCategory.FB: 2, PositionCategory.DM: 2, PositionCategory.W: 2, PositionCategory.ST: 2}},
            {"name": "4-4-2 Diamond Narrow", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 2, PositionCategory.FB: 2, PositionCategory.DM: 1, PositionCategory.CM: 2, PositionCategory.AM: 1, PositionCategory.ST: 2}},
            {"name": "4-2-2-2 DM AM Narrow", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 2, PositionCategory.FB: 2, PositionCategory.DM: 2, PositionCategory.AM: 2, PositionCategory.ST: 2}},
            {"name": "5-3-2 DM WB", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 3, PositionCategory.FB: 2, PositionCategory.DM: 1, PositionCategory.CM: 2, PositionCategory.ST: 2}},
            {"name": "3-4-3", "positions": {PositionCategory.GK: 1, PositionCategory.CB: 3, PositionCategory.FB: 2, PositionCategory.CM: 2, PositionCategory.W: 2, PositionCategory.ST: 1}}
        ]

        # Build position quality considering all positions each player can play
        position_quality = {}
        for pos in PositionCategory:
            # Get all players who CAN play this position (not just those whose best position is this)
            analyses = [a for a in result.player_analyses
                       if pos in self.player_evaluator.get_all_possible_positions(a.player)]
            elite_count = len([a for a in analyses if a.verdict == PerformanceVerdict.ELITE])
            good_count = len([a for a in analyses if a.verdict == PerformanceVerdict.GOOD])
            position_quality[pos] = {'elite': elite_count, 'good': good_count, 'total': len(analyses)}

        scored_formations = []
        for formation in FORMATIONS:
            score = 0
            can_fill = True
            position_breakdown = []
            for pos, required in formation['positions'].items():
                quality = position_quality.get(pos, {'elite': 0, 'good': 0, 'total': 0})
                if quality['total'] < required:
                    can_fill = False
                    break
                elite_filled = min(quality['elite'], required)
                good_filled = min(quality['good'], max(0, required - elite_filled))
                others_filled = max(0, required - elite_filled - good_filled)
                # Star Power Weighting: 10/4/1 (prioritizes formations that maximize elite players)
                score += (elite_filled * 10) + (good_filled * 4) + (others_filled * 1)
                # Calculate recruitment needed (elite + good players needed)
                quality_players_available = quality['elite'] + quality['good']
                recruitment_needed = max(0, required - quality_players_available)
                position_breakdown.append({
                    'position': pos.value,
                    'required': required,
                    'elite': quality['elite'],
                    'good': quality['good'],
                    'total_available': quality['total'],
                    'recruitment_needed': recruitment_needed
                })
            if can_fill:
                # Calculate total recruitment needed for this formation
                total_recruitment = sum(pos['recruitment_needed'] for pos in position_breakdown)
                scored_formations.append({
                    'name': formation['name'],
                    'score': score,
                    'breakdown': position_breakdown,
                    'total_recruitment_needed': total_recruitment
                })

        # Sort by score (highest first) - Star Power Weighting prioritizes elite players
        scored_formations.sort(key=lambda x: x['score'], reverse=True)
        return scored_formations[:top_n]
