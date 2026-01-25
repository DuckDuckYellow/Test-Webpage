"""
Squad Audit Analysis Service - Refactored.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from models.squad_audit import (
    Player,
    Squad,
    PlayerAnalysis,
    SquadAnalysisResult,
    StatusFlag,
    PerformanceVerdict,
    Recommendation,
    PlayerAssignment,
    BenchGap,
    FormationXI
)
from models.constants import PositionCategory, POSITION_METRICS, METRIC_NAMES
from models.league_baseline import LeagueWageBaseline, LeagueBaselineCollection
from services.player_evaluator_service import PlayerEvaluatorService

# Position to roles mapping for Best XI selection
POSITION_TO_ROLES = {
    PositionCategory.GK: ['GK'],
    PositionCategory.CB: ['CB-STOPPER', 'BCB'],
    PositionCategory.FB: ['FB', 'WB'],
    PositionCategory.DM: ['MD'],
    PositionCategory.CM: ['MC', 'MD'],
    PositionCategory.AM: ['AM(C)'],
    PositionCategory.W: ['WAP', 'WAS'],
    PositionCategory.ST: ['ST-GS', 'ST-PROVIDER']
}


class SquadAuditService:
    """Service for analyzing squad performance and value."""

    def __init__(self):
        self.player_evaluator = PlayerEvaluatorService()

    def analyze_squad(
        self,
        squad: Squad,
        selected_division: Optional[str] = None,
        league_baselines: Optional[LeagueBaselineCollection] = None
    ) -> SquadAnalysisResult:
        """Perform complete squad analysis with optional league comparison."""
        benchmarks = self._calculate_position_benchmarks(squad)
        squad_avg_wage = squad.get_average_wage()

        player_analyses = []
        for player in squad.players:
            analysis = self._analyze_player(
                player,
                benchmarks,
                squad_avg_wage,
                selected_division=selected_division,
                league_baselines=league_baselines
            )
            player_analyses.append(analysis)

        return SquadAnalysisResult(
            squad=squad,
            player_analyses=player_analyses,
            position_benchmarks=benchmarks,
            squad_avg_wage=squad_avg_wage,
            total_players=len(squad.players),
            selected_division=selected_division
        )

    def _analyze_player(
        self,
        player: Player,
        benchmarks: Dict[str, Dict[str, float]],
        squad_avg_wage: float,
        position_override: Optional[PositionCategory] = None,
        selected_division: Optional[str] = None,
        league_baselines: Optional[LeagueBaselineCollection] = None
    ) -> PlayerAnalysis:
        """
        Analyze a single player with minutes-based reliability thresholds.

        Minutes Thresholds:
        - < 200 mins: Hard Floor - Insufficient data, bypass performance calculation
        - 200-500 mins: Soft Floor - Apply Bayesian Average to prevent one-game outliers
        - > 500 mins: Normal calculation with full player stats

        Note: mins=None is treated as sufficient data for backward compatibility with legacy parsers.
        """
        mins = player.mins  # Keep as None if not set

        # Store all possible positions for filtering (always set this)
        player.all_possible_positions = self.player_evaluator.get_all_possible_positions(player)

        # HARD FLOOR: < 200 minutes (only if mins is explicitly set)
        if mins is not None and mins < 200:
            # Bypass performance calculation entirely
            # Still need to evaluate roles to set best_role for display
            if not player.best_role:
                self.player_evaluator.evaluate_roles(player)

            # No league value calculation for <200 mins players
            return PlayerAnalysis(
                player=player,
                performance_index=0.0,  # Not calculated
                value_score=0.0,        # Not calculated
                league_value_score=None,
                league_baseline=None,
                league_wage_percentile=None,
                verdict=PerformanceVerdict.POOR,  # Default tier
                recommendation=Recommendation(
                    badge="LOW DATA",
                    icon="",
                    color="secondary",
                    explanation=f"Insufficient data ({mins} mins played)",
                    has_contract_warning=False
                ),
                top_metrics=["N/A - Insufficient Data"],
                contract_warning=self._check_contract_warning(player.expires)
            )

        # SOFT FLOOR: 200-500 minutes - Apply Bayesian Average (only if mins is explicitly set)
        if mins is not None and 200 <= mins < 500:
            self._apply_bayesian_average(player, benchmarks, mins)

        # Evaluate roles (uses adjusted stats if Bayesian Average was applied)
        if not player.best_role:
            self.player_evaluator.evaluate_roles(player)

        performance_index = player.best_role.overall_score
        value_score = self._calculate_value_score(performance_index, player.wage, squad_avg_wage)
        verdict = PerformanceVerdict(player.best_role.tier)

        # Calculate league value score (if division selected)
        player_position = position_override if position_override else self.player_evaluator.get_position_category(player)
        league_value_score, league_baseline, league_percentile = self._calculate_league_value_score(
            performance_index,
            player.wage,
            player_position,
            selected_division,
            league_baselines
        )

        # Generate recommendation (Soft Floor players get is_projected=True)
        # mins=None is treated as full data for backward compatibility
        is_projected = mins is not None and 200 <= mins < 500
        recommendation = self._generate_role_recommendation(player, value_score, is_projected=is_projected)
        top_metrics = self._format_all_metrics(player.best_role.metric_scores, projected=is_projected)

        contract_warning = self._check_contract_warning(player.expires)

        return PlayerAnalysis(
            player=player,
            performance_index=performance_index,
            value_score=value_score,
            verdict=verdict,
            recommendation=recommendation,
            top_metrics=top_metrics,
            contract_warning=contract_warning,
            league_value_score=league_value_score,
            league_baseline=league_baseline,
            league_wage_percentile=league_percentile
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

    def _calculate_league_value_score(
        self,
        performance_index: float,
        player_wage: float,
        player_position: PositionCategory,
        selected_division: Optional[str],
        league_baselines: Optional[LeagueBaselineCollection]
    ) -> Tuple[Optional[float], Optional[LeagueWageBaseline], Optional[float]]:
        """
        Calculate league-based value score with GK multiplier fallback.

        Formula:
            league_wage_index = player_wage / league_avg_wage
            league_value_score = performance_index / league_wage_index

        GK Fallback:
            If no GK baseline exists for division:
            - Get avg outfield wage for division
            - Estimate GK wage = avg_outfield_wage × gk_wage_multiplier
            - Use estimated wage for comparison

        Returns:
            (league_value_score, baseline_used, wage_percentile)
        """
        if not league_baselines or not selected_division:
            return None, None, None

        # Try to get baseline with aggregation fallback
        baseline = league_baselines.get_baseline_with_aggregation(selected_division, player_position)

        # GK FALLBACK: If still no baseline (GK case), estimate using multiplier
        if not baseline and player_position == PositionCategory.GK:
            baseline = league_baselines.get_baseline_with_gk_estimation(selected_division, player_position)

        if not baseline or baseline.average_wage == 0.0 or player_wage == 0.0:
            return None, baseline, None

        league_wage_index = max(0.1, player_wage / baseline.average_wage)
        league_value_score = performance_index / league_wage_index

        # Calculate percentile (approximate using quartiles)
        if player_wage <= baseline.percentile_25:
            percentile = 25.0
        elif player_wage <= baseline.median_wage:
            percentile = 50.0
        elif player_wage <= baseline.percentile_75:
            percentile = 75.0
        else:
            percentile = 95.0

        return league_value_score, baseline, percentile

    def _generate_role_recommendation(
        self,
        player: Player,
        value_score: float,
        is_projected: bool = False
    ) -> Recommendation:
        """
        Generate structured recommendation with badge, icon, color, and explanation.

        Args:
            player: Player to generate recommendation for
            value_score: Calculated value score
            is_projected: True if player has 200-500 minutes (Soft Floor)

        Returns:
            Recommendation object with badge/icon/color/explanation
        """
        # Check contract status for warning overlay
        contract_warning = self._check_contract_expiring_soon(player)

        # LOW DATA: <500 minutes
        if player.mins is not None and player.mins < 500:
            mins = player.mins
            if mins < 200:
                return Recommendation(
                    badge="LOW DATA",
                    icon="",
                    color="secondary",
                    explanation=f"Insufficient data ({mins} mins played)",
                    has_contract_warning=contract_warning
                )
            else:
                return Recommendation(
                    badge="LOW DATA",
                    icon="",
                    color="secondary",
                    explanation=f"Projected stats only ({mins} mins played)",
                    has_contract_warning=contract_warning
                )

        # Check for low value score (poor value for money)
        if value_score < 50:
            if player.best_role and player.best_role.tier == 'ELITE':
                return Recommendation(
                    badge="WAGE CUT",
                    icon="💰",
                    color="warning",
                    explanation="Elite performance but overpaid",
                    has_contract_warning=contract_warning
                )
            else:
                return Recommendation(
                    badge="CONSIDER SALE",
                    icon="$",
                    color="danger",
                    explanation="Poor value for wage cost",
                    has_contract_warning=contract_warning
                )

        # Contract-related recommendations based on performance tier
        role = player.best_role
        status = player.get_status_flag()

        if role.tier == 'ELITE':
            if status == StatusFlag.TRANSFER_LISTED:
                return Recommendation(
                    badge="KEEP & PLAY",
                    icon="✓",
                    color="success",
                    explanation="Elite ratings despite transfer list",
                    has_contract_warning=contract_warning
                )
            elif status == StatusFlag.U21:
                return Recommendation(
                    badge="PROMOTE",
                    icon="↑",
                    color="info",
                    explanation="Elite young talent",
                    has_contract_warning=contract_warning
                )
            elif player.apps < 10:
                return Recommendation(
                    badge="INCREASE MINS",
                    icon="⏱",
                    color="info",
                    explanation="Elite output per 90",
                    has_contract_warning=contract_warning
                )
            else:
                return Recommendation(
                    badge="CORE STARTER",
                    icon="⭐",
                    color="success",
                    explanation="Elite performance",
                    has_contract_warning=contract_warning
                )

        elif role.tier == 'GOOD':
            if status == StatusFlag.TRANSFER_LISTED:
                return Recommendation(
                    badge="EVALUATE",
                    icon="⇄",
                    color="warning",
                    explanation="Good depth option on transfer list",
                    has_contract_warning=contract_warning
                )
            return Recommendation(
                badge="BACKUP",
                icon="◐",
                color="secondary",
                explanation="Solid rotation option",
                has_contract_warning=contract_warning
            )

        elif role.tier == 'POOR':
            if status == StatusFlag.U21:
                return Recommendation(
                    badge="DEVELOP",
                    icon="📈",
                    color="warning",
                    explanation="Not ready yet",
                    has_contract_warning=contract_warning
                )
            return Recommendation(
                badge="SELL/REPLACE",
                icon="✗",
                color="danger",
                explanation="Below standard",
                has_contract_warning=contract_warning
            )

        # AVERAGE tier
        return Recommendation(
            badge="BACKUP",
            icon="◐",
            color="secondary",
            explanation="Average performance",
            has_contract_warning=contract_warning
        )

    def _check_contract_expiring_soon(self, player: Player) -> bool:
        """Check if Elite/Good player has <6 months on contract."""
        if not player.best_role or player.best_role.tier not in ['ELITE', 'GOOD']:
            return False

        if not player.expires or player.expires == "-":
            return False

        try:
            expiry_date = datetime.strptime(player.expires, "%d/%m/%Y")
            today = datetime.now()
            months_remaining = (expiry_date.year - today.year) * 12 + (expiry_date.month - today.month)
            return months_remaining < 6
        except:
            return False

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
                "League Value Score": f"{analysis.league_value_score:.1f}" if analysis.league_value_score else "N/A",
                "League Wage Percentile": f"{analysis.league_wage_percentile:.0f}th" if analysis.league_wage_percentile else "N/A",
                "Value Insight": analysis.get_value_comparison_indicator() or "",
                "Performance": analysis.verdict.value,
                "Status": analysis.player.inf or "-",
                "Recommendation": f"{analysis.recommendation.badge} - {analysis.recommendation.explanation}",
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

    def _get_position_score(self, player_analysis: PlayerAnalysis,
                            target_position: PositionCategory) -> Tuple[float, str]:
        """Get best role score for a player in a specific position slot."""
        relevant_roles = POSITION_TO_ROLES.get(target_position, [])
        best_score = 0.0
        best_role = ""

        for role_score in player_analysis.player.all_role_scores:
            if role_score.role in relevant_roles and role_score.overall_score > best_score:
                best_score = role_score.overall_score
                best_role = role_score.role

        return best_score, best_role

    def generate_best_xi(self, formation: Dict,
                         result: SquadAnalysisResult) -> FormationXI:
        """Generate optimal XI and bench for a formation."""
        positions = formation['positions']
        used_players = set()
        starting_xi = {}
        total_score = 0.0

        # Sort positions by scarcity (fewest available players first)
        def count_available(pos):
            return len([a for a in result.player_analyses
                       if pos in self.player_evaluator.get_all_possible_positions(a.player)])

        sorted_positions = sorted(positions.items(), key=lambda x: count_available(x[0]))

        for position, slots_needed in sorted_positions:
            starting_xi[position] = []

            # Get candidates who can play this position and aren't used
            candidates = [
                a for a in result.player_analyses
                if position in self.player_evaluator.get_all_possible_positions(a.player)
                and a.player.name not in used_players
            ]

            # Score and sort candidates
            scored = []
            for candidate in candidates:
                pos_score, role = self._get_position_score(candidate, position)
                tier_priority = {PerformanceVerdict.ELITE: 4, PerformanceVerdict.GOOD: 3,
                               PerformanceVerdict.AVERAGE: 2, PerformanceVerdict.POOR: 1}
                scored.append((candidate, pos_score, role, tier_priority.get(candidate.verdict, 0)))

            scored.sort(key=lambda x: (x[3], x[1]), reverse=True)

            # Select top N
            for i in range(min(slots_needed, len(scored))):
                candidate, pos_score, role, _ = scored[i]
                is_natural = self.player_evaluator.get_position_category(candidate.player) == position
                assignment = PlayerAssignment(
                    player_analysis=candidate,
                    assigned_position=position,
                    assigned_role=role or position.value,
                    position_score=pos_score,
                    is_natural=is_natural
                )
                starting_xi[position].append(assignment)
                used_players.add(candidate.player.name)
                total_score += pos_score

        # Generate bench with gap tracking
        bench, bench_gaps = self._generate_bench(result, used_players)

        return FormationXI(
            formation_name=formation['name'],
            starting_xi=starting_xi,
            bench=bench,
            bench_gaps=bench_gaps,
            total_quality_score=total_score
        )

    def _generate_bench(self, result: SquadAnalysisResult,
                        used_players: set) -> Tuple[List[PlayerAssignment], List[BenchGap]]:
        """Generate balanced 11-player bench with guaranteed positional coverage.

        Returns:
            Tuple of (bench assignments, list of unfilled mandatory gaps)
        """
        remaining = [a for a in result.player_analyses if a.player.name not in used_players]

        # Sort by verdict tier then best_role score
        tier_priority = {PerformanceVerdict.ELITE: 4, PerformanceVerdict.GOOD: 3,
                        PerformanceVerdict.AVERAGE: 2, PerformanceVerdict.POOR: 1}
        remaining.sort(key=lambda a: (
            tier_priority.get(a.verdict, 0),
            a.player.best_role.overall_score if a.player.best_role else 0
        ), reverse=True)

        def create_assignment(analysis):
            pos = self.player_evaluator.get_position_category(analysis.player)
            role = analysis.player.best_role.role if analysis.player.best_role else pos.value
            score = analysis.player.best_role.overall_score if analysis.player.best_role else 0
            return PlayerAssignment(
                player_analysis=analysis,
                assigned_position=pos,
                assigned_role=role,
                position_score=score,
                is_natural=True
            )

        # Define position groups for bench balance
        POSITION_GROUPS = {
            'GK': [PositionCategory.GK],
            'DEF': [PositionCategory.CB, PositionCategory.FB],
            'MID': [PositionCategory.DM, PositionCategory.CM],
            'AM': [PositionCategory.AM, PositionCategory.W],
            'ST': [PositionCategory.ST]
        }

        # Minimum coverage requirements: 1 GK, 2 DEF, 1 MID, 2 AM, 1 ST = 7, then 4 flex
        BENCH_MINIMUMS = {'GK': 1, 'DEF': 2, 'MID': 1, 'AM': 2, 'ST': 1}

        # Display names for gap warnings
        GAP_DISPLAY_NAMES = {
            'GK': 'Backup GK',
            'DEF': 'Backup Defender',
            'MID': 'Backup Midfielder',
            'AM': 'Backup Attacker',
            'ST': 'Backup Striker'
        }

        bench = []
        bench_gaps = []
        used_in_bench = set()

        # Phase 1: Fill minimum coverage for each group, track gaps
        for group, min_count in BENCH_MINIMUMS.items():
            group_positions = POSITION_GROUPS[group]
            group_candidates = [
                a for a in remaining
                if self.player_evaluator.get_position_category(a.player) in group_positions
                and a.player.name not in used_in_bench
            ]

            filled = 0
            for i in range(min(min_count, len(group_candidates))):
                bench.append(create_assignment(group_candidates[i]))
                used_in_bench.add(group_candidates[i].player.name)
                filled += 1

            # Track unfilled mandatory slots
            if filled < min_count:
                bench_gaps.append(BenchGap(
                    group=group,
                    display_name=f"No {GAP_DISPLAY_NAMES[group]} Available",
                    count_missing=min_count - filled
                ))

        # Phase 2: Fill remaining slots (up to 11) with best available
        for analysis in remaining:
            if len(bench) >= 11:
                break
            if analysis.player.name not in used_in_bench:
                bench.append(create_assignment(analysis))
                used_in_bench.add(analysis.player.name)

        return bench[:11], bench_gaps

    def suggest_formations_with_xi(self, result: SquadAnalysisResult,
                                   top_n: int = 3) -> List[Dict]:
        """Get formation suggestions with best XI for each."""
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

        formations = self.suggest_formations(result, top_n)

        for formation_result in formations:
            # Find matching formation definition
            formation_def = next(
                (f for f in FORMATIONS if f['name'] == formation_result['name']),
                None
            )
            if formation_def:
                formation_result['best_xi'] = self.generate_best_xi(formation_def, result)

        return formations
