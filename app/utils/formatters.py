from datetime import datetime

def format_currency(amount, currency='USD'):
    """Format currency with symbol and 2 decimal places"""
    return f"{currency} {amount:,.2f}"

def format_date(date_obj):
    """Format datetime object to string"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    return str(date_obj)
