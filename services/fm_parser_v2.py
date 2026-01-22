"""
Football Manager HTML Parser V2 - New Format (2026+)

This parser handles the new FM export format with 32 columns including:
- Player information (Age, Wage, Contract)
- Comprehensive per-90 metrics
- Enhanced statistics for role evaluation

Format: 32 columns with Age/Wage/Contract at positions 4-6
"""

import re
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup
from models.squad_audit import Player, Squad


class FMHTMLParserV2:
    """Parser for Football Manager HTML squad exports (2026+ format)."""

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse_html(self, html_content: str) -> Squad:
        """
        Parse FM HTML export (new format) and return a Squad object.

        Args:
            html_content: Raw HTML content from FM export

        Returns:
            Squad object containing all parsed players

        Raises:
            ValueError: If HTML structure is invalid or required data is missing
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the main table
        table = soup.find('table')
        if not table:
            raise ValueError("No table found in HTML content")

        # Get headers to verify format
        headers = [th.get_text().strip() for th in table.find_all('th')]
        if len(headers) != 32:
            raise ValueError(f"Expected 32 columns in new format, found {len(headers)}")

        # Verify critical columns are present
        if 'Age' not in headers or 'Wage' not in headers or 'Expires' not in headers:
            raise ValueError("Missing critical columns (Age, Wage, Expires) in new format")

        # Get all rows (skip header row)
        rows = table.find_all('tr')[1:]
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

        New format (32 columns):
        0: Position Selected
        1: Inf
        2: Name
        3: Position
        4: Expires
        5: Wage
        6: Age
        7: Apps
        8: Gls
        9: Mins
        10: Ast
        11: Av Rat
        12: xGP/90
        13: Con/90
        14: Tck/90
        15: ShT/90
        16: Hdrs W/90
        17: Sprints/90
        18: xA/90
        19: NP-xG/90
        20: OP-KP/90
        21: Drb/90
        22: Conv %
        23: Pr passes/90
        24: Clr/90
        25: Pres C/90
        26: OP-Crs C/90
        27: Itc
        28: Shts Blckd/90
        29: Hdr %
        30: Pas %
        31: Int/90

        Args:
            row: BeautifulSoup table row element

        Returns:
            Player object or None if parsing fails
        """
        cells = row.find_all('td')
        if len(cells) < 32:
            return None

        # Extract text from each cell
        data = [self._clean_cell_text(cell.get_text()) for cell in cells]

        # Parse appearances (format: "13 (3)" = 13 starts, 3 subs)
        apps, subs = self._parse_appearances(data[7])

        # Parse wage (format: "£29,000 p/w" → 29000.0)
        wage = self._parse_wage(data[5])

        # Parse age
        age = self._parse_int(data[6])

        # Parse minutes
        mins = self._parse_int(data[9])

        # Create Player object with new format fields
        player = Player(
            name=data[2],
            position_selected=data[0],
            position=data[3],
            age=age,
            wage=wage,
            apps=apps,
            subs=subs,
            gls=self._parse_int(data[8]),
            ast=self._parse_int(data[10]),
            av_rat=self._parse_float(data[11]),
            expires=data[4],
            inf=data[1],
            mins=mins,
            # Per-90 statistics (new format)
            xgp_90=self._parse_float(data[12]),
            con_90=self._parse_float(data[13]),
            tck_90=self._parse_float(data[14]),
            sht_90=self._parse_float(data[15]),
            hdrs_w_90=self._parse_float(data[16]),
            sprints_90=self._parse_float(data[17]),
            xa_90=self._parse_float(data[18]),
            np_xg_90=self._parse_float(data[19]),
            op_kp_90=self._parse_float(data[20]),
            drb_90=self._parse_float(data[21]),
            conv_pct=self._parse_float(data[22]),
            pr_passes_90=self._parse_float(data[23]),
            clr_90=self._parse_float(data[24]),
            pres_c_90=self._parse_float(data[25]),
            op_crs_c_90=self._parse_float(data[26]),
            itc=self._parse_int(data[27]),
            shts_blckd_90=self._parse_float(data[28]),
            hdr_pct=self._parse_float(data[29]),
            pas_pct=self._parse_float(data[30]),
            int_90=self._parse_float(data[31])
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
        """
        if not apps_str or apps_str == "-":
            return (0, 0)

        # Use regex to extract numbers
        match = re.match(r'(\d+)\s*\((\d+)\)', apps_str)
        if match:
            starts = int(match.group(1))
            subs = int(match.group(2))
            return (starts, subs)

        # Fallback: try to parse as single number
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
        """
        if not wage_str or wage_str == "-":
            return 0.0

        # Remove currency symbol, commas, and "p/w"
        cleaned = wage_str.replace('£', '').replace(',', '').replace(' p/w', '').strip()

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _parse_int(self, value: str) -> int:
        """
        Parse string to integer, handling missing/invalid values.

        Args:
            value: String value

        Returns:
            Integer or 0 if parsing fails
        """
        if not value or value == "-":
            return 0

        # Remove commas for large numbers
        cleaned = value.replace(',', '').strip()

        try:
            return int(cleaned)
        except ValueError:
            return 0

    def _parse_float(self, value: str) -> float:
        """
        Parse string to float, handling missing/invalid values and percentages.

        Args:
            value: String value (may include %)

        Returns:
            Float or 0.0 if parsing fails
        """
        if not value or value == "-":
            return 0.0

        # Remove % symbol if present
        cleaned = value.replace('%', '').replace(',', '').strip()

        try:
            return float(cleaned)
        except ValueError:
            return 0.0
