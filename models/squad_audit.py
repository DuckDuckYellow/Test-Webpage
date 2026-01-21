"""
Squad Audit Tracker Data Models

This module contains dataclasses for representing Football Manager squad data,
including players, squads, and analysis results.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class PositionCategory(Enum):
    """Position categories for player classification."""
    GK = "GK"
    CB = "CB"
    FB = "FB"
    DM = "DM"
    CM = "CM"
    AM = "AM"
    W = "W"
    ST = "ST"


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

    Attributes:
        name: Player's full name
        position_selected: Position grouping (GK, DR, DCR, etc.)
        position: Exact role (GK, D (C), D/WB (R), etc.)
        age: Player's age
        wage: Weekly wage in pounds (converted from "£29,000 p/w" format)
        apps: Starting appearances
        subs: Substitute appearances
        gls: Goals scored
        ast: Assists
        av_rat: Average rating (0-10 scale)
        expires: Contract expiry date (DD/MM/YYYY format)
        inf: Status flag (Inj, Wnt, U21, etc.)

        Per-90 minute statistics:
        int_90: Interceptions per 90
        xg: Expected Goals
        shot_90: Shots per 90
        ch_c_90: Chances Created per 90
        drb_90: Dribbles per 90
        blk_90: Blocks per 90
        k_tck_90: Key Tackles per 90
        hdr_pct: Header success percentage
        tck_r: Tackle ratio percentage
        pas_pct: Pass success percentage
        con_90: Goals conceded per 90 (primarily GK)
        xgp: Expected Goals Prevented
        sv_pct: Save percentage (GK only)
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

    # Per-90 statistics
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

    def get_position_category(self) -> PositionCategory:
        """
        Determine the position category based on position_selected.

        Returns:
            PositionCategory enum value (GK, CB, FB, DM, CM, AM, W, ST)
        """
        pos = self.position_selected.upper()

        # Goalkeeper
        if pos == "GK":
            return PositionCategory.GK

        # Center Backs
        if pos in ["DCR", "DCL", "DC", "D (C)"]:
            return PositionCategory.CB

        # Fullbacks
        if pos in ["DR", "DL"] or "D/WB" in pos or "WB" in pos:
            return PositionCategory.FB

        # Defensive Midfield
        if pos == "DM" or "DM" in pos:
            return PositionCategory.DM

        # Central Midfield
        if pos in ["MCR", "MCL", "MC", "M (C)"]:
            return PositionCategory.CM

        # Attacking Midfield
        if pos in ["AMR", "AML", "AM"] or "AM" in pos:
            return PositionCategory.AM

        # Wingers
        if "W" in pos and "WB" not in pos:  # Exclude wingbacks
            return PositionCategory.W

        # Strikers
        if pos in ["STC", "S (C)", "ST"] or "ST" in pos:
            return PositionCategory.ST

        # Default fallback based on first letter
        if pos.startswith("D"):
            return PositionCategory.CB
        elif pos.startswith("M"):
            return PositionCategory.CM
        elif pos.startswith("S"):
            return PositionCategory.ST
        else:
            return PositionCategory.CM  # Safe default

    def get_total_apps(self) -> int:
        """Get total appearances (starts + subs)."""
        return self.apps + self.subs

    def has_status_flag(self) -> bool:
        """Check if player has any status flag."""
        return bool(self.inf and self.inf.strip())

    def get_status_flag(self) -> StatusFlag:
        """Get the status flag enum."""
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

    def get_wage_formatted(self) -> str:
        """Format wage as '£XX,XXX p/w'."""
        return f"£{self.wage:,.0f} p/w"


@dataclass
class Squad:
    """
    Represents a collection of players (squad).

    Attributes:
        players: List of Player objects
    """

    players: List[Player] = field(default_factory=list)

    def get_players_by_position(self, position: PositionCategory) -> List[Player]:
        """
        Get all players in a specific position category.

        Args:
            position: PositionCategory enum value

        Returns:
            List of Player objects in that position
        """
        return [p for p in self.players if p.get_position_category() == position]

    def get_average_wage(self) -> float:
        """
        Calculate average squad wage.

        Returns:
            Average weekly wage across all players
        """
        if not self.players:
            return 0.0
        return sum(p.wage for p in self.players) / len(self.players)

    def get_squad_size(self) -> int:
        """Get total number of players in squad."""
        return len(self.players)

    def get_positions_summary(self) -> Dict[str, int]:
        """
        Get count of players by position category.

        Returns:
            Dictionary mapping position category to player count
        """
        summary = {}
        for player in self.players:
            pos = player.get_position_category().value
            summary[pos] = summary.get(pos, 0) + 1
        return summary


@dataclass
class PlayerAnalysis:
    """
    Represents the analysis results for a single player.

    Attributes:
        player: The Player object being analyzed
        performance_index: Normalized performance score (100 = average)
        value_score: Value for money score (performance / wage)
        verdict: Performance verdict (ELITE, GOOD, AVERAGE, POOR)
        recommendation: Actionable recommendation text
        top_metrics: Top 2 metrics that drive the rating
        contract_warning: Flag if contract expiring soon
    """

    player: Player
    performance_index: float
    value_score: float
    verdict: PerformanceVerdict
    recommendation: str
    top_metrics: List[str] = field(default_factory=list)
    contract_warning: bool = False

    def get_value_score_color(self) -> str:
        """
        Get Bootstrap color class for value score.

        Returns:
            Bootstrap color class (success, info, warning, danger)
        """
        if self.value_score >= 150:
            return "success"  # Green
        elif self.value_score >= 120:
            return "info"  # Light blue
        elif self.value_score >= 100:
            return "warning"  # Yellow
        elif self.value_score >= 80:
            return "orange"  # Orange
        else:
            return "danger"  # Red


@dataclass
class SquadAnalysisResult:
    """
    Represents the complete squad analysis results.

    Attributes:
        squad: The Squad object analyzed
        player_analyses: List of PlayerAnalysis results
        position_benchmarks: Position-specific average metrics
        squad_avg_wage: Average squad wage
        total_players: Total number of players analyzed
    """

    squad: Squad
    player_analyses: List[PlayerAnalysis] = field(default_factory=list)
    position_benchmarks: Dict[str, Dict[str, float]] = field(default_factory=dict)
    squad_avg_wage: float = 0.0
    total_players: int = 0

    def get_sorted_by_value(self, reverse: bool = True) -> List[PlayerAnalysis]:
        """
        Get player analyses sorted by value score.

        Args:
            reverse: If True, sort descending (highest first)

        Returns:
            Sorted list of PlayerAnalysis objects
        """
        return sorted(self.player_analyses, key=lambda x: x.value_score, reverse=reverse)

    def get_elite_players(self) -> List[PlayerAnalysis]:
        """Get all players with ELITE verdict."""
        return [pa for pa in self.player_analyses if pa.verdict == PerformanceVerdict.ELITE]

    def get_poor_performers(self) -> List[PlayerAnalysis]:
        """Get all players with POOR verdict."""
        return [pa for pa in self.player_analyses if pa.verdict == PerformanceVerdict.POOR]

    def get_transfer_listed_elite(self) -> List[PlayerAnalysis]:
        """Get elite performers who are transfer listed."""
        return [
            pa for pa in self.player_analyses
            if pa.verdict == PerformanceVerdict.ELITE
            and pa.player.get_status_flag() == StatusFlag.TRANSFER_LISTED
        ]
