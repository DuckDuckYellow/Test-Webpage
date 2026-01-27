"""
Financial routes for PEAD screening.

Handles FTSE 100/250 Post-Earnings Announcement Drift screening workflow.
"""
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify, make_response
from werkzeug.utils import secure_filename
import csv
from io import StringIO


financial_bp = Blueprint('financial', __name__, url_prefix='/financial')


@financial_bp.route('/pead-screener', methods=['GET', 'POST'])
def pead_screener():
    """
    PEAD screener upload and results display.

    GET: Show upload form
    POST: Process CSV upload and display results
    """
    from app import pead_manager  # Import here to avoid circular import

    if request.method == 'POST':
        # Get form data
        file = request.files.get('csv_file')
        ftse_index = request.form.get('ftse_index', 'BOTH')
        drift_window = int(request.form.get('drift_window', 60))

        # Validate file
        if not file or file.filename == '':
            flash('No file uploaded', 'danger')
            return redirect(url_for('financial.pead_screener'))

        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file', 'danger')
            return redirect(url_for('financial.pead_screener'))

        # Process upload
        try:
            csv_content = file.read().decode('utf-8')

            # Log the processing start
            from flask import current_app
            current_app.logger.info(f"Starting PEAD screening with FTSE: {ftse_index}, Drift: {drift_window}")

            results, errors = pead_manager.process_csv_upload(
                csv_content,
                ftse_index,
                drift_window
            )

            # Display any parsing errors as warnings
            if errors:
                current_app.logger.warning(f"Processing errors: {errors}")
                for error in errors:
                    flash(error, 'warning')

            # If no results, redirect to upload form
            if not results:
                current_app.logger.warning("No results returned from screening")
                flash('No valid data found in CSV file', 'danger')
                return redirect(url_for('financial.pead_screener'))

            # Calculate summary statistics
            current_app.logger.info(f"Successfully screened {len(results)} opportunities")
            strong_buy_count = sum(1 for r in results if r.get('recommendation') == 'STRONG_BUY')
            buy_count = sum(1 for r in results if r.get('recommendation') == 'BUY')
            high_quality_count = sum(1 for r in results if r.get('quality_score', 0) >= 70)

            # Render results
            return render_template(
                'financial/pead_screener.html',
                results=results,
                ftse_index=ftse_index,
                drift_window=drift_window,
                strong_buy_count=strong_buy_count,
                buy_count=buy_count,
                high_quality_count=high_quality_count,
                total_count=len(results)
            )

        except Exception as e:
            from flask import current_app
            current_app.logger.error(f'Error processing CSV: {str(e)}', exc_info=True)
            flash(f'Error processing CSV: {str(e)}', 'danger')
            return redirect(url_for('financial.pead_screener'))

    # GET request - show upload form
    # Check if there's a session with results
    if pead_manager:
        session_results = pead_manager.get_screening_from_session()
        if session_results:
            # Calculate summary statistics
            strong_buy_count = sum(1 for r in session_results if r.get('recommendation') == 'STRONG_BUY')
            buy_count = sum(1 for r in session_results if r.get('recommendation') == 'BUY')
            high_quality_count = sum(1 for r in session_results if r.get('quality_score', 0) >= 70)

            return render_template(
                'financial/pead_screener.html',
                results=session_results,
                ftse_index=session.get('pead_ftse_index', 'BOTH'),
                drift_window=60,  # Default
                strong_buy_count=strong_buy_count,
                buy_count=buy_count,
                high_quality_count=high_quality_count,
                total_count=len(session_results)
            )

    return render_template('financial/pead_screener.html')


@financial_bp.route('/pead-screener/filter', methods=['POST'])
def filter_screening_results():
    """
    AJAX endpoint for filtering screening results.

    Accepts JSON with filter parameters and returns filtered opportunities.
    """
    from app import pead_manager
    from models.financial import UploadBatch

    data = request.get_json()

    # Get batch UUID from session
    batch_uuid = session.get('pead_batch_uuid')
    if not batch_uuid:
        return jsonify({'error': 'No screening session found'}), 404

    # Get batch
    batch = UploadBatch.query.filter_by(batch_uuid=batch_uuid).first()
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404

    # Apply filters
    try:
        results = pead_manager.screening_service.screen_opportunities(
            upload_batch_id=batch.id,
            min_sue_decile=data.get('min_sue_decile'),
            min_quality_score=data.get('min_quality_score'),
            sectors=data.get('sectors'),
            drift_window_days=data.get('drift_window_days'),
            limit=data.get('limit', 50)
        )

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@financial_bp.route('/pead-screener/export', methods=['GET'])
def export_pead_results():
    """
    Export screening results to CSV.

    Downloads all results from current session as CSV file.
    """
    from app import pead_manager

    # Get results from session
    results = pead_manager.get_screening_from_session()

    if not results:
        flash('No screening results to export', 'warning')
        return redirect(url_for('financial.pead_screener'))

    # Create CSV in memory
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'Ticker',
        'Company Name',
        'Sector',
        'FTSE Index',
        'Report Date',
        'Reporting Period',
        'Actual EPS',
        'Expected EPS',
        'SUE Score',
        'SUE Decile',
        'Global Decile',
        'Sector Decile',
        'Quality Score',
        'Quality Method',
        'Accruals Ratio',
        'Cash Flow / Assets',
        'Recommendation',
        'Recommendation Explanation',
        'Drift Window (Days)',
        'Drift Window End'
    ])

    writer.writeheader()

    for result in results:
        writer.writerow({
            'Ticker': result.get('ticker'),
            'Company Name': result.get('company_name'),
            'Sector': result.get('sector'),
            'FTSE Index': result.get('ftse_index'),
            'Report Date': result.get('report_date'),
            'Reporting Period': result.get('reporting_period'),
            'Actual EPS': result.get('actual_eps'),
            'Expected EPS': result.get('expected_eps'),
            'SUE Score': result.get('sue_score'),
            'SUE Decile': result.get('sue_decile'),
            'Global Decile': result.get('global_decile'),
            'Sector Decile': result.get('sector_decile'),
            'Quality Score': result.get('quality_score'),
            'Quality Method': result.get('quality_method'),
            'Accruals Ratio': result.get('accruals_ratio'),
            'Cash Flow / Assets': result.get('cf_to_assets'),
            'Recommendation': result.get('recommendation'),
            'Recommendation Explanation': result.get('recommendation_explanation'),
            'Drift Window (Days)': result.get('drift_window_days'),
            'Drift Window End': result.get('drift_window_end')
        })

    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=pead_screening_results.csv'

    return response


@financial_bp.route('/pead-screener/new', methods=['GET'])
def new_pead_screening():
    """
    Clear session and start new screening.

    Clears all session data and redirects to upload form.
    """
    session.pop('pead_batch_uuid', None)
    session.pop('pead_ftse_index', None)

    flash('Session cleared. Upload new data to start screening.', 'info')
    return redirect(url_for('financial.pead_screener'))
