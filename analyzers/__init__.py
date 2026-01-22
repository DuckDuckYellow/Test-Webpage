"""
Analyzers Package

Contains analysis engines for squad evaluation, role recommendations,
and player assessment.
"""

from .role_evaluator import RoleEvaluator, RoleScore

__all__ = ['RoleEvaluator', 'RoleScore']
