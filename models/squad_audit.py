"""
Squad Audit Tracker Data Models - Refactored PODOs.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from models.constants import PositionCategory

class StatusFlag(Enum):
    """Player status flags."""
    INJURED = "Inj"
    TRANSFER_LISTED = "Wnt"
    U21 = "U21"
    PRE_CONTRACT = "PR"
    UNRELIABLE = "Unr"
    YELLOW_CARD = "Yel"
    DEPARTED = "Lst"
    NONE = ""

class PerformanceVerdict(Enum):
    """Performance rating categories."""
    ELITE = "ELITE"
    GOOD = "GOOD"
    AVERAGE = "AVERAGE"
    POOR = "POOR"

@dataclass
class Player:
    """
    Represents a football player with all relevant statistics.
    PODO - Plain Old Data Object.
    """

    # Basic info
    name: str
    position_selected: str
    position: str
    age: int
    wage: float
    apps: int
    subs: int
    gls: int
    ast: int
    av_rat: float
    expires: str
    inf: str

    # Per-90 statistics (compatibility)
    int_90: Optional[float] = None
    xg: Optional[float] = None
    shot_90: Optional[float] = None
    ch_c_90: Optional[float] = None
    drb_90: Optional[float] = None
    blk_90: Optional[float] = None
    k_tck_90: Optional[float] = None
    hdr_pct: Optional[float] = None
    tck_r: Optional[float] = None
    pas_pct: Optional[float] = None
    con_90: Optional[float] = None
    xgp: Optional[float] = None
    sv_pct: Optional[float] = None

    # V2 fields
    mins: Optional[int] = None
    xgp_90: Optional[float] = None
    tck_90: Optional[float] = None
    sht_90: Optional[float] = None
    hdrs_w_90: Optional[float] = None
    sprints_90: Optional[float] = None
    xa_90: Optional[float] = None
    np_xg_90: Optional[float] = None
    op_kp_90: Optional[float] = None
    conv_pct: Optional[float] = None
    pr_passes_90: Optional[float] = None
    clr_90: Optional[float] = None
    pres_c_90: Optional[float] = None
    op_crs_c_90: Optional[float] = None
    itc: Optional[int] = None
    shts_blckd_90: Optional[float] = None
    
    # Analysis results
    all_role_scores: List = field(default_factory=list)
    best_role: Any = None
    current_role_score: Any = None
    recommended_role: Any = None
    role_change_confidence: float = 0.0
    role_change_reason: str = ""

    def get_total_apps(self) -> int:
        return self.apps + self.subs

    def get_wage_formatted(self) -> str:
        return f"£{self.wage:,.0f} p/w"

    def get_status_flag(self) -> StatusFlag:
        flag_map = {
            "Inj": StatusFlag.INJURED,
            "Wnt": StatusFlag.TRANSFER_LISTED,
            "U21": StatusFlag.U21,
            "PR": StatusFlag.PRE_CONTRACT,
            "Unr": StatusFlag.UNRELIABLE,
            "Yel": StatusFlag.YELLOW_CARD,
            "Lst": StatusFlag.DEPARTED,
        }
        return flag_map.get(self.inf, StatusFlag.NONE)

    def get_position_category(self):
        """Helper for templates to get position category."""
        from services.player_evaluator_service import PlayerEvaluatorService
        evaluator = PlayerEvaluatorService()
        return evaluator.get_position_category(self)

    def get_contract_expiry_relative(self) -> str:
        """
        Convert contract expiry date to relative time period.

        Returns:
            Relative time period string (<6m, <1yr, 2yrs, 3yrs, etc.)
        """
        from datetime import datetime

        if not self.expires or self.expires == "-":
            return "N/A"

        try:
            expiry_date = datetime.strptime(self.expires, "%d/%m/%Y")
            today = datetime.now()

            # Calculate months remaining
            months_remaining = (expiry_date.year - today.year) * 12 + (expiry_date.month - today.month)

            # Calculate years for display
            years_remaining = months_remaining // 12

            if months_remaining < 6:
                return "<6m"
            elif months_remaining < 12:
                return "<1yr"
            elif years_remaining == 1:
                return "1yr"
            elif years_remaining == 2:
                return "2yrs"
            elif years_remaining == 3:
                return "3yrs"
            elif years_remaining == 4:
                return "4yrs"
            else:
                return f"{years_remaining}yrs"
        except:
            return "N/A"

    def get_contract_expiry_color(self) -> str:
        """
        Get Bootstrap color class for contract expiry badge.

        Returns:
            Bootstrap color class (danger, warning, info, success)
        """
        from datetime import datetime

        if not self.expires or self.expires == "-":
            return "secondary"

        try:
            expiry_date = datetime.strptime(self.expires, "%d/%m/%Y")
            today = datetime.now()
            months_remaining = (expiry_date.year - today.year) * 12 + (expiry_date.month - today.month)

            if months_remaining < 6:
                return "danger"
            elif months_remaining < 12:
                return "warning"
            elif months_remaining <= 24:
                return "info"
            else:
                return "success"
        except:
            return "secondary"

    def get_contract_months_remaining(self) -> int:
        """
        Get months remaining on contract for sorting purposes.

        Returns:
            Months remaining (999 for N/A contracts to sort them to the end)
        """
        from datetime import datetime

        if not self.expires or self.expires == "-":
            return 999

        try:
            expiry_date = datetime.strptime(self.expires, "%d/%m/%Y")
            today = datetime.now()
            months_remaining = (expiry_date.year - today.year) * 12 + (expiry_date.month - today.month)
            return months_remaining
        except:
            return 999

@dataclass
class Squad:
    """Represents a collection of players."""
    players: List[Player] = field(default_factory=list)

    def get_average_wage(self) -> float:
        if not self.players:
            return 0.0
        return sum(p.wage for p in self.players) / len(self.players)

@dataclass
class PlayerAnalysis:
    """Analysis results for a single player."""
    player: Player
    performance_index: float
    value_score: float
    verdict: PerformanceVerdict
    recommendation: str
    top_metrics: List[str] = field(default_factory=list)
    contract_warning: bool = False

    def get_value_score_color(self) -> str:
        if self.value_score >= 150: return "success"
        elif self.value_score >= 120: return "info"
        elif self.value_score >= 100: return "warning"
        elif self.value_score >= 80: return "dark"
        else: return "danger"

    def get_verdict_color(self) -> str:
        if self.verdict == PerformanceVerdict.ELITE: return "success"
        elif self.verdict == PerformanceVerdict.GOOD: return "info"
        elif self.verdict == PerformanceVerdict.AVERAGE: return "warning"
        elif self.verdict == PerformanceVerdict.POOR: return "danger"
        return "secondary"

@dataclass
class SquadAnalysisResult:
    """Complete squad analysis results."""
    squad: Squad
    player_analyses: List[PlayerAnalysis] = field(default_factory=list)
    position_benchmarks: Dict[str, Dict[str, float]] = field(default_factory=dict)
    squad_avg_wage: float = 0.0
    total_players: int = 0

    def get_elite_players(self) -> List[PlayerAnalysis]:
        return [a for a in self.player_analyses if a.verdict == PerformanceVerdict.ELITE]

    def get_poor_performers(self) -> List[PlayerAnalysis]:
        return [a for a in self.player_analyses if a.verdict == PerformanceVerdict.POOR]

    def get_transfer_listed_elite(self) -> List[PlayerAnalysis]:
        return [a for a in self.get_elite_players() if a.player.get_status_flag() == StatusFlag.TRANSFER_LISTED]

    def get_low_value_players(self) -> List[PlayerAnalysis]:
        """
        Get players with value score < 50 who are not already in poor performers.
        These are players who may be performing adequately but are overpaid.
        """
        return [a for a in self.player_analyses
                if a.value_score < 50
                and a.verdict != PerformanceVerdict.POOR
                and (a.player.mins is not None and a.player.mins >= 200)]

    def get_sorted_by_value(self) -> List[PlayerAnalysis]:
        return sorted(self.player_analyses, key=lambda x: x.value_score, reverse=True)
