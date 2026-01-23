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

    MIGRATION NOTE (2026-01-23): Now supports Primary (70%) and Secondary (30%) KPI weighting.
    This allows the system to prioritize role-defining metrics over supporting attributes.

    Attributes:
        name: Role name (e.g., "CB-STOPPER", "BCB")
        display_name: Display name for UI
        primary_position: Base position category (e.g., "CB", "CM")
        description: Role description
        primary_metrics: List of PRIMARY KPI metric names (70% weight in scoring)
        secondary_metrics: List of SECONDARY KPI metric names (30% weight in scoring)
        thresholds: Dict of metric thresholds {metric: {tier: value}}
        interchangeable_with: List of roles this can interchange with
    """
    name: str
    display_name: str
    primary_position: str
    description: str
    primary_metrics: List[str]
    secondary_metrics: List[str]
    thresholds: Dict[str, Dict[str, float]]
    interchangeable_with: List[str]

    @property
    def metrics(self) -> List[str]:
        """
        Returns all metrics (primary + secondary) for backward compatibility.

        This property ensures existing code that accesses role.metrics continues to work
        without modification during the migration to weighted scoring.
        """
        return self.primary_metrics + self.secondary_metrics


# =============================================================================
# TIER 1: SPECIALIZED ROLES
# =============================================================================

GK = RoleProfile(
    name='GK',
    display_name='Goalkeeper',
    primary_position='GK',
    description='Goalkeeper - shot-stopping and distribution',
    # PRIMARY KPIs (70% weight) - Core goalkeeping duties
    primary_metrics=['xgp_90', 'conceded_90'],
    # SECONDARY KPIs (30% weight) - Supporting attributes
    secondary_metrics=['pass_pct', 'interceptions_90'],
    thresholds={
        # Primary thresholds
        'xgp_90': {'good': 0.25, 'ok': 0, 'poor': -0.38},
        'conceded_90': {'good': 0.75, 'ok': 1.41, 'poor': 2.15},
        # Secondary thresholds
        'pass_pct': {'good': 97, 'ok': 78, 'poor': 47},
        'interceptions_90': {'good': 0.22, 'ok': 0.1, 'poor': 0.04}
    },
    interchangeable_with=[]
)

CB_STOPPER = RoleProfile(
    name='CB-STOPPER',
    display_name='Center-Back',
    primary_position='CB',
    description='Traditional Defender - tackling and aerial dominance',
    # PRIMARY KPIs (70% weight) - Core defensive duties
    primary_metrics=['header_win_pct', 'tackles_90', 'interceptions_90'],
    # SECONDARY KPIs (30% weight) - Supporting defensive attributes
    secondary_metrics=['blocks_90', 'clearances_90'],
    thresholds={
        # Primary thresholds
        'header_win_pct': {'good': 82, 'ok': 72, 'poor': 59},
        'tackles_90': {'good': 2.38, 'ok': 1.29, 'poor': 0.8},
        'interceptions_90': {'good': 3.18, 'ok': 2.15, 'poor': 1.36},
        # Secondary thresholds
        'blocks_90': {'good': 0.72, 'ok': 0.42, 'poor': 0.19},
        'clearances_90': {'good': 1.64, 'ok': 0.85, 'poor': 0.44}
    },
    interchangeable_with=['BCB']
)

BCB = RoleProfile(
    name='BCB',
    display_name='Ball-Playing Center-Back',
    primary_position='CB',
    description='Ball-Playing Center Back - distribution and possession',
    # PRIMARY KPIs (70% weight) - Key differentiators from CB-Stopper
    primary_metrics=['prog_passes_90', 'interceptions_90'],
    # SECONDARY KPIs (30% weight) - Supporting defensive attributes
    secondary_metrics=['tackles_90', 'clearances_90', 'blocks_90'],
    thresholds={
        # Primary thresholds
        'prog_passes_90': {'good': 6.9, 'ok': 4.52, 'poor': 3.17},
        'interceptions_90': {'good': 3, 'ok': 2.33, 'poor': 1.69},
        # Secondary thresholds
        'tackles_90': {'good': 2.36, 'ok': 1.24, 'poor': 0.88},
        'clearances_90': {'good': 0.89, 'ok': 0.64, 'poor': 0.39},
        'blocks_90': {'good': 0.63, 'ok': 0.34, 'poor': 0.16}
    },
    interchangeable_with=['CB-STOPPER', 'FB']
)

FB = RoleProfile(
    name='FB',
    display_name='Full-Back',
    primary_position='FB',
    description='Full Back - balanced defense and width',
    # PRIMARY KPIs (70% weight) - Core defensive duties
    primary_metrics=['tackles_90', 'interceptions_90', 'pressures_90'],
    # SECONDARY KPIs (30% weight) - Attacking contribution
    secondary_metrics=['crosses_90', 'prog_passes_90'],
    thresholds={
        # Primary thresholds
        'tackles_90': {'good': 3.66, 'ok': 2.75, 'poor': 1.44},
        'interceptions_90': {'good': 3.31, 'ok': 2.75, 'poor': 2},
        'pressures_90': {'good': 3.5, 'ok': 2.48, 'poor': 1.35},
        # Secondary thresholds
        'crosses_90': {'good': 0.47, 'ok': 0.14, 'poor': 0.03},
        'prog_passes_90': {'good': 8.59, 'ok': 6.13, 'poor': 4.14}
    },
    interchangeable_with=['WB', 'BCB']
)

WB = RoleProfile(
    name='WB',
    display_name='Wing-Back',
    primary_position='FB',
    description='Wing Back - attack, defense, and width',
    # PRIMARY KPIs (70% weight) - Attacking emphasis
    primary_metrics=['dribbles_90', 'crosses_90', 'pressures_90'],
    # SECONDARY KPIs (30% weight) - Defensive contribution
    secondary_metrics=['tackles_90', 'interceptions_90'],
    thresholds={
        # Primary thresholds
        'dribbles_90': {'good': 3.03, 'ok': 1.69, 'poor': 0.39},
        'crosses_90': {'good': 0.71, 'ok': 0.25, 'poor': 0.04},
        'pressures_90': {'good': 3.64, 'ok': 2.79, 'poor': 1.51},
        # Secondary thresholds
        'tackles_90': {'good': 3.88, 'ok': 2.89, 'poor': 1.57},
        'interceptions_90': {'good': 3.48, 'ok': 2.78, 'poor': 1.89}
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
    # PRIMARY KPIs (70% weight) - Core defensive duties
    primary_metrics=['tackles_90', 'interceptions_90', 'pressures_90'],
    # SECONDARY KPIs (30% weight) - Supporting attributes
    secondary_metrics=['pass_pct', 'blocks_90'],
    thresholds={
        # Primary thresholds
        'tackles_90': {'good': 3.01, 'ok': 2.16, 'poor': 1.17},
        'interceptions_90': {'good': 2.75, 'ok': 1.97, 'poor': 1.32},
        'pressures_90': {'good': 3.81, 'ok': 2.84, 'poor': 1.13},
        # Secondary thresholds
        'pass_pct': {'good': 94, 'ok': 90, 'poor': 86},
        'blocks_90': {'good': 0.75, 'ok': 0.41, 'poor': 0.2}
    },
    interchangeable_with=['MC']
)

MC = RoleProfile(
    name='MC',
    display_name='Central Midfielder',
    primary_position='CM',
    description='Midfielder Creator - playmaking focus',
    # PRIMARY KPIs (70% weight) - Creative output
    primary_metrics=['key_passes_90', 'prog_passes_90', 'xassists_90'],
    # SECONDARY KPIs (30% weight) - Supporting attributes
    secondary_metrics=['dribbles_90', 'pass_pct'],
    thresholds={
        # Primary thresholds
        'key_passes_90': {'good': 1.82, 'ok': 1.23, 'poor': 0.76},
        'prog_passes_90': {'good': 7.19, 'ok': 4.86, 'poor': 2.67},
        'xassists_90': {'good': 0.33, 'ok': 0.19, 'poor': 0.1},
        # Secondary thresholds
        'dribbles_90': {'good': 2.5, 'ok': 1.32, 'poor': 0.43},
        'pass_pct': {'good': 91, 'ok': 88, 'poor': 82}
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
    # PRIMARY KPIs (70% weight) - Creative output and ball-carrying
    primary_metrics=['key_passes_90', 'xassists_90', 'dribbles_90'],
    # SECONDARY KPIs (30% weight) - Passing and finishing
    secondary_metrics=['pass_pct', 'shots_on_target_90'],
    thresholds={
        # Primary thresholds
        'key_passes_90': {'good': 1.81, 'ok': 1.27, 'poor': 0.75},
        'xassists_90': {'good': 0.32, 'ok': 0.21, 'poor': 0.13},
        'dribbles_90': {'good': 3.7, 'ok': 1.85, 'poor': 0.89},
        # Secondary thresholds
        'pass_pct': {'good': 88, 'ok': 85, 'poor': 82},
        'shots_on_target_90': {'good': 1.1, 'ok': 0.71, 'poor': 0.37}
    },
    interchangeable_with=['MC', 'WAP', 'WAS']
)

WAP = RoleProfile(
    name='WAP',
    display_name='Winger',
    primary_position='W',
    description='Wide Attacker - Provider (crossing and creating)',
    # PRIMARY KPIs (70% weight) - Ball-carrying and width
    primary_metrics=['dribbles_90', 'crosses_90', 'sprints_90'],
    # SECONDARY KPIs (30% weight) - Creative output
    secondary_metrics=['key_passes_90', 'xassists_90'],
    thresholds={
        # Primary thresholds
        'dribbles_90': {'good': 4.69, 'ok': 2.4, 'poor': 1.05},
        'crosses_90': {'good': 0.66, 'ok': 0.33, 'poor': 0.1},
        'sprints_90': {'good': 18.03, 'ok': 14.19, 'poor': 8.57},
        # Secondary thresholds
        'key_passes_90': {'good': 1.94, 'ok': 1.15, 'poor': 0.59},
        'xassists_90': {'good': 0.36, 'ok': 0.19, 'poor': 0.1}
    },
    interchangeable_with=['WAS', 'AM(C)', 'WB']
)

WAS = RoleProfile(
    name='WAS',
    display_name='Inside Forward',
    primary_position='W',
    description='Wide Attacker - Striker (finishing focus)',
    # PRIMARY KPIs (70% weight) - Ball-carrying and shooting
    primary_metrics=['dribbles_90', 'shots_on_target_90', 'sprints_90'],
    # SECONDARY KPIs (30% weight) - Finishing quality
    secondary_metrics=['xg_90', 'conversion_pct'],
    thresholds={
        # Primary thresholds
        'dribbles_90': {'good': 4.6, 'ok': 3.01, 'poor': 1.5},
        'shots_on_target_90': {'good': 1.34, 'ok': 0.82, 'poor': 0.43},
        'sprints_90': {'good': 17.49, 'ok': 14.17, 'poor': 8.24},
        # Secondary thresholds
        'xg_90': {'good': 0.44, 'ok': 0.25, 'poor': 0.15},
        'conversion_pct': {'good': 28, 'ok': 16, 'poor': 7}
    },
    interchangeable_with=['WAP', 'ST-GS', 'AM(C)']
)

ST_PROVIDER = RoleProfile(
    name='ST-PROVIDER',
    display_name='Target Forward',
    primary_position='ST',
    description='Striker - Provider (target man and link play)',
    # PRIMARY KPIs (70% weight) - Hold-up play and creativity
    primary_metrics=['headers_won_90', 'xassists_90', 'xg_90'],
    # SECONDARY KPIs (30% weight) - Finishing
    secondary_metrics=['shots_on_target_90', 'conversion_pct'],
    thresholds={
        # Primary thresholds
        'headers_won_90': {'good': 3.98, 'ok': 1.95, 'poor': 0.67},
        'xassists_90': {'good': 0.25, 'ok': 0.14, 'poor': 0.08},
        'xg_90': {'good': 0.52, 'ok': 0.3, 'poor': 0.21},
        # Secondary thresholds
        'shots_on_target_90': {'good': 1.51, 'ok': 0.94, 'poor': 0.64},
        'conversion_pct': {'good': 30, 'ok': 20, 'poor': 13}
    },
    interchangeable_with=['ST-GS', 'AM(C)']
)

ST_GS = RoleProfile(
    name='ST-GS',
    display_name='Advanced Forward',
    primary_position='ST',
    description='Striker - Goalscorer (pure finisher)',
    # PRIMARY KPIs (70% weight) - Scoring threat
    primary_metrics=['headers_won_90', 'dribbles_90', 'xg_90'],
    # SECONDARY KPIs (30% weight) - Finishing efficiency
    secondary_metrics=['shots_on_target_90', 'conversion_pct'],
    thresholds={
        # Primary thresholds
        'headers_won_90': {'good': 5.08, 'ok': 2.76, 'poor': 1.03},
        'dribbles_90': {'good': 3.05, 'ok': 1.17, 'poor': 0.69},
        'xg_90': {'good': 0.5, 'ok': 0.35, 'poor': 0.22},
        # Secondary thresholds
        'shots_on_target_90': {'good': 1.57, 'ok': 1.09, 'poor': 0.73},
        'conversion_pct': {'good': 30, 'ok': 21, 'poor': 15}
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


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_role_definitions() -> List[str]:
    """
    Validates all role definitions for completeness and consistency.

    This function checks:
    1. All metrics (primary + secondary) have corresponding thresholds
    2. All thresholds have good/ok/poor values defined
    3. No duplicate metrics within a role (primary ∩ secondary = ∅)
    4. Threshold ordering is valid (for normal and inverse metrics)

    Returns:
        List of validation warnings/errors. Empty list if all validations pass.

    Example:
        >>> issues = validate_role_definitions()
        >>> if issues:
        ...     for issue in issues:
        ...         print(f"⚠️  {issue}")
        ... else:
        ...     print("✅ All role definitions valid")
    """
    issues = []

    # Inverse metrics (lower is better)
    INVERSE_METRICS = {'conceded_90'}

    for role_name, role in ROLES.items():
        # Check 1: All metrics have thresholds
        all_metrics = role.primary_metrics + role.secondary_metrics
        for metric in all_metrics:
            if metric not in role.thresholds:
                issues.append(f"{role_name}: Missing threshold for '{metric}'")
            else:
                # Check 2: All thresholds have good/ok/poor
                thresholds = role.thresholds[metric]
                if not all(k in thresholds for k in ['good', 'ok', 'poor']):
                    issues.append(
                        f"{role_name}: Incomplete threshold for '{metric}' "
                        f"(needs good/ok/poor, has {list(thresholds.keys())})"
                    )
                else:
                    # Check 4: Threshold ordering
                    good = thresholds['good']
                    ok = thresholds['ok']
                    poor = thresholds['poor']

                    if metric in INVERSE_METRICS:
                        # For inverse metrics: good < ok < poor (lower is better)
                        if not (good < ok < poor):
                            issues.append(
                                f"{role_name}: Invalid threshold ordering for inverse metric '{metric}' "
                                f"(expected good < ok < poor, got {good} / {ok} / {poor})"
                            )
                    else:
                        # For normal metrics: poor < ok < good (higher is better)
                        if not (poor < ok < good):
                            issues.append(
                                f"{role_name}: Invalid threshold ordering for '{metric}' "
                                f"(expected poor < ok < good, got {poor} / {ok} / {good})"
                            )

        # Check 3: No duplicate metrics
        primary_set = set(role.primary_metrics)
        secondary_set = set(role.secondary_metrics)
        overlap = primary_set & secondary_set
        if overlap:
            issues.append(
                f"{role_name}: Duplicate metrics in primary and secondary lists: {overlap}"
            )

        # Check for metrics with no thresholds (orphaned thresholds)
        for metric in role.thresholds:
            if metric not in all_metrics:
                issues.append(
                    f"{role_name}: Orphaned threshold for '{metric}' "
                    f"(not in primary_metrics or secondary_metrics)"
                )

    return issues
