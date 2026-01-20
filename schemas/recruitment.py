"""
Recruitment Validation Schemas

Pydantic models for validating recruitment capacity tracker inputs.
Provides type-safe validation with automatic sanitization.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from enum import Enum


class RoleTypeEnum(str, Enum):
    """Valid role type values."""
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class RecruitmentStageEnum(str, Enum):
    """Valid recruitment stage values."""
    SOURCING = 'sourcing'
    SCREENING = 'screening'
    INTERVIEW = 'interview'
    OFFER = 'offer'
    PRE_HIRE_CHECKS = 'pre-hire checks'
    NONE = ''


class VacancySchema(BaseModel):
    """
    Validation schema for a single vacancy.

    Ensures all vacancy data is properly formatted and within valid ranges.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Vacancy name"
    )
    role_type: RoleTypeEnum = Field(
        ...,
        description="Difficulty level: easy, medium, or hard"
    )
    is_internal: bool = Field(
        default=False,
        description="Whether this is an internal-only role"
    )
    stage: RecruitmentStageEnum = Field(
        default=RecruitmentStageEnum.NONE,
        description="Current recruitment stage"
    )

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Strip whitespace and validate name is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Vacancy name cannot be empty")
        return v

    @field_validator('role_type', mode='before')
    @classmethod
    def normalize_role_type(cls, v) -> str:
        """Convert role type to lowercase."""
        if isinstance(v, str):
            return v.lower().strip()
        return v

    @field_validator('stage', mode='before')
    @classmethod
    def normalize_stage(cls, v) -> str:
        """Convert stage to lowercase and handle empty values."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return ''
        if isinstance(v, str):
            return v.lower().strip()
        return v


class RecruiterSchema(BaseModel):
    """
    Validation schema for a recruiter with their vacancies.

    Validates recruiter name and ensures at least one vacancy exists.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Recruiter name"
    )
    vacancies: List[VacancySchema] = Field(
        ...,
        min_length=1,
        description="List of vacancies assigned to this recruiter"
    )

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Strip whitespace and validate name is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Recruiter name cannot be empty")
        return v


class ManualInputSchema(BaseModel):
    """
    Validation schema for manual capacity tracker form input.

    Validates the entire form submission with multiple recruiters and vacancies.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    recruiters: List[RecruiterSchema] = Field(
        ...,
        min_length=1,
        description="List of recruiters with their vacancies"
    )


def validate_vacancy_dict(data: dict) -> VacancySchema:
    """
    Validate and sanitize a vacancy dictionary.

    Args:
        data: Raw dictionary from form or Excel

    Returns:
        Validated VacancySchema instance

    Raises:
        ValueError: If validation fails
    """
    try:
        return VacancySchema(**data)
    except Exception as e:
        raise ValueError(f"Invalid vacancy data: {str(e)}")


def validate_recruiter_dict(name: str, vacancies: List[dict]) -> RecruiterSchema:
    """
    Validate and sanitize a recruiter with their vacancies.

    Args:
        name: Recruiter name
        vacancies: List of vacancy dictionaries

    Returns:
        Validated RecruiterSchema instance

    Raises:
        ValueError: If validation fails
    """
    try:
        validated_vacancies = [validate_vacancy_dict(v) for v in vacancies]
        return RecruiterSchema(name=name, vacancies=validated_vacancies)
    except Exception as e:
        raise ValueError(f"Invalid recruiter data for {name}: {str(e)}")
