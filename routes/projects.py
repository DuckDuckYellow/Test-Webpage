"""
Projects Routes Blueprint

Handles all project-related routes including the Recruitment Capacity Tracker.
"""

from flask import Blueprint, render_template, request, send_file, current_app, session, make_response
from io import BytesIO, StringIO
import csv
from pydantic import ValidationError
from app import csrf

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route("/")
def projects_home():
    """Projects overview page."""
    from app import PROJECTS

    current_app.logger.info("Projects page accessed")
    return render_template("projects.html", projects=PROJECTS)


@projects_bp.route("/capacity-tracker", methods=["GET", "POST"])
def capacity_tracker():
    """
    Recruitment Capacity Tracker tool.

    GET: Display the input form
    POST: Process form data (manual or Excel upload) and display results
    Rate limited to prevent abuse.
    """
    from app import capacity_service, file_service
    from schemas import VacancySchema

    recruiters_data = []
    team_summary = None
    errors = []
    input_method = None

    if request.method == "POST":
        # Check if this is an Excel upload or manual input
        if 'excel_file' in request.files and request.files['excel_file'].filename:
            # Excel upload processing
            input_method = 'excel'
            file = request.files['excel_file']

            current_app.logger.info(f"Excel upload: {file.filename}")

            # Validate file using service
            is_valid, error_msg = file_service.validate_uploaded_file(file)
            if not is_valid:
                current_app.logger.warning(f"Invalid file upload: {error_msg}")
                errors.append(error_msg)
            else:
                # Process Excel file using service
                recruiters_dict, excel_errors = file_service.process_excel_upload(file)
                errors.extend(excel_errors)

                # Validate with Pydantic and calculate capacity
                if not errors:
                    for recruiter_name, vacancies in recruiters_dict.items():
                        try:
                            # Validate each vacancy with Pydantic
                            validated_vacancies = []
                            for vacancy in vacancies:
                                try:
                                    # Map dictionary keys to VacancySchema field names
                                    validated = VacancySchema(
                                        name=vacancy['vacancy_name'],
                                        role_type=vacancy['role_type'],
                                        is_internal=vacancy.get('is_internal', False),
                                        stage=vacancy.get('stage', '')
                                    )
                                    validated_vacancies.append({
                                        'vacancy_name': validated.name,
                                        'role_type': validated.role_type.value,
                                        'is_internal': validated.is_internal,
                                        'stage': validated.stage.value
                                    })
                                except ValidationError as ve:
                                    errors.append(f"Validation error in {vacancy.get('vacancy_name', 'unknown')}: {ve}")
                                    current_app.logger.error(f"Pydantic validation failed: {ve}")

                            if validated_vacancies:
                                capacity_info = capacity_service.calculate_recruiter_capacity_from_vacancies(validated_vacancies)
                                recruiter = {
                                    'name': recruiter_name,
                                    **capacity_info
                                }
                                recruiters_data.append(recruiter)
                                current_app.logger.info(f"Calculated capacity for {recruiter_name}: {capacity_info['capacity_percentage']}%")

                        except Exception as e:
                            error_msg = f"Error calculating capacity for {recruiter_name}: {str(e)}"
                            errors.append(error_msg)
                            current_app.logger.error(error_msg)

        else:
            # Manual input processing
            input_method = 'manual'
            current_app.logger.info("Manual capacity tracker input")

            # Collect all vacancy data from form
            index = 0
            vacancies_by_recruiter = {}

            while f'recruiter_{index}' in request.form:
                recruiter_name = request.form.get(f'recruiter_{index}', '').strip()
                vacancy_name = request.form.get(f'vacancy_name_{index}', '').strip()
                role_type = request.form.get(f'role_type_{index}', '').strip().lower()
                internal_str = request.form.get(f'internal_{index}', 'no').strip().lower()
                stage = request.form.get(f'stage_{index}', '').strip().lower()

                # Skip if recruiter name is empty
                if not recruiter_name:
                    index += 1
                    continue

                # Default vacancy name if not provided
                if not vacancy_name:
                    vacancy_name = f"Vacancy {index + 1}"

                # Validate with Pydantic
                try:
                    validated = VacancySchema(
                        name=vacancy_name,
                        role_type=role_type,
                        is_internal=(internal_str == 'yes'),
                        stage=stage if stage else ''
                    )

                    # Add to recruiter's vacancy list
                    if recruiter_name not in vacancies_by_recruiter:
                        vacancies_by_recruiter[recruiter_name] = []

                    vacancies_by_recruiter[recruiter_name].append({
                        'vacancy_name': validated.name,
                        'role_type': validated.role_type.value,
                        'is_internal': validated.is_internal,
                        'stage': validated.stage.value
                    })

                except ValidationError as ve:
                    error_msg = f"Validation error for vacancy {index + 1}: {ve}"
                    errors.append(error_msg)
                    current_app.logger.error(error_msg)

                index += 1

            # Calculate capacity for each recruiter using service
            if not errors and vacancies_by_recruiter:
                for recruiter_name, vacancies in vacancies_by_recruiter.items():
                    try:
                        capacity_info = capacity_service.calculate_recruiter_capacity_from_vacancies(vacancies)
                        recruiter = {
                            'name': recruiter_name,
                            **capacity_info
                        }
                        recruiters_data.append(recruiter)
                        current_app.logger.info(f"Calculated capacity for {recruiter_name}: {capacity_info['capacity_percentage']}%")
                    except Exception as e:
                        error_msg = f"Error calculating capacity for {recruiter_name}: {str(e)}"
                        errors.append(error_msg)
                        current_app.logger.error(error_msg)

        # Calculate team summary if we have data using service
        if recruiters_data:
            team_summary = capacity_service.calculate_team_summary(recruiters_data)
            current_app.logger.info(f"Team summary: {team_summary['average_capacity']}% average capacity")

    return render_template(
        "projects/capacity_tracker.html",
        recruiters=recruiters_data,
        team_summary=team_summary,
        errors=errors,
        input_method=input_method
    )


@projects_bp.route("/capacity-tracker/download-template")
def download_capacity_template():
    """
    Generate and download a sample Excel template for capacity tracker.
    """
    from app import file_service

    current_app.logger.info("Capacity tracker template download requested")

    # Generate template using file service
    workbook = file_service.generate_capacity_template()

    # Save to BytesIO
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='capacity_tracker_template.xlsx'
    )


@projects_bp.route("/squad-audit-tracker", methods=["GET", "POST"])
def squad_audit_tracker():
    """
    Squad Audit Tracker tool for Football Manager squad analysis.

    GET: Display the upload form
    POST: Process uploaded HTML file and display analysis results
    """
    from services.fm_parser import FMHTMLParser
    from services.squad_audit_service import SquadAuditService

    analysis_result = None
    errors = []

    if request.method == "POST":
        # Check if file was uploaded
        if 'html_file' not in request.files:
            errors.append("No file uploaded")
            current_app.logger.warning("Squad audit: No file in request")
        else:
            file = request.files['html_file']

            if file.filename == '':
                errors.append("No file selected")
                current_app.logger.warning("Squad audit: Empty filename")
            elif not file.filename.endswith('.html'):
                errors.append("Please upload an HTML file (.html)")
                current_app.logger.warning(f"Squad audit: Invalid file type: {file.filename}")
            else:
                try:
                    current_app.logger.info(f"Squad audit: Processing {file.filename}")

                    # Clean up old temporary file if it exists
                    import os
                    if 'squad_html_path' in session:
                        old_file = session['squad_html_path']
                        if os.path.exists(old_file):
                            try:
                                os.remove(old_file)
                                current_app.logger.info(f"Squad audit: Cleaned up old file {old_file}")
                            except Exception as e:
                                current_app.logger.warning(f"Squad audit: Could not remove old file: {e}")

                    # Read HTML content
                    html_content = file.read().decode('utf-8')

                    # Parse HTML
                    parser = FMHTMLParser()
                    squad = parser.parse_html(html_content)

                    current_app.logger.info(f"Squad audit: Parsed {len(squad.players)} players")

                    # Analyze squad
                    service = SquadAuditService()
                    analysis_result = service.analyze_squad(squad)

                    # Store HTML content in a temporary file for position recalculation and CSV re-generation
                    import tempfile
                    import os

                    temp_dir = tempfile.gettempdir()

                    # Create a temporary file to store the HTML
                    temp_file = tempfile.NamedTemporaryFile(
                        mode='w',
                        suffix='.html',
                        prefix='squad_audit_',
                        dir=temp_dir,
                        delete=False
                    )
                    temp_file.write(html_content)
                    temp_file_path = temp_file.name
                    temp_file.close()

                    # Store only the file path in session (avoids exceeding cookie size limits)
                    session.permanent = True  # Make session permanent so it persists
                    session['squad_html_path'] = temp_file_path
                    session.modified = True  # Explicitly mark session as modified
                    current_app.logger.info(f"Squad audit: Stored HTML in {temp_file_path}")
                    current_app.logger.info(f"Squad audit: Session size check - squad_html_path length: {len(temp_file_path)} chars")
                    current_app.logger.info(f"Squad audit: Session keys after storage: {list(session.keys())}")

                    # Verify we can immediately read back the session data
                    verification = session.get('squad_html_path')
                    current_app.logger.info(f"Squad audit: Session verification - can read back: {verification == temp_file_path}")

                    current_app.logger.info("Squad audit: Analysis complete")

                except ValueError as ve:
                    error_msg = f"Invalid HTML format: {str(ve)}"
                    errors.append(error_msg)
                    current_app.logger.error(f"Squad audit parse error: {ve}")
                except Exception as e:
                    error_msg = f"Error processing file: {str(e)}"
                    errors.append(error_msg)
                    current_app.logger.error(f"Squad audit error: {e}")

    # Generate formation suggestions if we have an analysis result
    formation_suggestions = None
    if analysis_result:
        try:
            service = SquadAuditService()
            formation_suggestions = service.suggest_formations(analysis_result, top_n=3)
            current_app.logger.info(f"Squad audit: Generated {len(formation_suggestions) if formation_suggestions else 0} formation suggestions")
        except Exception as e:
            current_app.logger.error(f"Squad audit: Error generating formation suggestions: {e}")
            errors.append(f"Could not generate formation suggestions: {str(e)}")

    return render_template(
        "projects/squad_audit_tracker.html",
        analysis_result=analysis_result,
        errors=errors,
        formation_suggestions=formation_suggestions
    )


@projects_bp.route("/squad-audit-tracker/export")
def export_squad_audit():
    """
    Export squad audit analysis results to CSV.
    """
    from services.fm_parser import FMHTMLParser
    from services.squad_audit_service import SquadAuditService
    import os

    current_app.logger.info("Squad audit CSV export requested")

    # Check if we have the HTML file path in session
    if 'squad_html_path' not in session:
        current_app.logger.warning("Squad audit export: No session data found")
        return "No analysis data available. Please analyze a squad first.", 400

    html_file_path = session['squad_html_path']

    # Check if the temporary file still exists
    if not os.path.exists(html_file_path):
        current_app.logger.error(f"Squad audit export: HTML file not found at {html_file_path}")
        return "Session expired. Please analyze your squad again.", 400

    try:
        # Read and re-parse the HTML to regenerate analysis
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParser()
        squad = parser.parse_html(html_content)

        service = SquadAuditService()
        analysis_result = service.analyze_squad(squad)

        # Generate CSV data
        csv_data = service.export_to_csv_data(analysis_result)

        if not csv_data:
            return "No data to export.", 400

        # Create CSV in memory
        output = StringIO()
        fieldnames = csv_data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)

        # Create response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=squad_audit_analysis.csv"
        response.headers["Content-Type"] = "text/csv"

        current_app.logger.info("Squad audit: CSV export complete")
        return response

    except Exception as e:
        current_app.logger.error(f"Squad audit export error: {e}")
        return f"Error generating CSV: {str(e)}", 500


@projects_bp.route("/squad-audit-tracker/debug-session", methods=["GET"])
def debug_session():
    """Debug endpoint to check session state."""
    import os
    session_info = {
        'session_exists': bool(session),
        'session_keys': list(session.keys()),
        'has_squad_html_path': 'squad_html_path' in session,
    }

    if 'squad_html_path' in session:
        html_path = session['squad_html_path']
        session_info['squad_html_path'] = html_path
        session_info['file_exists'] = os.path.exists(html_path)
        if os.path.exists(html_path):
            session_info['file_size'] = os.path.getsize(html_path)

    return session_info


@projects_bp.route("/squad-audit-tracker/recalculate", methods=["POST"])
@csrf.exempt  # Exempt from CSRF for AJAX JSON API endpoint
def recalculate_player_position():
    """
    Recalculate analysis for a player with a new position.

    Expects JSON: {"player_name": "John Doe", "new_position": "ST"}
    Returns: Updated player analysis data as JSON
    """
    from services.squad_audit_service import SquadAuditService
    from models.squad_audit import PositionCategory
    import json

    try:
        current_app.logger.info("Position recalculation requested")
        current_app.logger.info(f"Session keys available: {list(session.keys())}")

        data = request.get_json()
        player_name = data.get('player_name')
        new_position = data.get('new_position')
        current_app.logger.info(f"Recalculation for player: {player_name}, new position: {new_position}")

        if not player_name or not new_position:
            return {"error": "Missing player_name or new_position", "success": False}, 400

        # Get stored HTML file path from session
        if 'squad_html_path' not in session:
            session_info = {
                'has_session': bool(session),
                'session_keys': list(session.keys()),
                'session_id': session.get('_id', 'no_id')
            }
            current_app.logger.warning(f"Position recalculation: No session data found. Session info: {session_info}")
            return {
                "error": "No analysis data in session. Please upload a squad file first.",
                "success": False,
                "debug": session_info
            }, 400

        html_file_path = session['squad_html_path']

        # Check if the temporary file still exists
        import os
        if not os.path.exists(html_file_path):
            current_app.logger.error(f"Position recalculation: HTML file not found at {html_file_path}")
            return {"error": "Session expired. Please upload your squad file again.", "success": False}, 400

        # Read and re-parse the HTML
        from services.fm_parser import FMHTMLParser
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        parser = FMHTMLParser()
        squad = parser.parse_html(html_content)

        # Find the player
        player = None
        for p in squad.players:
            if p.name == player_name:
                player = p
                break

        if not player:
            current_app.logger.warning(f"Position recalculation: Player {player_name} not found")
            return {"error": f"Player {player_name} not found", "success": False}, 404

        # Validate the new position is valid for this player
        try:
            new_pos_category = PositionCategory(new_position)
        except ValueError:
            return {"error": f"Invalid position: {new_position}", "success": False}, 400

        possible_positions = player.get_all_possible_positions()
        if new_pos_category not in possible_positions:
            return {"error": f"Player cannot play {new_position}", "success": False}, 400

        # Recalculate analysis with the new position
        service = SquadAuditService()

        # Get the full analysis result to access position benchmarks
        full_result = service.analyze_squad(squad)
        position_benchmarks = full_result.position_benchmarks
        squad_avg_wage = full_result.squad_avg_wage

        # Analyze this specific player with the new position override
        analysis = service._analyze_player(
            player,
            position_benchmarks,
            squad_avg_wage,
            position_override=new_pos_category
        )

        current_app.logger.info(f"Position recalculation successful for {player_name}")

        # Return the updated analysis data
        return {
            "success": True,
            "player_name": player.name,
            "position": new_position,
            "value_score": round(analysis.value_score, 1),
            "value_score_color": analysis.get_value_score_color(),
            "performance_index": round(analysis.performance_index, 1),
            "verdict": analysis.verdict.value,
            "recommendation": analysis.recommendation,
            "top_metrics": analysis.top_metrics,
            "contract_warning": analysis.contract_warning
        }

    except Exception as e:
        current_app.logger.error(f"Position recalculation error: {str(e)}")
        return {"error": f"An error occurred: {str(e)}", "success": False}, 500
