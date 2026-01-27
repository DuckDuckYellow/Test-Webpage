"""
CSV Parser Service for PEAD Screener.

Parses uploaded CSV files containing FTSE 100/250 earnings data.
Validates required columns, converts data types, and handles malformed data.
"""
import pandas as pd
from io import StringIO
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class CSVParserService:
    """
    CSV parser for earnings data uploads.

    Validates structure, parses financial metrics, and reports errors.
    """

    # Required columns (must be present)
    REQUIRED_COLUMNS = [
        'Ticker',
        'Company Name',
        'Report Date',
        'Reporting Period',
        'Period Type',
        'Actual EPS',
        'Net Income',
        'Operating Cash Flow',
        'Total Assets'
    ]

    # Optional columns (used for operating accruals calculation)
    OPTIONAL_COLUMNS = [
        'Change in Receivables',
        'Change in Inventory',
        'Change in Payables',
        'Depreciation',
        'Total Debt',
        'Sector',
        'Fiscal Year End Month'
    ]

    # Valid period types
    VALID_PERIOD_TYPES = {'HALF', 'QUARTER', 'ANNUAL'}

    @classmethod
    def parse_csv(cls, csv_content: str) -> Tuple[List[Dict], List[str]]:
        """
        Parse CSV content into list of stock dictionaries.

        Args:
            csv_content: Raw CSV file content as string

        Returns:
            Tuple of (parsed_data, errors)
            - parsed_data: List of dictionaries with validated stock data
            - errors: List of error messages
        """
        errors = []
        parsed_data = []

        try:
            # Parse CSV with pandas
            df = pd.read_csv(StringIO(csv_content))

            # Validate required columns
            missing_cols = set(cls.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")
                return [], errors

            # Process each row
            for idx, row in df.iterrows():
                row_num = idx + 2  # Excel row number (1-indexed + header)

                # Validate row
                row_error = cls.validate_row(row, row_num)
                if row_error:
                    errors.append(row_error)
                    continue

                # Convert to dictionary with validated data types
                try:
                    stock_data = {
                        'ticker': str(row['Ticker']).strip().upper(),
                        'company_name': str(row['Company Name']).strip(),
                        'report_date': cls._parse_date(row['Report Date'], row_num, 'Report Date'),
                        'reporting_period': str(row['Reporting Period']).strip(),
                        'period_type': str(row['Period Type']).strip().upper(),
                        'actual_eps': float(row['Actual EPS']),
                        'net_income': float(row['Net Income']),
                        'operating_cash_flow': float(row['Operating Cash Flow']),
                        'total_assets': float(row['Total Assets']),
                    }

                    # Add optional columns if present
                    for col in cls.OPTIONAL_COLUMNS:
                        if col in df.columns and pd.notna(row[col]):
                            # Convert column name to snake_case key
                            key = col.lower().replace(' ', '_')

                            # Parse fiscal year end month as integer
                            if col == 'Fiscal Year End Month':
                                try:
                                    stock_data[key] = int(row[col])
                                    if not (1 <= stock_data[key] <= 12):
                                        errors.append(f"Row {row_num}: Fiscal Year End Month must be 1-12")
                                        continue
                                except ValueError:
                                    errors.append(f"Row {row_num}: Invalid Fiscal Year End Month")
                                    continue
                            else:
                                # Numeric columns
                                try:
                                    stock_data[key] = float(row[col])
                                except ValueError:
                                    # Skip invalid optional numeric values
                                    pass

                    parsed_data.append(stock_data)

                except (ValueError, TypeError) as e:
                    errors.append(f"Row {row_num}: Data type conversion error - {str(e)}")
                    continue

            # Check if we got any valid data
            if not parsed_data and not errors:
                errors.append("No valid data found in CSV file")

            return parsed_data, errors

        except pd.errors.ParserError as e:
            errors.append(f"CSV parsing error: {str(e)}")
            return [], errors
        except Exception as e:
            errors.append(f"Unexpected error parsing CSV: {str(e)}")
            return [], errors

    @classmethod
    def validate_row(cls, row: pd.Series, row_num: int) -> Optional[str]:
        """
        Validate a single row of data.

        Args:
            row: Pandas Series representing a row
            row_num: Row number for error reporting

        Returns:
            Error message if validation fails, None if valid
        """
        # Check ticker
        if pd.isna(row['Ticker']) or str(row['Ticker']).strip() == '':
            return f"Row {row_num}: Missing Ticker"

        ticker = str(row['Ticker']).strip()
        if len(ticker) > 10:
            return f"Row {row_num}: Ticker '{ticker}' exceeds 10 characters"

        # Check company name
        if pd.isna(row['Company Name']) or str(row['Company Name']).strip() == '':
            return f"Row {row_num}: Missing Company Name"

        # Check period type
        if pd.isna(row['Period Type']):
            return f"Row {row_num}: Missing Period Type"

        period_type = str(row['Period Type']).strip().upper()
        if period_type not in cls.VALID_PERIOD_TYPES:
            return f"Row {row_num}: Period Type must be one of {cls.VALID_PERIOD_TYPES}, got '{period_type}'"

        # Check numeric fields are not missing
        numeric_fields = ['Actual EPS', 'Net Income', 'Operating Cash Flow', 'Total Assets']
        for field in numeric_fields:
            if pd.isna(row[field]):
                return f"Row {row_num}: Missing {field}"

        # Check Total Assets > 0 (prevent division by zero)
        try:
            total_assets = float(row['Total Assets'])
            if total_assets <= 0:
                return f"Row {row_num}: Total Assets must be positive (got {total_assets})"
        except (ValueError, TypeError):
            return f"Row {row_num}: Total Assets must be a number"

        # Check report date is valid
        try:
            date_obj = cls._parse_date(row['Report Date'], row_num, 'Report Date')

            # Check date is not in future
            if date_obj > datetime.now().date():
                return f"Row {row_num}: Report Date cannot be in the future"
        except ValueError as e:
            return str(e)

        return None

    @classmethod
    def _parse_date(cls, date_str: str, row_num: int, field_name: str) -> datetime.date:
        """
        Parse date string to datetime.date object.

        Args:
            date_str: Date string (YYYY-MM-DD or other common formats)
            row_num: Row number for error reporting
            field_name: Field name for error reporting

        Returns:
            datetime.date object

        Raises:
            ValueError: If date parsing fails
        """
        if pd.isna(date_str):
            raise ValueError(f"Row {row_num}: Missing {field_name}")

        # Try common date formats
        date_formats = [
            '%Y-%m-%d',  # 2024-08-15
            '%d/%m/%Y',  # 15/08/2024
            '%m/%d/%Y',  # 08/15/2024
            '%Y/%m/%d',  # 2024/08/15
            '%d-%m-%Y',  # 15-08-2024
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt).date()
            except ValueError:
                continue

        # If no format worked, raise error
        raise ValueError(f"Row {row_num}: Invalid {field_name} format (expected YYYY-MM-DD)")
