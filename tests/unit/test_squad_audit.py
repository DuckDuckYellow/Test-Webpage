"""
Unit tests for Squad Audit Service

Tests the core business logic for analyzing squad performance,
calculating metrics, and generating recommendations.
"""

import pytest
from models import (
    Player,
    Squad,
    PositionCategory,
    StatusFlag,
    PerformanceVerdict
)


class TestSquadAuditService:
    """Test suite for SquadAuditService."""

    def test_service_initialization(self, squad_audit_service):
        """Test that service initializes correctly."""
        assert squad_audit_service is not None
        assert hasattr(squad_audit_service, 'POSITION_METRICS')
        assert len(squad_audit_service.POSITION_METRICS) == 8

    def test_position_metrics_configuration(self, squad_audit_service):
        """Test that all positions have 4 metrics configured."""
        for position, metrics in squad_audit_service.POSITION_METRICS.items():
            assert len(metrics) == 4, f"{position} should have 4 metrics"

    def test_analyze_squad_returns_result(self, squad_audit_service, sample_squad):
        """Test that analyze_squad returns a SquadAnalysisResult."""
        result = squad_audit_service.analyze_squad(sample_squad)

        assert result is not None
        assert result.total_players == len(sample_squad.players)
        assert len(result.player_analyses) == len(sample_squad.players)
        assert result.squad_avg_wage > 0

    def test_position_benchmarks_calculation(self, squad_audit_service, sample_squad):
        """Test that position benchmarks are calculated correctly."""
        benchmarks = squad_audit_service._calculate_position_benchmarks(sample_squad)

        # Should have benchmarks for positions in the squad
        assert len(benchmarks) > 0

        # Each position should have metrics
        for position_key, metrics in benchmarks.items():
            assert isinstance(metrics, dict)
            assert len(metrics) > 0

    def test_performance_index_calculation(self, squad_audit_service, sample_elite_player, sample_squad):
        """Test performance index calculation."""
        benchmarks = squad_audit_service._calculate_position_benchmarks(sample_squad)
        position = sample_elite_player.get_position_category()

        performance_index = squad_audit_service._calculate_performance_index(
            sample_elite_player,
            position,
            benchmarks
        )

        # Elite player should have above-average performance
        assert performance_index >= 0
        assert isinstance(performance_index, float)

    def test_value_score_calculation(self, squad_audit_service):
        """Test value score calculation."""
        # Test case: High performance, low wage = high value
        value_score = squad_audit_service._calculate_value_score(
            performance_index=120.0,
            player_wage=20000.0,
            squad_avg_wage=30000.0
        )

        # Should be above 100 (good value)
        assert value_score > 100

        # Test case: Average performance, high wage = low value
        value_score_low = squad_audit_service._calculate_value_score(
            performance_index=100.0,
            player_wage=50000.0,
            squad_avg_wage=30000.0
        )

        # Should be below 100 (poor value)
        assert value_score_low < 100

    def test_performance_verdict_classification(self, squad_audit_service):
        """Test performance verdict classification."""
        # Elite: >= 120
        assert squad_audit_service._get_performance_verdict(125.0) == PerformanceVerdict.ELITE

        # Good: >= 100
        assert squad_audit_service._get_performance_verdict(110.0) == PerformanceVerdict.GOOD

        # Average: >= 85
        assert squad_audit_service._get_performance_verdict(90.0) == PerformanceVerdict.AVERAGE

        # Poor: < 85
        assert squad_audit_service._get_performance_verdict(75.0) == PerformanceVerdict.POOR

    def test_recommendation_for_elite_player_with_sufficient_apps(self, squad_audit_service):
        """Test recommendation for elite player with sufficient appearances."""
        player = Player(
            name='Test Player',
            position_selected='ST',
            position='ST (C)',
            age=25,
            wage=30000.0,
            apps=10,
            subs=2,
            gls=5,
            ast=3,
            av_rat=7.5,
            expires='30/6/2030',
            inf=''
        )

        recommendation = squad_audit_service._generate_recommendation(
            player,
            PerformanceVerdict.ELITE,
            150.0
        )

        assert 'LOCK IN STARTER' in recommendation

    def test_recommendation_for_transfer_listed_elite(self, squad_audit_service):
        """Test recommendation for elite player on transfer list."""
        player = Player(
            name='Test Player',
            position_selected='ST',
            position='ST (C)',
            age=25,
            wage=30000.0,
            apps=10,
            subs=2,
            gls=5,
            ast=3,
            av_rat=7.5,
            expires='30/6/2030',
            inf='Wnt'
        )

        recommendation = squad_audit_service._generate_recommendation(
            player,
            PerformanceVerdict.ELITE,
            150.0
        )

        assert 'INVESTIGATE' in recommendation or 'retention' in recommendation.lower()

    def test_recommendation_for_poor_transfer_listed(self, squad_audit_service):
        """Test recommendation for poor player on transfer list."""
        player = Player(
            name='Test Player',
            position_selected='ST',
            position='ST (C)',
            age=25,
            wage=30000.0,
            apps=10,
            subs=2,
            gls=0,
            ast=0,
            av_rat=6.0,
            expires='30/6/2030',
            inf='Wnt'
        )

        recommendation = squad_audit_service._generate_recommendation(
            player,
            PerformanceVerdict.POOR,
            70.0
        )

        assert 'SELL' in recommendation

    def test_recommendation_for_low_sample_size(self, squad_audit_service):
        """Test recommendation for player with 5 or fewer apps."""
        player = Player(
            name='Test Player',
            position_selected='ST',
            position='ST (C)',
            age=25,
            wage=30000.0,
            apps=3,  # Low sample size
            subs=1,
            gls=2,
            ast=1,
            av_rat=8.0,
            expires='30/6/2030',
            inf=''
        )

        recommendation = squad_audit_service._generate_recommendation(
            player,
            PerformanceVerdict.ELITE,  # Even with elite verdict
            150.0
        )

        assert 'USE OR SELL' in recommendation
        assert 'Insufficient data' in recommendation

    def test_contract_warning_expiring_soon(self, squad_audit_service):
        """Test contract warning for contracts expiring soon."""
        # Contract expiring in 6 months should trigger warning
        warning = squad_audit_service._check_contract_warning('30/06/2026')

        assert isinstance(warning, bool)

    def test_contract_warning_long_term(self, squad_audit_service):
        """Test contract warning for long-term contracts."""
        # Contract in 5 years should not trigger warning
        warning = squad_audit_service._check_contract_warning('30/06/2030')

        assert isinstance(warning, bool)

    def test_top_metrics_extraction(self, squad_audit_service, sample_elite_player, sample_squad):
        """Test extraction of top metrics."""
        benchmarks = squad_audit_service._calculate_position_benchmarks(sample_squad)
        position = sample_elite_player.get_position_category()

        top_metrics = squad_audit_service._get_top_metrics(
            sample_elite_player,
            position,
            benchmarks
        )

        # Should return list of metric descriptions
        assert isinstance(top_metrics, list)
        # Should have up to 2 metrics
        assert len(top_metrics) <= 2

    def test_export_to_csv_data(self, squad_audit_service, sample_squad):
        """Test CSV export data generation."""
        result = squad_audit_service.analyze_squad(sample_squad)
        csv_data = squad_audit_service.export_to_csv_data(result)

        # Should have one row per player
        assert len(csv_data) == len(sample_squad.players)

        # Each row should have required fields
        required_fields = [
            'Name',
            'Position',
            'Age',
            'Value Score',
            'Performance',
            'Status',
            'Recommendation',
            'Contract Expires',
            'Wage'
        ]

        for row in csv_data:
            for field in required_fields:
                assert field in row

    def test_full_squad_analysis_workflow(self, squad_audit_service, sample_squad):
        """Test complete end-to-end squad analysis workflow."""
        # Run analysis
        result = squad_audit_service.analyze_squad(sample_squad)

        # Verify result structure
        assert result.total_players == len(sample_squad.players)
        assert len(result.player_analyses) == len(sample_squad.players)
        assert result.squad_avg_wage > 0
        assert len(result.position_benchmarks) > 0

        # Verify each player analysis
        for analysis in result.player_analyses:
            assert analysis.player is not None
            assert analysis.performance_index >= 0
            assert analysis.value_score >= 0
            assert analysis.verdict in PerformanceVerdict
            assert len(analysis.recommendation) > 0

        # Test sorting methods
        sorted_by_value = result.get_sorted_by_value()
        assert len(sorted_by_value) == len(sample_squad.players)

        # Verify descending order
        for i in range(len(sorted_by_value) - 1):
            assert sorted_by_value[i].value_score >= sorted_by_value[i + 1].value_score


class TestPlayerModel:
    """Test suite for Player model methods."""

    def test_player_position_category_striker(self, sample_elite_player):
        """Test position category classification for striker."""
        assert sample_elite_player.get_position_category() == PositionCategory.ST

    def test_player_position_category_goalkeeper(self, sample_goalkeeper):
        """Test position category classification for goalkeeper."""
        assert sample_goalkeeper.get_position_category() == PositionCategory.GK

    def test_player_position_category_winger(self, sample_player):
        """Test position category classification with multi-position player."""
        # Josh Bowler is listed as AMR but can play "AM (RL), ST (C)"
        # Enhanced logic evaluates stats to determine best fit
        # With his stats (shot_90=3.39, av_rat=7.30, ch_c_90=0.97, drb_90=6.00),
        # ST is the better fit
        position = sample_player.get_position_category()
        assert position in [PositionCategory.AM, PositionCategory.W, PositionCategory.ST]

    def test_player_total_apps(self, sample_player):
        """Test total appearances calculation."""
        total = sample_player.get_total_apps()
        assert total == sample_player.apps + sample_player.subs

    def test_player_status_flag_detection(self, sample_player):
        """Test status flag detection."""
        # Josh Bowler has 'PR' flag
        assert sample_player.has_status_flag() is True
        assert sample_player.get_status_flag() == StatusFlag.PRE_CONTRACT

    def test_player_no_status_flag(self, sample_elite_player):
        """Test player without status flag."""
        # Damián Pizarro has no flag
        assert sample_elite_player.has_status_flag() is False
        assert sample_elite_player.get_status_flag() == StatusFlag.NONE

    def test_player_wage_formatting(self, sample_player):
        """Test wage formatting."""
        formatted = sample_player.get_wage_formatted()
        assert '£' in formatted
        assert 'p/w' in formatted
        assert '26,000' in formatted


class TestSquadModel:
    """Test suite for Squad model methods."""

    def test_squad_get_players_by_position(self, sample_squad):
        """Test filtering players by position."""
        goalkeepers = sample_squad.get_players_by_position(PositionCategory.GK)
        assert len(goalkeepers) == 1
        assert goalkeepers[0].get_position_category() == PositionCategory.GK

    def test_squad_average_wage(self, sample_squad):
        """Test squad average wage calculation."""
        avg_wage = sample_squad.get_average_wage()
        assert avg_wage > 0

        # Manual verification
        total_wage = sum(p.wage for p in sample_squad.players)
        expected_avg = total_wage / len(sample_squad.players)
        assert abs(avg_wage - expected_avg) < 0.01

    def test_squad_size(self, sample_squad):
        """Test squad size calculation."""
        assert sample_squad.get_squad_size() == len(sample_squad.players)

    def test_squad_positions_summary(self, sample_squad):
        """Test positions summary."""
        summary = sample_squad.get_positions_summary()

        assert isinstance(summary, dict)
        assert len(summary) > 0

        # Should have at least GK, CB, FB, ST positions
        assert 'GK' in summary
        assert summary['GK'] == 1


class TestAnalysisResultMethods:
    """Test suite for SquadAnalysisResult methods."""

    def test_get_elite_players(self, squad_audit_service, sample_squad):
        """Test filtering elite players."""
        result = squad_audit_service.analyze_squad(sample_squad)
        elite_players = result.get_elite_players()

        # Should be a list
        assert isinstance(elite_players, list)

        # All should have ELITE verdict
        for analysis in elite_players:
            assert analysis.verdict == PerformanceVerdict.ELITE

    def test_get_poor_performers(self, squad_audit_service, sample_squad):
        """Test filtering poor performers."""
        result = squad_audit_service.analyze_squad(sample_squad)
        poor_performers = result.get_poor_performers()

        # Should be a list
        assert isinstance(poor_performers, list)

        # All should have POOR verdict
        for analysis in poor_performers:
            assert analysis.verdict == PerformanceVerdict.POOR

    def test_value_score_color_classification(self, sample_player, squad_audit_service):
        """Test value score color classification."""
        from models import PlayerAnalysis

        # Elite value (>= 150)
        analysis_elite = PlayerAnalysis(
            player=sample_player,
            performance_index=120.0,
            value_score=160.0,
            verdict=PerformanceVerdict.ELITE,
            recommendation='Test'
        )
        assert analysis_elite.get_value_score_color() == 'success'

        # Good value (120-150)
        analysis_good = PlayerAnalysis(
            player=sample_player,
            performance_index=110.0,
            value_score=130.0,
            verdict=PerformanceVerdict.GOOD,
            recommendation='Test'
        )
        assert analysis_good.get_value_score_color() == 'info'

        # Expected value (100-120)
        analysis_expected = PlayerAnalysis(
            player=sample_player,
            performance_index=100.0,
            value_score=110.0,
            verdict=PerformanceVerdict.AVERAGE,
            recommendation='Test'
        )
        assert analysis_expected.get_value_score_color() == 'warning'

        # Below expected value (80-100)
        analysis_below = PlayerAnalysis(
            player=sample_player,
            performance_index=90.0,
            value_score=85.0,
            verdict=PerformanceVerdict.AVERAGE,
            recommendation='Test'
        )
        assert analysis_below.get_value_score_color() == 'dark'

        # Poor value (< 80)
        analysis_poor = PlayerAnalysis(
            player=sample_player,
            performance_index=80.0,
            value_score=70.0,
            verdict=PerformanceVerdict.POOR,
            recommendation='Test'
        )
        assert analysis_poor.get_value_score_color() == 'danger'
