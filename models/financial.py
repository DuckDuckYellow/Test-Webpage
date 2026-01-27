"""
Financial data models for PEAD screening.

Database schema for FTSE 100/250 earnings analysis with SQLAlchemy ORM.
Tables: Stock, EarningsReport, SUECalculation, UploadBatch, SectorStatistics
"""
from extensions import db
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship


class Stock(db.Model):
    """FTSE 100/250 stock master record."""
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    ftse_index = Column(String(10), nullable=False)  # 'FTSE100' or 'FTSE250'
    sector = Column(String(100), nullable=True)
    fiscal_year_end_month = Column(Integer, nullable=True)  # 1-12

    # Relationships
    earnings_reports = relationship('EarningsReport', back_populates='stock', cascade='all, delete-orphan')
    sue_calculations = relationship('SUECalculation', back_populates='stock', cascade='all, delete-orphan')

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Stock {self.ticker} - {self.company_name}>'


class EarningsReport(db.Model):
    """Individual earnings announcement with financial metrics."""
    __tablename__ = 'earnings_reports'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)

    # Reporting details
    report_date = Column(Date, nullable=False, index=True)
    reporting_period = Column(String(20), nullable=False)  # 'H1-24', 'H2-24', 'Q1-24', etc.
    period_type = Column(String(10), nullable=False)  # 'HALF', 'QUARTER', 'ANNUAL'
    fiscal_year_end_month = Column(Integer, nullable=True)

    # Earnings data
    actual_eps = Column(Float, nullable=False)
    net_income = Column(Float, nullable=False)

    # Cash flow metrics
    operating_cash_flow = Column(Float, nullable=False)

    # Balance sheet metrics
    total_assets = Column(Float, nullable=False)

    # Operating accruals components (for industrial quality calculation)
    change_in_receivables = Column(Float, nullable=True)
    change_in_inventory = Column(Float, nullable=True)
    change_in_payables = Column(Float, nullable=True)
    depreciation = Column(Float, nullable=True)

    # Calculated fields (populated by service)
    total_accruals = Column(Float, nullable=True)  # NI - OCF
    operating_accruals = Column(Float, nullable=True)  # ΔAR + ΔInv - ΔAP - Dep

    # Financial-specific metrics (for bank/insurance quality)
    return_on_assets = Column(Float, nullable=True)  # NI / Total Assets
    total_debt = Column(Float, nullable=True)  # For leverage calculations

    # Upload tracking
    upload_batch_id = Column(Integer, ForeignKey('upload_batches.id'), nullable=False)

    # Relationships
    stock = relationship('Stock', back_populates='earnings_reports')
    upload_batch = relationship('UploadBatch', back_populates='earnings_reports')

    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite index for time-series queries
    __table_args__ = (
        Index('idx_stock_report_date', 'stock_id', 'report_date'),
    )

    def __repr__(self):
        return f'<EarningsReport {self.stock_id} - {self.report_date} - {self.reporting_period}>'


class SUECalculation(db.Model):
    """SUE score and quality metrics for earnings announcement."""
    __tablename__ = 'sue_calculations'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)

    # SUE calculation
    actual_eps = Column(Float, nullable=False)
    expected_eps = Column(Float, nullable=True)  # From seasonal model
    forecast_error = Column(Float, nullable=True)  # Actual - Expected
    forecast_error_stddev = Column(Float, nullable=True)  # StdDev of historical errors
    sue_score = Column(Float, nullable=True)  # (Actual - Expected) / StdDev
    small_sample_corrected = Column(Boolean, default=False)  # Bayesian shrinkage applied?

    # Decile rankings (1-10, where 10 = highest SUE)
    global_decile = Column(Integer, nullable=True)  # Across all FTSE stocks
    sector_decile = Column(Integer, nullable=True)  # Within sector only

    # Quality metrics
    accruals_ratio = Column(Float, nullable=True)  # Total Accruals / Total Assets
    operating_accruals_ratio = Column(Float, nullable=True)  # Operating Accruals / Total Assets
    cash_flow_to_assets = Column(Float, nullable=True)  # OCF / Total Assets
    quality_score = Column(Float, nullable=True)  # Composite 0-100
    quality_calculation_method = Column(String(30), nullable=True)  # 'INDUSTRIAL_OPERATING', 'FINANCIAL_COMPOSITE', etc.

    # Recommendation
    recommendation = Column(String(20), nullable=True)  # 'STRONG_BUY', 'BUY', 'HOLD', 'AVOID'
    recommendation_explanation = Column(String(500), nullable=True)

    # Drift tracking (for backtesting)
    drift_window_days = Column(Integer, nullable=True)  # 60, 90, or 120
    drift_window_start = Column(Date, nullable=True)
    drift_window_end = Column(Date, nullable=True)
    drift_return_pct = Column(Float, nullable=True)

    # Upload tracking
    upload_batch_id = Column(Integer, ForeignKey('upload_batches.id'), nullable=False, index=True)

    # Relationships
    stock = relationship('Stock', back_populates='sue_calculations')
    upload_batch = relationship('UploadBatch', back_populates='sue_calculations')

    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite indexes for screening queries
    __table_args__ = (
        Index('idx_batch_decile', 'upload_batch_id', 'global_decile'),
        Index('idx_batch_quality', 'upload_batch_id', 'quality_score'),
    )

    def __repr__(self):
        return f'<SUECalculation {self.stock_id} - {self.report_date} - SUE: {self.sue_score}>'


class UploadBatch(db.Model):
    """Track data upload sessions for multi-user isolation."""
    __tablename__ = 'upload_batches'

    id = Column(Integer, primary_key=True)
    batch_uuid = Column(String(36), unique=True, nullable=False, index=True)
    user_session_id = Column(String(100), nullable=False)  # Flask session.sid

    # Upload metadata
    ftse_index = Column(String(10), nullable=False)  # 'FTSE100', 'FTSE250', or 'BOTH'
    stock_count = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)

    # User preferences
    default_drift_window = Column(Integer, nullable=False, default=60)  # Days (60/90/120)

    # Relationships
    earnings_reports = relationship('EarningsReport', back_populates='upload_batch', cascade='all, delete-orphan')
    sue_calculations = relationship('SUECalculation', back_populates='upload_batch', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<UploadBatch {self.batch_uuid} - {self.stock_count} stocks>'


class SectorStatistics(db.Model):
    """Sector-level SUE statistics for cross-sectional normalization."""
    __tablename__ = 'sector_statistics'

    id = Column(Integer, primary_key=True)
    upload_batch_id = Column(Integer, ForeignKey('upload_batches.id'), nullable=False, index=True)
    sector = Column(String(100), nullable=False)

    # SUE distribution statistics
    sue_mean = Column(Float, nullable=False)
    sue_median = Column(Float, nullable=False)
    sue_stddev = Column(Float, nullable=False)
    stock_count = Column(Integer, nullable=False)

    # Thresholds for sector-adjusted decile ranking
    decile_1_threshold = Column(Float, nullable=True)  # Lowest 10%
    decile_10_threshold = Column(Float, nullable=True)  # Highest 10%

    __table_args__ = (
        Index('idx_batch_sector', 'upload_batch_id', 'sector'),
    )

    def __repr__(self):
        return f'<SectorStatistics {self.sector} - {self.stock_count} stocks>'
