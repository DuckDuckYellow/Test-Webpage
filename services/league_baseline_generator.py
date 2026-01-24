"""
League baseline generator service.

This service parses FM wage export HTML files and generates league-wide
wage baselines for position-based comparisons.
"""

import re
import json
from typing import List, Dict, Optional
from datetime import date
from bs4 import BeautifulSoup
import statistics

from models.league_baseline import LeagueWageBaseline, LeagueBaselineCollection
from models.constants import PositionCategory


class LeagueBaselineGenerator:
    """
    Generates league wage baselines from FM wage export HTML files.

    Handles:
    - Parsing 61-column wage export format
    - Position mapping to PositionCategory
    - GK multiplier calculation from top 5 leagues
    - Position aggregation for small sample sizes (<30 players)
    - JSON serialization/deserialization
    """

    # Top 5 European leagues for GK multiplier calculation
    TOP_5_LEAGUES = [
        "English Premier Division",
        "Spanish Primera División",
        "Italian Serie A",
        "German Bundesliga",
        "French Ligue 1"
    ]

    def _parse_wage(self, wage_str: str) -> float:
        """
        Parse wage strings to float values with robust regex.

        Handles formats:
        - "£3,400,000 p/w" → 3400000.0
        - "£29,000 p/w" → 29000.0
        - "£750 p/w" → 750.0
        - "€50,000 p/w" → 50000.0 (handles different currencies)
        - "-" → 0.0

        Args:
            wage_str: Wage string from HTML

        Returns:
            Wage as float
        """
        if not wage_str or wage_str == "-":
            return 0.0

        # Use regex to extract numeric portion
        # Removes currency symbols (£, €, $), commas, spaces, "p/w"
        match = re.search(r'[\d,]+\.?\d*', wage_str)
        if match:
            # Remove commas from matched number
            cleaned = match.group(0).replace(',', '')
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        return 0.0

    def _map_position_to_category(self, fm_position: str) -> Optional[PositionCategory]:
        """
        Map FM wage export position strings to PositionCategory.

        Position Mappings:
        - "GK" → GK
        - "D (C)" → CB
        - "D (R)", "D (L)", "D/WB (R)", "D/WB (L)" → FB
        - "DM" → DM
        - "M (C)", "M (R)", "M (L)" → CM
        - "AM (C)", "AM (R)", "AM (L)", "AM (RLC)" → AM
        - "ST (C)", "ST" → ST

        Args:
            fm_position: Position string from FM export

        Returns:
            PositionCategory if mappable, None otherwise
        """
        if not fm_position:
            return None

        # Normalize position string
        pos = fm_position.upper().strip()

        # GK
        if pos == "GK":
            return PositionCategory.GK

        # Center Backs
        if "D (C)" in pos or "DC" == pos:
            return PositionCategory.CB

        # Full Backs / Wing Backs
        if any(x in pos for x in ["D (R)", "D (L)", "D/WB", "WB"]):
            return PositionCategory.FB

        # Defensive Midfielders
        if pos == "DM" or "DM (" in pos:
            return PositionCategory.DM

        # Attacking Midfielders (check before CM to avoid false matches)
        if "AM" in pos:
            return PositionCategory.AM

        # Central Midfielders
        if "M (C)" in pos or pos == "MC" or any(x in pos for x in ["M (R)", "M (L)"]):
            return PositionCategory.CM

        # Wingers
        if pos == "W" or "W (" in pos or pos in ["AML", "AMR"]:
            return PositionCategory.W

        # Strikers
        if "ST" in pos:
            return PositionCategory.ST

        return None

    def parse_wage_export_html(self, html_content: str) -> List[Dict]:
        """
        Parse FM wage export HTML and extract player data.

        Expected columns (61 total):
        Inf(0), Name(1), Position(2), Nat(3), Age(4), Club(5), Wage(6),
        Personality(7), Left Foot(8), Right Foot(9), ...attributes..., Division(~42), Expires(~49)

        Args:
            html_content: HTML content from wage export

        Returns:
            List of player dicts with name, position, wage, division
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table')

        if not table:
            raise ValueError("No table found in HTML")

        # Get all rows
        all_rows = table.find_all('tr')
        if len(all_rows) < 2:
            raise ValueError("Table has no data rows")

        # Read header row to find column indices
        header_row = all_rows[0]
        headers = [th.get_text().strip() for th in header_row.find_all('th')]

        # Find critical column indices
        name_idx = None
        position_idx = None
        wage_idx = None
        division_idx = None

        for i, header in enumerate(headers):
            header_lower = header.lower()
            if header_lower == 'name':
                name_idx = i
            elif header_lower == 'position':
                position_idx = i
            elif header_lower == 'wage':
                wage_idx = i
            elif header_lower == 'division':
                division_idx = i

        # Validate we found all required columns
        if name_idx is None or position_idx is None or wage_idx is None or division_idx is None:
            print(f"Warning: Could not find all required columns. Found headers: {headers[:20]}")
            # Use fallback indices (educated guess based on typical format)
            name_idx = 1
            position_idx = 2
            wage_idx = 6
            division_idx = len(headers) - 3 if len(headers) > 10 else 10

        print(f"Using column indices - Name: {name_idx}, Position: {position_idx}, Wage: {wage_idx}, Division: {division_idx}")

        # Parse data rows
        players = []
        for row in all_rows[1:]:  # Skip header
            cells = row.find_all('td')
            if len(cells) < max(name_idx, position_idx, wage_idx, division_idx) + 1:
                continue

            try:
                # Extract key fields
                name = cells[name_idx].get_text().strip() if len(cells) > name_idx else ""
                fm_position = cells[position_idx].get_text().strip() if len(cells) > position_idx else ""
                wage_str = cells[wage_idx].get_text().strip() if len(cells) > wage_idx else "0"
                division = cells[division_idx].get_text().strip() if len(cells) > division_idx else ""

                # Parse values
                wage = self._parse_wage(wage_str)
                position_category = self._map_position_to_category(fm_position)

                # Skip if invalid
                if not name or not division or not position_category or wage == 0:
                    continue

                players.append({
                    'name': name,
                    'position': fm_position,
                    'position_category': position_category,
                    'wage': wage,
                    'division': division
                })

            except Exception as e:
                # Log warning but continue processing
                print(f"Warning: Failed to parse row: {e}")
                continue

        return players

    def calculate_gk_multiplier(self, player_data: List[Dict]) -> float:
        """
        Calculate GK-to-outfield wage ratio from top 5 European leagues.

        Formula:
            avg_gk_wage_top5 / avg_outfield_wage_top5

        Args:
            player_data: List of player dicts from parse_wage_export_html

        Returns:
            Multiplier (e.g., 0.75 means GKs earn 75% of outfield players)
        """
        # Filter to top 5 leagues
        top5_players = [p for p in player_data if p['division'] in self.TOP_5_LEAGUES]

        if not top5_players:
            print(f"Warning: No players found from top 5 leagues. Using default GK multiplier 0.75")
            return 0.75

        # Separate GKs and outfield players
        gk_wages = [p['wage'] for p in top5_players if p['position_category'] == PositionCategory.GK]
        outfield_wages = [p['wage'] for p in top5_players if p['position_category'] != PositionCategory.GK]

        if not gk_wages or not outfield_wages:
            print(f"Warning: Insufficient GK or outfield data in top 5 leagues. Using default 0.75")
            return 0.75

        avg_gk_wage = statistics.mean(gk_wages)
        avg_outfield_wage = statistics.mean(outfield_wages)

        if avg_outfield_wage == 0:
            return 0.75

        multiplier = avg_gk_wage / avg_outfield_wage
        print(f"Calculated GK multiplier: {multiplier:.3f} (from {len(gk_wages)} GKs, {len(outfield_wages)} outfield)")
        return multiplier

    def generate_baselines(self, player_data: List[Dict]) -> LeagueBaselineCollection:
        """
        Generate wage baselines from player data.

        Groups players by (division, position_category) and calculates:
        - Average, median, 25th/75th percentiles
        - Position aggregation for sample sizes <30
        - Division metadata (total player counts)

        Args:
            player_data: List of player dicts from parse_wage_export_html

        Returns:
            LeagueBaselineCollection with all baselines
        """
        # Calculate GK multiplier first
        gk_multiplier = self.calculate_gk_multiplier(player_data)

        # Group by division and position
        grouped = {}
        for player in player_data:
            key = (player['division'], player['position_category'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(player)

        # Calculate division metadata (total players per division)
        division_metadata = {}
        for player in player_data:
            div = player['division']
            division_metadata[div] = division_metadata.get(div, 0) + 1

        baselines = []

        # Process each division
        divisions = set(p['division'] for p in player_data)
        for division in divisions:
            division_positions = {}

            # Collect all positions for this division
            for position_cat in PositionCategory:
                key = (division, position_cat)
                if key in grouped:
                    division_positions[position_cat] = grouped[key]

            # Create specific baselines (for positions with ≥30 players)
            for position_cat, players in division_positions.items():
                player_count = len(players)
                if player_count >= 30:
                    wages = [p['wage'] for p in players]
                    baselines.append(self._create_baseline(
                        division=division,
                        position=players[0]['position'],  # Use FM position string
                        position_category=position_cat,
                        wages=wages,
                        is_aggregated=False
                    ))

            # Create aggregated baselines
            # Defenders (CB + FB)
            defender_players = []
            if PositionCategory.CB in division_positions:
                defender_players.extend(division_positions[PositionCategory.CB])
            if PositionCategory.FB in division_positions:
                defender_players.extend(division_positions[PositionCategory.FB])
            if len(defender_players) >= 5:
                wages = [p['wage'] for p in defender_players]
                baselines.append(self._create_baseline(
                    division=division,
                    position="Defenders",
                    position_category=PositionCategory.CB,  # Use CB as representative
                    wages=wages,
                    is_aggregated=True
                ))

            # Midfielders (DM + CM + AM)
            midfielder_players = []
            for pos in [PositionCategory.DM, PositionCategory.CM, PositionCategory.AM]:
                if pos in division_positions:
                    midfielder_players.extend(division_positions[pos])
            if len(midfielder_players) >= 5:
                wages = [p['wage'] for p in midfielder_players]
                baselines.append(self._create_baseline(
                    division=division,
                    position="Midfielders",
                    position_category=PositionCategory.CM,  # Use CM as representative
                    wages=wages,
                    is_aggregated=True
                ))

            # Attackers (W + ST)
            attacker_players = []
            for pos in [PositionCategory.W, PositionCategory.ST]:
                if pos in division_positions:
                    attacker_players.extend(division_positions[pos])
            if len(attacker_players) >= 5:
                wages = [p['wage'] for p in attacker_players]
                baselines.append(self._create_baseline(
                    division=division,
                    position="Attackers",
                    position_category=PositionCategory.ST,  # Use ST as representative
                    wages=wages,
                    is_aggregated=True
                ))

        return LeagueBaselineCollection(
            baselines=baselines,
            gk_wage_multiplier=gk_multiplier,
            division_metadata=division_metadata
        )

    def _create_baseline(
        self,
        division: str,
        position: str,
        position_category: PositionCategory,
        wages: List[float],
        is_aggregated: bool
    ) -> LeagueWageBaseline:
        """
        Create a single baseline from wage data.

        Args:
            division: Division name
            position: Position string (FM format or aggregated group name)
            position_category: Position category
            wages: List of wage values
            is_aggregated: Whether this is an aggregated baseline

        Returns:
            LeagueWageBaseline
        """
        return LeagueWageBaseline(
            division=division,
            position=position,
            position_category=position_category,
            average_wage=statistics.mean(wages),
            median_wage=statistics.median(wages),
            percentile_25=statistics.quantiles(wages, n=4)[0] if len(wages) >= 4 else min(wages),
            percentile_75=statistics.quantiles(wages, n=4)[2] if len(wages) >= 4 else max(wages),
            player_count=len(wages),
            is_aggregated=is_aggregated
        )

    def export_to_json(self, collection: LeagueBaselineCollection, output_path: str):
        """
        Serialize baselines to JSON file.

        Args:
            collection: LeagueBaselineCollection to export
            output_path: Output file path
        """
        data = {
            "version": "1.0",
            "generated_date": date.today().isoformat(),
            "gk_wage_multiplier": collection.gk_wage_multiplier,
            "division_metadata": collection.division_metadata,
            "baselines": [
                {
                    "division": b.division,
                    "position": b.position,
                    "position_category": b.position_category.value,
                    "average_wage": b.average_wage,
                    "median_wage": b.median_wage,
                    "percentile_25": b.percentile_25,
                    "percentile_75": b.percentile_75,
                    "player_count": b.player_count,
                    "is_aggregated": b.is_aggregated
                }
                for b in collection.baselines
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"Exported {len(collection.baselines)} baselines to {output_path}")

    def load_from_json(self, json_path: str) -> LeagueBaselineCollection:
        """
        Load baselines from JSON file.

        Args:
            json_path: Path to JSON file

        Returns:
            LeagueBaselineCollection

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON format is invalid
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate required fields
        if 'baselines' not in data or 'gk_wage_multiplier' not in data:
            raise ValueError("Invalid baseline JSON: missing required fields")

        baselines = []
        for b_data in data['baselines']:
            baselines.append(LeagueWageBaseline(
                division=b_data['division'],
                position=b_data['position'],
                position_category=PositionCategory(b_data['position_category']),
                average_wage=b_data['average_wage'],
                median_wage=b_data['median_wage'],
                percentile_25=b_data['percentile_25'],
                percentile_75=b_data['percentile_75'],
                player_count=b_data['player_count'],
                is_aggregated=b_data.get('is_aggregated', False)
            ))

        return LeagueBaselineCollection(
            baselines=baselines,
            gk_wage_multiplier=data['gk_wage_multiplier'],
            division_metadata=data.get('division_metadata', {})
        )
