"""
Squad Audit Analysis Service

This service provides the core business logic for analyzing Football Manager
squad data, calculating performance metrics, value scores, and generating
actionable recommendations.
"""

from typing import Dict, List, Optional
from datetime import datetime
from models.squad_audit import (
    Player,
    Squad,
    PlayerAnalysis,
    SquadAnalysisResult,
    PositionCategory,
    StatusFlag,
    PerformanceVerdict
)


class SquadAuditService:
    """Service for analyzing squad performance and value."""

    # Position-specific metrics configuration
    # Each position uses 4 key metrics for evaluation
    POSITION_METRICS = {
        PositionCategory.GK: ["sv_pct", "xgp", "pas_pct", "av_rat"],
        PositionCategory.CB: ["k_tck_90", "int_90", "hdr_pct", "pas_pct"],
        PositionCategory.FB: ["k_tck_90", "drb_90", "pas_pct", "blk_90"],
        PositionCategory.DM: ["k_tck_90", "int_90", "pas_pct", "av_rat"],
        PositionCategory.CM: ["pas_pct", "k_tck_90", "drb_90", "shot_90"],
        PositionCategory.AM: ["ch_c_90", "drb_90", "xg", "pas_pct"],
        PositionCategory.W: ["drb_90", "ch_c_90", "shot_90", "pas_pct"],
        PositionCategory.ST: ["shot_90", "xg", "ch_c_90", "av_rat"]
    }

    # Metric display names for readable output
    METRIC_NAMES = {
        "sv_pct": "Save %",
        "xgp": "xG Prevented",
        "pas_pct": "Pass %",
        "av_rat": "Avg Rating",
        "k_tck_90": "Key Tackles/90",
        "int_90": "Int/90",
        "hdr_pct": "Header %",
        "drb_90": "Dribbles/90",
        "blk_90": "Blocks/90",
        "shot_90": "Shots/90",
        "ch_c_90": "Chances Created/90",
        "xg": "xG"
    }

    def __init__(self):
        """Initialize the service."""
        pass

    def analyze_squad(self, squad: Squad) -> SquadAnalysisResult:
        """
        Perform complete squad analysis.

        Args:
            squad: Squad object containing all players

        Returns:
            SquadAnalysisResult with complete analysis for all players
        """
        # Calculate position benchmarks (averages by position)
        benchmarks = self._calculate_position_benchmarks(squad)

        # Calculate squad average wage
        squad_avg_wage = squad.get_average_wage()

        # Analyze each player
        player_analyses = []
        for player in squad.players:
            analysis = self._analyze_player(player, benchmarks, squad_avg_wage)
            player_analyses.append(analysis)

        # Create and return result
        result = SquadAnalysisResult(
            squad=squad,
            player_analyses=player_analyses,
            position_benchmarks=benchmarks,
            squad_avg_wage=squad_avg_wage,
            total_players=len(squad.players)
        )

        return result

    def _analyze_player(
        self,
        player: Player,
        benchmarks: Dict[str, Dict[str, float]],
        squad_avg_wage: float,
        position_override: Optional[PositionCategory] = None
    ) -> PlayerAnalysis:
        """
        Analyze a single player.

        Args:
            player: Player to analyze
            benchmarks: Position benchmarks for normalization
            squad_avg_wage: Squad average wage for value calculation
            position_override: Optional position to override automatic detection

        Returns:
            PlayerAnalysis with performance index, value score, and recommendation
        """
        # Get position category (use override if provided)
        position = position_override if position_override else player.get_position_category()

        # Calculate performance index
        performance_index = self._calculate_performance_index(player, position, benchmarks)

        # Calculate value score
        value_score = self._calculate_value_score(
            performance_index,
            player.wage,
            squad_avg_wage
        )

        # Determine verdict
        verdict = self._get_performance_verdict(performance_index)

        # Generate recommendation
        recommendation = self._generate_recommendation(player, verdict, value_score)

        # Check contract expiry
        contract_warning = self._check_contract_warning(player.expires)

        # Get top metrics
        top_metrics = self._get_top_metrics(player, position, benchmarks)

        return PlayerAnalysis(
            player=player,
            performance_index=performance_index,
            value_score=value_score,
            verdict=verdict,
            recommendation=recommendation,
            top_metrics=top_metrics,
            contract_warning=contract_warning
        )

    def _calculate_position_benchmarks(self, squad: Squad) -> Dict[str, Dict[str, float]]:
        """
        Calculate average metrics for each position.

        Args:
            squad: Squad object

        Returns:
            Dictionary mapping position to metric averages
            Example: {"GK": {"sv_pct": 68.5, "xgp": 2.1, ...}, ...}
        """
        benchmarks = {}

        for position in PositionCategory:
            # Get all players in this position
            position_players = squad.get_players_by_position(position)

            if not position_players:
                continue

            # Get metrics for this position
            metrics = self.POSITION_METRICS.get(position, [])

            # Calculate averages
            position_benchmarks = {}
            for metric in metrics:
                values = []
                for player in position_players:
                    value = getattr(player, metric, None)
                    if value is not None:
                        values.append(value)

                if values:
                    position_benchmarks[metric] = sum(values) / len(values)
                else:
                    position_benchmarks[metric] = 0.0

            benchmarks[position.value] = position_benchmarks

        return benchmarks

    def _calculate_performance_index(
        self,
        player: Player,
        position: PositionCategory,
        benchmarks: Dict[str, Dict[str, float]]
    ) -> float:
        """
        Calculate performance index (normalized to 100 = average).

        Args:
            player: Player to evaluate
            position: Player's position category
            benchmarks: Position benchmarks

        Returns:
            Performance index (100 = average, >100 = above average)
        """
        # Get metrics for this position
        metrics = self.POSITION_METRICS.get(position, [])

        if not metrics:
            return 100.0  # Default average if no metrics defined

        # Get position benchmarks
        position_benchmarks = benchmarks.get(position.value, {})

        if not position_benchmarks:
            return 100.0  # Default if no benchmarks available

        # Calculate normalized scores for each metric
        normalized_scores = []
        for metric in metrics:
            player_value = getattr(player, metric, None)
            benchmark_value = position_benchmarks.get(metric, 0.0)

            if player_value is None or benchmark_value == 0.0:
                continue  # Skip missing or zero benchmarks

            # Normalize to 100 = average
            normalized = (player_value / benchmark_value) * 100
            normalized_scores.append(normalized)

        # Return average of normalized scores
        if normalized_scores:
            return sum(normalized_scores) / len(normalized_scores)
        else:
            return 100.0  # Default if no valid metrics

    def _calculate_value_score(
        self,
        performance_index: float,
        player_wage: float,
        squad_avg_wage: float
    ) -> float:
        """
        Calculate value score (performance relative to wage).

        Formula: (Performance_Index / Wage_Index) × 100

        Args:
            performance_index: Player's performance index
            player_wage: Player's weekly wage
            squad_avg_wage: Squad average weekly wage

        Returns:
            Value score (100 = expected value, >100 = good value)
        """
        if squad_avg_wage == 0.0 or player_wage == 0.0:
            return 100.0  # Default if wage data unavailable

        # Calculate wage index (normalized to 100 = average)
        wage_index = (player_wage / squad_avg_wage) * 100

        # Value score = performance / wage
        value_score = (performance_index / wage_index) * 100

        return value_score

    def _get_performance_verdict(self, performance_index: float) -> PerformanceVerdict:
        """
        Get performance verdict based on performance index.

        Args:
            performance_index: Performance index value

        Returns:
            PerformanceVerdict enum
        """
        if performance_index >= 120:
            return PerformanceVerdict.ELITE
        elif performance_index >= 100:
            return PerformanceVerdict.GOOD
        elif performance_index >= 85:
            return PerformanceVerdict.AVERAGE
        else:
            return PerformanceVerdict.POOR

    def _generate_recommendation(
        self,
        player: Player,
        verdict: PerformanceVerdict,
        value_score: float
    ) -> str:
        """
        Generate actionable recommendation based on player status and performance.

        Args:
            player: Player object
            verdict: Performance verdict
            value_score: Value score

        Returns:
            Recommendation text
        """
        # Check for insufficient sample size (0-5 appearances)
        if player.apps <= 5:
            return "USE OR SELL - Insufficient data (low appearances)"

        status = player.get_status_flag()
        age = player.age

        # Elite performers
        if verdict == PerformanceVerdict.ELITE:
            if status == StatusFlag.TRANSFER_LISTED:
                return "INVESTIGATE TRANSFER LISTING - Elite metrics suggest retention"
            elif status == StatusFlag.U21:
                return "PROMOTE TO SENIOR TEAM - Elite performance at young age"
            elif status == StatusFlag.PRE_CONTRACT:
                return "USE NOW FOR IMPACT - Elite performer leaving soon"
            elif status == StatusFlag.UNRELIABLE:
                return "ADDRESS TACTICAL ISSUE - Elite metrics despite unreliability"
            elif player.apps < 10:
                return f"DEPLOY MORE ({player.apps} starts) - Elite per-90 metrics"
            else:
                return "LOCK IN STARTER - Elite performance across all metrics"

        # Good performers
        elif verdict == PerformanceVerdict.GOOD:
            if status == StatusFlag.TRANSFER_LISTED:
                return "Reconsider transfer - Good performance metrics"
            elif status == StatusFlag.U21:
                return "Continue development - Good progress for age"
            elif player.apps < 10:
                return f"Increase minutes ({player.apps} starts) - Good per-90"
            else:
                return "Maintain current role - Solid contributor"

        # Average performers
        elif verdict == PerformanceVerdict.AVERAGE:
            if status == StatusFlag.TRANSFER_LISTED:
                return "SELL - Average metrics, listed for transfer"
            elif status == StatusFlag.U21:
                return "Continue rotation - Development ongoing"
            elif age >= 30:
                return "Rotation option - Average veteran"
            else:
                return "Squad rotation - Meeting minimum standards"

        # Poor performers
        else:  # POOR
            if status == StatusFlag.TRANSFER_LISTED:
                return "SELL IMMEDIATELY - Poor metrics, already listed"
            elif status == StatusFlag.U21:
                if age <= 21:
                    return "Loan or development squad - Needs improvement"
                else:
                    return "Review future - Poor performance for age"
            elif status == StatusFlag.UNRELIABLE:
                return "SELL - Poor metrics and unreliable"
            elif age >= 30:
                return "DECLINING - Consider replacement"
            elif value_score < 80:
                return "UNDERPERFORMING - Review role or sell"
            else:
                return "Monitor closely - Below expected standards"

    def _check_contract_warning(self, expires: str) -> bool:
        """
        Check if contract is expiring soon (within 12 months).

        Args:
            expires: Contract expiry date (DD/MM/YYYY format)

        Returns:
            True if contract expires within 12 months
        """
        if not expires or expires == "-":
            return False

        try:
            # Parse date (format: "30/06/2032")
            expiry_date = datetime.strptime(expires, "%d/%m/%Y")
            today = datetime.now()

            # Check if expiring within 12 months
            months_remaining = (expiry_date.year - today.year) * 12 + (expiry_date.month - today.month)

            return months_remaining <= 12

        except (ValueError, AttributeError):
            return False

    def _get_top_metrics(
        self,
        player: Player,
        position: PositionCategory,
        benchmarks: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """
        Get the top 2 metrics that drive the player's rating.

        Args:
            player: Player object
            position: Position category
            benchmarks: Position benchmarks

        Returns:
            List of top 2 metric descriptions (e.g., ["Dribbles/90: 6.00", "Pass %: 91"])
        """
        metrics = self.POSITION_METRICS.get(position, [])
        position_benchmarks = benchmarks.get(position.value, {})

        if not metrics or not position_benchmarks:
            return []

        # Calculate relative performance for each metric
        metric_scores = []
        for metric in metrics:
            player_value = getattr(player, metric, None)
            benchmark_value = position_benchmarks.get(metric, 0.0)

            if player_value is None or benchmark_value == 0.0:
                continue

            # Calculate relative score
            relative_score = (player_value / benchmark_value) * 100
            metric_scores.append((metric, player_value, relative_score))

        # Sort by relative score (descending)
        metric_scores.sort(key=lambda x: x[2], reverse=True)

        # Get top 2 metrics
        top_metrics = []
        for metric, value, _ in metric_scores[:2]:
            metric_name = self.METRIC_NAMES.get(metric, metric)
            top_metrics.append(f"{metric_name}: {value:.2f}")

        return top_metrics

    def export_to_csv_data(self, result: SquadAnalysisResult) -> List[Dict[str, str]]:
        """
        Export analysis results to CSV-ready data.

        Args:
            result: SquadAnalysisResult object

        Returns:
            List of dictionaries ready for CSV export
        """
        csv_data = []

        for analysis in result.player_analyses:
            row = {
                "Name": analysis.player.name,
                "Position": analysis.player.get_position_category().value,
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
        """
        Suggest optimal formations based on available elite/good performers.

        Args:
            result: SquadAnalysisResult object
            top_n: Number of top formations to return

        Returns:
            List of formation suggestions with scores
        """
        # Common FM24 formations with position requirements
        FORMATIONS = [
            {
                "name": "4-2-3-1 DM AM Wide",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 2,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 2,
                    PositionCategory.AM: 1,
                    PositionCategory.W: 2,
                    PositionCategory.ST: 1
                }
            },
            {
                "name": "4-3-3 DM Wide",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 2,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 1,
                    PositionCategory.CM: 2,
                    PositionCategory.W: 2,
                    PositionCategory.ST: 1
                }
            },
            {
                "name": "4-3-2-1 DM AM Narrow",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 2,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 1,
                    PositionCategory.CM: 2,
                    PositionCategory.AM: 2,
                    PositionCategory.ST: 1
                }
            },
            {
                "name": "5-2-2-1 DM AM",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 3,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 2,
                    PositionCategory.AM: 2,
                    PositionCategory.ST: 1
                }
            },
            {
                "name": "5-2-3 DM Wide",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 3,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 2,
                    PositionCategory.W: 2,
                    PositionCategory.ST: 1
                }
            },
            {
                "name": "4-4-2",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 2,
                    PositionCategory.FB: 2,
                    PositionCategory.CM: 2,
                    PositionCategory.W: 2,
                    PositionCategory.ST: 2
                }
            },
            {
                "name": "4-2-4 DM Wide",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 2,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 2,
                    PositionCategory.W: 2,
                    PositionCategory.ST: 2
                }
            },
            {
                "name": "4-4-2 Diamond Narrow",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 2,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 1,
                    PositionCategory.CM: 2,
                    PositionCategory.AM: 1,
                    PositionCategory.ST: 2
                }
            },
            {
                "name": "4-2-2-2 DM AM Narrow",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 2,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 2,
                    PositionCategory.AM: 2,
                    PositionCategory.ST: 2
                }
            },
            {
                "name": "5-3-2 DM WB",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 3,
                    PositionCategory.FB: 2,
                    PositionCategory.DM: 1,
                    PositionCategory.CM: 2,
                    PositionCategory.ST: 2
                }
            },
            {
                "name": "3-4-3",
                "positions": {
                    PositionCategory.GK: 1,
                    PositionCategory.CB: 3,
                    PositionCategory.FB: 2,
                    PositionCategory.CM: 2,
                    PositionCategory.W: 2,
                    PositionCategory.ST: 1
                }
            }
        ]

        # Count elite/good players by position
        position_quality = {}
        for pos in PositionCategory:
            elite_count = len([a for a in result.player_analyses
                             if a.player.get_position_category() == pos
                             and a.verdict == PerformanceVerdict.ELITE])
            good_count = len([a for a in result.player_analyses
                            if a.player.get_position_category() == pos
                            and a.verdict == PerformanceVerdict.GOOD])
            position_quality[pos] = {
                'elite': elite_count,
                'good': good_count,
                'total': elite_count + good_count
            }

        # Get total player count by position (including all performance levels)
        position_totals = {}
        for pos in PositionCategory:
            total = len([a for a in result.player_analyses
                        if a.player.get_position_category() == pos])
            position_totals[pos] = total

        # Score each formation
        scored_formations = []
        for formation in FORMATIONS:
            score = 0
            can_fill = True
            position_breakdown = []

            for pos, required in formation['positions'].items():
                available = position_quality.get(pos, {})
                elite_count = available.get('elite', 0)
                good_count = available.get('good', 0)
                total_available = position_totals.get(pos, 0)

                # Check if we have enough total players (any quality)
                if total_available < required:
                    can_fill = False
                    break

                # Score based on quality (elite = 3 points, good = 2 points, others = 1 point)
                elite_filled = min(elite_count, required)
                good_filled = min(good_count, max(0, required - elite_filled))
                others_filled = max(0, required - elite_filled - good_filled)

                position_score = (elite_filled * 3) + (good_filled * 2) + (others_filled * 1)
                score += position_score

                position_breakdown.append({
                    'position': pos.value,
                    'required': required,
                    'elite': elite_count,
                    'good': good_count,
                    'total_available': total_available
                })

            if can_fill:
                scored_formations.append({
                    'name': formation['name'],
                    'score': score,
                    'breakdown': position_breakdown
                })

        # Sort by score (descending) and return top N
        scored_formations.sort(key=lambda x: x['score'], reverse=True)
        return scored_formations[:top_n]
