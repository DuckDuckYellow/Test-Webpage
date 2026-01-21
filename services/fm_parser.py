"""
Football Manager HTML Parser Service

This service parses Football Manager squad export HTML files and converts them
into structured Player and Squad objects for analysis.
"""

import re
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup
from models.squad_audit import Player, Squad


class FMHTMLParser:
    """Parser for Football Manager HTML squad exports."""

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse_html(self, html_content: str) -> Squad:
        """
        Parse FM HTML export and return a Squad object.

        Args:
            html_content: Raw HTML content from FM export

        Returns:
            Squad object containing all parsed players

        Raises:
            ValueError: If HTML structure is invalid or required data is missing
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the main table (look for table with player data)
        table = soup.find('table')
        if not table:
            raise ValueError("No table found in HTML content")

        # Get all rows (skip header row)
        rows = table.find_all('tr')[1:]  # Skip header
        if not rows:
            raise ValueError("No player data rows found")

        players = []
        for row in rows:
            try:
                player = self._parse_player_row(row)
                if player:
                    players.append(player)
            except Exception as e:
                # Log warning but continue parsing other players
                print(f"Warning: Failed to parse row: {e}")
                continue

        if not players:
            raise ValueError("No players could be parsed from HTML")

        return Squad(players=players)

    def _parse_player_row(self, row) -> Optional[Player]:
        """
        Parse a single table row into a Player object.

        Args:
            row: BeautifulSoup table row element

        Returns:
            Player object or None if parsing fails
        """
        cells = row.find_all('td')
        if len(cells) < 24:  # Minimum expected columns
            return None

        # Extract text from each cell
        data = [self._clean_cell_text(cell.get_text()) for cell in cells]

        # Parse appearances (format: "13 (3)" = 13 starts, 3 subs)
        apps, subs = self._parse_appearances(data[4])

        # Parse wage (format: "£29,000 p/w" → 29000.0)
        wage = self._parse_wage(data[8])

        # Create Player object
        player = Player(
            name=data[2],
            position_selected=data[0],
            position=data[3],
            age=self._parse_int(data[9]),
            wage=wage,
            apps=apps,
            subs=subs,
            gls=self._parse_int(data[5]),
            ast=self._parse_int(data[6]),
            av_rat=self._parse_float(data[7]),
            expires=data[10],
            inf=data[1],
            # Per-90 statistics
            int_90=self._parse_float(data[11]),
            xg=self._parse_float(data[12]),
            shot_90=self._parse_float(data[13]),
            ch_c_90=self._parse_float(data[14]),
            drb_90=self._parse_float(data[15]),
            blk_90=self._parse_float(data[16]),
            k_tck_90=self._parse_float(data[17]),
            hdr_pct=self._parse_float(data[18]),
            tck_r=self._parse_float(data[19]),
            pas_pct=self._parse_float(data[20]),
            con_90=self._parse_float(data[21]),
            xgp=self._parse_float(data[22]),
            sv_pct=self._parse_float(data[23])
        )

        return player

    def _clean_cell_text(self, text: str) -> str:
        """
        Clean cell text (strip whitespace, normalize).

        Args:
            text: Raw cell text

        Returns:
            Cleaned text
        """
        return text.strip()

    def _parse_appearances(self, apps_str: str) -> Tuple[int, int]:
        """
        Parse appearances string in format "13 (3)" to (starts, subs).

        Args:
            apps_str: Appearances string (e.g., "13 (3)", "15 (1)", "4 (9)")

        Returns:
            Tuple of (starts, subs)

        Examples:
            "13 (3)" → (13, 3)
            "15 (1)" → (15, 1)
            "4 (9)" → (4, 9)
            "0 (0)" → (0, 0)
        """
        # Handle missing or malformed data
        if not apps_str or apps_str == "-":
            return (0, 0)

        # Use regex to extract numbers
        match = re.match(r'(\d+)\s*\((\d+)\)', apps_str)
        if match:
            starts = int(match.group(1))
            subs = int(match.group(2))
            return (starts, subs)

        # Fallback: try to parse as single number (just starts, no subs)
        try:
            return (int(apps_str), 0)
        except ValueError:
            return (0, 0)

    def _parse_wage(self, wage_str: str) -> float:
        """
        Parse wage string to float value.

        Args:
            wage_str: Wage string (e.g., "£29,000 p/w", "£15,000 p/w")

        Returns:
            Wage as float (e.g., 29000.0)

        Examples:
            "£29,000 p/w" → 29000.0
            "£15,000 p/w" → 15000.0
            "£750 p/w" → 750.0
        """
        if not wage_str or wage_str == "-":
            return 0.0

        # Remove currency symbol, commas, and " p/w"
        cleaned = wage_str.replace("£", "").replace(",", "").replace("p/w", "").strip()

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _parse_int(self, value_str: str) -> int:
        """
        Parse integer value, handling "-" as 0.

        Args:
            value_str: String value

        Returns:
            Integer value or 0 if invalid
        """
        if not value_str or value_str == "-":
            return 0

        try:
            return int(value_str)
        except ValueError:
            return 0

    def _parse_float(self, value_str: str) -> Optional[float]:
        """
        Parse float value, handling "-" as None.

        Args:
            value_str: String value

        Returns:
            Float value or None if invalid/missing
        """
        if not value_str or value_str == "-":
            return None

        # Handle percentage values (e.g., "66%" → 66.0)
        if "%" in value_str:
            value_str = value_str.replace("%", "")

        try:
            return float(value_str)
        except ValueError:
            return None


class FMParserError(Exception):
    """Exception raised for FM parsing errors."""
    pass
