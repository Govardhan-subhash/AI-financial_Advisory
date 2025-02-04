import requests
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# API Key for inflation data
API_KEY = os.getenv("INF_API_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO)

def get_inflation_data():
    """Fetch inflation rates for Austria, Germany, and Mexico from API."""
    try:
        url = "https://api.api-ninjas.com/v1/inflation"
        headers = {"X-Api-Key": API_KEY}
        
        # Make the API call to get inflation data
        response = requests.get(url, headers=headers)
        
        # Check if the API call was successful
        if response.status_code == 200:
            data = response.json()
            logging.info(f"API Response: {data}")
            
            # Initialize a dictionary to store inflation rates
            inflation_rates = {"Austria": 0.0,
                               "Germany": 0.0,
                               "Belgium": 0.0}
            
            # Country mapping for better handling of variations
            country_mapping = {
                "austria": "Austria",
                "germany": "Germany",
                "belgium": "Belgium"
            }
            
            # Process each entry in the API response
            for entry in data:
                country = entry.get("country", "").lower()
                yearly_rate_pct = entry.get("yearly_rate_pct", 0)
                
                # Update the inflation rate for the relevant countries
                country_key = country_mapping.get(country)
                if country_key:
                    inflation_rates[country_key] = yearly_rate_pct
            
            return inflation_rates
        else:
            raise ValueError(f"Failed to fetch inflation data. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error fetching inflation data: {e}")
        return {"Austria": 0.0, "Germany": 0.0, "Mexico": 0.0}

# Test the function
if __name__ == "__main__":
    print(get_inflation_data())
