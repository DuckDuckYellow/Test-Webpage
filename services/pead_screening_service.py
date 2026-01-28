"""
PEAD Screening Service.

Combines SUE scores with earnings quality metrics to generate
investment recommendations based on academic PEAD research.

Recommendation Logic:
- STRONG_BUY: High SUE (Decile 9-10) + High Quality (70+)
- BUY: High SUE (Decile 8+) + Medium Quality (50+)
- HOLD: High SUE but Low Quality, OR Medium SUE
- AVOID: Low SUE (Decile 1-3)
"""
from typing import List, Dict, Optional
from datetime import date, timedelta
from models.financial import SUECalculation, Stock, EarningsReport, UploadBatch
from extensions import db


class PEADScreeningService:
    """
    PEAD screening engine with configurable drift windows and filters.
    """

    # Drift window presets (days)
    DRIFT_WINDOW_QUARTERLY = 60  # Standard for quarterly reporters
    DRIFT_WINDOW_SEMI_ANNUAL = 90  # Standard for semi-annual reporters (UK)
    DRIFT_WINDOW_EXTENDED = 120  # Extended window for slow price adjusters

    # Recommendation thresholds
    STRONG_BUY_SUE_DECILE = 9
    STRONG_BUY_QUALITY = 70

    BUY_SUE_DECILE = 8
    BUY_QUALITY = 50

    AVOID_SUE_DECILE = 3

    @classmethod
    def screen_opportunities(
        cls,
        upload_batch_id: int,
        use_sector_adjusted: bool = True,
        drift_window_days: Optional[int] = None,
        ftse_index: Optional[str] = None,
        min_sue_decile: Optional[int] = None,
        min_quality_score: Optional[float] = None,
        sectors: Optional[List[str]] = None,
        date_range_start: Optional[date] = None,
        date_range_end: Optional[date] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Screen for PEAD opportunities with configurable filters.

        Args:
            upload_batch_id: Upload batch ID
            use_sector_adjusted: Use sector-specific deciles vs global
            drift_window_days: Override drift window (60/90/120)
            ftse_index: Filter by 'FTSE100', 'FTSE250', or None for both
            min_sue_decile: Minimum SUE decile (1-10)
            min_quality_score: Minimum quality score (0-100)
            sectors: List of sectors to include
            date_range_start: Filter by report date >= this
            date_range_end: Filter by report date <= this
            limit: Maximum number of results

        Returns:
            List of opportunity dictionaries with all screening data
        """
        # Get batch default drift window if not specified
        if drift_window_days is None:
            batch = UploadBatch.query.get(upload_batch_id)
            drift_window_days = batch.default_drift_window if batch else 60

        # Build base query
        query = (
            db.session.query(SUECalculation, Stock, EarningsReport)
            .join(Stock, SUECalculation.stock_id == Stock.id)
            .join(EarningsReport, db.and_(
                EarningsReport.stock_id == Stock.id,
                EarningsReport.report_date == SUECalculation.report_date,
                EarningsReport.upload_batch_id == upload_batch_id  # Ensure report is from same batch
            ))
            .filter(SUECalculation.upload_batch_id == upload_batch_id)
            .filter(SUECalculation.sue_score.isnot(None))
        )

        # Apply filters
        if ftse_index:
            query = query.filter(Stock.ftse_index == ftse_index)

        if min_sue_decile:
            decile_field = SUECalculation.sector_decile if use_sector_adjusted else SUECalculation.global_decile
            query = query.filter(decile_field >= min_sue_decile)

        if min_quality_score:
            query = query.filter(SUECalculation.quality_score >= min_quality_score)

        if sectors:
            query = query.filter(Stock.sector.in_(sectors))

        if date_range_start:
            query = query.filter(EarningsReport.report_date >= date_range_start)

        if date_range_end:
            query = query.filter(EarningsReport.report_date <= date_range_end)

        # Order by quality score descending (best opportunities first)
        query = query.order_by(SUECalculation.quality_score.desc())

        # Debug logging
        from flask import current_app
        if current_app:
            # Count total SUE calculations for this batch
            total_sue = db.session.query(SUECalculation).filter_by(upload_batch_id=upload_batch_id).count()
            current_app.logger.debug(f"Total SUE calculations in batch: {total_sue}")
            current_app.logger.debug(f"Screening query filters: ftse_index={ftse_index}, min_sue_decile={min_sue_decile}, min_quality_score={min_quality_score}")

        # Execute query with limit
        results = query.limit(limit).all()

        # Format results
        opportunities = []
        for sue_calc, stock, report in results:
            # Calculate drift window end date
            drift_end = report.report_date + timedelta(days=drift_window_days)

            # Get recommended window for this report type
            recommended_window = cls.get_recommended_drift_window(report.period_type)

            # Determine which decile to display (fall back to global if sector not available)
            if use_sector_adjusted and sue_calc.sector_decile is not None:
                display_decile = sue_calc.sector_decile
            else:
                display_decile = sue_calc.global_decile

            opportunities.append({
                'ticker': stock.ticker,
                'company_name': stock.company_name,
                'sector': stock.sector or 'Unknown',
                'ftse_index': stock.ftse_index,
                'report_date': report.report_date.isoformat(),
                'reporting_period': report.reporting_period,
                'period_type': report.period_type,
                'actual_eps': report.actual_eps,
                'expected_eps': sue_calc.expected_eps,
                'sue_score': round(sue_calc.sue_score, 2) if sue_calc.sue_score else None,
                'sue_decile': display_decile,
                'global_decile': sue_calc.global_decile,
                'sector_decile': sue_calc.sector_decile,
                'quality_score': round(sue_calc.quality_score, 1) if sue_calc.quality_score else None,
                'quality_method': sue_calc.quality_calculation_method,
                'accruals_ratio': round(sue_calc.accruals_ratio, 3) if sue_calc.accruals_ratio else None,
                'cf_to_assets': round(sue_calc.cash_flow_to_assets, 3) if sue_calc.cash_flow_to_assets else None,
                'recommendation': sue_calc.recommendation,
                'recommendation_explanation': sue_calc.recommendation_explanation,
                'drift_window_days': drift_window_days,
                'drift_window_end': drift_end.isoformat(),
                'recommended_drift_window': recommended_window,
                'using_recommended_window': drift_window_days == recommended_window,
                # UI helper fields
                'decile_color': cls._get_decile_color(display_decile),
                'quality_color': cls._get_quality_color(sue_calc.quality_score),
                'rec_color': cls._get_recommendation_color(sue_calc.recommendation)
            })

        return opportunities

    @classmethod
    def generate_recommendation(
        cls,
        sue_score: float,
        sue_decile: int,
        quality_score: float,
        drift_window_days: int
    ) -> tuple[str, str]:
        """
        Generate investment recommendation based on SUE + quality.

        Recommendation Methodology:
        - HIGH SUE + HIGH QUALITY = STRONG_BUY (exploit drift with confidence)
        - HIGH SUE + MEDIUM QUALITY = BUY (positive signal, some risk)
        - HIGH SUE + LOW QUALITY = HOLD (risky - may be accruals-driven)
        - LOW SUE = AVOID (negative drift expected)

        Args:
            sue_score: SUE score value
            sue_decile: SUE decile rank (1-10)
            quality_score: Earnings quality score (0-100)
            drift_window_days: Drift window in days

        Returns:
            Tuple of (recommendation, explanation)
        """
        # HIGH SUE + HIGH QUALITY = STRONG_BUY
        if sue_decile >= cls.STRONG_BUY_SUE_DECILE and quality_score >= cls.STRONG_BUY_QUALITY:
            return (
                'STRONG_BUY',
                f'High earnings surprise (Decile {sue_decile}) backed by strong cash flow quality '
                f'({quality_score:.0f}/100). Academic research shows strongest PEAD effect in this category.'
            )

        # HIGH SUE + MEDIUM QUALITY = BUY
        elif sue_decile >= cls.BUY_SUE_DECILE and quality_score >= cls.BUY_QUALITY:
            return (
                'BUY',
                f'Positive earnings surprise (Decile {sue_decile}) with acceptable quality '
                f'({quality_score:.0f}/100). Expected drift over {drift_window_days} days.'
            )

        # HIGH SUE + LOW QUALITY = HOLD (Risky)
        elif sue_decile >= cls.BUY_SUE_DECILE and quality_score < cls.BUY_QUALITY:
            return (
                'HOLD',
                f'High earnings surprise (Decile {sue_decile}) but low quality ({quality_score:.0f}/100). '
                'Surprise may be driven by aggressive accounting (high accruals). Proceed with caution.'
            )

        # LOW SUE = AVOID (regardless of quality)
        elif sue_decile <= cls.AVOID_SUE_DECILE:
            return (
                'AVOID',
                f'Negative earnings surprise (Decile {sue_decile}) indicates downward drift risk '
                f'over {drift_window_days} days. Quality score: {quality_score:.0f}/100.'
            )

        # MEDIUM SUE + HIGH QUALITY = HOLD
        elif quality_score >= cls.STRONG_BUY_QUALITY:
            return (
                'HOLD',
                f'Moderate earnings surprise (Decile {sue_decile}) with high quality '
                f'({quality_score:.0f}/100). Weaker PEAD signal but solid fundamentals.'
            )

        # MEDIUM SUE + MEDIUM QUALITY = HOLD
        else:
            return (
                'HOLD',
                f'Moderate earnings surprise (Decile {sue_decile}) with medium quality '
                f'({quality_score:.0f}/100). Insufficient signal strength for action.'
            )

    @classmethod
    def get_recommended_drift_window(cls, period_type: str) -> int:
        """
        Get recommended drift window based on reporting frequency.

        UK companies use semi-annual reporting (H1/H2), which has longer
        drift periods than US quarterly reporting.

        Args:
            period_type: 'QUARTER', 'HALF', or 'ANNUAL'

        Returns:
            Recommended drift window in days
        """
        if period_type == 'QUARTER':
            return cls.DRIFT_WINDOW_QUARTERLY
        elif period_type == 'HALF':
            return cls.DRIFT_WINDOW_SEMI_ANNUAL
        else:  # ANNUAL
            return cls.DRIFT_WINDOW_EXTENDED

    @classmethod
    def _get_decile_color(cls, decile: Optional[int]) -> str:
        """Get Bootstrap color class for SUE decile badge."""
        if decile is None:
            return 'secondary'
        elif decile >= 9:
            return 'success'
        elif decile >= 7:
            return 'primary'
        elif decile >= 4:
            return 'warning'
        else:
            return 'danger'

    @classmethod
    def _get_quality_color(cls, quality: Optional[float]) -> str:
        """Get Bootstrap color class for quality score badge."""
        if quality is None:
            return 'secondary'
        elif quality >= 70:
            return 'success'
        elif quality >= 50:
            return 'primary'
        elif quality >= 30:
            return 'warning'
        else:
            return 'danger'

    @classmethod
    def _get_recommendation_color(cls, recommendation: Optional[str]) -> str:
        """Get Bootstrap color class for recommendation badge."""
        if recommendation == 'STRONG_BUY':
            return 'success'
        elif recommendation == 'BUY':
            return 'primary'
        elif recommendation == 'HOLD':
            return 'warning'
        elif recommendation == 'AVOID':
            return 'danger'
        else:
            return 'secondary'
