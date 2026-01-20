"""
Recruitment vacancy and recruiter models.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RoleType(Enum):
    """Enumeration of recruitment role difficulty types."""
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class RecruitmentStage(Enum):
    """Enumeration of recruitment process stages."""
    SOURCING = 'sourcing'
    SCREENING = 'screening'
    INTERVIEW = 'interview'
    OFFER = 'offer'
    PRE_HIRE_CHECKS = 'pre-hire checks'
    NONE = ''


@dataclass
class Vacancy:
    """Represents an individual recruitment vacancy."""
    name: str
    role_type: RoleType
    is_internal: bool = False
    stage: RecruitmentStage = RecruitmentStage.NONE

    def __post_init__(self):
        """Allow string initialization for convenience."""
        if isinstance(self.role_type, str):
            self.role_type = RoleType(self.role_type.lower())
        if isinstance(self.stage, str):
            stage_str = self.stage.lower().strip()
            self.stage = RecruitmentStage(stage_str)


@dataclass
class Recruiter:
    """Represents a Recruiter managing multiple vacancies."""
    name: str
    vacancies: List[Vacancy] = field(default_factory=list)

    @property
    def vacancy_count(self) -> int:
        """Return count of vacancies assigned to this recruiter."""
        return len(self.vacancies)
