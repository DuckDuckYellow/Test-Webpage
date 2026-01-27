"""
Recommendation Engine - Rule-based system for player recommendations.

Replaces nested conditionals with clear, testable rules.
"""

from typing import Optional, List, Callable
from datetime import date, datetime
from dataclasses import dataclass
from models.squad_audit import Player, Recommendation, StatusFlag


@dataclass
class RecommendationContext:
    """Context object containing all data needed for recommendation."""
    player: Player
    value_score: float
    is_projected: bool
    game_date: Optional[date]
    contract_warning: bool


class RecommendationRule:
    """Base class for recommendation rules."""

    def __init__(self, name: str, condition: Callable[[RecommendationContext], bool],
                 recommendation_fn: Callable[[RecommendationContext], Recommendation]):
        self.name = name
        self.condition = condition
        self.recommendation_fn = recommendation_fn

    def applies(self, context: RecommendationContext) -> bool:
        """Check if this rule applies to the given context."""
        return self.condition(context)

    def generate(self, context: RecommendationContext) -> Recommendation:
        """Generate recommendation for this rule."""
        return self.recommendation_fn(context)


class RecommendationEngine:
    """
    Rule-based recommendation engine.

    Evaluates rules in order and returns the first matching recommendation.
    Much easier to test and maintain than nested conditionals.
    """

    def __init__(self):
        self.rules: List[RecommendationRule] = self._initialize_rules()

    def _initialize_rules(self) -> List[RecommendationRule]:
        """Initialize recommendation rules in priority order."""
        return [
            # Rule 1: Insufficient data (<200 mins)
            RecommendationRule(
                name="insufficient_data",
                condition=lambda ctx: ctx.player.mins is not None and ctx.player.mins < 200,
                recommendation_fn=lambda ctx: Recommendation(
                    badge="LOW DATA",
                    icon="",
                    color="secondary",
                    explanation=f"Insufficient data ({ctx.player.mins} mins played)",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 2: Projected stats (200-500 mins)
            RecommendationRule(
                name="projected_stats",
                condition=lambda ctx: ctx.player.mins is not None and 200 <= ctx.player.mins < 500,
                recommendation_fn=lambda ctx: Recommendation(
                    badge="LOW DATA",
                    icon="",
                    color="secondary",
                    explanation=f"Projected stats only ({ctx.player.mins} mins played)",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 3: Elite but overpaid
            RecommendationRule(
                name="elite_overpaid",
                condition=lambda ctx: (ctx.value_score < 50
                                      and ctx.player.best_role
                                      and ctx.player.best_role.tier == 'ELITE'),
                recommendation_fn=lambda ctx: Recommendation(
                    badge="WAGE CUT",
                    icon="",
                    color="warning",
                    explanation="Elite performance but overpaid",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 4: Poor value (not elite)
            RecommendationRule(
                name="poor_value",
                condition=lambda ctx: ctx.value_score < 50,
                recommendation_fn=lambda ctx: Recommendation(
                    badge="CONSIDER SALE",
                    icon="",
                    color="danger",
                    explanation="Poor value for wage cost",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 5: Elite on transfer list
            RecommendationRule(
                name="elite_transfer_listed",
                condition=lambda ctx: (ctx.player.best_role
                                      and ctx.player.best_role.tier == 'ELITE'
                                      and ctx.player.get_status_flag() == StatusFlag.TRANSFER_LISTED),
                recommendation_fn=lambda ctx: Recommendation(
                    badge="KEEP & PLAY",
                    icon="",
                    color="success",
                    explanation="Elite ratings despite transfer list",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 6: Elite U21 talent
            RecommendationRule(
                name="elite_u21",
                condition=lambda ctx: (ctx.player.best_role
                                      and ctx.player.best_role.tier == 'ELITE'
                                      and ctx.player.get_status_flag() == StatusFlag.U21),
                recommendation_fn=lambda ctx: Recommendation(
                    badge="PROMOTE",
                    icon="",
                    color="info",
                    explanation="Elite young talent",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 7: Elite low apps
            RecommendationRule(
                name="elite_low_apps",
                condition=lambda ctx: (ctx.player.best_role
                                      and ctx.player.best_role.tier == 'ELITE'
                                      and ctx.player.apps < 10),
                recommendation_fn=lambda ctx: Recommendation(
                    badge="INCREASE MINS",
                    icon="",
                    color="info",
                    explanation="Elite output per 90",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 8: Elite core starter
            RecommendationRule(
                name="elite_core",
                condition=lambda ctx: ctx.player.best_role and ctx.player.best_role.tier == 'ELITE',
                recommendation_fn=lambda ctx: Recommendation(
                    badge="CORE STARTER",
                    icon="",
                    color="success",
                    explanation="Elite performance",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 9: Good on transfer list
            RecommendationRule(
                name="good_transfer_listed",
                condition=lambda ctx: (ctx.player.best_role
                                      and ctx.player.best_role.tier == 'GOOD'
                                      and ctx.player.get_status_flag() == StatusFlag.TRANSFER_LISTED),
                recommendation_fn=lambda ctx: Recommendation(
                    badge="EVALUATE",
                    icon="",
                    color="warning",
                    explanation="Good depth option on transfer list",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 10: Good backup
            RecommendationRule(
                name="good_backup",
                condition=lambda ctx: ctx.player.best_role and ctx.player.best_role.tier == 'GOOD',
                recommendation_fn=lambda ctx: Recommendation(
                    badge="BACKUP",
                    icon="",
                    color="secondary",
                    explanation="Solid rotation option",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 11: Poor U21 development
            RecommendationRule(
                name="poor_u21",
                condition=lambda ctx: (ctx.player.best_role
                                      and ctx.player.best_role.tier == 'POOR'
                                      and ctx.player.get_status_flag() == StatusFlag.U21),
                recommendation_fn=lambda ctx: Recommendation(
                    badge="DEVELOP",
                    icon="",
                    color="warning",
                    explanation="Not ready yet",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 12: Poor sell/replace
            RecommendationRule(
                name="poor_sell",
                condition=lambda ctx: ctx.player.best_role and ctx.player.best_role.tier == 'POOR',
                recommendation_fn=lambda ctx: Recommendation(
                    badge="SELL/REPLACE",
                    icon="",
                    color="danger",
                    explanation="Below standard",
                    has_contract_warning=ctx.contract_warning
                )
            ),

            # Rule 13: Default (Average tier)
            RecommendationRule(
                name="average_backup",
                condition=lambda ctx: True,  # Catch-all
                recommendation_fn=lambda ctx: Recommendation(
                    badge="BACKUP",
                    icon="",
                    color="secondary",
                    explanation="Average performance",
                    has_contract_warning=ctx.contract_warning
                )
            ),
        ]

    def generate_recommendation(
        self,
        player: Player,
        value_score: float,
        is_projected: bool = False,
        game_date: Optional[date] = None
    ) -> Recommendation:
        """
        Generate recommendation using rule-based system.

        Evaluates rules in order and returns first match.
        Much clearer than nested conditionals.
        """
        # Check contract warning
        contract_warning = self._check_contract_expiring_soon(player, game_date)

        # Create context
        context = RecommendationContext(
            player=player,
            value_score=value_score,
            is_projected=is_projected,
            game_date=game_date,
            contract_warning=contract_warning
        )

        # Evaluate rules in order
        for rule in self.rules:
            if rule.applies(context):
                return rule.generate(context)

        # Should never reach here due to catch-all rule
        return Recommendation(
            badge="UNKNOWN",
            icon="",
            color="secondary",
            explanation="Unable to classify",
            has_contract_warning=contract_warning
        )

    def _check_contract_expiring_soon(self, player: Player, game_date: Optional[date] = None) -> bool:
        """Check if Elite/Good player has <6 months on contract."""
        if not player.best_role or player.best_role.tier not in ['ELITE', 'GOOD']:
            return False

        if not player.expires or player.expires == "-":
            return False

        try:
            expiry_date = datetime.strptime(player.expires, "%d/%m/%Y").date()
            today = game_date if game_date else datetime.now().date()
            months_remaining = (expiry_date.year - today.year) * 12 + (expiry_date.month - today.month)
            return months_remaining < 6
        except (ValueError, TypeError) as e:
            # Log but don't crash
            import logging
            logging.getLogger(__name__).debug(
                f"Failed to check contract expiry for '{player.name}': {e}"
            )
            return False
