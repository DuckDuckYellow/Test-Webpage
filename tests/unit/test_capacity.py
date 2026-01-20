"""
Unit Tests for CapacityService

Tests the actual capacity calculation logic from services/capacity_service.py
without reimplementing business rules.
"""

import pytest
from models import Vacancy, Recruiter, RoleType, RecruitmentStage


class TestVacancyLoadCalculation:
    """Test single vacancy capacity calculations."""

    def test_easy_external_no_stage(self, capacity_service):
        """Test: External Easy role with no stage = 3.33% capacity."""
        vacancy = Vacancy(
            name='Test Role',
            role_type=RoleType.EASY,
            is_internal=False,
            stage=RecruitmentStage.NONE
        )
        load = capacity_service.calculate_vacancy_load(vacancy)
        assert round(load, 4) == round(1/30, 4)  # 3.33%

    def test_medium_external_no_stage(self, capacity_service):
        """Test: External Medium role with no stage = 5% capacity."""
        vacancy = Vacancy(
            name='Test Role',
            role_type=RoleType.MEDIUM,
            is_internal=False,
            stage=RecruitmentStage.NONE
        )
        load = capacity_service.calculate_vacancy_load(vacancy)
        assert round(load, 4) == round(1/20, 4)  # 5%

    def test_hard_external_no_stage(self, capacity_service):
        """Test: External Hard role with no stage = 8.33% capacity."""
        vacancy = Vacancy(
            name='Test Role',
            role_type=RoleType.HARD,
            is_internal=False,
            stage=RecruitmentStage.NONE
        )
        load = capacity_service.calculate_vacancy_load(vacancy)
        assert round(load, 4) == round(1/12, 4)  # 8.33%

    def test_internal_multiplier(self, capacity_service):
        """Test: Internal roles use 0.25 multiplier (75% time reduction)."""
        external = Vacancy(
            name='External',
            role_type=RoleType.MEDIUM,
            is_internal=False,
            stage=RecruitmentStage.NONE
        )
        internal = Vacancy(
            name='Internal',
            role_type=RoleType.MEDIUM,
            is_internal=True,
            stage=RecruitmentStage.NONE
        )

        external_load = capacity_service.calculate_vacancy_load(external)
        internal_load = capacity_service.calculate_vacancy_load(internal)

        assert internal_load == external_load * 0.25

    def test_stage_sourcing(self, capacity_service):
        """Test: Sourcing stage = 20% of base capacity."""
        vacancy = Vacancy(
            name='Test',
            role_type=RoleType.MEDIUM,
            is_internal=False,
            stage=RecruitmentStage.SOURCING
        )
        load = capacity_service.calculate_vacancy_load(vacancy)
        expected = (1/20) * 0.2  # Base * stage multiplier
        assert round(load, 4) == round(expected, 4)

    def test_stage_screening(self, capacity_service):
        """Test: Screening stage = 40% of base capacity."""
        vacancy = Vacancy(
            name='Test',
            role_type=RoleType.MEDIUM,
            is_internal=False,
            stage=RecruitmentStage.SCREENING
        )
        load = capacity_service.calculate_vacancy_load(vacancy)
        expected = (1/20) * 0.4  # Base * stage multiplier
        assert round(load, 4) == round(expected, 4)

    def test_complex_calculation(self, capacity_service):
        """Test: Internal Hard role in Screening = (1/12) * 0.25 * 0.4."""
        vacancy = Vacancy(
            name='Complex Role',
            role_type=RoleType.HARD,
            is_internal=True,
            stage=RecruitmentStage.SCREENING
        )
        load = capacity_service.calculate_vacancy_load(vacancy)
        expected = (1/12) * 0.25 * 0.4  # Base * internal * stage
        assert round(load, 6) == round(expected, 6)


class TestRecruiterSummary:
    """Test recruiter capacity summary calculations."""

    def test_single_vacancy_recruiter(self, capacity_service):
        """Test: Recruiter with single vacancy."""
        vacancy = Vacancy(
            name='Role',
            role_type=RoleType.MEDIUM,
            is_internal=False,
            stage=RecruitmentStage.NONE
        )
        recruiter = Recruiter(name='Test Recruiter', vacancies=[vacancy])

        summary = capacity_service.get_recruiter_summary(recruiter)

        assert summary['name'] == 'Test Recruiter'
        assert summary['capacity_percentage'] == 5.0  # 1/20 * 100
        assert summary['status'] == 'available'

    def test_multiple_vacancies(self, capacity_service):
        """Test: Recruiter with multiple vacancies."""
        vacancies = [
            Vacancy(name='Role 1', role_type=RoleType.EASY),
            Vacancy(name='Role 2', role_type=RoleType.EASY),
            Vacancy(name='Role 3', role_type=RoleType.MEDIUM),
        ]
        recruiter = Recruiter(name='Busy Recruiter', vacancies=vacancies)

        summary = capacity_service.get_recruiter_summary(recruiter)

        # (1/30 + 1/30 + 1/20) * 100 = 11.67%
        expected_percentage = round(((1/30) + (1/30) + (1/20)) * 100, 1)
        assert summary['capacity_percentage'] == expected_percentage

    def test_status_available(self, capacity_service):
        """Test: Status 'available' when < 70% capacity."""
        vacancies = [
            Vacancy(name='Role', role_type=RoleType.EASY),
        ]
        recruiter = Recruiter(name='Available', vacancies=vacancies)
        summary = capacity_service.get_recruiter_summary(recruiter)
        assert summary['status'] == 'available'

    def test_status_near_capacity(self, capacity_service):
        """Test: Status 'near-capacity' when 70-90% capacity."""
        # 15 easy roles = 50%, need more to reach 70%
        # Let's use 15 easy + 5 medium = 50% + 25% = 75%
        vacancies = [Vacancy(name=f'Easy {i}', role_type=RoleType.EASY) for i in range(15)]
        vacancies += [Vacancy(name=f'Med {i}', role_type=RoleType.MEDIUM) for i in range(5)]

        recruiter = Recruiter(name='Near Capacity', vacancies=vacancies)
        summary = capacity_service.get_recruiter_summary(recruiter)

        assert summary['status'] == 'near-capacity'
        assert 70 <= summary['capacity_percentage'] < 90

    def test_status_at_capacity(self, capacity_service):
        """Test: Status 'at-capacity' when 90-100% capacity."""
        # 18 medium roles = 90%
        vacancies = [Vacancy(name=f'Role {i}', role_type=RoleType.MEDIUM) for i in range(18)]
        recruiter = Recruiter(name='At Capacity', vacancies=vacancies)
        summary = capacity_service.get_recruiter_summary(recruiter)

        assert summary['status'] == 'at-capacity'
        assert summary['capacity_percentage'] >= 90

    def test_status_overloaded(self, capacity_service):
        """Test: Status 'overloaded' when > 100% capacity."""
        # 25 medium roles = 125%
        vacancies = [Vacancy(name=f'Role {i}', role_type=RoleType.MEDIUM) for i in range(25)]
        recruiter = Recruiter(name='Overloaded', vacancies=vacancies)
        summary = capacity_service.get_recruiter_summary(recruiter)

        assert summary['status'] == 'overloaded'
        assert summary['capacity_percentage'] > 100


class TestRecruiterCapacityFromDicts:
    """Test backward-compatible dict-based capacity calculations."""

    def test_dict_based_calculation(self, capacity_service):
        """Test: Calculate capacity from vacancy dictionaries."""
        vacancies = [
            {'vacancy_name': 'Role 1', 'role_type': 'easy', 'is_internal': False, 'stage': ''},
            {'vacancy_name': 'Role 2', 'role_type': 'medium', 'is_internal': True, 'stage': 'screening'},
        ]

        result = capacity_service.calculate_recruiter_capacity_from_vacancies(vacancies)

        assert 'capacity_percentage' in result
        assert 'status' in result
        assert 'vacancies' in result
        assert len(result['vacancies']) == 2

    def test_dict_validation(self, capacity_service):
        """Test: Invalid role type raises error."""
        vacancies = [
            {'vacancy_name': 'Bad Role', 'role_type': 'invalid', 'is_internal': False, 'stage': ''},
        ]

        with pytest.raises(ValueError):
            capacity_service.calculate_recruiter_capacity_from_vacancies(vacancies)


class TestTeamSummary:
    """Test team-wide statistics."""

    def test_team_summary_calculation(self, capacity_service):
        """Test: Team summary with multiple recruiters."""
        recruiters_data = [
            {'capacity_percentage': 50.0, 'status': 'available'},
            {'capacity_percentage': 75.0, 'status': 'near-capacity'},
            {'capacity_percentage': 95.0, 'status': 'at-capacity'},
        ]

        summary = capacity_service.calculate_team_summary(recruiters_data)

        assert summary['total_recruiters'] == 3
        assert summary['average_capacity'] == round((50 + 75 + 95) / 3, 1)
        assert summary['status_counts']['available'] == 1
        assert summary['status_counts']['near-capacity'] == 1
        assert summary['status_counts']['at-capacity'] == 1

    def test_team_health_critical(self, capacity_service):
        """Test: Team health 'critical' when >30% overloaded."""
        # 2 out of 5 overloaded = 40% > 30%
        recruiters_data = [
            {'capacity_percentage': 110.0, 'status': 'overloaded'},
            {'capacity_percentage': 120.0, 'status': 'overloaded'},
            {'capacity_percentage': 50.0, 'status': 'available'},
            {'capacity_percentage': 60.0, 'status': 'available'},
            {'capacity_percentage': 70.0, 'status': 'near-capacity'},
        ]

        summary = capacity_service.calculate_team_summary(recruiters_data)
        assert summary['team_health'] == 'critical'

    def test_empty_team(self, capacity_service):
        """Test: Empty team returns None."""
        summary = capacity_service.calculate_team_summary([])
        assert summary is None
