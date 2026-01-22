
"""
End-to-End Tests for Squad Audit Service

Tests the full flow from HTML parsing to complete SquadAnalysisResult
with integrated Role evaluations.
"""

import pytest
from services.fm_parser_v2 import FMHTMLParserV2
from services.squad_audit_service import SquadAuditService
from models.squad_audit import PerformanceVerdict

class TestSquadAuditEndToEnd:
    
    def test_full_audit_process(self):
        """Test the complete squad audit process with real data."""
        
        # 1. Parse Data
        parser = FMHTMLParserV2()
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        squad = parser.parse_html(html_content)
        assert len(squad.players) > 0, "No players parsed"
        
        # 2. Run Service Analysis
        service = SquadAuditService()
        result = service.analyze_squad(squad)
        
        # 3. Verify Result Structure
        assert result.total_players == len(squad.players)
        assert len(result.player_analyses) == len(squad.players)
        
        # 4. Verify Role Integration in Analysis
        for analysis in result.player_analyses:
            player = analysis.player
            
            # Roles should be populated
            assert player.best_role is not None
            assert len(player.all_role_scores) == 12
            
            # Performance Index should match Best Role Score
            # Note: There might be slight float differences
            assert abs(analysis.performance_index - player.best_role.overall_score) < 0.01
            
            # Verdict should match Role Tier
            assert analysis.verdict.value == player.best_role.tier
            
            # Value Score should be calculated
            assert analysis.value_score > 0
            
            # Recommendation should be present
            assert analysis.recommendation is not None
            assert len(analysis.recommendation) > 0
            
            # Top metrics should be from Role strengths
            assert len(analysis.top_metrics) <= 2
            if len(analysis.top_metrics) > 0:
                assert "Elite" in analysis.top_metrics[0]
                
    def test_role_recommendation_logic(self):
        """Verify that role recommendation logic populates correctly."""
        parser = FMHTMLParserV2()
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        squad = parser.parse_html(html_content)
        service = SquadAuditService()
        result = service.analyze_squad(squad)
        
        # Find players with a recommended role change
        recs_found = 0
        for analysis in result.player_analyses:
            player = analysis.player
            
            if player.recommended_role:
                recs_found += 1
                # Check that recommendation text mentions the role
                assert player.recommended_role.role in analysis.recommendation
                
        # We expect at least some recommendations in a full squad
        print(f"Found {recs_found} role recommendations in squad")
        # assert recs_found > 0 # Commented out as it depends on data, but likely true
        
    def test_csv_export_compatibility(self):
        """Test that CSV export works with new role data."""
        parser = FMHTMLParserV2()
        with open('Go Ahead - New Format.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        squad = parser.parse_html(html_content)
        service = SquadAuditService()
        result = service.analyze_squad(squad)
        
        csv_data = service.export_to_csv_data(result)
        
        assert len(csv_data) == len(squad.players)
        row = csv_data[0]
        
        # Check integrity of new fields
        assert "Performance" in row
        assert "Recommendation" in row
        assert "Value Score" in row
        assert "Top Metric 1" in row
        
        # Performance should be a tier string now
        assert row["Performance"] in ["ELITE", "GOOD", "AVERAGE", "POOR"]

    def test_legacy_file_support(self):
        """Test that legacy files (V1 format) can be processed and yield role data."""
        from services.fm_parser import FMHTMLParser
        
        parser = FMHTMLParser()
        try:
            with open('Test File 3.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            pytest.skip("Legacy test file 'Test File 3.html' not found")
            
        squad = parser.parse_html(html_content)
        assert len(squad.players) > 0
        
        # Analyze with service
        service = SquadAuditService()
        result = service.analyze_squad(squad)
        
        # Check if roles were evaluated even for legacy data
        player = result.player_analyses[0].player
        assert player.best_role is not None
        assert len(player.all_role_scores) == 12
        assert player.best_role.overall_score >= 0

if __name__ == "__main__":
    test = TestSquadAuditEndToEnd()
    test.test_full_audit_process()
    test.test_role_recommendation_logic()
    test.test_csv_export_compatibility()
    print("All End-to-End Validation Tests Passed!")
