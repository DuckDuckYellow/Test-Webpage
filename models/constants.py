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
    "sv_pct": "Save %",
    "xgp": "xG Prevented",
    "pas_pct": "Pass %",
    "av_rat": "Avg Rating",
    "k_tck_90": "Key Tackles/90",
    "int_90": "Int/90",
    "hdr_pct": "Header %",
    "drb_90": "Dribbles/90",
    "blk_90": "Blocks/90",
    "shot_90": "Shots/90",
    "ch_c_90": "Chances Created/90",
    "xg": "xG"
}
