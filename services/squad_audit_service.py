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
        """Analyze a single player."""
        if not player.best_role:
            self.player_evaluator.evaluate_roles(player)
            
        performance_index = player.best_role.overall_score
        value_score = self._calculate_value_score(performance_index, player.wage, squad_avg_wage)
        verdict = PerformanceVerdict(player.best_role.tier)
        recommendation = self._generate_role_recommendation(player)
        contract_warning = self._check_contract_warning(player.expires)
        top_metrics = [f"{m}: Elite" for m in player.best_role.strengths[:2]]
        
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

    def _generate_role_recommendation(self, player: Player) -> str:
        if player.mins is not None and player.mins < 500:
            return "USE OR SELL - Insufficient data to judge (Sub 500 mins)"

        if player.recommended_role:
             return f"{player.recommended_role.role} - {player.role_change_reason}"
             
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

        position_quality = {}
        for pos in PositionCategory:
            analyses = [a for a in result.player_analyses if self.player_evaluator.get_position_category(a.player) == pos]
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
                score += (elite_filled * 3) + (good_filled * 2) + (others_filled * 1)
                position_breakdown.append({'position': pos.value, 'required': required, 'elite': quality['elite'], 'good': quality['good'], 'total_available': quality['total']})
            if can_fill:
                scored_formations.append({'name': formation['name'], 'score': score, 'breakdown': position_breakdown})
        scored_formations.sort(key=lambda x: x['score'], reverse=True)
        return scored_formations[:top_n]
