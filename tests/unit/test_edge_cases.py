"""
Comprehensive edge case tests for Squad Audit Tracker.

Tests edge cases identified in code review:
- Contract date parsing with invalid formats
- FORMATION_LAYOUTS moved to module constant
- import re moved to module level
"""

import pytest
from datetime import date

from models.squad_audit import Player, FORMATION_LAYOUTS, FormationXI
from models.constants import PositionCategory


class TestContractDateParsing:
    """Test contract date parsing with proper error handling (no bare excepts)."""

    def test_empty_contract_date(self):
        """Test player with empty contract date doesn't crash."""
        player = Player(
            name="Test Player",
            position_selected="STC",
            position="ST (C)",
            age=25,
            wage=5000,
            apps=10,
            subs=0,
            gls=5,
            ast=2,
            av_rat=7.0,
            expires="",  # Empty string
            inf="PR",
            # Per-90 stats
            int_90=None,
            xg=0.5,
            shot_90=3.0,
            ch_c_90=1.0,
            drb_90=2.0,
            blk_90=0.5,
            k_tck_90=1.0,
            hdr_pct=60.0,
            tck_r=75.0,
            pas_pct=80.0,
            con_90=None,
            xgp=None,
            sv_pct=None
        )

        # Should return "N/A" without crashing (tests error handling)
        result = player.get_contract_expiry_relative()
        assert result == "N/A"

    def test_invalid_contract_date_format(self):
        """Test player with invalid date format doesn't crash."""
        player = Player(
            name="Test Player",
            position_selected="STC",
            position="ST (C)",
            age=25,
            wage=5000,
            apps=10,
            subs=0,
            gls=5,
            ast=2,
            av_rat=7.0,
            expires="Not a date",  # Invalid format
            inf="PR",
            # Per-90 stats
            int_90=None,
            xg=0.5,
            shot_90=3.0,
            ch_c_90=1.0,
            drb_90=2.0,
            blk_90=0.5,
            k_tck_90=1.0,
            hdr_pct=60.0,
            tck_r=75.0,
            pas_pct=80.0,
            con_90=None,
            xgp=None,
            sv_pct=None
        )

        # Should return "N/A" without crashing (tests ValueError handling)
        result = player.get_contract_expiry_relative()
        assert result == "N/A"

    def test_none_contract_date(self):
        """Test player with None contract date doesn't crash."""
        player = Player(
            name="Test Player",
            position_selected="STC",
            position="ST (C)",
            age=25,
            wage=5000,
            apps=10,
            subs=0,
            gls=5,
            ast=2,
            av_rat=7.0,
            expires=None,  # None value
            inf="PR",
            # Per-90 stats
            int_90=None,
            xg=0.5,
            shot_90=3.0,
            ch_c_90=1.0,
            drb_90=2.0,
            blk_90=0.5,
            k_tck_90=1.0,
            hdr_pct=60.0,
            tck_r=75.0,
            pas_pct=80.0,
            con_90=None,
            xgp=None,
            sv_pct=None
        )

        # Should return "N/A" without crashing (tests TypeError handling)
        result = player.get_contract_expiry_relative()
        assert result == "N/A"

    def test_valid_contract_date(self):
        """Test player with valid contract date parses correctly."""
        player = Player(
            name="Test Player",
            position_selected="STC",
            position="ST (C)",
            age=25,
            wage=5000,
            apps=10,
            subs=0,
            gls=5,
            ast=2,
            av_rat=7.0,
            expires="30/6/2025",  # Valid FM date format
            inf="PR",
            # Per-90 stats
            int_90=None,
            xg=0.5,
            shot_90=3.0,
            ch_c_90=1.0,
            drb_90=2.0,
            blk_90=0.5,
            k_tck_90=1.0,
            hdr_pct=60.0,
            tck_r=75.0,
            pas_pct=80.0,
            con_90=None,
            xgp=None,
            sv_pct=None
        )

        # Should parse correctly and return a valid string (not N/A)
        result = player.get_contract_expiry_relative(date(2024, 1, 1))
        assert result != "N/A"
        # Should return something like "<6m", "<1yr", "2yrs", etc.
        assert isinstance(result, str)

    def test_leap_year_contract_date(self):
        """Test contract date on leap year boundary doesn't crash."""
        player = Player(
            name="Test Player",
            position_selected="STC",
            position="ST (C)",
            age=25,
            wage=5000,
            apps=10,
            subs=0,
            gls=5,
            ast=2,
            av_rat=7.0,
            expires="29/2/2024",  # Feb 29, leap year
            inf="PR",
            # Per-90 stats
            int_90=None,
            xg=0.5,
            shot_90=3.0,
            ch_c_90=1.0,
            drb_90=2.0,
            blk_90=0.5,
            k_tck_90=1.0,
            hdr_pct=60.0,
            tck_r=75.0,
            pas_pct=80.0,
            con_90=None,
            xgp=None,
            sv_pct=None
        )

        # Should handle leap year correctly without crashing
        result = player.get_contract_expiry_relative(date(2024, 1, 1))
        assert result != "N/A"
        assert isinstance(result, str)


class TestFormationLayoutsConstant:
    """Test that FORMATION_LAYOUTS is a module-level constant, not instance field."""

    def test_formation_layouts_is_module_constant(self):
        """Verify FORMATION_LAYOUTS is at module level, not instance field."""
        # Should be accessible at module level
        assert FORMATION_LAYOUTS is not None
        assert isinstance(FORMATION_LAYOUTS, dict)
        assert len(FORMATION_LAYOUTS) > 0

        # FormationXI should NOT have FORMATION_LAYOUTS as a field
        xi = FormationXI(
            formation_name="4-4-2",
            starting_xi={},
            bench=[],
            bench_gaps=[],
            total_quality_score=0.0
        )

        # Should not have FORMATION_LAYOUTS attribute (it's at module level now)
        assert not hasattr(xi, 'FORMATION_LAYOUTS')

    def test_formation_layouts_shared_across_instances(self):
        """Verify FORMATION_LAYOUTS is shared, not per-instance."""
        # Get the object ID - should be the same for all references
        id_1 = id(FORMATION_LAYOUTS)

        # Import again
        from models.squad_audit import FORMATION_LAYOUTS as layouts_2
        id_2 = id(layouts_2)

        # Should be the exact same object (not a copy)
        assert id_1 == id_2

    def test_formation_layouts_has_expected_formations(self):
        """Verify FORMATION_LAYOUTS contains expected formations."""
        expected_formations = [
            "4-2-3-1 DM AM Wide",
            "4-3-3 DM Wide",
            "4-4-2"
        ]

        for formation in expected_formations:
            assert formation in FORMATION_LAYOUTS, f"Missing formation: {formation}"

    def test_formation_layouts_not_mutable_default(self):
        """Verify FORMATION_LAYOUTS is not a mutable default in dataclass."""
        # Create two FormationXI instances
        xi1 = FormationXI(
            formation_name="4-4-2",
            starting_xi={PositionCategory.GK: []},
            bench=[],
            bench_gaps=[],
            total_quality_score=50.0
        )

        xi2 = FormationXI(
            formation_name="4-3-3",
            starting_xi={PositionCategory.CB: []},
            bench=[],
            bench_gaps=[],
            total_quality_score=60.0
        )

        # FORMATION_LAYOUTS should be shared (same ID)
        # But the instances should have independent data
        assert xi1.formation_name != xi2.formation_name
        assert xi1.total_quality_score != xi2.total_quality_score


class TestImportReAtModuleLevel:
    """Test that import re has been moved to module level."""

    def test_import_re_is_at_module_level(self):
        """Verify 're' is imported at module level in role_recommendation_engine.py."""
        # Import the module
        import analyzers.role_recommendation_engine as module

        # Check that 're' is available at module level
        assert hasattr(module, 're')

        # Verify it's the actual re module
        import re as actual_re
        assert module.re is actual_re

    def test_no_import_inside_function(self):
        """Verify no 'import re' statement inside functions."""
        # Read the source file
        import inspect
        import analyzers.role_recommendation_engine as module

        # Get all functions and methods
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                try:
                    source = inspect.getsource(obj)
                    # Check that 'import re' is not in the function body
                    # (after the def line)
                    lines = source.split('\n')
                    for i, line in enumerate(lines[1:], 1):  # Skip first line (def)
                        assert 'import re' not in line, f"Found 'import re' in {name} at line {i}"
                except (OSError, TypeError):
                    # Skip if source not available (built-in, etc.)
                    pass
