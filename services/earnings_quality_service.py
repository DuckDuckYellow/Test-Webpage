"""
Earnings Quality Service for PEAD Screener.

Sector-aware earnings quality metrics:
- Industrials/Retail: Operating Accruals (Sloan 1996) + Cash Flow
- Financials: ROA Persistence + Cash Flow Quality
- Utilities: Conservative Accounting (MVP uses industrial method)

Quality score scale: 0-100 (higher = better quality earnings)
"""
import statistics
from typing import List, Tuple, Optional
from models.financial import Stock, EarningsReport


class EarningsQualityService:
    """
    Earnings quality calculation engine with sector-specific methodologies.

    Key Innovation: Different quality metrics for different sectors
    (operating accruals don't work for banks/insurance).
    """

    # Sector classifications
    FINANCIAL_SECTORS = {'Financials', 'Banks', 'Insurance', 'Financial Services'}
    UTILITY_SECTORS = {'Utilities', 'Energy'}

    # Quality score weights (sector-dependent)
    INDUSTRIAL_WEIGHTS = {
        'accruals': 0.6,  # 60% weight on accruals quality
        'cash_flow': 0.4  # 40% weight on cash flow
    }

    FINANCIAL_WEIGHTS = {
        'roa_persistence': 0.5,  # 50% weight on earnings stability
        'cash_flow': 0.3,  # 30% weight on cash flow quality
        'leverage': 0.2  # 20% weight on leverage stability (future enhancement)
    }

    @classmethod
    def calculate_quality_score_for_stock(
        cls,
        stock: Stock,
        current_report: EarningsReport,
        historical_reports: List[EarningsReport]
    ) -> Tuple[Optional[float], str]:
        """
        Calculate quality score with sector-aware methodology.

        Args:
            stock: Stock model instance
            current_report: Current earnings report
            historical_reports: Historical reports for this stock

        Returns:
            Tuple of (quality_score, methodology_used)
            - quality_score: 0-100 scale (None if insufficient data)
            - methodology: 'INDUSTRIAL_OPERATING', 'FINANCIAL_COMPOSITE', etc.
        """
        sector = stock.sector or 'Unknown'

        # Route to sector-specific calculation
        if sector in cls.FINANCIAL_SECTORS:
            return cls._calculate_financial_quality(
                current_report,
                historical_reports
            )
        elif sector in cls.UTILITY_SECTORS:
            # MVP: Use industrial method for utilities
            return cls._calculate_industrial_quality(
                current_report,
                historical_reports
            )
        else:
            # Default: Industrial methodology
            return cls._calculate_industrial_quality(
                current_report,
                historical_reports
            )

    @classmethod
    def _calculate_industrial_quality(
        cls,
        current_report: EarningsReport,
        historical_reports: List[EarningsReport]
    ) -> Tuple[Optional[float], str]:
        """
        Industrial quality: Operating Accruals + Cash Flow.

        Uses Sloan (1996) methodology for accruals-based earnings quality.

        Formula:
        - Accruals Score = 100 - |Accruals Ratio| * Multiplier
        - Cash Flow Score = Cash Flow / Assets * 100
        - Quality = 60% Accruals + 40% Cash Flow

        Args:
            current_report: Current earnings report
            historical_reports: Historical reports (not used in MVP)

        Returns:
            Tuple of (quality_score, methodology)
        """
        quality_components = []

        # Component 1: Accruals Ratio (60% weight)
        accruals_ratio, method = cls.calculate_accruals_ratio(
            current_report.net_income,
            current_report.operating_cash_flow,
            current_report.total_assets,
            current_report.change_in_receivables,
            current_report.change_in_inventory,
            current_report.change_in_payables,
            current_report.depreciation
        )

        if accruals_ratio is not None:
            # Calculate accruals score
            # Multiplier depends on whether we have operating accruals
            multiplier = 500 if method == 'OPERATING' else 250

            # Lower accruals = higher quality
            accruals_score = max(0, 100 - (abs(accruals_ratio) * multiplier))
            quality_components.append(accruals_score * cls.INDUSTRIAL_WEIGHTS['accruals'])

        # Component 2: Cash Flow to Assets (40% weight)
        cf_ratio = cls.calculate_cash_flow_to_assets(
            current_report.operating_cash_flow,
            current_report.total_assets
        )

        if cf_ratio is not None:
            # Convert to 0-100 scale
            # Typical CF/Assets range: -0.2 to 0.3
            # Normalize to 0-100
            cf_score = min(max(cf_ratio * 100, 0), 100)
            quality_components.append(cf_score * cls.INDUSTRIAL_WEIGHTS['cash_flow'])

        # Calculate composite quality score
        if quality_components:
            quality_score = sum(quality_components)
            methodology = f'INDUSTRIAL_{method}' if accruals_ratio is not None else 'INDUSTRIAL_CF_ONLY'
            return quality_score, methodology

        # Insufficient data
        return None, 'INSUFFICIENT_DATA'

    @classmethod
    def _calculate_financial_quality(
        cls,
        current_report: EarningsReport,
        historical_reports: List[EarningsReport]
    ) -> Tuple[Optional[float], str]:
        """
        Financial services quality: ROA Persistence + Cash Flow + Leverage.

        Banks/insurance don't have meaningful "inventory" or "receivables"
        in the industrial sense. Instead, focus on earnings stability.

        Components:
        1. ROA Persistence (50% weight) - Stable earnings generation
        2. Cash Flow Quality (30% weight) - Operating cash flow / assets
        3. Leverage Stability (20% weight) - Capital adequacy (MVP: not implemented)

        Args:
            current_report: Current earnings report
            historical_reports: Historical reports for stability calculation

        Returns:
            Tuple of (quality_score, methodology)
        """
        quality_components = []

        # Component 1: ROA Persistence (50% weight)
        roa_persistence = cls._calculate_roa_persistence(
            current_report,
            historical_reports
        )

        if roa_persistence is not None:
            quality_components.append(
                roa_persistence * cls.FINANCIAL_WEIGHTS['roa_persistence']
            )

        # Component 2: Cash Flow Quality (30% weight)
        cf_ratio = cls.calculate_cash_flow_to_assets(
            current_report.operating_cash_flow,
            current_report.total_assets
        )

        if cf_ratio is not None:
            cf_score = min(max(cf_ratio * 100, 0), 100)
            quality_components.append(
                cf_score * cls.FINANCIAL_WEIGHTS['cash_flow']
            )

        # Component 3: Leverage Stability (20% weight) - MVP: Placeholder
        # Future enhancement: Calculate leverage ratio volatility
        # For now, omit this component

        # Calculate composite quality score
        if quality_components:
            # Normalize to account for missing leverage component
            total_weight = (
                cls.FINANCIAL_WEIGHTS['roa_persistence'] +
                cls.FINANCIAL_WEIGHTS['cash_flow']
            )
            quality_score = sum(quality_components) * (1.0 / total_weight)

            return quality_score, 'FINANCIAL_COMPOSITE'

        # Insufficient data
        return None, 'INSUFFICIENT_DATA'

    @classmethod
    def calculate_accruals_ratio(
        cls,
        net_income: float,
        operating_cash_flow: float,
        total_assets: float,
        change_receivables: Optional[float],
        change_inventory: Optional[float],
        change_payables: Optional[float],
        depreciation: Optional[float]
    ) -> Tuple[Optional[float], str]:
        """
        Calculate accruals ratio (Sloan 1996).

        Two methods:
        1. Operating Accruals (preferred): ΔAR + ΔInv - ΔAP - Dep
        2. Total Accruals (fallback): Net Income - Operating Cash Flow

        Args:
            net_income: Net income
            operating_cash_flow: Operating cash flow
            total_assets: Total assets
            change_receivables: Year-over-year change in receivables
            change_inventory: Year-over-year change in inventory
            change_payables: Year-over-year change in payables
            depreciation: Depreciation expense

        Returns:
            Tuple of (accruals_ratio, method_used)
            - accruals_ratio: Accruals / Total Assets
            - method: 'OPERATING' or 'TOTAL'
        """
        if total_assets <= 0:
            return None, 'INVALID_ASSETS'

        # Try operating accruals first (more precise)
        if all(x is not None for x in [change_receivables, change_inventory, change_payables, depreciation]):
            operating_accruals = (
                change_receivables +
                change_inventory -
                change_payables -
                depreciation
            )
            operating_accruals_ratio = operating_accruals / total_assets
            return operating_accruals_ratio, 'OPERATING'

        # Fallback to total accruals
        total_accruals = net_income - operating_cash_flow
        total_accruals_ratio = total_accruals / total_assets
        return total_accruals_ratio, 'TOTAL'

    @classmethod
    def calculate_cash_flow_to_assets(
        cls,
        operating_cash_flow: float,
        total_assets: float
    ) -> Optional[float]:
        """
        Calculate cash flow to assets ratio.

        Formula: Operating Cash Flow / Total Assets

        Higher ratio = better cash-generating efficiency

        Args:
            operating_cash_flow: Operating cash flow
            total_assets: Total assets

        Returns:
            Cash flow to assets ratio (None if invalid)
        """
        if total_assets <= 0:
            return None

        return operating_cash_flow / total_assets

    @classmethod
    def _calculate_roa_persistence(
        cls,
        current_report: EarningsReport,
        historical_reports: List[EarningsReport]
    ) -> Optional[float]:
        """
        Calculate ROA (Return on Assets) persistence for financial institutions.

        Methodology:
        1. Calculate ROA for each period: Net Income / Total Assets
        2. Measure stability (inverse of StdDev)
        3. Higher stability = higher quality (persistent earnings)

        Lower ROA volatility = higher earnings quality

        Args:
            current_report: Current earnings report
            historical_reports: Historical reports

        Returns:
            Persistence score 0-100 (higher = more stable ROA)
        """
        # Need at least 2 periods for standard deviation
        if len(historical_reports) < 2:
            return None

        # Calculate ROA for current and historical periods
        roa_values = []

        # Current ROA
        if current_report.total_assets > 0:
            current_roa = current_report.net_income / current_report.total_assets
            roa_values.append(current_roa)

        # Historical ROAs
        for report in historical_reports[:7]:  # Use up to 8 periods total
            if report.total_assets > 0:
                roa = report.net_income / report.total_assets
                roa_values.append(roa)

        if len(roa_values) < 2:
            return None

        # Calculate stability (lower StdDev = higher quality)
        try:
            roa_mean = statistics.mean(roa_values)
            roa_std = statistics.stdev(roa_values)
        except statistics.StatisticsError:
            # All values identical (perfect stability)
            return 100.0

        # Normalize StdDev to 0-100 score
        # Typical bank ROA StdDev: 0.005 - 0.02
        # Lower StdDev = higher score
        normalized_std = min(roa_std / 0.02, 1.0)
        persistence_score = 100 * (1 - normalized_std)

        return max(0, persistence_score)

    @classmethod
    def _calculate_leverage_stability(
        cls,
        current_report: EarningsReport,
        historical_reports: List[EarningsReport]
    ) -> Optional[float]:
        """
        Calculate leverage stability (for financial institutions).

        MVP Placeholder: Not implemented in current version.

        Lower volatility in leverage = better capital management = higher quality

        Args:
            current_report: Current earnings report
            historical_reports: Historical reports

        Returns:
            Leverage stability score 0-100 (None for MVP)
        """
        # MVP: Return None (component not calculated)
        # Future enhancement: Calculate Total Debt / Total Assets volatility
        return None
