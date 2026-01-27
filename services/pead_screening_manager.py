"""
PEAD Screening Manager.

Orchestrates the complete PEAD screening workflow:
1. CSV upload → parsing
2. Database persistence (stocks, earnings reports)
3. SUE calculation for all stocks
4. Quality metrics calculation (sector-aware)
5. Decile ranking (global + sector)
6. Recommendation generation
7. Screening results

Handles transaction management, error recovery, and session persistence.
"""
import uuid
from typing import List, Dict, Tuple, Optional
from datetime import date
from flask import session, current_app, has_request_context
from models.financial import Stock, EarningsReport, SUECalculation, UploadBatch
from services.csv_parser_service import CSVParserService
from services.sue_calculation_service import SUECalculationService
from services.earnings_quality_service import EarningsQualityService
from services.pead_screening_service import PEADScreeningService
from extensions import db


class PEADScreeningManager:
    """
    PEAD screening orchestrator.

    Coordinates all services to transform CSV upload into
    actionable screening results.
    """

    def __init__(self):
        """Initialize manager with all required services."""
        self.csv_parser = CSVParserService()
        self.sue_service = SUECalculationService()
        self.quality_service = EarningsQualityService()
        self.screening_service = PEADScreeningService()

    def process_csv_upload(
        self,
        csv_content: str,
        ftse_index: str,
        default_drift_window: int = 60
    ) -> Tuple[Optional[List[Dict]], List[str]]:
        """
        Process CSV upload with full PEAD screening workflow.

        Workflow:
        1. Create upload batch
        2. Parse CSV
        3. Persist stocks + earnings reports
        4. Calculate SUE for all stocks
        5. Assign decile ranks
        6. Calculate quality metrics (sector-aware)
        7. Generate recommendations
        8. Screen opportunities

        Args:
            csv_content: Raw CSV file content
            ftse_index: 'FTSE100', 'FTSE250', or 'BOTH'
            default_drift_window: Default drift window for this batch (60/90/120 days)

        Returns:
            Tuple of (screening_results, errors)
            - screening_results: List of opportunity dictionaries
            - errors: List of error messages
        """
        errors = []

        try:
            # Step 1: Create upload batch
            batch = UploadBatch(
                batch_uuid=str(uuid.uuid4()),
                user_session_id=session.get('_id', str(uuid.uuid4())) if has_request_context() else str(uuid.uuid4()),
                ftse_index=ftse_index,
                stock_count=0,  # Will update after parsing
                default_drift_window=default_drift_window
            )
            db.session.add(batch)
            db.session.flush()  # Get batch.id

            current_app.logger.info(f"Created upload batch {batch.batch_uuid}")

            # Step 2: Parse CSV
            parsed_data, parse_errors = self.csv_parser.parse_csv(csv_content)

            if parse_errors:
                errors.extend(parse_errors)

            if not parsed_data:
                db.session.rollback()
                current_app.logger.warning("No valid data in CSV upload")
                return None, errors

            # Update stock count
            batch.stock_count = len(set(d['ticker'] for d in parsed_data))
            current_app.logger.info(f"Parsed {len(parsed_data)} earnings reports for {batch.stock_count} stocks")

            # Step 3: Persist stocks + earnings reports
            self._persist_data(parsed_data, ftse_index, batch.id)
            current_app.logger.info("Persisted stocks and earnings reports to database")

            # Step 4: Calculate SUE for all stocks
            sue_calculations = self._calculate_sue_batch(ftse_index, batch.id)
            current_app.logger.info(f"Calculated SUE scores for {len(sue_calculations)} stocks")

            # Step 5: Assign decile ranks (global + sector)
            self._assign_decile_ranks(sue_calculations, batch.id)
            current_app.logger.info("Assigned global and sector-specific decile ranks")

            # Step 6: Calculate quality metrics (sector-aware)
            self._calculate_quality_metrics_sector_aware(sue_calculations)
            current_app.logger.info("Calculated earnings quality metrics")

            # Step 7: Generate recommendations
            self._generate_recommendations(sue_calculations, default_drift_window)
            current_app.logger.info("Generated investment recommendations")

            # Step 8: Commit all changes
            db.session.commit()
            current_app.logger.info(f"Successfully committed batch {batch.batch_uuid}")

            # Step 9: Store batch UUID in session
            self._persist_to_session(csv_content, ftse_index, batch.batch_uuid)

            # Step 10: Screen opportunities
            results = self.screening_service.screen_opportunities(
                upload_batch_id=batch.id,
                drift_window_days=default_drift_window
            )

            return results, errors

        except Exception as e:
            current_app.logger.error(f"PEAD screening error: {e}", exc_info=True)
            errors.append(f"Processing error: {str(e)}")
            db.session.rollback()
            return None, errors

    def _persist_data(
        self,
        parsed_data: List[Dict],
        ftse_index: str,
        batch_id: int
    ) -> None:
        """
        Persist stocks and earnings reports to database.

        Handles duplicate stocks (upsert pattern).

        Args:
            parsed_data: List of parsed stock dictionaries from CSV
            ftse_index: FTSE index filter
            batch_id: Upload batch ID
        """
        for data in parsed_data:
            # Get or create stock
            stock = Stock.query.filter_by(ticker=data['ticker']).first()

            if not stock:
                # Create new stock
                stock = Stock(
                    ticker=data['ticker'],
                    company_name=data['company_name'],
                    ftse_index=ftse_index,
                    sector=data.get('sector'),
                    fiscal_year_end_month=data.get('fiscal_year_end_month')
                )
                db.session.add(stock)
                db.session.flush()  # Get stock.id
            else:
                # Update existing stock metadata if changed
                if 'sector' in data and data['sector']:
                    stock.sector = data['sector']
                if 'fiscal_year_end_month' in data and data['fiscal_year_end_month']:
                    stock.fiscal_year_end_month = data['fiscal_year_end_month']

            # Create earnings report
            report = EarningsReport(
                stock_id=stock.id,
                report_date=data['report_date'],
                reporting_period=data['reporting_period'],
                period_type=data['period_type'],
                fiscal_year_end_month=data.get('fiscal_year_end_month'),
                actual_eps=data['actual_eps'],
                net_income=data['net_income'],
                operating_cash_flow=data['operating_cash_flow'],
                total_assets=data['total_assets'],
                change_in_receivables=data.get('change_in_receivables'),
                change_in_inventory=data.get('change_in_inventory'),
                change_in_payables=data.get('change_in_payables'),
                depreciation=data.get('depreciation'),
                total_debt=data.get('total_debt'),
                upload_batch_id=batch_id
            )

            # Calculate total accruals
            report.total_accruals = report.net_income - report.operating_cash_flow

            # Calculate operating accruals if components available
            if all(getattr(report, field, None) is not None for field in
                   ['change_in_receivables', 'change_in_inventory', 'change_in_payables', 'depreciation']):
                report.operating_accruals = (
                    report.change_in_receivables +
                    report.change_in_inventory -
                    report.change_in_payables -
                    report.depreciation
                )

            # Calculate ROA if assets available
            if report.total_assets > 0:
                report.return_on_assets = report.net_income / report.total_assets

            db.session.add(report)

    def _calculate_sue_batch(
        self,
        ftse_index: str,
        batch_id: int
    ) -> List[SUECalculation]:
        """
        Calculate SUE scores for all stocks in batch.

        Args:
            ftse_index: FTSE index filter
            batch_id: Upload batch ID

        Returns:
            List of SUECalculation objects
        """
        sue_calculations = []

        # Get all stocks in this batch
        stocks = (
            db.session.query(Stock)
            .join(EarningsReport, EarningsReport.stock_id == Stock.id)
            .filter(EarningsReport.upload_batch_id == batch_id)
            .distinct()
            .all()
        )

        for stock in stocks:
            # Get all earnings reports for this stock
            all_reports = (
                EarningsReport.query
                .filter_by(stock_id=stock.id)
                .order_by(EarningsReport.report_date.desc())
                .all()
            )

            # Get current batch reports
            current_batch_reports = [r for r in all_reports if r.upload_batch_id == batch_id]

            for current_report in current_batch_reports:
                # Get historical reports (excluding current)
                historical_reports = [r for r in all_reports if r.report_date < current_report.report_date]

                # Calculate SUE
                sue_score, metadata = self.sue_service.calculate_sue_for_stock(
                    stock.id,
                    current_report,
                    historical_reports
                )

                # Create SUE calculation record
                sue_calc = SUECalculation(
                    stock_id=stock.id,
                    report_date=current_report.report_date,
                    actual_eps=current_report.actual_eps,
                    expected_eps=metadata.get('expected_eps'),
                    forecast_error=metadata.get('forecast_error'),
                    forecast_error_stddev=metadata.get('forecast_error_stddev'),
                    sue_score=sue_score,
                    small_sample_corrected=metadata.get('small_sample_corrected', False),
                    upload_batch_id=batch_id
                )

                db.session.add(sue_calc)
                sue_calculations.append(sue_calc)

        db.session.flush()  # Ensure all SUE calculations have IDs

        return sue_calculations

    def _assign_decile_ranks(
        self,
        sue_calculations: List[SUECalculation],
        batch_id: int
    ) -> None:
        """
        Assign global and sector-specific decile ranks.

        Uses SUECalculationService for ranking logic.

        Args:
            sue_calculations: List of SUE calculations
            batch_id: Upload batch ID
        """
        self.sue_service.assign_decile_ranks(
            sue_calculations,
            batch_id,
            use_sector_adjusted=True
        )

    def _calculate_quality_metrics_sector_aware(
        self,
        sue_calculations: List[SUECalculation]
    ) -> None:
        """
        Calculate quality metrics with sector-aware methodology.

        Industrial/Retail: Operating Accruals
        Financials: ROA Persistence + Cash Flow
        Utilities: Conservative Accounting

        Args:
            sue_calculations: List of SUE calculations
        """
        for sue_calc in sue_calculations:
            # Get stock and current report
            stock = Stock.query.get(sue_calc.stock_id)
            current_report = EarningsReport.query.filter_by(
                stock_id=sue_calc.stock_id,
                report_date=sue_calc.report_date
            ).first()

            if not stock or not current_report:
                continue

            # Get historical reports (for ROA persistence calculation)
            historical_reports = (
                EarningsReport.query
                .filter(
                    EarningsReport.stock_id == stock.id,
                    EarningsReport.report_date < sue_calc.report_date
                )
                .order_by(EarningsReport.report_date.desc())
                .limit(8)
                .all()
            )

            # Calculate sector-aware quality score
            quality_score, methodology = self.quality_service.calculate_quality_score_for_stock(
                stock,
                current_report,
                historical_reports
            )

            # Update SUE calculation with quality metrics
            sue_calc.quality_score = quality_score
            sue_calc.quality_calculation_method = methodology

            # Store individual components (for detail view)
            if current_report.total_assets > 0:
                sue_calc.accruals_ratio = current_report.total_accruals / current_report.total_assets
                sue_calc.cash_flow_to_assets = current_report.operating_cash_flow / current_report.total_assets

                if current_report.operating_accruals is not None:
                    sue_calc.operating_accruals_ratio = current_report.operating_accruals / current_report.total_assets

    def _generate_recommendations(
        self,
        sue_calculations: List[SUECalculation],
        drift_window: int
    ) -> None:
        """
        Generate investment recommendations for all stocks.

        Args:
            sue_calculations: List of SUE calculations
            drift_window: Drift window in days
        """
        for sue_calc in sue_calculations:
            if sue_calc.sue_score is None or sue_calc.quality_score is None:
                continue

            # Use global decile for recommendations
            decile = sue_calc.global_decile or 5

            # Generate recommendation
            recommendation, explanation = self.screening_service.generate_recommendation(
                sue_calc.sue_score,
                decile,
                sue_calc.quality_score,
                drift_window
            )

            sue_calc.recommendation = recommendation
            sue_calc.recommendation_explanation = explanation

    def _persist_to_session(
        self,
        csv_content: str,
        ftse_index: str,
        batch_uuid: str
    ) -> None:
        """
        Store batch UUID in session for retrieval.

        Args:
            csv_content: CSV content (not stored, just logged)
            ftse_index: FTSE index
            batch_uuid: Batch UUID
        """
        # Only store in session if we're in a request context
        if has_request_context():
            session['pead_batch_uuid'] = batch_uuid
            session['pead_ftse_index'] = ftse_index
            session.permanent = True
            current_app.logger.info(f"Stored batch {batch_uuid} in session")
        else:
            current_app.logger.info(f"Skipping session storage (no request context) for batch {batch_uuid}")

    def get_screening_from_session(self) -> Optional[List[Dict]]:
        """
        Retrieve screening results from session.

        Returns:
            List of screening results (None if no session)
        """
        batch_uuid = session.get('pead_batch_uuid')

        if not batch_uuid:
            return None

        # Get batch
        batch = UploadBatch.query.filter_by(batch_uuid=batch_uuid).first()

        if not batch:
            return None

        # Screen opportunities
        results = self.screening_service.screen_opportunities(
            upload_batch_id=batch.id,
            drift_window_days=batch.default_drift_window
        )

        return results
