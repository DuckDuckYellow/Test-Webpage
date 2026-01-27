"""
Test PEAD upload processing to diagnose issues.
"""
from app import create_app

app = create_app()

with app.app_context():
    from app import pead_manager

    # Read the sample CSV
    with open('static/sample_pead_data.csv', 'r') as f:
        csv_content = f.read()

    print("Testing PEAD screening with sample data...")
    print(f"CSV length: {len(csv_content)} characters")
    print("-" * 60)

    try:
        results, errors = pead_manager.process_csv_upload(
            csv_content,
            'BOTH',
            90
        )

        print(f"\n[SUCCESS] Processing completed!")
        print(f"  - Errors: {len(errors)}")
        if errors:
            for error in errors:
                print(f"    * {error}")

        print(f"  - Results: {len(results) if results else 0}")

        if results:
            print(f"\n[SUCCESS] Sample results (first 5):")
            for i, result in enumerate(results[:5], 1):
                print(f"\n  {i}. {result['ticker']} - {result['company_name']}")
                print(f"     SUE Score: {result.get('sue_score')}")
                print(f"     SUE Decile: {result.get('sue_decile')}")
                print(f"     Quality Score: {result.get('quality_score')}")
                print(f"     Quality Method: {result.get('quality_method')}")
                print(f"     Recommendation: {result.get('recommendation')}")
                print(f"     Sector: {result.get('sector')}")
        else:
            print("\n[WARNING] No results returned")

    except Exception as e:
        print(f"\n[ERROR] Error during processing:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
