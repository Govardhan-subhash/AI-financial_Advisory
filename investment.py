import json
from inflation import get_inflation_data
#from market_data import fetch_market_data  # Fetching real-time investment data

# Dynamic Investment Calculation Functions
def calculate_compound_interest(investment, rate, years):
    """Calculate returns using compound interest formula."""
    return round(investment * ((1 + (rate / 100)) ** years), 2)

def adjust_for_inflation(base_rate, inflation_rate):
    """Dynamically adjust investment rates based on inflation."""
    return base_rate + inflation_rate

def get_investment_recommendations(investment_data, countries, investment_amount):
    """Get dynamically adjusted investment recommendations based on inflation."""
    inflation_data = get_inflation_data()
    investments_adjusted = {}

    for country in countries:
        inflation_rate = inflation_data.get(country, 0)
        investments_adjusted[country] = {}

        for investment_type, base_rate in investment_data.items():
            adjusted_rate = adjust_for_inflation(base_rate, inflation_rate)
            investments_adjusted[country][investment_type] = calculate_compound_interest(
                investment=investment_amount, rate=adjusted_rate, years=10
            )

    return investments_adjusted
