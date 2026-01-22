"""
End-to-End Tests for Squad Audit Service - Refactored.
"""

import pytest
from services.fm_parser_v2 import FMHTMLParserV2
from services.squad_audit_service import SquadAuditService


class TestSquadAuditEndToEnd:

    @pytest.fixture
    def parser(self):
        return FMHTMLParserV2()

    @pytest.fixture
    def service(self):
        return SquadAuditService()

    @pytest.fixture
    def html_content(self):
        with open('tests/fixtures/Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            return f.read()

    def test_full_audit_process(self, parser, service, html_content):
        """Test the complete squad audit process."""
        squad = parser.parse_html(html_content)
        result = service.analyze_squad(squad)

        assert result.total_players == len(squad.players)
        assert len(result.player_analyses) == len(squad.players)

        for analysis in result.player_analyses:
            player = analysis.player
            assert player.best_role is not None
            assert analysis.value_score >= 0
            assert analysis.recommendation is not None

    def test_csv_export_compatibility(self, parser, service, html_content):
        """Test CSV export."""
        squad = parser.parse_html(html_content)
        result = service.analyze_squad(squad)
        csv_data = service.export_to_csv_data(result)

        assert len(csv_data) == len(squad.players)
        row = csv_data[0]
        assert "Performance" in row
        assert "Recommendation" in row
        assert "Value Score" in row
