#!/usr/bin/env python
"""
Squad Audit Demo Script

This script demonstrates the squad audit functionality by parsing an FM HTML
export file and displaying the analysis results.

Usage:
    python demo_squad_audit.py <path_to_html_file>

Example:
    python demo_squad_audit.py test_file_3.html
"""

import sys
from pathlib import Path
from services.fm_parser import FMHTMLParser
from services.squad_audit_service import SquadAuditService


def format_table_row(columns, widths):
    """Format a table row with fixed column widths."""
    row = " | ".join(str(col).ljust(width) for col, width in zip(columns, widths))
    return row


def print_separator(widths):
    """Print a table separator line."""
    print("-+-".join("-" * width for width in widths))


def main():
    """Main demo function."""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python demo_squad_audit.py <path_to_html_file>")
        print("\nExample:")
        print("    python demo_squad_audit.py test_file_3.html")
        sys.exit(1)

    html_file = Path(sys.argv[1])

    # Check if file exists
    if not html_file.exists():
        print(f"Error: File '{html_file}' not found")
        sys.exit(1)

    print("=" * 120)
    print(" " * 35 + "SQUAD AUDIT TRACKER - DEMO")
    print("=" * 120)
    print()

    # Read HTML file
    print(f"📄 Reading HTML file: {html_file}")
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Parse HTML
    print("🔍 Parsing squad data...")
    try:
        parser = FMHTMLParser()
        squad = parser.parse_html(html_content)
        print(f"✓ Successfully parsed {len(squad.players)} players")
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        sys.exit(1)

    print()

    # Analyze squad
    print("📊 Analyzing squad performance...")
    try:
        service = SquadAuditService()
        result = service.analyze_squad(squad)
        print(f"✓ Analysis complete")
    except Exception as e:
        print(f"Error analyzing squad: {e}")
        sys.exit(1)

    print()
    print("=" * 120)

    # Display results
    print("\n📈 SQUAD ANALYSIS RESULTS")
    print(f"   Total Players: {result.total_players}")
    print(f"   Average Wage: £{result.squad_avg_wage:,.0f} p/w")
    print()

    # Sort by value score (descending)
    sorted_analyses = result.get_sorted_by_value()

    # Define column widths
    widths = [25, 4, 4, 8, 8, 6, 50]
    headers = ["Name", "Pos", "Age", "Value", "Perf", "Flag", "Recommendation"]

    print("TOP PERFORMERS BY VALUE SCORE:")
    print()
    print(format_table_row(headers, widths))
    print_separator(widths)

    # Display top 15 players
    for analysis in sorted_analyses[:15]:
        player = analysis.player
        columns = [
            player.name[:24],  # Truncate long names
            player.get_position_category().value,
            str(player.age),
            f"{analysis.value_score:.1f}",
            analysis.verdict.value[:8],  # Truncate if needed
            player.inf if player.inf else "-",
            analysis.recommendation[:49]  # Truncate long recommendations
        ]
        print(format_table_row(columns, widths))

    print()
    print("=" * 120)

    # Show elite players
    elite = result.get_elite_players()
    print(f"\n⭐ ELITE PERFORMERS: {len(elite)} players")
    if elite:
        for analysis in elite[:5]:  # Show top 5
            player = analysis.player
            metrics = " | ".join(analysis.top_metrics) if analysis.top_metrics else "N/A"
            print(f"   • {player.name} ({player.get_position_category().value}, {player.age})")
            print(f"     Value: {analysis.value_score:.1f} | Performance: {analysis.performance_index:.1f}")
            print(f"     Top Metrics: {metrics}")
            print(f"     → {analysis.recommendation}")
            print()

    # Show poor performers
    poor = result.get_poor_performers()
    if poor:
        print(f"\n⚠️  POOR PERFORMERS: {len(poor)} players")
        for analysis in poor[:3]:  # Show worst 3
            player = analysis.player
            print(f"   • {player.name} ({player.get_position_category().value}, {player.age})")
            print(f"     Value: {analysis.value_score:.1f} | Performance: {analysis.performance_index:.1f}")
            print(f"     → {analysis.recommendation}")
            print()

    # Show transfer-listed elite players
    transfer_elite = result.get_transfer_listed_elite()
    if transfer_elite:
        print(f"\n🚨 ELITE PLAYERS ON TRANSFER LIST: {len(transfer_elite)}")
        for analysis in transfer_elite:
            player = analysis.player
            print(f"   • {player.name} ({player.get_position_category().value}, {player.age})")
            print(f"     Value: {analysis.value_score:.1f} | Performance: {analysis.performance_index:.1f}")
            print(f"     → {analysis.recommendation}")
            print()

    print("=" * 120)
    print("\n✓ Analysis complete!")
    print()

    # Offer CSV export
    print("To export to CSV, you can use:")
    print(f"    csv_data = service.export_to_csv_data(result)")
    print()


if __name__ == "__main__":
    main()
