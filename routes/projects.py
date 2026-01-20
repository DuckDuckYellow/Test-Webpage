"""
Projects Routes Blueprint

Handles all project-related routes including the Recruitment Capacity Tracker.
"""

from flask import Blueprint, render_template, request, send_file, current_app
from io import BytesIO
from pydantic import ValidationError

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
                                    validated = VacancySchema(**vacancy)
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
