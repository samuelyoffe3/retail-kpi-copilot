import pandas as pd
import datetime
import calendar
import numpy as np

def calculate_kpis(df, target=0):
    """
    Calculates monthly KPIs based on normalized sales dataframe.
    
    Args:
        df: DataFrame with 'date', 'transaction_id', 'line_amount'
        target: Monthly target amount (float)
        
    Returns:
        Dictionary containing calculated KPIs and period info.
    """
    if df is None or df.empty:
        return None

    # 1. Period Logic
    period_end = df['date'].max()
    year = period_end.year
    month = period_end.month
    
    # Get last day of the specific month (e.g., 28, 30, 31)
    _, days_in_month = calendar.monthrange(year, month)
    
    month_start = period_end.replace(day=1)
    
    # Elapsed days (inclusive of period_end)
    elapsed_days = (period_end - month_start).days + 1
    
    # Remaining days
    remaining_days = days_in_month - period_end.day

    # 2. Transaction Netting Logic
    # Group by transaction_id to handle returns (negative rows in same txn)
    txn_totals = df.groupby('transaction_id')['line_amount'].sum()
    
    # Only positive transactions count as sales (standard retail logic)
    positive_txns = txn_totals[txn_totals > 0]
    
    actual_to_date = positive_txns.sum()

    # 3. KPI Calculations
    avg_daily_performance = actual_to_date / max(elapsed_days, 1)

    # Required daily to hit target
    remainder_to_target = max(target - actual_to_date, 0)
    # Avoid div by zero if remaining_days is 0
    if remaining_days > 0:
        required_daily_performance = remainder_to_target / remaining_days
    else:
        # If no days left, required is technically local infinity or 0 if matched
        required_daily_performance = 0 

    projected_finish_amount = avg_daily_performance * days_in_month
    
    projected_finish_percent = 0
    if target > 0:
        projected_finish_percent = (projected_finish_amount / target) * 100

    return {
        "period_end_date": period_end,
        "actual_to_date": actual_to_date,
        "target": target,
        "avg_daily": avg_daily_performance,
        "required_daily": required_daily_performance,
        "projected_amount": projected_finish_amount,
        "projected_percent": projected_finish_percent,
        "days_in_month": days_in_month,
        "elapsed_days": elapsed_days
    }
