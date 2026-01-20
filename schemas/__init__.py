"""
Validation Schemas Package

Contains Pydantic models for input validation and data sanitization.
"""

from .recruitment import VacancySchema, RecruiterSchema

__all__ = ['VacancySchema', 'RecruiterSchema']
