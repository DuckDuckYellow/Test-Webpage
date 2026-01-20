"""
Capacity Service - Handles recruitment capacity calculations

This service encapsulates all business logic for calculating recruiter
workload, capacity usage, and team summaries.
"""

from typing import List, Dict
from models import Vacancy, Recruiter, RoleType, RecruitmentStage


class CapacityService:
    """Service for calculating recruitment capacity and workload."""

    # Stage-based time weighting multipliers
    STAGE_MULTIPLIERS = {
        RecruitmentStage.SOURCING: 0.2,
        RecruitmentStage.SCREENING: 0.4,
        RecruitmentStage.INTERVIEW: 0.2,
        RecruitmentStage.OFFER: 0.1,
        RecruitmentStage.PRE_HIRE_CHECKS: 0.1,
        RecruitmentStage.NONE: 1.0
    }

    # Base capacity values
    BASE_CAPACITY = {
        RoleType.EASY: 1/30,      # 3.33% per vacancy
        RoleType.MEDIUM: 1/20,    # 5% per vacancy
        RoleType.HARD: 1/12       # 8.33% per vacancy
    }

    @classmethod
    def calculate_vacancy_load(cls, vacancy: Vacancy) -> float:
        """
        Calculate capacity usage for a single vacancy.

        Business rules:
        - Easy: 1/30 = 3.33% base capacity
        - Medium: 1/20 = 5% base capacity
        - Hard: 1/12 = 8.33% base capacity
        - Internal roles: 0.25 multiplier (75% less time)
        - Stage-based: Sourcing (20%), Screening (40%), Interview (20%),
                       Offer (10%), Pre-Hire Checks (10%), None (100%)

        Formula: base_capacity × internal_multiplier × stage_multiplier

        Args:
            vacancy: Vacancy object

        Returns:
            Capacity used by this vacancy (0-1 scale)
        """
        base = cls.BASE_CAPACITY[vacancy.role_type]
        internal_mult = 0.25 if vacancy.is_internal else 1.0
        stage_mult = cls.STAGE_MULTIPLIERS[vacancy.stage]
        return base * internal_mult * stage_mult

    @classmethod
    def calculate_vacancy_capacity_from_dict(cls, role_type: str, is_internal: bool = False, stage: str = '') -> float:
        """
        Calculate capacity usage from raw dictionary values (for backward compatibility).

        Args:
            role_type: 'easy', 'medium', or 'hard'
            is_internal: True if internal-only role
            stage: Recruitment stage or empty string

        Returns:
            Capacity used by this vacancy (0-1 scale)
        """
        # Convert string to enum
        role_type_lower = role_type.lower()
        if role_type_lower not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid role type: {role_type}")

        role_type_enum = RoleType(role_type_lower)

        # Convert stage string to enum
        stage_lower = stage.lower().strip()
        stage_enum = RecruitmentStage(stage_lower) if stage_lower else RecruitmentStage.NONE

        # Create temporary Vacancy object and calculate
        vacancy = Vacancy(
            name="temp",
            role_type=role_type_enum,
            is_internal=is_internal,
            stage=stage_enum
        )

        return cls.calculate_vacancy_load(vacancy)

    @classmethod
    def get_recruiter_summary(cls, recruiter: Recruiter) -> Dict:
        """
        Calculate capacity summary for a recruiter.

        Args:
            recruiter: Recruiter object with vacancies

        Returns:
            Dictionary with capacity info, status, and recommendations
        """
        total_capacity_used = sum(cls.calculate_vacancy_load(v) for v in recruiter.vacancies)
        capacity_percentage = round(total_capacity_used * 100, 1)

        # Determine status
        if total_capacity_used > 1.0:
            status = 'overloaded'
            status_text = 'Overloaded'
        elif total_capacity_used >= 0.9:
            status = 'at-capacity'
            status_text = 'At Capacity'
        elif total_capacity_used >= 0.7:
            status = 'near-capacity'
            status_text = 'Near Capacity'
        else:
            status = 'available'
            status_text = 'Available'

        # Calculate remaining capacity
        remaining_capacity = 1.0 - total_capacity_used

        if remaining_capacity >= 0:
            additional_easy = max(0, int(remaining_capacity * 30))
            additional_medium = max(0, int(remaining_capacity * 20))
            additional_hard = max(0, int(remaining_capacity * 12))
            remaining_message = f"Can take {additional_easy} more easy OR {additional_medium} more medium OR {additional_hard} more hard vacancies"
        else:
            overload = abs(remaining_capacity)
            overload_easy = int(overload * 30)
            overload_medium = int(overload * 20)
            overload_hard = int(overload * 12)
            remaining_message = f"Overloaded by {overload_easy} easy OR {overload_medium} medium OR {overload_hard} hard vacancies"

        # Build vacancy details
        vacancy_details = []
        for vacancy in recruiter.vacancies:
            vacancy_capacity = cls.calculate_vacancy_load(vacancy)
            vacancy_details.append({
                'name': vacancy.name,
                'role_type': vacancy.role_type.value.capitalize(),
                'is_internal': vacancy.is_internal,
                'stage': vacancy.stage.value.title() if vacancy.stage.value else 'None',
                'capacity_percentage': round(vacancy_capacity * 100, 2)
            })

        return {
            'name': recruiter.name,
            'capacity_used': total_capacity_used,
            'capacity_percentage': capacity_percentage,
            'status': status,
            'status_text': status_text,
            'remaining_message': remaining_message,
            'remaining_capacity': remaining_capacity,
            'vacancies': vacancy_details
        }

    @classmethod
    def calculate_recruiter_capacity_from_vacancies(cls, vacancies: List[Dict]) -> Dict:
        """
        Calculate capacity for a recruiter from a list of vacancy dictionaries.

        Args:
            vacancies: List of vacancy dicts with keys:
                      - vacancy_name
                      - role_type
                      - is_internal
                      - stage

        Returns:
            Dictionary with capacity info, vacancy details, and status
        """
        total_capacity_used = 0.0
        vacancy_details = []

        for vacancy in vacancies:
            vacancy_capacity = cls.calculate_vacancy_capacity_from_dict(
                vacancy['role_type'],
                vacancy.get('is_internal', False),
                vacancy.get('stage', '')
            )

            total_capacity_used += vacancy_capacity

            # Store details for display
            vacancy_details.append({
                'name': vacancy.get('vacancy_name', 'Unnamed'),
                'role_type': vacancy['role_type'].capitalize(),
                'is_internal': vacancy.get('is_internal', False),
                'stage': vacancy.get('stage', 'None'),
                'capacity_percentage': round(vacancy_capacity * 100, 2)
            })

        capacity_percentage = round(total_capacity_used * 100, 1)

        # Determine status
        if total_capacity_used > 1.0:
            status = 'overloaded'
            status_text = 'Overloaded'
        elif total_capacity_used >= 0.9:
            status = 'at-capacity'
            status_text = 'At Capacity'
        elif total_capacity_used >= 0.7:
            status = 'near-capacity'
            status_text = 'Near Capacity'
        else:
            status = 'available'
            status_text = 'Available'

        # Calculate remaining capacity
        remaining_capacity = 1.0 - total_capacity_used

        if remaining_capacity >= 0:
            additional_easy = max(0, int(remaining_capacity * 30))
            additional_medium = max(0, int(remaining_capacity * 20))
            additional_hard = max(0, int(remaining_capacity * 12))
            remaining_message = f"Can take {additional_easy} more easy OR {additional_medium} more medium OR {additional_hard} more hard vacancies"
        else:
            overload = abs(remaining_capacity)
            overload_easy = int(overload * 30)
            overload_medium = int(overload * 20)
            overload_hard = int(overload * 12)
            remaining_message = f"Overloaded by {overload_easy} easy OR {overload_medium} medium OR {overload_hard} hard vacancies"

        return {
            'capacity_used': total_capacity_used,
            'capacity_percentage': capacity_percentage,
            'status': status,
            'status_text': status_text,
            'remaining_message': remaining_message,
            'remaining_capacity': remaining_capacity,
            'vacancies': vacancy_details
        }

    @classmethod
    def calculate_team_summary(cls, recruiters_data: List[Dict]) -> Dict:
        """
        Calculate team-wide summary statistics.

        Args:
            recruiters_data: List of recruiter dictionaries with capacity info

        Returns:
            Dictionary with team summary and health indicators
        """
        if not recruiters_data:
            return None

        total_recruiters = len(recruiters_data)
        total_capacity = sum(r['capacity_percentage'] for r in recruiters_data)
        average_capacity = round(total_capacity / total_recruiters, 1)

        # Count by status
        status_counts = {
            'available': sum(1 for r in recruiters_data if r['status'] == 'available'),
            'near-capacity': sum(1 for r in recruiters_data if r['status'] == 'near-capacity'),
            'at-capacity': sum(1 for r in recruiters_data if r['status'] == 'at-capacity'),
            'overloaded': sum(1 for r in recruiters_data if r['status'] == 'overloaded')
        }

        # Determine overall team health
        if status_counts['overloaded'] > total_recruiters * 0.3:
            team_health = 'critical'
            team_health_text = 'Critical - Team Overloaded'
        elif status_counts['at-capacity'] + status_counts['overloaded'] > total_recruiters * 0.5:
            team_health = 'warning'
            team_health_text = 'Warning - High Utilization'
        elif average_capacity < 50:
            team_health = 'underutilized'
            team_health_text = 'Good - Capacity Available'
        else:
            team_health = 'healthy'
            team_health_text = 'Healthy - Balanced Load'

        return {
            'total_recruiters': total_recruiters,
            'average_capacity': average_capacity,
            'status_counts': status_counts,
            'team_health': team_health,
            'team_health_text': team_health_text
        }
