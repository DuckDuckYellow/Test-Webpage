#!/usr/bin/env python3
"""
Generate league baseline data from FM wage export.

Usage:
    python scripts/generate_league_baselines.py wage_player_export.html

Optional: Add GK-specific data from top 5 leagues:
    python scripts/generate_league_baselines.py wage_player_export.html gk_top5_export.html
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.league_baseline_generator import LeagueBaselineGenerator


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_league_baselines.py <wage_export.html> [gk_top5_export.html]")
        sys.exit(1)

    input_file = sys.argv[1]
    gk_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = os.path.join(project_root, 'data', 'league_baselines.json')

    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"Processing wage export: {input_file}")

    # Read main wage export file
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    generator = LeagueBaselineGenerator()
    print("Parsing player data...")
    player_data = generator.parse_wage_export_html(html_content)
    print(f"Parsed {len(player_data)} players")

    # Add GK data if provided
    if gk_file:
        print(f"\nProcessing GK data from: {gk_file}")
        with open(gk_file, 'r', encoding='utf-8') as f:
            gk_html = f.read()
        gk_data = generator.parse_wage_export_html(gk_html)
        player_data.extend(gk_data)
        print(f"Added {len(gk_data)} GK records")

    # Generate baselines
    print("\nGenerating baselines...")
    baselines = generator.generate_baselines(player_data)

    # Export to JSON
    generator.export_to_json(baselines, output_file)

    # Print summary
    print(f"\n{'='*60}")
    print("BASELINE GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total Baselines: {len(baselines.baselines)}")
    print(f"GK Wage Multiplier: {baselines.gk_wage_multiplier:.3f}")
    print(f"Divisions Covered: {len(baselines.get_available_divisions())}")
    print(f"\nDivisions: {', '.join(baselines.get_available_divisions()[:10])}")
    if len(baselines.get_available_divisions()) > 10:
        print(f"  ... and {len(baselines.get_available_divisions()) - 10} more")
    print(f"\nOutput: {output_file}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
