from typing import List, Optional, Dict
from models.squad_audit import Player
from models.role_definitions import ROLES, RoleProfile
from analyzers.role_evaluator import RoleEvaluator, RoleScore

class RoleChangeDetector:
    """Specific logic for detecting when role change is warranted."""
    
    def should_change_role(self, player: Player, current_role: RoleScore, alternative_role: RoleScore) -> bool:
        """
        Determine if an alternative role should be recommended over the current role.
        """
        # Generic checks first
        if alternative_role.overall_score < 65:
            return False
            
        # Specific detection logic based on role pairs
        method_name = f"detect_{current_role.role.lower().replace('-', '_').replace('(', '').replace(')', '')}_to_{alternative_role.role.lower().replace('-', '_').replace('(', '').replace(')', '')}"
        
        if hasattr(self, method_name):
            return getattr(self, method_name)(player, current_role, alternative_role)
            
        # Fallback to generic compatibility check
        if self._are_positions_compatible(current_role.role, alternative_role.role):
            # If compatible, recommend if score is significantly higher
            return alternative_role.overall_score > current_role.overall_score + 10
            
        return False

    def _are_positions_compatible(self, role1, role2) -> bool:
        role1_profile = ROLES[role1]
        role2_profile = ROLES[role2]
        return role2 in role1_profile.interchangeable_with or role1 in role2_profile.interchangeable_with

    def _get_metric(self, player, metric_name, default=0.0):
        from services.player_evaluator_service import PlayerEvaluatorService
        evaluator_service = PlayerEvaluatorService()
        metrics = evaluator_service.get_normalized_metrics(player)
        return metrics.get(metric_name, default)

    def detect_cb_stopper_to_bcb(self, player, current, alt) -> bool:
        """
        CB-STOPPER -> BCB if:
        - Progressive Passes/90 > 5.5 (elite ball player)
        - AND Tackles/90 still > 1.5 (maintains defense)
        - AND Pass % > 90% (technical ability)
        """
        prog_passes = self._get_metric(player, 'prog_passes_90')
        tackles = self._get_metric(player, 'tackles_90')
        pass_pct = self._get_metric(player, 'pass_pct')
        
        if prog_passes > 5.5 and tackles > 1.5 and pass_pct > 90:
            return True
            
        # Fallback to score comparison if specific metrics fail but score is WAY higher
        return alt.overall_score > current.overall_score + 12

    def detect_fb_to_wb(self, player, current, alt) -> bool:
        """
        FB -> WB if:
        - Dribbles/90 > 3.0 (elite dribbler)
        - AND Crosses/90 still > 0.3 (maintains delivery)
        - AND Sprints/90 > 14 (high intensity)
        """
        dribbles = self._get_metric(player, 'dribbles_90')
        crosses = self._get_metric(player, 'crosses_90')
        sprints = self._get_metric(player, 'sprints_90')
        
        if dribbles > 3.0 and crosses > 0.3 and sprints > 14:
            return True
            
        return alt.overall_score > current.overall_score + 12

    def detect_md_to_mc(self, player, current, alt) -> bool:
        """
        MD (Destroyer) -> MC (Creator) if:
        - Key Passes/90 > 1.5 (creative threat)
        - AND Tackles/90 still > 1.5 (not pure attacker)
        - AND Progressive Passes/90 > 5 (playmaker skill)
        """
        key_passes = self._get_metric(player, 'key_passes_90')
        tackles = self._get_metric(player, 'tackles_90')
        prog_passes = self._get_metric(player, 'prog_passes_90')
        
        if key_passes > 1.5 and tackles > 1.5 and prog_passes > 5:
            return True
            
        return alt.overall_score > current.overall_score + 12

    def detect_amc_to_wap(self, player, current, alt) -> bool:
        """
        AM(C) -> WAP if:
        - Dribbles/90 > 3.5 (elite dribbler)
        - AND Crosses/90 > 0.4 (wide play)
        """
        dribbles = self._get_metric(player, 'dribbles_90')
        crosses = self._get_metric(player, 'crosses_90')
        
        if dribbles > 3.5 and crosses > 0.4:
            return True
            
        return alt.overall_score > current.overall_score + 12

    def detect_amc_to_was(self, player, current, alt) -> bool:
        """
        AM(C) -> WAS if:
        - Shots on Target/90 > 1.0 (clinical finisher)
        - AND xG/90 > 0.35 (elite output)
        - AND Conversion Rate > 25%
        """
        shots = self._get_metric(player, 'shots_on_target_90')
        xg = self._get_metric(player, 'xg_90')
        conv = self._get_metric(player, 'conversion_pct')
        
        if shots > 1.0 and xg > 0.35 and conv > 25:
            return True
            
        return alt.overall_score > current.overall_score + 12


class RoleRecommendationEngine:
    """Evaluates player against all roles and recommends best fit."""

    def __init__(self):
        self.evaluator = RoleEvaluator()
        self.detector = RoleChangeDetector()

    def evaluate_all_roles(self, player: Player, allowed_positions: Optional[List[str]] = None) -> List[RoleScore]:
        return self.evaluator.evaluate_all_roles(player, allowed_positions=allowed_positions)
    
    def get_best_role(self, player: Player) -> RoleScore:
        return self.evaluator.get_best_role(player)
        
    def get_current_roles(self, player: Player) -> List[RoleScore]:
        """
        Get role scores for roles matching the player's current position.
        """
        valid_roles = self._map_position_to_roles(player.position)
        all_scores = self.evaluate_all_roles(player)
        return [s for s in all_scores if s.role in valid_roles]

    def _map_position_to_roles(self, position_str: str) -> List[str]:
        """Map FM position string to potential roles."""
        roles = []
        pos = position_str.upper()
        
        if 'GK' in pos:
            roles.append('GK')
            
        if any(x in pos for x in ['D (C)', 'D(C)', 'DC']):
            roles.extend(['CB-STOPPER', 'BCB'])
            
        if any(x in pos for x in ['D (R)', 'D (L)', 'D(R)', 'D(L)', 'WB']):
            if 'DM' not in pos: # Avoid confusion with DM
                 roles.extend(['FB', 'WB'])
            
        if 'DM' in pos:
            roles.append('MD')
            
        if any(x in pos for x in ['M (C)', 'M(C)', 'MC']):
            roles.extend(['MD', 'MC'])
            
        if any(x in pos for x in ['AM (C)', 'AM(C)', 'AMC']):
            roles.append('AM(C)')
            
        if any(x in pos for x in ['M (R)', 'M (L)', 'AM (R)', 'AM (L)', 'MR', 'ML', 'AMR', 'AML']):
            roles.extend(['WAP', 'WAS'])
            
        if any(x in pos for x in ['ST', 'S (C)']):
            roles.extend(['ST-PROVIDER', 'ST-GS'])
            
        return list(set(roles))

    def get_best_role_in_current_position(self, player: Player, all_scores: List[RoleScore] = None) -> Optional[RoleScore]:
        """
        Get the highest scoring role that matches player's "natural" position.
        """
        if not all_scores:
            all_scores = self.evaluate_all_roles(player)
            
        valid_roles = self._map_position_to_roles(player.position)
        if not valid_roles:
            return None
            
        valid_scores = [s for s in all_scores if s.role in valid_roles]
        if not valid_scores:
            return None
            
        return max(valid_scores, key=lambda s: s.overall_score)

    def get_role_recommendations(self, player: Player) -> List[RoleScore]:
        """
        Get sophisticated role recommendations using specific intelligence rules.
        """
        all_scores = self.evaluate_all_roles(player)
        current_best_role = self.get_best_role_in_current_position(player, all_scores)
        
        # Fallback if we can't determine current role
        if not current_best_role:
             return self.evaluator.get_role_recommendations(player)

        recommendations = []
        valid_role_names = self._map_position_to_roles(player.position)
        
        for score in all_scores:
            if score.role in valid_role_names:
                continue # Skip roles they already play
                
            # Check logic
            if self.detector.should_change_role(player, current_best_role, score):
                recommendations.append(score)
                
        # Sort by score difference
        recommendations.sort(key=lambda x: x.overall_score - current_best_role.overall_score, reverse=True)
        return recommendations
