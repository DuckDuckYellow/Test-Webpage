"""
League baseline models for wage comparison.

This module defines data structures for league-wide wage baselines,
used to compare player wages against league averages by position and division.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from models.constants import PositionCategory


@dataclass
class LeagueWageBaseline:
    """
    League-wide wage baseline for a specific division and position.

    Represents aggregated wage statistics for a position within a division,
    used for league-based value comparison.
    """
    division: str  # Division name (e.g., "English Premier Division")
    position: str  # FM position string (e.g., "ST (C)") or aggregated group ("Defenders")
    position_category: PositionCategory  # Mapped position category (GK, CB, ST, etc.)
    average_wage: float  # Mean wage for this division/position
    median_wage: float  # Median wage
    percentile_25: float  # 25th percentile (lower quartile)
    percentile_75: float  # 75th percentile (upper quartile)
    player_count: int  # Number of players in this baseline (0 = estimated)
    is_aggregated: bool = False  # True if this combines multiple positions (e.g., Defenders)


@dataclass
class LeagueBaselineCollection:
    """
    Collection of league wage baselines with efficient lookup capabilities.

    Provides methods to retrieve baselines with fallback strategies:
    - Position aggregation (FB → Defenders if <30 players)
    - GK multiplier estimation (if no GK data available)
    """
    baselines: List[LeagueWageBaseline]
    gk_wage_multiplier: float  # GK-to-outfield wage ratio from top 5 leagues
    division_metadata: Dict[str, int]  # Division → total player count
    _lookup_cache: Dict[Tuple[str, str], LeagueWageBaseline] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Build O(1) lookup cache on initialization."""
        self._build_lookup_cache()

    def _build_lookup_cache(self):
        """Create lookup cache for fast baseline retrieval."""
        self._lookup_cache = {}
        for baseline in self.baselines:
            key = (baseline.division, baseline.position_category.value)
            # Store first match (prefer specific over aggregated if multiple exist)
            if key not in self._lookup_cache or not baseline.is_aggregated:
                self._lookup_cache[key] = baseline

    def get_baseline(self, division: str, position_category: PositionCategory) -> Optional[LeagueWageBaseline]:
        """
        Get baseline for a specific division and position category.

        Args:
            division: Division name
            position_category: Position category

        Returns:
            Baseline if found, None otherwise
        """
        return self._lookup_cache.get((division, position_category.value))

    def get_baseline_with_aggregation(
        self,
        division: str,
        position_category: PositionCategory
    ) -> Optional[LeagueWageBaseline]:
        """
        Get baseline with position aggregation fallback.

        Cascade logic:
        1. Try specific position (e.g., FB)
        2. If not found or <30 players, try aggregated group:
           - CB/FB → "Defenders"
           - DM/CM/AM → "Midfielders"
           - W/ST → "Attackers"
           - GK → separate (no aggregation)

        Args:
            division: Division name
            position_category: Position category

        Returns:
            Baseline (specific or aggregated) if found, None otherwise
        """
        # Try specific position first
        specific = self.get_baseline(division, position_category)
        if specific and specific.player_count >= 30:
            return specific

        # Map to aggregated group
        group_map = {
            PositionCategory.CB: "Defenders",
            PositionCategory.FB: "Defenders",
            PositionCategory.DM: "Midfielders",
            PositionCategory.CM: "Midfielders",
            PositionCategory.AM: "Midfielders",
            PositionCategory.W: "Attackers",
            PositionCategory.ST: "Attackers",
        }

        group_name = group_map.get(position_category)
        if not group_name:
            return specific  # GK or unknown - return whatever we found

        # Look for aggregated baseline
        for baseline in self.baselines:
            if (baseline.division == division and
                baseline.position == group_name and
                baseline.is_aggregated):
                return baseline

        return specific  # Fallback to specific even if <30

    def get_baseline_with_gk_estimation(
        self,
        division: str,
        position_category: PositionCategory
    ) -> Optional[LeagueWageBaseline]:
        """
        Get GK baseline with multiplier estimation if no direct data exists.

        Logic:
        1. Check if GK baseline exists for division → return it
        2. If not, calculate avg outfield wage for division
        3. Estimate GK wage = avg_outfield_wage × gk_wage_multiplier
        4. Return synthetic baseline with estimated values

        Args:
            division: Division name
            position_category: Position category (must be GK)

        Returns:
            GK baseline (real or estimated) if possible, None otherwise
        """
        # Try direct lookup first
        direct_baseline = self.get_baseline(division, position_category)
        if direct_baseline:
            return direct_baseline

        # Only estimate for GK position
        if position_category != PositionCategory.GK:
            return None

        # Calculate avg outfield wage for division
        outfield_positions = [
            PositionCategory.CB, PositionCategory.FB, PositionCategory.DM,
            PositionCategory.CM, PositionCategory.AM, PositionCategory.W,
            PositionCategory.ST
        ]
        outfield_wages = []
        for pos in outfield_positions:
            baseline = self.get_baseline(division, pos)
            if baseline:
                outfield_wages.append(baseline.average_wage)

        if not outfield_wages:
            return None  # Division has no data at all

        avg_outfield_wage = sum(outfield_wages) / len(outfield_wages)
        estimated_gk_wage = avg_outfield_wage * self.gk_wage_multiplier

        # Return synthetic baseline (flagged as estimated with player_count=0)
        return LeagueWageBaseline(
            division=division,
            position="GK (Estimated)",
            position_category=PositionCategory.GK,
            average_wage=estimated_gk_wage,
            median_wage=estimated_gk_wage,  # Assume median = average for estimation
            percentile_25=estimated_gk_wage * 0.6,  # Rough approximation
            percentile_75=estimated_gk_wage * 1.4,
            player_count=0  # Flag as estimated
        )

    def get_available_divisions(self) -> List[str]:
        """
        Get list of all divisions with baseline data.

        Returns:
            Sorted list of division names
        """
        divisions = set(baseline.division for baseline in self.baselines)
        return sorted(list(divisions))

    def get_division_player_count(self, division: str) -> int:
        """
        Get total player count for a division.

        Args:
            division: Division name

        Returns:
            Player count, or 0 if division not found
        """
        return self.division_metadata.get(division, 0)

    def is_low_sample_size(self, division: str, threshold: int = 100) -> bool:
        """
        Check if a division has low sample size.

        Args:
            division: Division name
            threshold: Minimum player count (default: 100)

        Returns:
            True if division has fewer than threshold players
        """
        return self.get_division_player_count(division) < threshold
