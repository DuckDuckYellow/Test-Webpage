"""
Service for evaluating player positions, metrics, and roles.
"""

from typing import List, Dict, Optional, Any
from models.squad_audit import Player
from models.constants import PositionCategory, POSITION_METRICS

class PlayerEvaluatorService:
    """Handles business logic for player evaluation."""

    def __init__(self):
        pass

    def get_position_category(self, player: Player) -> PositionCategory:
        """
        Determine the best-fit position category for the player.
        """
        position_strings = [p.strip() for p in player.position.split(',')]
        possible_positions = []
        for pos_str in position_strings:
            try:
                pos_cat = self._parse_position_string(pos_str)
                if pos_cat not in possible_positions:
                    possible_positions.append(pos_cat)
            except:
                continue

        if not possible_positions:
            pos = player.position_selected.upper()
            if pos == "GK": return PositionCategory.GK
            elif pos in ["DCR", "DCL", "DC"]: return PositionCategory.CB
            elif pos in ["DR", "DL"] or "WB" in pos: return PositionCategory.FB
            elif "DM" in pos: return PositionCategory.DM
            elif pos in ["MCR", "MCL", "MC"]: return PositionCategory.CM
            elif pos in ["AMR", "AML", "AM"] or "AM" in pos: return PositionCategory.AM
            elif "W" in pos and "WB" not in pos: return PositionCategory.W
            elif pos in ["STC", "ST"] or "ST" in pos: return PositionCategory.ST
            else: return PositionCategory.CM

        if len(possible_positions) == 1:
            return possible_positions[0]

        best_position = possible_positions[0]
        best_score = self._evaluate_position_fit(player, best_position)

        for position in possible_positions[1:]:
            score = self._evaluate_position_fit(player, position)
            if score > best_score:
                best_score = score
                best_position = position

        return best_position

    def get_all_possible_positions(self, player: Player) -> List[PositionCategory]:
        """
        Get all possible position categories this player can play.
        """
        position_strings = [p.strip() for p in player.position.split(',')]
        possible_positions = []
        for pos_str in position_strings:
            try:
                pos_cat = self._parse_position_string(pos_str)
                if pos_cat not in possible_positions:
                    possible_positions.append(pos_cat)
            except:
                continue

        if not possible_positions:
            possible_positions.append(self.get_position_category(player))

        return possible_positions

    def get_normalized_metrics(self, player: Player) -> Dict[str, float]:
        """
        Get standardized metric dictionary for role evaluation.
        """
        metrics = {}
        metrics['tackles_90'] = player.tck_90 or player.k_tck_90 or 0.0
        metrics['headers_won_90'] = player.hdrs_w_90 or 0.0
        metrics['header_win_pct'] = player.hdr_pct or 0.0
        metrics['clearances_90'] = player.clr_90 or 0.0
        metrics['interceptions_90'] = player.int_90 or 0.0
        metrics['blocks_90'] = player.shts_blckd_90 or player.blk_90 or 0.0
        metrics['prog_passes_90'] = player.pr_passes_90 or 0.0
        metrics['pressures_90'] = player.pres_c_90 or 0.0
        metrics['dribbles_90'] = player.drb_90 or 0.0
        metrics['key_passes_90'] = player.op_kp_90 or player.ch_c_90 or 0.0
        metrics['xassists_90'] = player.xa_90 or 0.0
        metrics['crosses_90'] = player.op_crs_c_90 or 0.0
        metrics['sprints_90'] = player.sprints_90 or 0.0
        metrics['shots_on_target_90'] = player.sht_90 or player.shot_90 or 0.0
        metrics['xg_90'] = player.np_xg_90 or player.xg or 0.0
        metrics['conversion_pct'] = player.conv_pct or 0.0
        metrics['pass_pct'] = player.pas_pct or 0.0
        metrics['xgp_90'] = player.xgp_90 or player.xgp or 0.0
        metrics['conceded_90'] = player.con_90 or 0.0
        metrics['save_pct'] = player.sv_pct or 0.0
        return metrics

    def _parse_position_string(self, pos_str: str) -> PositionCategory:
        pos = pos_str.upper().strip()
        if pos.startswith("GK"): return PositionCategory.GK
        if any(x in pos for x in ["DC", "D (C)"]): return PositionCategory.CB
        if any(x in pos for x in ["DR", "DL", "D/WB", "WB"]) and "DM" not in pos: return PositionCategory.FB
        if "DM" in pos: return PositionCategory.DM
        if any(x in pos for x in ["MC", "M (C)"]): return PositionCategory.CM
        if "AM" in pos: return PositionCategory.AM
        if "W" in pos and "WB" not in pos and "DM" not in pos: return PositionCategory.W
        if any(x in pos for x in ["ST", "S (C)"]): return PositionCategory.ST
        if pos.startswith("D"): return PositionCategory.CB
        elif pos.startswith("M"): return PositionCategory.CM
        elif pos.startswith("S"): return PositionCategory.ST
        else: return PositionCategory.CM

    def _evaluate_position_fit(self, player: Player, position_cat: PositionCategory) -> float:
        metrics = POSITION_METRICS.get(position_cat, [])
        score = 0.0
        count = 0
        for metric in metrics:
            value = getattr(player, metric, None)
            if value is not None and value > 0:
                score += value
                count += 1
        return score / count if count > 0 else 0.0

    def evaluate_roles(self, player: Player):
        """
        Evaluate and store all role scores.
        """
        from analyzers.role_recommendation_engine import RoleRecommendationEngine
        engine = RoleRecommendationEngine()

        # Get the actual roles this player can play based on their position string
        # This is more specific than just position categories (e.g., distinguishes AM(C) vs WAP/WAS)
        playable_roles = engine._map_position_to_roles(player.position)

        # Also get position categories for backwards compatibility with formation suggestions
        positions = self.get_all_possible_positions(player)

        # Evaluate only roles the player can actually play
        if playable_roles:
            from models.role_definitions import ROLES
            player.all_role_scores = []
            for role_name in playable_roles:
                if role_name in ROLES:
                    role_profile = ROLES[role_name]
                    score = engine.evaluator.evaluate_player_for_role(player, role_profile)
                    player.all_role_scores.append(score)
            # Sort by overall score
            player.all_role_scores.sort(key=lambda s: s.overall_score, reverse=True)
        else:
            # Fallback: evaluate all roles
            player.all_role_scores = engine.evaluate_all_roles(player)

        if not player.all_role_scores:
            player.all_role_scores = engine.evaluate_all_roles(player)

        player.best_role = player.all_role_scores[0]
        player.current_role_score = engine.get_best_role_in_current_position(player, player.all_role_scores)

        recommendations = engine.get_role_recommendations(player)
        if recommendations:
            top_rec = recommendations[0]
            player.recommended_role = top_rec
            player.role_change_confidence = top_rec.overall_score
            compare_to = player.current_role_score if player.current_role_score else player.best_role
            player.role_change_reason = engine.evaluator.generate_role_recommendation_text(top_rec, compare_to)
