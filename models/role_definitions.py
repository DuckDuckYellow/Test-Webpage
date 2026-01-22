"""
Role Definitions for Football Manager Squad Analysis

Defines 12 distinct playing roles with metric requirements and thresholds.
Each role has specific metrics that determine player suitability.

Tier 1: SPECIALIZED ROLES (Most specific, least interchange)
Tier 2: MIDFIELD ROLES (High interchange potential)
Tier 3: ATTACKING ROLES (Highest interchange potential)
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class RoleProfile:
    """
    Defines metrics and thresholds for a specific playing role.

    Attributes:
        name: Role name (e.g., "CB-STOPPER", "BCB")
        primary_position: Base position category (e.g., "CB", "CM")
        description: Role description
        metrics: List of metric names required for this role
        thresholds: Dict of metric thresholds {metric: {tier: value}}
        interchangeable_with: List of roles this can interchange with
    """
    name: str
    display_name: str
    primary_position: str
    description: str
    metrics: List[str]
    thresholds: Dict[str, Dict[str, float]]
    interchangeable_with: List[str]


# =============================================================================
# TIER 1: SPECIALIZED ROLES
# =============================================================================

GK = RoleProfile(
    name='GK',
    display_name='Goalkeeper',
    primary_position='GK',
    description='Goalkeeper - shot-stopping and distribution',
    metrics=['xgp_90', 'conceded_90', 'interceptions_90', 'pass_pct'],
    thresholds={
        'xgp_90': {'good': 0.25, 'ok': 0, 'poor': -0.38},
        'conceded_90': {'good': 0.75, 'ok': 1.41, 'poor': 2.15},
        'interceptions_90': {'good': 0.22, 'ok': 0.1, 'poor': 0.04},
        'pass_pct': {'good': 97, 'ok': 78, 'poor': 47}
    },
    interchangeable_with=[]
)

CB_STOPPER = RoleProfile(
    name='CB-STOPPER',
    display_name='Center-Back',
    primary_position='CB',
    description='Traditional Defender - tackling and aerial dominance',
    metrics=['tackles_90', 'header_win_pct', 'clearances_90', 'interceptions_90', 'blocks_90'],
    thresholds={
        'tackles_90': {'good': 2.38, 'ok': 1.29, 'poor': 0.8},
        'header_win_pct': {'good': 82, 'ok': 72, 'poor': 59},
        'clearances_90': {'good': 1.64, 'ok': 0.85, 'poor': 0.44},
        'interceptions_90': {'good': 3.18, 'ok': 2.15, 'poor': 1.36},
        'blocks_90': {'good': 0.72, 'ok': 0.42, 'poor': 0.19}
    },
    interchangeable_with=['BCB']
)

BCB = RoleProfile(
    name='BCB',
    display_name='Ball-Playing Center-Back',
    primary_position='CB',
    description='Ball-Playing Center Back - distribution and possession',
    metrics=['tackles_90', 'clearances_90', 'interceptions_90', 'blocks_90', 'prog_passes_90', 'pass_pct'],
    thresholds={
        'tackles_90': {'good': 2.0, 'ok': 1.2, 'poor': 0.7},
        'clearances_90': {'good': 1.5, 'ok': 0.8, 'poor': 0.4},
        'interceptions_90': {'good': 3.0, 'ok': 2.0, 'poor': 1.3},
        'blocks_90': {'good': 0.6, 'ok': 0.35, 'poor': 0.15},
        'prog_passes_90': {'good': 5.5, 'ok': 3.5, 'poor': 2.0},
        'pass_pct': {'good': 92, 'ok': 85, 'poor': 78}
    },
    interchangeable_with=['CB-STOPPER', 'FB']
)

FB = RoleProfile(
    name='FB',
    display_name='Full-Back',
    primary_position='FB',
    description='Full Back - balanced defense and width',
    metrics=['tackles_90', 'interceptions_90', 'pressures_90', 'crosses_90', 'prog_passes_90', 'pass_pct'],
    thresholds={
        'tackles_90': {'good': 2.2, 'ok': 1.4, 'poor': 0.9},
        'interceptions_90': {'good': 2.8, 'ok': 1.8, 'poor': 1.0},
        'pressures_90': {'good': 12.0, 'ok': 8.0, 'poor': 5.0},
        'crosses_90': {'good': 0.5, 'ok': 0.25, 'poor': 0.1},
        'prog_passes_90': {'good': 4.5, 'ok': 2.5, 'poor': 1.5},
        'pass_pct': {'good': 88, 'ok': 80, 'poor': 72}
    },
    interchangeable_with=['WB', 'BCB']
)

WB = RoleProfile(
    name='WB',
    display_name='Wing-Back',
    primary_position='FB',
    description='Wing Back - attack, defense, and width',
    metrics=['tackles_90', 'interceptions_90', 'pressures_90', 'dribbles_90', 'crosses_90', 'sprints_90'],
    thresholds={
        'tackles_90': {'good': 2.0, 'ok': 1.2, 'poor': 0.7},
        'interceptions_90': {'good': 2.5, 'ok': 1.5, 'poor': 0.9},
        'pressures_90': {'good': 11.0, 'ok': 7.5, 'poor': 4.5},
        'dribbles_90': {'good': 3.0, 'ok': 1.8, 'poor': 1.0},
        'crosses_90': {'good': 0.6, 'ok': 0.3, 'poor': 0.15},
        'sprints_90': {'good': 14, 'ok': 10, 'poor': 7}
    },
    interchangeable_with=['FB', 'WAP']
)

# =============================================================================
# TIER 2: MIDFIELD ROLES
# =============================================================================

MD = RoleProfile(
    name='MD',
    display_name='Defensive Midfielder',
    primary_position='DM',
    description='Midfielder Destroyer - defensive focus',
    metrics=['tackles_90', 'interceptions_90', 'blocks_90', 'pressures_90', 'pass_pct'],
    thresholds={
        'tackles_90': {'good': 2.5, 'ok': 1.6, 'poor': 1.0},
        'interceptions_90': {'good': 3.0, 'ok': 2.0, 'poor': 1.2},
        'blocks_90': {'good': 0.5, 'ok': 0.3, 'poor': 0.15},
        'pressures_90': {'good': 13.0, 'ok': 9.0, 'poor': 6.0},
        'pass_pct': {'good': 90, 'ok': 83, 'poor': 76}
    },
    interchangeable_with=['MC']
)

MC = RoleProfile(
    name='MC',
    display_name='Central Midfielder',
    primary_position='CM',
    description='Midfielder Creator - playmaking focus',
    metrics=['key_passes_90', 'prog_passes_90', 'xassists_90', 'dribbles_90', 'pass_pct', 'tackles_90'],
    thresholds={
        'key_passes_90': {'good': 1.5, 'ok': 0.8, 'poor': 0.4},
        'prog_passes_90': {'good': 5.0, 'ok': 3.0, 'poor': 1.8},
        'xassists_90': {'good': 0.15, 'ok': 0.08, 'poor': 0.04},
        'dribbles_90': {'good': 2.5, 'ok': 1.5, 'poor': 0.8},
        'pass_pct': {'good': 89, 'ok': 82, 'poor': 75},
        'tackles_90': {'good': 1.8, 'ok': 1.0, 'poor': 0.5}
    },
    interchangeable_with=['MD', 'AM(C)']
)

# =============================================================================
# TIER 3: ATTACKING ROLES
# =============================================================================

AM_C = RoleProfile(
    name='AM(C)',
    display_name='Attacking Midfielder (C)',
    primary_position='AM',
    description='Central Attacking Midfielder - creating and scoring',
    metrics=['key_passes_90', 'xassists_90', 'dribbles_90', 'pass_pct', 'shots_on_target_90', 'xg_90'],
    thresholds={
        'key_passes_90': {'good': 2.0, 'ok': 1.2, 'poor': 0.6},
        'xassists_90': {'good': 0.2, 'ok': 0.12, 'poor': 0.06},
        'dribbles_90': {'good': 3.5, 'ok': 2.0, 'poor': 1.0},
        'pass_pct': {'good': 86, 'ok': 78, 'poor': 70},
        'shots_on_target_90': {'good': 0.8, 'ok': 0.5, 'poor': 0.25},
        'xg_90': {'good': 0.25, 'ok': 0.15, 'poor': 0.08}
    },
    interchangeable_with=['MC', 'WAP', 'WAS']
)

WAP = RoleProfile(
    name='WAP',
    display_name='Winger',
    primary_position='W',
    description='Wide Attacker - Provider (crossing and creating)',
    metrics=['dribbles_90', 'crosses_90', 'sprints_90', 'key_passes_90', 'xassists_90'],
    thresholds={
        'dribbles_90': {'good': 4.0, 'ok': 2.5, 'poor': 1.5},
        'crosses_90': {'good': 0.7, 'ok': 0.4, 'poor': 0.2},
        'sprints_90': {'good': 16, 'ok': 12, 'poor': 8},
        'key_passes_90': {'good': 1.8, 'ok': 1.0, 'poor': 0.5},
        'xassists_90': {'good': 0.22, 'ok': 0.13, 'poor': 0.07}
    },
    interchangeable_with=['WAS', 'AM(C)', 'WB']
)

WAS = RoleProfile(
    name='WAS',
    display_name='Inside Forward',
    primary_position='W',
    description='Wide Attacker - Striker (finishing focus)',
    metrics=['dribbles_90', 'shots_on_target_90', 'sprints_90', 'xg_90', 'conversion_pct'],
    thresholds={
        'dribbles_90': {'good': 4.5, 'ok': 3.0, 'poor': 1.8},
        'shots_on_target_90': {'good': 1.2, 'ok': 0.7, 'poor': 0.4},
        'sprints_90': {'good': 17, 'ok': 13, 'poor': 9},
        'xg_90': {'good': 0.38, 'ok': 0.22, 'poor': 0.12},
        'conversion_pct': {'good': 25, 'ok': 18, 'poor': 12}
    },
    interchangeable_with=['WAP', 'ST-GS', 'AM(C)']
)

ST_PROVIDER = RoleProfile(
    name='ST-PROVIDER',
    display_name='Target Forward',
    primary_position='ST',
    description='Striker - Provider (target man and link play)',
    metrics=['headers_won_90', 'xassists_90', 'xg_90', 'shots_on_target_90', 'key_passes_90'],
    thresholds={
        'headers_won_90': {'good': 1.2, 'ok': 0.7, 'poor': 0.4},
        'xassists_90': {'good': 0.18, 'ok': 0.1, 'poor': 0.05},
        'xg_90': {'good': 0.35, 'ok': 0.22, 'poor': 0.13},
        'shots_on_target_90': {'good': 1.0, 'ok': 0.6, 'poor': 0.35},
        'key_passes_90': {'good': 1.3, 'ok': 0.7, 'poor': 0.35}
    },
    interchangeable_with=['ST-GS', 'WAP']
)

ST_GS = RoleProfile(
    name='ST-GS',
    display_name='Advanced Forward',
    primary_position='ST',
    description='Striker - Goalscorer (pure finisher)',
    metrics=['headers_won_90', 'dribbles_90', 'xg_90', 'shots_on_target_90', 'conversion_pct'],
    thresholds={
        'headers_won_90': {'good': 1.0, 'ok': 0.6, 'poor': 0.3},
        'dribbles_90': {'good': 2.5, 'ok': 1.5, 'poor': 0.8},
        'xg_90': {'good': 0.45, 'ok': 0.28, 'poor': 0.16},
        'shots_on_target_90': {'good': 1.5, 'ok': 0.9, 'poor': 0.5},
        'conversion_pct': {'good': 28, 'ok': 20, 'poor': 14}
    },
    interchangeable_with=['ST-PROVIDER', 'WAS']
)

# =============================================================================
# ROLE REGISTRY
# =============================================================================

ROLES = {
    'GK': GK,
    'CB-STOPPER': CB_STOPPER,
    'BCB': BCB,
    'FB': FB,
    'WB': WB,
    'MD': MD,
    'MC': MC,
    'AM(C)': AM_C,
    'WAP': WAP,
    'WAS': WAS,
    'ST-PROVIDER': ST_PROVIDER,
    'ST-GS': ST_GS
}

# Role categories for UI grouping
ROLE_CATEGORIES = {
    'Goalkeeper': ['GK'],
    'Defense': ['CB-STOPPER', 'BCB', 'FB', 'WB'],
    'Midfield': ['MD', 'MC'],
    'Attack': ['AM(C)', 'WAP', 'WAS', 'ST-PROVIDER', 'ST-GS']
}
