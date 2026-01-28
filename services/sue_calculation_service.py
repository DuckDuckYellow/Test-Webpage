"""
SUE Calculation Service for PEAD Screener.

Implements Standardized Unexpected Earnings (SUE) methodology:
- Expected EPS using seasonal random walk model
- Forecast error standard deviation calculation
- Bayesian shrinkage for small samples
- Global and sector-specific decile ranking
"""
import statistics
from typing import List, Dict, Tuple, Optional
from datetime import date
from models.financial import EarningsReport, SUECalculation, Stock, SectorStatistics
from extensions import db


class SUECalculationService:
    """
    SUE calculation engine.

    Academic methodology: (Actual - Expected) / StdDev(forecast errors)
    """

    # Minimum historical periods required for SUE calculation
    MIN_HISTORY_QUARTERS = 4

    # Threshold for Bayesian shrinkage (reduce impact of small samples)
    BAYESIAN_SAMPLE_THRESHOLD = 6

    # Bayesian shrinkage weights
    BAYESIAN_WEIGHT_RAW = 0.7  # Weight for raw SUE score
    BAYESIAN_WEIGHT_SECTOR = 0.3  # Weight for sector mean

    @classmethod
    def calculate_sue_for_stock(
        cls,
        stock_id: int,
        current_report: EarningsReport,
        historical_reports: List[EarningsReport]
    ) -> Tuple[Optional[float], Dict]:
        """
        Calculate SUE score for a single earnings announcement.

        Formula: SUE = (Actual - Expected) / StdDev(forecast errors)

        Args:
            stock_id: Stock database ID
            current_report: Current earnings report
            historical_reports: List of past reports (ordered desc by date)

        Returns:
            Tuple of (sue_score, metadata)
            - sue_score: Standardized unexpected earnings (None if insufficient data)
            - metadata: Dict with expected_eps, forecast_error, stddev, etc.
        """
        metadata = {
            'expected_eps': None,
            'forecast_error': None,
            'forecast_error_stddev': None,
            'method': None,
            'small_sample_corrected': False
        }

        # Check minimum history requirement
        if len(historical_reports) < cls.MIN_HISTORY_QUARTERS:
            metadata['method'] = 'INSUFFICIENT_DATA'
            return None, metadata

        # Step 1: Calculate expected EPS (seasonal random walk)
        expected_eps, method = cls.calculate_expected_eps(current_report, historical_reports)
        if expected_eps is None:
            metadata['method'] = method
            return None, metadata

        metadata['expected_eps'] = expected_eps
        metadata['method'] = method

        # Step 2: Calculate forecast error
        forecast_error = current_report.actual_eps - expected_eps
        metadata['forecast_error'] = forecast_error

        # Step 3: Calculate standard deviation of historical forecast errors
        forecast_error_stddev = cls.calculate_forecast_error_stddev(historical_reports)

        if forecast_error_stddev is None:
            metadata['method'] = 'INSUFFICIENT_DATA'
            return None, metadata

        metadata['forecast_error_stddev'] = forecast_error_stddev

        # Step 4: Calculate raw SUE score
        # For very small stddev (consistent growth), prevent extreme values by capping
        EPSILON = 1e-10  # Threshold for essentially-zero stddev

        if forecast_error_stddev < EPSILON:
            # Perfect or near-perfect consistency - use sign of forecast error only
            sue_score = 10.0 if forecast_error > 0 else -10.0 if forecast_error < 0 else 0.0
        else:
            sue_score = forecast_error / forecast_error_stddev
            # Cap SUE scores to prevent outliers from dominating (academic literature uses ±10)
            sue_score = max(-10.0, min(10.0, sue_score))

        # Step 5: Apply Bayesian shrinkage if small sample
        if len(historical_reports) < cls.BAYESIAN_SAMPLE_THRESHOLD:
            # Note: Sector mean adjustment happens later in batch processing
            # For now, just flag that this should be corrected
            metadata['small_sample_corrected'] = True

        return sue_score, metadata

    @classmethod
    def calculate_expected_eps(
        cls,
        current_report: EarningsReport,
        historical_reports: List[EarningsReport]
    ) -> Tuple[Optional[float], str]:
        """
        Calculate expected EPS using seasonal random walk model.

        Methodology: Expected EPS = EPS from same period last year

        For semi-annual reporters (UK standard):
        - H1-24 → H1-23
        - H2-24 → H2-23

        For quarterly reporters:
        - Q1-24 → Q1-23
        - Q2-24 → Q2-23

        Args:
            current_report: Current earnings report
            historical_reports: List of past reports (ordered desc by date)

        Returns:
            Tuple of (expected_eps, method_used)
        """
        # Find matching period from last year
        target_period = cls._find_same_period_last_year(
            current_report.reporting_period,
            current_report.period_type
        )

        if target_period is None:
            return None, 'INVALID_PERIOD_FORMAT'

        # Search for matching historical report
        for report in historical_reports:
            if report.reporting_period == target_period:
                return report.actual_eps, 'SEASONAL_RANDOM_WALK'

        # If no exact match, return None
        return None, 'NO_MATCHING_PERIOD'

    @classmethod
    def calculate_forecast_error_stddev(
        cls,
        historical_reports: List[EarningsReport]
    ) -> Optional[float]:
        """
        Calculate standard deviation of forecast errors.

        Uses actual vs same-period-last-year errors from historical data.

        Args:
            historical_reports: List of past reports (ordered desc by date)

        Returns:
            Standard deviation of forecast errors (None if insufficient data)
        """
        if len(historical_reports) < cls.MIN_HISTORY_QUARTERS:
            return None

        forecast_errors = []

        # Calculate forecast errors for each historical period
        for i, current in enumerate(historical_reports[:-1]):  # Exclude last (oldest) report
            # Find matching period from previous year
            target_period = cls._find_same_period_last_year(
                current.reporting_period,
                current.period_type
            )

            if target_period is None:
                continue

            # Search for matching prior report
            for prior in historical_reports[i+1:]:
                if prior.reporting_period == target_period:
                    # Forecast error = Actual - Expected (same period last year)
                    error = current.actual_eps - prior.actual_eps
                    forecast_errors.append(error)
                    break

        # Need at least 2 data points for standard deviation
        if len(forecast_errors) < 2:
            return None

        try:
            return statistics.stdev(forecast_errors)
        except statistics.StatisticsError:
            # All values identical (zero variance)
            return 0.0

    @classmethod
    def _find_same_period_last_year(
        cls,
        reporting_period: str,
        period_type: str
    ) -> Optional[str]:
        """
        Find the corresponding reporting period from last year.

        Examples:
        - H1-24 → H1-23
        - H2-24 → H2-23
        - Q1-24 → Q1-23
        - Q4-23 → Q4-22

        Args:
            reporting_period: Current period (e.g., 'H1-24', 'Q2-23')
            period_type: Period type ('HALF', 'QUARTER', 'ANNUAL')

        Returns:
            Corresponding period from last year (None if format invalid)
        """
        try:
            # Split period into components
            parts = reporting_period.split('-')
            if len(parts) != 2:
                return None

            period_label = parts[0]  # e.g., 'H1', 'Q2', 'FY'
            year_suffix = parts[1]  # e.g., '24', '23'

            # Convert year suffix to integer and decrement
            year_int = int(year_suffix)
            prior_year = year_int - 1

            # Handle century rollover (00 → 99)
            if prior_year < 0:
                prior_year = 99

            # Format back to 2-digit year
            prior_year_str = f"{prior_year:02d}"

            return f"{period_label}-{prior_year_str}"

        except (ValueError, IndexError):
            return None

    @classmethod
    def assign_decile_ranks(
        cls,
        sue_calculations: List[SUECalculation],
        batch_id: int,
        use_sector_adjusted: bool = True
    ) -> None:
        """
        Assign global and sector-specific decile ranks to SUE calculations.

        Decile 10 = highest SUE (good news)
        Decile 1 = lowest SUE (bad news)

        Also calculates sector statistics for Bayesian shrinkage.

        Args:
            sue_calculations: List of SUE calculations for this batch
            batch_id: Upload batch ID
            use_sector_adjusted: If True, also compute sector-specific deciles
        """
        # Filter out calculations without valid SUE scores
        valid_calcs = [calc for calc in sue_calculations if calc.sue_score is not None]

        if not valid_calcs:
            return

        # Sort by SUE score (ascending)
        sorted_calcs = sorted(valid_calcs, key=lambda x: x.sue_score)

        # Assign global deciles (1-10)
        total_count = len(sorted_calcs)
        for idx, calc in enumerate(sorted_calcs):
            # Calculate decile (1-indexed)
            # Use ceiling division to ensure values 1-10
            decile = min(10, max(1, int((idx + 1) / total_count * 10) + 1))
            calc.global_decile = decile

        # Assign sector-specific deciles if requested
        if use_sector_adjusted:
            cls._assign_sector_deciles(valid_calcs, batch_id)

        # Apply Bayesian shrinkage to small sample stocks
        cls._apply_bayesian_shrinkage_batch(sue_calculations, batch_id)

    @classmethod
    def _assign_sector_deciles(
        cls,
        sue_calculations: List[SUECalculation],
        batch_id: int
    ) -> None:
        """
        Assign sector-specific decile ranks.

        Stocks are ranked within their sector, allowing for sector rotation strategies.

        Args:
            sue_calculations: List of valid SUE calculations
            batch_id: Upload batch ID
        """
        # Group calculations by sector
        sector_groups = {}
        for calc in sue_calculations:
            # Get stock to access sector
            stock = Stock.query.get(calc.stock_id)
            if not stock or not stock.sector:
                continue

            sector = stock.sector
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(calc)

        # Assign deciles within each sector
        for sector, calcs in sector_groups.items():
            if not calcs:
                continue

            # Sort by SUE score within sector
            sorted_sector_calcs = sorted(calcs, key=lambda x: x.sue_score)
            sector_count = len(sorted_sector_calcs)

            for idx, calc in enumerate(sorted_sector_calcs):
                # Calculate sector-specific decile
                sector_decile = min(10, max(1, int((idx + 1) / sector_count * 10) + 1))
                calc.sector_decile = sector_decile

            # Calculate sector statistics for Bayesian shrinkage
            cls._calculate_sector_statistics(sector, calcs, batch_id)

    @classmethod
    def _calculate_sector_statistics(
        cls,
        sector: str,
        calcs: List[SUECalculation],
        batch_id: int
    ) -> None:
        """
        Calculate sector-level SUE statistics for Bayesian shrinkage.

        Args:
            sector: Sector name
            calcs: SUE calculations for this sector
            batch_id: Upload batch ID
        """
        sue_scores = [calc.sue_score for calc in calcs if calc.sue_score is not None]

        if len(sue_scores) < 2:
            return

        sue_mean = statistics.mean(sue_scores)
        sue_median = statistics.median(sue_scores)

        try:
            sue_stddev = statistics.stdev(sue_scores)
        except statistics.StatisticsError:
            sue_stddev = 0.0

        # Calculate decile thresholds
        sorted_scores = sorted(sue_scores)
        decile_1_threshold = sorted_scores[max(0, int(len(sorted_scores) * 0.1) - 1)]
        decile_10_threshold = sorted_scores[min(len(sorted_scores) - 1, int(len(sorted_scores) * 0.9))]

        # Create sector statistics record
        sector_stats = SectorStatistics(
            upload_batch_id=batch_id,
            sector=sector,
            sue_mean=sue_mean,
            sue_median=sue_median,
            sue_stddev=sue_stddev,
            stock_count=len(sue_scores),
            decile_1_threshold=decile_1_threshold,
            decile_10_threshold=decile_10_threshold
        )

        db.session.add(sector_stats)

    @classmethod
    def _apply_bayesian_shrinkage_batch(
        cls,
        sue_calculations: List[SUECalculation],
        batch_id: int
    ) -> None:
        """
        Apply Bayesian shrinkage to stocks with small sample sizes.

        Methodology: If stock has <6 historical periods, shrink SUE score
        toward sector mean to reduce noise from limited data.

        Adjusted SUE = 0.7 * Raw SUE + 0.3 * Sector Mean SUE

        Args:
            sue_calculations: All SUE calculations for batch
            batch_id: Upload batch ID
        """
        # Get sector statistics
        sector_stats_map = {}
        sector_stats = SectorStatistics.query.filter_by(upload_batch_id=batch_id).all()

        for stats in sector_stats:
            sector_stats_map[stats.sector] = stats

        # Apply shrinkage to small sample stocks
        for calc in sue_calculations:
            if not calc.small_sample_corrected:
                continue

            # Get stock sector
            stock = Stock.query.get(calc.stock_id)
            if not stock or not stock.sector:
                continue

            # Get sector statistics
            stats = sector_stats_map.get(stock.sector)
            if not stats:
                continue

            # Apply Bayesian shrinkage
            if calc.sue_score is not None:
                adjusted_sue = (
                    cls.BAYESIAN_WEIGHT_RAW * calc.sue_score +
                    cls.BAYESIAN_WEIGHT_SECTOR * stats.sue_mean
                )
                calc.sue_score = adjusted_sue
