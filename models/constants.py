"""
Centralized constants and metrics for Squad Audit.
"""

from enum import Enum

class PositionCategory(Enum):
    GK = "GK"
    CB = "CB"
    FB = "FB"
    DM = "DM"
    CM = "CM"
    AM = "AM"
    W = "W"
    ST = "ST"

# Position-specific metrics configuration
# Each position uses specific key metrics for evaluation
POSITION_METRICS = {
    PositionCategory.GK: ["sv_pct", "xgp", "pas_pct", "av_rat"],
    PositionCategory.CB: ["k_tck_90", "int_90", "hdr_pct", "pas_pct"],
    PositionCategory.FB: ["k_tck_90", "drb_90", "pas_pct", "blk_90"],
    PositionCategory.DM: ["k_tck_90", "int_90", "pas_pct", "av_rat"],
    PositionCategory.CM: ["pas_pct", "k_tck_90", "drb_90", "shot_90"],
    PositionCategory.AM: ["ch_c_90", "drb_90", "xg", "pas_pct"],
    PositionCategory.W: ["drb_90", "ch_c_90", "shot_90", "pas_pct"],
    PositionCategory.ST: ["shot_90", "xg", "ch_c_90", "av_rat"]
}

# Metric display names for readable output
METRIC_NAMES = {
    # Goalkeeper metrics
    "sv_pct": "Save %",
    "save_pct": "Save %",
    "xgp": "xG Prevented",
    "xgp_90": "xG Prevented/90",
    "conceded_90": "Conceded/90",

    # Passing metrics
    "pas_pct": "Pass %",
    "pass_pct": "Pass %",
    "prog_passes_90": "Prog Passes/90",

    # Defensive metrics
    "k_tck_90": "Key Tackles/90",
    "tck_90": "Tackles/90",
    "tackles_90": "Tackles/90",
    "int_90": "Int/90",
    "interceptions_90": "Int/90",
    "hdr_pct": "Header %",
    "header_win_pct": "Header Win %",
    "headers_won_90": "Headers Won/90",
    "hdrs_w_90": "Headers Won/90",
    "blk_90": "Blocks/90",
    "blocks_90": "Blocks/90",
    "shts_blckd_90": "Shots Blocked/90",
    "clr_90": "Clearances/90",
    "clearances_90": "Clearances/90",
    "pres_c_90": "Pressures/90",
    "pressures_90": "Pressures/90",

    # Attacking metrics
    "drb_90": "Dribbles/90",
    "dribbles_90": "Dribbles/90",
    "shot_90": "Shots/90",
    "sht_90": "Shots/90",
    "shots_on_target_90": "Shots on Target/90",
    "ch_c_90": "Chances Created/90",
    "key_passes_90": "Key Passes/90",
    "op_kp_90": "Key Passes/90",
    "xg": "xG",
    "xg_90": "xG/90",
    "np_xg_90": "npxG/90",
    "xa_90": "xA/90",
    "xassists_90": "xA/90",
    "conv_pct": "Conversion %",
    "conversion_pct": "Conversion %",
    "op_crs_c_90": "Crosses/90",
    "crosses_90": "Crosses/90",
    "sprints_90": "Sprints/90",

    # General metrics
    "av_rat": "Avg Rating"
}
