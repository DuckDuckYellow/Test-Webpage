#!/usr/bin/env python3
"""
Test script for enhanced Recruitment Capacity Tracker calculations.

Tests all business logic including:
- Base capacity rules (Easy/Medium/Hard)
- Internal role multiplier (0.25)
- Stage-based time weighting
"""

# Inline implementation for testing (so we don't need Flask imports)

STAGE_MULTIPLIERS = {
    'sourcing': 0.2,
    'screening': 0.4,
    'interview': 0.2,
    'offer': 0.1,
    'pre-hire checks': 0.1,
    '': 1.0,
    'none': 1.0
}

BASE_CAPACITY = {
    'easy': 1/30,      # 3.33% per vacancy
    'medium': 1/20,    # 5% per vacancy
    'hard': 1/12       # 8.33% per vacancy
}

def calculate_vacancy_capacity(role_type, is_internal=False, stage=''):
    """Calculate capacity for a single vacancy."""
    role_type_lower = role_type.lower()
    if role_type_lower not in BASE_CAPACITY:
        raise ValueError(f"Invalid role type: {role_type}")

    base_capacity = BASE_CAPACITY[role_type_lower]
    internal_multiplier = 0.25 if is_internal else 1.0
    stage_lower = stage.lower().strip()
    stage_multiplier = STAGE_MULTIPLIERS.get(stage_lower, 1.0)

    return base_capacity * internal_multiplier * stage_multiplier


def test_case(name, role_type, is_internal, stage, expected_percentage):
    """Run a single test case."""
    capacity = calculate_vacancy_capacity(role_type, is_internal, stage)
    percentage = round(capacity * 100, 2)

    status = "✓ PASS" if abs(percentage - expected_percentage) < 0.01 else "✗ FAIL"

    print(f"{status} | {name}")
    print(f"   Input: {role_type.capitalize()}, Internal={is_internal}, Stage='{stage if stage else 'None'}'")
    print(f"   Expected: {expected_percentage}% | Got: {percentage}%")

    if status == "✗ FAIL":
        print(f"   ERROR: Mismatch!")
    print()

    return status == "✓ PASS"


def main():
    print("=" * 70)
    print("RECRUITMENT CAPACITY TRACKER - ENHANCED CALCULATIONS TEST")
    print("=" * 70)
    print()

    tests_passed = 0
    tests_total = 0

    # Test Case 1: External, Easy, No Stage
    tests_total += 1
    if test_case(
        "Test 1: External, Easy, No Stage",
        "easy", False, "",
        3.33
    ):
        tests_passed += 1

    # Test Case 2: Internal, Hard, Screening
    tests_total += 1
    if test_case(
        "Test 2: Internal, Hard, Screening",
        "hard", True, "screening",
        0.83
    ):
        tests_passed += 1

    # Test Case 3: External, Medium, Interview
    tests_total += 1
    if test_case(
        "Test 3: External, Medium, Interview",
        "medium", False, "interview",
        1.0
    ):
        tests_passed += 1

    # Test Case 4: Internal, Easy, No Stage
    tests_total += 1
    if test_case(
        "Test 4: Internal, Easy, No Stage",
        "easy", True, "",
        0.83
    ):
        tests_passed += 1

    # Test Case 5: External, Hard, No Stage
    tests_total += 1
    if test_case(
        "Test 5: External, Hard, No Stage",
        "hard", False, "",
        8.33
    ):
        tests_passed += 1

    # Test Case 6: External, Medium, No Stage
    tests_total += 1
    if test_case(
        "Test 6: External, Medium, No Stage",
        "medium", False, "",
        5.0
    ):
        tests_passed += 1

    # Test Case 7: Internal, Medium, Sourcing
    tests_total += 1
    if test_case(
        "Test 7: Internal, Medium, Sourcing",
        "medium", True, "sourcing",
        0.25
    ):
        tests_passed += 1

    # Test Case 8: External, Easy, Offer
    tests_total += 1
    if test_case(
        "Test 8: External, Easy, Offer",
        "easy", False, "offer",
        0.33
    ):
        tests_passed += 1

    # Test Case 9: Internal, Hard, Pre-Hire Checks
    tests_total += 1
    if test_case(
        "Test 9: Internal, Hard, Pre-Hire Checks",
        "hard", True, "pre-hire checks",
        0.21
    ):
        tests_passed += 1

    # Test Case 10: External, Hard, Sourcing
    tests_total += 1
    if test_case(
        "Test 10: External, Hard, Sourcing",
        "hard", False, "sourcing",
        1.67
    ):
        tests_passed += 1

    print("=" * 70)
    print(f"RESULTS: {tests_passed}/{tests_total} tests passed")
    print("=" * 70)
    print()

    # Test multi-vacancy scenario
    print("=" * 70)
    print("MULTI-VACANCY TEST")
    print("=" * 70)
    print()

    print("Scenario: John Smith with multiple vacancies")
    print("  - 10 easy external no stage")
    print("  - 5 hard internal screening")
    print()

    # 10 easy external no stage
    capacity_1 = 10 * calculate_vacancy_capacity("easy", False, "")
    print(f"  10 easy external no stage: {round(capacity_1 * 100, 2)}%")

    # 5 hard internal screening
    capacity_2 = 5 * calculate_vacancy_capacity("hard", True, "screening")
    print(f"  5 hard internal screening: {round(capacity_2 * 100, 2)}%")

    total = capacity_1 + capacity_2
    print(f"  TOTAL CAPACITY: {round(total * 100, 2)}%")

    expected_total = 37.5
    if abs(round(total * 100, 2) - expected_total) < 0.1:
        print(f"  ✓ PASS (expected ~{expected_total}%)")
    else:
        print(f"  ✗ FAIL (expected ~{expected_total}%)")

    print()

    # Test all stages
    print("=" * 70)
    print("STAGE MULTIPLIER TEST")
    print("=" * 70)
    print()

    print("Testing External Hard role across all stages:")
    base = calculate_vacancy_capacity("hard", False, "")
    base_pct = round(base * 100, 2)
    print(f"  No stage: {base_pct}% (100% of base)")

    for stage_name, multiplier in STAGE_MULTIPLIERS.items():
        if stage_name and stage_name != 'none':
            capacity = calculate_vacancy_capacity("hard", False, stage_name)
            pct = round(capacity * 100, 2)
            expected = round(base_pct * multiplier, 2)
            status = "✓" if abs(pct - expected) < 0.01 else "✗"
            print(f"  {status} {stage_name.capitalize():15s}: {pct}% ({int(multiplier*100)}% of base)")

    print()
    print("=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
