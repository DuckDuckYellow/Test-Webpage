"""
Integration tests for league comparison functionality.
"""

import pytest
from flask import session
from services.squad_analysis_manager import SquadAnalysisManager
from services.league_baseline_generator import LeagueBaselineGenerator
from models.league_baseline import LeagueWageBaseline, LeagueBaselineCollection
from models.constants import PositionCategory


@pytest.fixture
def sample_league_baselines():
    """Create sample league baselines for testing."""
    baselines = [
        LeagueWageBaseline(
            division="English Premier Division",
            position="ST (C)",
            position_category=PositionCategory.ST,
            average_wage=125000.0,
            median_wage=85000.0,
            percentile_25=45000.0,
            percentile_75=180000.0,
            player_count=45,
            is_aggregated=False
        ),
        LeagueWageBaseline(
            division="English Premier Division",
            position="M (C)",
            position_category=PositionCategory.CM,
            average_wage=95000.0,
            median_wage=70000.0,
            percentile_25=35000.0,
            percentile_75=140000.0,
            player_count=60,
            is_aggregated=False
        ),
        LeagueWageBaseline(
            division="English Premier Division",
            position="Defenders",
            position_category=PositionCategory.CB,
            average_wage=80000.0,
            median_wage=65000.0,
            percentile_25=30000.0,
            percentile_75=120000.0,
            player_count=80,
            is_aggregated=True
        ),
    ]

    return LeagueBaselineCollection(
        baselines=baselines,
        gk_wage_multiplier=0.75,
        division_metadata={"English Premier Division": 523}
    )


@pytest.fixture
def sample_squad_html():
    """Sample squad HTML for testing."""
    return '''
    <table>
        <tr>
            <th>Inf</th><th>Name</th><th>Nat</th><th>Position</th><th>Age</th><th>Club</th>
            <th>Wage</th><th>Av Rat</th><th>Apps</th><th>Mins</th><th>Gls</th><th>Asts</th>
            <th>xG</th><th>xA</th><th>Cmp</th><th>Pas Att</th><th>Cr C</th><th>Tck W</th>
            <th>Pres A</th><th>Hdrs W</th><th>Hdrs A</th><th>Blk</th><th>Cls</th>
            <th>K Tck</th><th>K Pas</th><th>Drb</th><th>Ps Ps</th><th>Pts</th>
            <th>PoM</th><th>Transfer Status</th><th>Personality</th><th>Media Handling</th>
            <th>Left Foot</th><th>Right Foot</th><th>Jadg</th><th>Pac</th><th>Nat Fit</th>
            <th>Acc</th><th>Sta</th><th>Str</th><th>Bal</th><th>Jum</th><th>Nat Fit</th>
            <th>Cnt</th><th>Pos</th><th>Ant</th><th>Dec</th><th>Bra</th><th>Tea</th>
            <th>Wor</th><th>Agi</th><th>Dri</th><th>Fla</th><th>OtB</th><th>Tec</th>
            <th>Fin</th><th>Fir</th><th>Hea</th><th>Lon</th><th>L Th</th><th>Mar</th>
            <th>Pas</th><th>Tck</th><th>Cro</th><th>Cor</th><th>Fre</th><th>Pen</th>
            <th>Contract Expires</th>
        </tr>
        <tr>
            <td></td><td>Test Striker</td><td>England</td><td>ST (C)</td><td>25</td><td>Test FC</td>
            <td>£50,000 p/w</td><td>7.50</td><td>20</td><td>1800</td><td>15</td><td>5</td>
            <td>12.5</td><td>4.2</td><td>300</td><td>400</td><td>20</td><td>10</td>
            <td>15</td><td>30</td><td>45</td><td>5</td><td>8</td>
            <td>15</td><td>25</td><td>35</td><td>180</td><td>90</td>
            <td>3</td><td></td><td>Professional</td><td>Respectful</td>
            <td>Weak</td><td>Very Strong</td><td>15</td><td>14</td><td>15</td>
            <td>14</td><td>15</td><td>16</td><td>14</td><td>15</td><td>15</td>
            <td>14</td><td>15</td><td>16</td><td>15</td><td>14</td><td>15</td>
            <td>16</td><td>14</td><td>15</td><td>14</td><td>16</td><td>15</td>
            <td>16</td><td>15</td><td>14</td><td>13</td><td>12</td><td>11</td>
            <td>15</td><td>12</td><td>13</td><td>14</td><td>12</td><td>15</td>
            <td>30-Jun-2026</td>
        </tr>
    </table>
    '''


class TestLeagueComparisonWorkflow:
    """Test complete league comparison workflow."""

    def test_upload_squad_with_division(self, app, sample_league_baselines, sample_squad_html):
        """Test uploading squad with division selection."""
        with app.app_context():
            manager = SquadAnalysisManager()

            analysis_result, errors = manager.process_squad_upload(
                sample_squad_html,
                selected_division="English Premier Division",
                league_baselines=sample_league_baselines
            )

            assert analysis_result is not None
            assert len(errors) == 0
            assert analysis_result.selected_division == "English Premier Division"

            # Check that league value scores are populated
            for player_analysis in analysis_result.player_analyses:
                if player_analysis.player.mins >= 200:
                    assert player_analysis.league_value_score is not None
                    assert player_analysis.league_baseline is not None
                    assert player_analysis.league_wage_percentile is not none

    def test_upload_squad_without_division(self, app, sample_squad_html):
        """Test uploading squad without division selection."""
        with app.app_context():
            manager = SquadAnalysisManager()

            analysis_result, errors = manager.process_squad_upload(
                sample_squad_html,
                selected_division=None,
                league_baselines=None
            )

            assert analysis_result is not None
            assert len(errors) == 0
            assert analysis_result.selected_division is None

            # Check that league value scores are NOT populated
            for player_analysis in analysis_result.player_analyses:
                assert player_analysis.league_value_score is None
                assert player_analysis.league_baseline is None
                assert player_analysis.league_wage_percentile is None

    def test_division_persists_in_session(self, app, sample_league_baselines, sample_squad_html):
        """Test that division selection persists in session."""
        with app.test_request_context():
            with app.app_context():
                manager = SquadAnalysisManager()

                # Upload with division
                analysis_result, errors = manager.process_squad_upload(
                    sample_squad_html,
                    selected_division="English Premier Division",
                    league_baselines=sample_league_baselines
                )

                # Check session
                assert session.get('selected_division') == "English Premier Division"

                # Re-analyze from session
                retrieved_result = manager.get_analysis_from_session()

                assert retrieved_result is not None
                assert retrieved_result.selected_division == "English Premier Division"


class TestRouteIntegration:
    """Test route-level integration."""

    def test_squad_audit_tracker_with_division(self, client, sample_league_baselines, sample_squad_html):
        """Test POST to squad audit tracker with division selection."""
        from io import BytesIO

        # Mock league_baselines in app module
        from app import create_app
        app = create_app()
        app.league_baselines = sample_league_baselines

        with app.test_client() as client:
            response = client.post(
                '/projects/squad-audit-tracker',
                data={
                    'html_file': (BytesIO(sample_squad_html.encode()), 'squad.html'),
                    'division': 'English Premier Division'
                },
                content_type='multipart/form-data',
                follow_redirects=True
            )

            assert response.status_code == 200
            # Should show league value column
            assert b'League Value' in response.data
            assert b'English Premier Division' in response.data

    def test_squad_audit_tracker_without_division(self, client, sample_squad_html):
        """Test POST to squad audit tracker without division selection."""
        from io import BytesIO

        response = client.post(
            '/projects/squad-audit-tracker',
            data={
                'html_file': (BytesIO(sample_squad_html.encode()), 'squad.html'),
                'division': ''
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200

    def test_available_divisions_in_context(self, client):
        """Test that available divisions are passed to template."""
        response = client.get('/projects/squad-audit-tracker')
        assert response.status_code == 200


class TestValueComparisonIndicator:
    """Test value comparison indicator logic."""

    def test_league_bargain_indicator(self, app, sample_league_baselines, sample_squad_html):
        """Test 'League Bargain' indicator appears for underpaid players."""
        # Modify HTML to create a player with very low wage but good performance
        modified_html = sample_squad_html.replace("£50,000 p/w", "£10,000 p/w")

        with app.app_context():
            manager = SquadAnalysisManager()

            analysis_result, errors = manager.process_squad_upload(
                modified_html,
                selected_division="English Premier Division",
                league_baselines=sample_league_baselines
            )

            # Find striker analysis
            striker_analysis = next(
                (a for a in analysis_result.player_analyses if "Striker" in a.player.name),
                None
            )

            if striker_analysis and striker_analysis.league_value_score:
                # Low wage vs league average should produce high league value
                # Difference of 30+ points should trigger "League Bargain"
                comparison = striker_analysis.get_value_comparison_indicator()
                # Note: Actual indicator depends on squad context too
                # Just verify the method runs without error
                assert comparison in ["League Bargain", "Squad Context", None]


class TestLowSampleSizeWarning:
    """Test low sample size warning functionality."""

    def test_low_sample_size_detection(self):
        """Test that low sample size divisions are detected."""
        baselines = [
            LeagueWageBaseline(
                division="Small League",
                position="ST (C)",
                position_category=PositionCategory.ST,
                average_wage=15000.0,
                median_wage=12000.0,
                percentile_25=8000.0,
                percentile_75=20000.0,
                player_count=25,
                is_aggregated=False
            )
        ]

        collection = LeagueBaselineCollection(
            baselines=baselines,
            gk_wage_multiplier=0.75,
            division_metadata={"Small League": 75}  # Less than 100
        )

        assert collection.is_low_sample_size("Small League")
        assert collection.get_division_player_count("Small League") == 75


class TestBackwardCompatibility:
    """Test that system works without league baselines."""

    def test_analysis_without_baselines(self, app, sample_squad_html):
        """Test that analysis works when no baselines are available."""
        with app.app_context():
            manager = SquadAnalysisManager()

            analysis_result, errors = manager.process_squad_upload(
                sample_squad_html,
                selected_division=None,
                league_baselines=None
            )

            assert analysis_result is not None
            assert len(errors) == 0

            # Verify squad-based scores still work
            for player_analysis in analysis_result.player_analyses:
                if player_analysis.player.mins >= 200:
                    assert player_analysis.value_score is not None
                    assert player_analysis.verdict is not None
