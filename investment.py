from inflation import get_inflation_data

# Investment Calculation Functions

def calculate_sip_returns(investment, rate, years):
    """Calculate SIP returns using compound interest formula."""
    return round(investment * ((1 + (rate / 100)) ** years), 2)

def calculate_fd_returns(investment, rate, years):
    """Calculate Fixed Deposit (FD) returns."""
    return round(investment * ((1 + (rate / 100)) ** years), 2)

def calculate_mutual_fund_returns(investment, rate, years):
    """Calculate Mutual Fund returns."""
    return round(investment * ((1 + (rate / 100)) ** years), 2)

def calculate_gold_returns(investment, rate, years):
    """Calculate Gold investment returns."""
    return round(investment * ((1 + (rate / 100)) ** years), 2)

def adjust_for_inflation(base_rate, inflation_rate):
    """Adjust the base rate for inflation. The adjusted rate will be dynamic."""
    adjusted_rate = base_rate + inflation_rate
    return adjusted_rate

def get_investment_recommendations(investment_data, countries):
    """Get dynamically adjusted investment recommendations based on real-time inflation."""
    # Fetch inflation data dynamically from the API
    inflation_data = get_inflation_data()

    # Initialize dictionary to store adjusted investments for each country
    investments_adjusted = {}

    # Loop over each country
    for country in countries:
        # Get inflation rate for the selected country (default to 0 if no data for the country)
        inflation_rate = inflation_data.get(country, 0)

        # Initialize dictionary for adjusted investments for this country
        investments_adjusted[country] = {}

        # Loop over each investment type and apply the inflation adjustment
        for investment_type, base_rate in investment_data.items():
            # Adjust the base rate using the selected country's inflation rate
            adjusted_rate = adjust_for_inflation(base_rate, inflation_rate)

            # Calculate the returns for each investment type
            if investment_type == "SIP":
                investments_adjusted[country][investment_type] = calculate_sip_returns(investment=10000, rate=adjusted_rate, years=10)
            elif investment_type == "Fixed Deposit (FD)":
                investments_adjusted[country][investment_type] = calculate_fd_returns(investment=10000, rate=adjusted_rate, years=5)
            elif investment_type == "Mutual Funds":
                investments_adjusted[country][investment_type] = calculate_mutual_fund_returns(investment=10000, rate=adjusted_rate, years=10)
            elif investment_type == "Gold Investment":
                investments_adjusted[country][investment_type] = calculate_gold_returns(investment=10000, rate=adjusted_rate, years=10)

    return investments_adjusted


# Test the function
if __name__ == "__main__":
    # Investment base rates for each type of investment
    investment_data = {
        "SIP": 12,  # Base rate for SIP
        "Fixed Deposit (FD)": 7,  # Base rate for FD
        "Mutual Funds": 15,  # Base rate for Mutual Funds
        "Gold Investment": 8  # Base rate for Gold
    }

    # List of countries for inflation adjustment
    countries = ["Austria", "Germany", "MBelgium"]

    # Get the adjusted investment recommendations for each country
    investments = get_investment_recommendations(investment_data, countries)
    print(investments)
