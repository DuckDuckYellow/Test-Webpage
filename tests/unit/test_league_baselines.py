"""
Unit tests for league baseline generation and lookup.
"""

import pytest
from services.league_baseline_generator import LeagueBaselineGenerator
from models.league_baseline import LeagueWageBaseline, LeagueBaselineCollection
from models.constants import PositionCategory


class TestWageParsing:
    """Test wage string parsing with various formats."""

    def test_parse_basic_wage(self):
        """Test parsing standard UK wage format."""
        generator = LeagueBaselineGenerator()
        assert generator._parse_wage("£29,000 p/w") == 29000.0

    def test_parse_large_wage(self):
        """Test parsing large wage with multiple commas."""
        generator = LeagueBaselineGenerator()
        assert generator._parse_wage("£3,400,000 p/w") == 3400000.0

    def test_parse_small_wage(self):
        """Test parsing small wage without commas."""
        generator = LeagueBaselineGenerator()
        assert generator._parse_wage("£750 p/w") == 750.0

    def test_parse_euro_wage(self):
        """Test parsing euro currency."""
        generator = LeagueBaselineGenerator()
        assert generator._parse_wage("€50,000 p/w") == 50000.0

    def test_parse_dash(self):
        """Test parsing dash (no wage) returns 0."""
        generator = LeagueBaselineGenerator()
        assert generator._parse_wage("-") == 0.0

    def test_parse_empty_string(self):
        """Test parsing empty string returns 0."""
        generator = LeagueBaselineGenerator()
        assert generator._parse_wage("") == 0.0

    def test_parse_none(self):
        """Test parsing None returns 0."""
        generator = LeagueBaselineGenerator()
        assert generator._parse_wage(None) == 0.0


class TestPositionMapping:
    """Test FM position string mapping to PositionCategory."""

    def test_map_goalkeeper(self):
        """Test GK mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("GK") == PositionCategory.GK

    def test_map_center_back(self):
        """Test center back mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("D (C)") == PositionCategory.CB

    def test_map_fullback_right(self):
        """Test right fullback mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("D (R)") == PositionCategory.FB

    def test_map_fullback_left(self):
        """Test left fullback mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("D (L)") == PositionCategory.FB

    def test_map_wingback(self):
        """Test wingback mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("D/WB (R)") == PositionCategory.FB

    def test_map_defensive_midfielder(self):
        """Test defensive midfielder mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("DM") == PositionCategory.DM

    def test_map_central_midfielder(self):
        """Test central midfielder mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("M (C)") == PositionCategory.CM

    def test_map_attacking_midfielder(self):
        """Test attacking midfielder mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("AM (C)") == PositionCategory.AM

    def test_map_winger(self):
        """Test winger mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("W (R)") == PositionCategory.W

    def test_map_striker(self):
        """Test striker mapping."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("ST (C)") == PositionCategory.ST

    def test_map_invalid_position(self):
        """Test invalid position returns None."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("INVALID") is None

    def test_map_empty_position(self):
        """Test empty position returns None."""
        generator = LeagueBaselineGenerator()
        assert generator._map_position_to_category("") is None


class TestGKMultiplier:
    """Test GK wage multiplier calculation."""

    def test_gk_multiplier_calculation(self):
        """Test GK multiplier from top 5 leagues."""
        generator = LeagueBaselineGenerator()

        # Create test data with top 5 leagues
        player_data = [
            # Premier League GKs
            {'division': 'English Premier Division', 'position_category': PositionCategory.GK, 'wage': 100000.0},
            {'division': 'English Premier Division', 'position_category': PositionCategory.GK, 'wage': 80000.0},
            # Premier League outfield
            {'division': 'English Premier Division', 'position_category': PositionCategory.ST, 'wage': 150000.0},
            {'division': 'English Premier Division', 'position_category': PositionCategory.CM, 'wage': 120000.0},
            # La Liga GKs
            {'division': 'Spanish Primera División', 'position_category': PositionCategory.GK, 'wage': 90000.0},
            # La Liga outfield
            {'division': 'Spanish Primera División', 'position_category': PositionCategory.ST, 'wage': 130000.0},
        ]

        multiplier = generator.calculate_gk_multiplier(player_data)

        # GK avg = (100000 + 80000 + 90000) / 3 = 90000
        # Outfield avg = (150000 + 120000 + 130000) / 3 = 133333.33
        # Multiplier = 90000 / 133333.33 ≈ 0.675
        assert 0.6 < multiplier < 0.8

    def test_gk_multiplier_no_top5_leagues(self):
        """Test GK multiplier with no top 5 league data returns default."""
        generator = LeagueBaselineGenerator()

        player_data = [
            {'division': 'Other League', 'position_category': PositionCategory.GK, 'wage': 10000.0},
            {'division': 'Other League', 'position_category': PositionCategory.ST, 'wage': 15000.0},
        ]

        multiplier = generator.calculate_gk_multiplier(player_data)
        assert multiplier == 0.75  # Default fallback

    def test_gk_multiplier_no_gk_data(self):
        """Test GK multiplier with no GK data returns default."""
        generator = LeagueBaselineGenerator()

        player_data = [
            {'division': 'English Premier Division', 'position_category': PositionCategory.ST, 'wage': 150000.0},
        ]

        multiplier = generator.calculate_gk_multiplier(player_data)
        assert multiplier == 0.75  # Default fallback


class TestBaselineCollection:
    """Test LeagueBaselineCollection lookup and fallback logic."""

    def test_get_baseline_direct_lookup(self):
        """Test direct baseline lookup."""
        baseline = LeagueWageBaseline(
            division="English Premier Division",
            position="ST (C)",
            position_category=PositionCategory.ST,
            average_wage=125000.0,
            median_wage=85000.0,
            percentile_25=45000.0,
            percentile_75=180000.0,
            player_count=45,
            is_aggregated=False
        )

        collection = LeagueBaselineCollection(
            baselines=[baseline],
            gk_wage_multiplier=0.75,
            division_metadata={"English Premier Division": 523}
        )

        result = collection.get_baseline("English Premier Division", PositionCategory.ST)
        assert result == baseline

    def test_get_baseline_not_found(self):
        """Test baseline lookup when not found."""
        collection = LeagueBaselineCollection(
            baselines=[],
            gk_wage_multiplier=0.75,
            division_metadata={}
        )

        result = collection.get_baseline("English Premier Division", PositionCategory.ST)
        assert result is None

    def test_position_aggregation_fallback(self):
        """Test aggregation fallback for positions with <30 players."""
        # Create a specific FB baseline with <30 players
        fb_baseline = LeagueWageBaseline(
            division="Austrian First Division",
            position="D (R)",
            position_category=PositionCategory.FB,
            average_wage=10000.0,
            median_wage=8000.0,
            percentile_25=5000.0,
            percentile_75=12000.0,
            player_count=15,  # Less than 30
            is_aggregated=False
        )

        # Create aggregated Defenders baseline
        defenders_baseline = LeagueWageBaseline(
            division="Austrian First Division",
            position="Defenders",
            position_category=PositionCategory.CB,
            average_wage=12000.0,
            median_wage=10000.0,
            percentile_25=7000.0,
            percentile_75=15000.0,
            player_count=52,
            is_aggregated=True
        )

        collection = LeagueBaselineCollection(
            baselines=[fb_baseline, defenders_baseline],
            gk_wage_multiplier=0.75,
            division_metadata={"Austrian First Division": 87}
        )

        # Should return aggregated baseline because FB has <30 players
        result = collection.get_baseline_with_aggregation(
            "Austrian First Division",
            PositionCategory.FB
        )
        assert result == defenders_baseline

    def test_gk_estimation_fallback(self):
        """Test GK estimation when no GK baseline exists."""
        # Create outfield baselines
        st_baseline = LeagueWageBaseline(
            division="Test Division",
            position="ST (C)",
            position_category=PositionCategory.ST,
            average_wage=50000.0,
            median_wage=40000.0,
            percentile_25=25000.0,
            percentile_75=60000.0,
            player_count=35,
            is_aggregated=False
        )

        cm_baseline = LeagueWageBaseline(
            division="Test Division",
            position="M (C)",
            position_category=PositionCategory.CM,
            average_wage=40000.0,
            median_wage=35000.0,
            percentile_25=20000.0,
            percentile_75=50000.0,
            player_count=40,
            is_aggregated=False
        )

        collection = LeagueBaselineCollection(
            baselines=[st_baseline, cm_baseline],
            gk_wage_multiplier=0.75,
            division_metadata={"Test Division": 150}
        )

        # Should estimate GK wage
        result = collection.get_baseline_with_gk_estimation(
            "Test Division",
            PositionCategory.GK
        )

        assert result is not None
        assert result.position_category == PositionCategory.GK
        assert result.player_count == 0  # Indicates estimated
        # GK avg should be ~0.75 * ((50000 + 40000) / 2) = 33750
        assert 30000 < result.average_wage < 40000

    def test_low_sample_size_detection(self):
        """Test low sample size detection."""
        collection = LeagueBaselineCollection(
            baselines=[],
            gk_wage_multiplier=0.75,
            division_metadata={
                "Large League": 250,
                "Small League": 75
            }
        )

        assert not collection.is_low_sample_size("Large League")
        assert collection.is_low_sample_size("Small League")

    def test_get_available_divisions(self):
        """Test getting available divisions list."""
        baseline1 = LeagueWageBaseline(
            division="English Premier Division",
            position="ST (C)",
            position_category=PositionCategory.ST,
            average_wage=125000.0,
            median_wage=85000.0,
            percentile_25=45000.0,
            percentile_75=180000.0,
            player_count=45,
            is_aggregated=False
        )

        baseline2 = LeagueWageBaseline(
            division="Austrian First Division",
            position="ST (C)",
            position_category=PositionCategory.ST,
            average_wage=15000.0,
            median_wage=12000.0,
            percentile_25=8000.0,
            percentile_75=20000.0,
            player_count=25,
            is_aggregated=False
        )

        collection = LeagueBaselineCollection(
            baselines=[baseline1, baseline2],
            gk_wage_multiplier=0.75,
            division_metadata={}
        )

        divisions = collection.get_available_divisions()
        assert len(divisions) == 2
        assert "English Premier Division" in divisions
        assert "Austrian First Division" in divisions


class TestJSONSerialization:
    """Test JSON export and import."""

    def test_export_and_load_json(self, tmp_path):
        """Test exporting and loading baselines from JSON."""
        baseline = LeagueWageBaseline(
            division="Test Division",
            position="ST (C)",
            position_category=PositionCategory.ST,
            average_wage=50000.0,
            median_wage=40000.0,
            percentile_25=25000.0,
            percentile_75=60000.0,
            player_count=35,
            is_aggregated=False
        )

        collection = LeagueBaselineCollection(
            baselines=[baseline],
            gk_wage_multiplier=0.677,
            division_metadata={"Test Division": 150}
        )

        # Export to temp file
        json_path = tmp_path / "test_baselines.json"
        generator = LeagueBaselineGenerator()
        generator.export_to_json(collection, str(json_path))

        # Load from file
        loaded_collection = generator.load_from_json(str(json_path))

        assert len(loaded_collection.baselines) == 1
        assert loaded_collection.gk_wage_multiplier == 0.677
        assert loaded_collection.baselines[0].division == "Test Division"
        assert loaded_collection.baselines[0].average_wage == 50000.0
        assert loaded_collection.baselines[0].is_aggregated is False
        assert loaded_collection.division_metadata["Test Division"] == 150
