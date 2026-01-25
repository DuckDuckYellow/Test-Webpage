"""
Unit tests for FM HTML Parser Service

Tests the parsing of Football Manager HTML squad exports.
"""

import pytest
from services.fm_parser import FMHTMLParser, FMParserError
from models import Squad


class TestFMHTMLParser:
    """Test suite for FMHTMLParser."""

    def test_parser_initialization(self, fm_parser):
        """Test that parser initializes correctly."""
        assert fm_parser is not None
        assert isinstance(fm_parser, FMHTMLParser)

    def test_parse_appearances_standard_format(self, fm_parser):
        """Test parsing standard appearances format."""
        # Test "13 (3)" format
        starts, subs = fm_parser._parse_appearances("13 (3)")
        assert starts == 13
        assert subs == 3

        # Test "4 (9)" format
        starts, subs = fm_parser._parse_appearances("4 (9)")
        assert starts == 4
        assert subs == 9

    def test_parse_appearances_zero_format(self, fm_parser):
        """Test parsing zero appearances."""
        starts, subs = fm_parser._parse_appearances("0 (0)")
        assert starts == 0
        assert subs == 0

    def test_parse_appearances_missing_data(self, fm_parser):
        """Test parsing missing appearances data."""
        starts, subs = fm_parser._parse_appearances("-")
        assert starts == 0
        assert subs == 0

        starts, subs = fm_parser._parse_appearances("")
        assert starts == 0
        assert subs == 0

    def test_parse_wage_standard_format(self, fm_parser):
        """Test parsing standard wage format."""
        # Test "£29,000 p/w"
        wage = fm_parser._parse_wage("£29,000 p/w")
        assert wage == 29000.0

        # Test "£15,000 p/w"
        wage = fm_parser._parse_wage("£15,000 p/w")
        assert wage == 15000.0

    def test_parse_wage_small_amount(self, fm_parser):
        """Test parsing small wage amounts."""
        wage = fm_parser._parse_wage("£750 p/w")
        assert wage == 750.0

    def test_parse_wage_large_amount(self, fm_parser):
        """Test parsing large wage amounts."""
        wage = fm_parser._parse_wage("£125,000 p/w")
        assert wage == 125000.0

    def test_parse_wage_missing_data(self, fm_parser):
        """Test parsing missing wage data."""
        wage = fm_parser._parse_wage("-")
        assert wage == 0.0

        wage = fm_parser._parse_wage("")
        assert wage == 0.0

    def test_parse_int_standard(self, fm_parser):
        """Test parsing standard integer values."""
        assert fm_parser._parse_int("5") == 5
        assert fm_parser._parse_int("0") == 0
        assert fm_parser._parse_int("100") == 100

    def test_parse_int_missing_data(self, fm_parser):
        """Test parsing missing integer data."""
        assert fm_parser._parse_int("-") == 0
        assert fm_parser._parse_int("") == 0

    def test_parse_int_invalid_data(self, fm_parser):
        """Test parsing invalid integer data."""
        assert fm_parser._parse_int("invalid") == 0
        assert fm_parser._parse_int("12.5") == 0

    def test_parse_float_standard(self, fm_parser):
        """Test parsing standard float values."""
        assert fm_parser._parse_float("7.25") == 7.25
        assert fm_parser._parse_float("0.5") == 0.5
        assert fm_parser._parse_float("100.0") == 100.0

    def test_parse_float_percentage(self, fm_parser):
        """Test parsing percentage values."""
        assert fm_parser._parse_float("66%") == 66.0
        assert fm_parser._parse_float("95%") == 95.0

    def test_parse_float_missing_data(self, fm_parser):
        """Test parsing missing float data."""
        assert fm_parser._parse_float("-") is None
        assert fm_parser._parse_float("") is None

    def test_parse_float_invalid_data(self, fm_parser):
        """Test parsing invalid float data."""
        assert fm_parser._parse_float("invalid") is None

    def test_clean_cell_text(self, fm_parser):
        """Test cell text cleaning."""
        assert fm_parser._clean_cell_text("  test  ") == "test"
        assert fm_parser._clean_cell_text("test") == "test"
        assert fm_parser._clean_cell_text("\n  test  \n") == "test"

    def test_parse_html_missing_table(self, fm_parser):
        """Test parsing HTML without table."""
        html = "<html><body><p>No table here</p></body></html>"

        with pytest.raises(ValueError, match="No table found"):
            fm_parser.parse_html(html)

    def test_parse_html_empty_table(self, fm_parser):
        """Test parsing HTML with empty table."""
        html = """
        <html>
            <body>
                <table>
                    <tr><th>Header</th></tr>
                </table>
            </body>
        </html>
        """

        with pytest.raises(ValueError, match="No player data rows found"):
            fm_parser.parse_html(html)

    def test_parse_html_valid_single_player(self, fm_parser):
        """Test parsing HTML with single valid player."""
        html = """
        <html>
            <body>
                <table>
                    <tr><th>Headers</th></tr>
                    <tr>
                        <td>GK</td>
                        <td></td>
                        <td>Alban Lafont</td>
                        <td>GK</td>
                        <td>18 (0)</td>
                        <td>0</td>
                        <td>0</td>
                        <td>6.84</td>
                        <td>£29,000 p/w</td>
                        <td>29</td>
                        <td>30/6/2032</td>
                        <td>0.11</td>
                        <td>0.00</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>0.06</td>
                        <td>-</td>
                        <td>-</td>
                        <td>95%</td>
                        <td>1.50</td>
                        <td>-6.33</td>
                        <td>56%</td>
                    </tr>
                </table>
            </body>
        </html>
        """

        squad = fm_parser.parse_html(html)

        assert isinstance(squad, Squad)
        assert len(squad.players) == 1

        player = squad.players[0]
        assert player.name == "Alban Lafont"
        assert player.position_selected == "GK"
        assert player.age == 29
        assert player.wage == 29000.0
        assert player.apps == 18
        assert player.subs == 0
        assert player.av_rat == 6.84
        assert player.sv_pct == 56.0
        assert player.pas_pct == 95.0

    def test_parse_html_valid_multiple_players(self, fm_parser):
        """Test parsing HTML with multiple valid players."""
        html = """
        <html>
            <body>
                <table>
                    <tr><th>Headers</th></tr>
                    <tr>
                        <td>GK</td><td></td><td>Player 1</td><td>GK</td>
                        <td>10 (0)</td><td>0</td><td>0</td><td>7.0</td>
                        <td>£30,000 p/w</td><td>25</td><td>30/6/2030</td>
                        <td>0.5</td><td>0.0</td><td>-</td><td>-</td>
                        <td>-</td><td>-</td><td>0.1</td><td>-</td>
                        <td>-</td><td>90%</td><td>1.0</td><td>2.5</td><td>70%</td>
                    </tr>
                    <tr>
                        <td>ST</td><td>PR</td><td>Player 2</td><td>ST (C)</td>
                        <td>5 (3)</td><td>3</td><td>1</td><td>7.5</td>
                        <td>£40,000 p/w</td><td>22</td><td>30/6/2031</td>
                        <td>1.0</td><td>3.5</td><td>2.0</td><td>0.5</td>
                        <td>1.5</td><td>0.2</td><td>0.0</td><td>75%</td>
                        <td>85%</td><td>88%</td><td>-</td><td>-</td><td>-</td>
                    </tr>
                </table>
            </body>
        </html>
        """

        squad = fm_parser.parse_html(html)

        assert len(squad.players) == 2

        # Verify first player (GK)
        player1 = squad.players[0]
        assert player1.name == "Player 1"
        assert player1.position_selected == "GK"
        assert player1.apps == 10

        # Verify second player (ST)
        player2 = squad.players[1]
        assert player2.name == "Player 2"
        assert player2.position_selected == "ST"
        assert player2.apps == 5
        assert player2.subs == 3
        assert player2.gls == 3
        assert player2.inf == "PR"

    def test_parse_html_with_various_status_flags(self, fm_parser):
        """Test parsing HTML with different status flags."""
        html = """
        <html>
            <body>
                <table>
                    <tr><th>Headers</th></tr>
                    <tr>
                        <td>DR</td><td>Yel</td><td>Player 1</td><td>D/WB (R)</td>
                        <td>10 (2)</td><td>1</td><td>2</td><td>7.0</td>
                        <td>£25,000 p/w</td><td>24</td><td>30/6/2030</td>
                        <td>2.5</td><td>0.5</td><td>0.8</td><td>0.4</td>
                        <td>1.2</td><td>0.6</td><td>0.15</td><td>70%</td>
                        <td>85%</td><td>87%</td><td>-</td><td>-</td><td>-</td>
                    </tr>
                    <tr>
                        <td>AM</td><td>Inj</td><td>Player 2</td><td>AM (RL)</td>
                        <td>5 (1)</td><td>2</td><td>3</td><td>7.8</td>
                        <td>£35,000 p/w</td><td>23</td><td>30/6/2031</td>
                        <td>1.0</td><td>1.5</td><td>1.2</td><td>2.5</td>
                        <td>3.0</td><td>0.1</td><td>0.0</td><td>-</td>
                        <td>-</td><td>89%</td><td>-</td><td>-</td><td>-</td>
                    </tr>
                </table>
            </body>
        </html>
        """

        squad = fm_parser.parse_html(html)

        assert len(squad.players) == 2

        # Verify status flags
        assert squad.players[0].inf == "Yel"
        assert squad.players[1].inf == "Inj"

    def test_parse_player_row_insufficient_columns(self, fm_parser):
        """Test parsing row with insufficient columns."""
        from bs4 import BeautifulSoup

        html = "<tr><td>Only</td><td>Few</td><td>Columns</td></tr>"
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')

        player = fm_parser._parse_player_row(row)
        assert player is None

    def test_parser_handles_special_characters(self, fm_parser):
        """Test parser handles special characters in names."""
        html = """
        <html>
            <body>
                <table>
                    <tr><th>Headers</th></tr>
                    <tr>
                        <td>ST</td><td></td><td>Damián Pizarro</td><td>ST (C)</td>
                        <td>10 (2)</td><td>5</td><td>2</td><td>7.5</td>
                        <td>£50,000 p/w</td><td>23</td><td>30/6/2030</td>
                        <td>1.0</td><td>5.0</td><td>3.0</td><td>0.5</td>
                        <td>2.0</td><td>0.1</td><td>0.0</td><td>80%</td>
                        <td>90%</td><td>85%</td><td>-</td><td>-</td><td>-</td>
                    </tr>
                </table>
            </body>
        </html>
        """

        squad = fm_parser.parse_html(html)
        assert len(squad.players) == 1
        assert squad.players[0].name == "Damián Pizarro"


class TestFMParserIntegration:
    """Integration tests for full parsing workflow."""

    def test_parse_and_analyze_workflow(self, fm_parser, squad_audit_service):
        """Test complete workflow: parse HTML → analyze squad."""
        html = """
        <html>
            <body>
                <table>
                    <tr><th>Headers</th></tr>
                    <tr>
                        <td>GK</td><td></td><td>Test GK</td><td>GK</td>
                        <td>15 (0)</td><td>0</td><td>0</td><td>7.0</td>
                        <td>£30,000 p/w</td><td>28</td><td>30/6/2030</td>
                        <td>0.5</td><td>0.0</td><td>-</td><td>-</td>
                        <td>-</td><td>-</td><td>0.1</td><td>-</td>
                        <td>-</td><td>92%</td><td>1.2</td><td>3.0</td><td>68%</td>
                    </tr>
                    <tr>
                        <td>ST</td><td></td><td>Test ST</td><td>ST (C)</td>
                        <td>12 (3)</td><td>8</td><td>3</td><td>7.5</td>
                        <td>£45,000 p/w</td><td>25</td><td>30/6/2031</td>
                        <td>1.2</td><td>6.0</td><td>3.5</td><td>0.8</td>
                        <td>2.0</td><td>0.2</td><td>0.05</td><td>78%</td>
                        <td>88%</td><td>86%</td><td>-</td><td>-</td><td>-</td>
                    </tr>
                </table>
            </body>
        </html>
        """

        # Parse HTML
        squad = fm_parser.parse_html(html)
        assert len(squad.players) == 2

        # Analyze squad
        result = squad_audit_service.analyze_squad(squad)
        assert result.total_players == 2
        assert len(result.player_analyses) == 2

        # Verify analysis completed successfully
        for analysis in result.player_analyses:
            assert analysis.performance_index > 0
            assert analysis.value_score > 0
            assert analysis.recommendation is not None
            assert len(analysis.recommendation.badge) > 0
