import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests
import numpy as np
import openai
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import joblib
from inflation import get_inflation_data
import json
from investment import get_investment_recommendations
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load trained model and preprocessing tools
model = joblib.load("risk_prediction_model.pkl")
scaler = joblib.load("scaler.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# Use .env variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
INF_API_KEY = os.getenv("INF_API_KEY")
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

API_BASE = "https://api.api-ninjas.com/v1/"
HEADERS = {"X-Api-Key": INF_API_KEY}

# Base percentage values for fallback
BASE_VALUES = {
    "gold": 8.0,  # Default percentage return for gold
    "stocks": 10.0,  # Default percentage return for stocks
    "crypto": 15.0,  # Default percentage return for cryptocurrency
    "interest_rate": 7.0,  # Default interest rate for Fixed Deposits
    "sip": 12.0,  # Default percentage return for SIP
    "mutual_funds": 10.0,  # Default percentage return for Mutual Funds
    "reits": 8.0 , # Default percentage return for REITs
    "aggressive_mutual_funds":14,
    
    #"Fixed_Deposits": 7.0 # Default percentage return for Fixed Deposits
    
}

# Function to fetch the investment value
def fetch_investment_value(investment_type):
    try:
        # Fetch market data for different investments
        market_data = fetch_market_data()

        # Based on the investment_type, return the correct value from market_data
        if investment_type == "Gold":
            return market_data.get("gold", BASE_VALUES["gold"])
        elif investment_type == "Stocks":
            return market_data.get("stocks", BASE_VALUES["stocks"])
        elif investment_type == "Crypto":
            return market_data.get("crypto", BASE_VALUES["crypto"])
        elif investment_type == "Fixed_Deposit":
            return market_data.get("interest_rate", BASE_VALUES["interest_rate"])
        elif investment_type == "SIP":
            return market_data.get("sip", BASE_VALUES["sip"])
        elif investment_type == "Mutual Funds":
            return market_data.get("mutual_funds", BASE_VALUES["mutual_funds"])
        elif investment_type == "REITs":
            return market_data.get("reits", BASE_VALUES["reits"])
        elif investment_type=="Aggressive mutual funds":
            return market_data.get("aggressive_mutual_funds", BASE_VALUES["aggressive_mutual_funds"])
        else:
            return 0  # Default value for other investments
    except Exception as e:
        print(f"Error fetching investment value for {investment_type}: {e}")
        return 0  # Return a default value in case of an error

# Function to fetch market data (returns percentage values for investments)
def fetch_market_data():
    try:
        # Example API calls for different investments
        gold = requests.get(API_BASE + "goldprice", headers=HEADERS).json()
        stocks = requests.get(API_BASE + "stockprice?symbol=TSLA", headers=HEADERS).json()
        crypto = requests.get(API_BASE + "cryptoprice?symbol=BTCUSDT", headers=HEADERS).json()
        interest_rate = requests.get(API_BASE + "interestrate", headers=HEADERS).json()
        sip = requests.get(API_BASE + "sipreturns", headers=HEADERS).json()  # Example for SIP
        mutual_funds = requests.get(API_BASE + "mutualfunds", headers=HEADERS).json()  # Example for Mutual Funds
        reits = requests.get(API_BASE + "reitsreturns", headers=HEADERS).json()  # Example for REITs
        aggressive_mutual_funds=requests.get(API_BASE + "aggressivemutualfunds", headers=HEADERS).json()
    

        # Validate and set fallback values if response is empty or invalid
        return {
            "gold": gold.get("percentage_return", BASE_VALUES["gold"]) if gold else BASE_VALUES["gold"],
            "stocks": stocks.get("percentage_return", BASE_VALUES["stocks"]) if stocks else BASE_VALUES["stocks"],
            "crypto": crypto.get("percentage_return", BASE_VALUES["crypto"]) if crypto else BASE_VALUES["crypto"],
            "interest_rate": interest_rate.get("percentage_return", BASE_VALUES["interest_rate"]) if interest_rate else BASE_VALUES["interest_rate"],
            "sip": sip.get("percentage_return", BASE_VALUES["sip"]) if sip else BASE_VALUES["sip"],
            "mutual_funds": mutual_funds.get("percentage_return", BASE_VALUES["mutual_funds"]) if mutual_funds else BASE_VALUES["mutual_funds"],
            "reits": reits.get("percentage_return", BASE_VALUES["reits"]) if reits else BASE_VALUES["reits"],
            "aggressive_mutual_funds":aggressive_mutual_funds.get("percentage_return",BASE_VALUES["aggressive_mutual_funds"]) if aggressive_mutual_funds else BASE_VALUES["aggressive_mutual_funds"]
            
        }
    except Exception as e:
        # If there's any exception, return base values
        print(f"Error fetching market data: {e}")
        return BASE_VALUES  # Return base values if any error occurs

# Home Page Route
@app.route('/')
def index():
    return render_template('index.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Getting JSON data (instead of form data)
        data = request.get_json()

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Check if password is empty
        if not password:
            return jsonify({'message': 'Password cannot be empty'}), 400

        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'Email already exists'}), 400

        # Create new user
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Return success message
        return jsonify({'message': 'User registered successfully!'}), 201

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return jsonify({'message': 'Login successful'}), 200

        return jsonify({'message': 'Invalid credentials'}), 401

    return render_template('login.html')

@app.route("/input", methods=["GET", "POST"])
def input():
    if request.method == "POST":
        age = int(request.form["age"])
        salary = float(request.form["salary"])
        Medical=float(request.form["Medical"])
        Entertainment=float(request.form["Entertainment"])
        Groceries=float(request.form["Groceries"])
        Vacation=float(request.form["Vacation"])
        Other=float(request.form["Other"])
        
        

        # Store session data
        session.update({"age": age, "salary": salary,"Other":Other,"Vacation":Vacation,"Medical":Medical,"Groceries":Groceries,"Entertainment":Entertainment})
        expenses=Medical+Groceries+Vacation+Entertainment+Other
        # Preprocess user input
        input_data = np.array([[age, salary, expenses]])
        input_scaled = scaler.transform(input_data)
        
        # Predict risk category
        prediction = model.predict(input_scaled)
        risk_category = label_encoder.inverse_transform(prediction)[0]

        # Get inflation rates dynamically
        inflation_rates = get_inflation_data()

        # Define investment types & base rates
        investment_data = {"SIP": 12, "Fixed Deposit": 7, "Mutual Funds": 15, "Gold Investment": 8}
        countries = ["India", "Belgium", "Germany"]  # More relevant countries

        # Allocate salary using the 50/30/20 budgeting rule
        needs = salary * 0.50
        wants = salary * 0.30
        investments_amount = salary * 0.20  # Dynamic investment amount

        # Get investment recommendations based on real-time inflation data
        investments = get_investment_recommendations(investment_data, countries, investments_amount)

        return render_template(
           "result.html",
            risk=risk_category,
            age=age,
            salary=salary,
            expenses=expenses,
            inflation=inflation_rates,
            investments=investments
        )

    return render_template("input.html")

# AI-Generated Investment Advice
def get_ai_investment_advice(age, salary, expenses, risk, inflation_rates):
    prompt = f"""
    You are a financial advisor. Based on the following user data:
    - Age: {age} years
    - Salary: ₹{salary}
    - Monthly Expenses: ₹{expenses}
    - Risk Appetite: {risk} (Low, Medium, or High)
    - Inflation Rates: {inflation_rates}
    - Market Data: {fetch_market_data()}  

    Apply the 50/30/20 rule to allocate salary:
    - 50% for Needs
    - 30% for Wants
    - 20% for Investments

    Suggest the following investment options based on the risk appetite:
    - **Low Risk**: Fixed Deposit,Mutual Funds, Gold.
    - **Medium Risk**: SIPs, Balanced Mutual Funds, REITs,Gold.
    - **High Risk**: Stocks, Crypto, Gold ,REITs,Aggressive mutual funds.
    Set aside an emergency fund equal to 6 months of expenses.

    Your response should include ONLY the following in **JSON format**:

     {{
        "emergency_fund": "₹{expenses * 6}",
        "investable_amount": "₹{salary * 0.20}",
        "investments": {{
            "Fixed Deposit": "{fetch_investment_value('Fixed_Deposit')}",
            "SIP": "{fetch_investment_value('SIP')}",
            "Mutual Funds": "{fetch_investment_value('Mutual Funds')}",
            "Gold": "{fetch_investment_value('Gold')}",
            "Stocks": "{fetch_investment_value('Stocks')}",
            "Crypto": "{fetch_investment_value('Crypto')}",
            "REITs": "{fetch_investment_value('REITs')}",
            "Aggressive mutual funds": "{fetch_investment_value('Aggressive Mutual Funds')}"
        }},
        "returns": {{
            "1_year": "12%",
            "3_years": "14%",
            "5_years": "17.6%"
        }}
    }}

    **Do not include anything else** such as salary breakdown, inflation rates, or returns projections.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "You are a financial advisor. Provide responses in JSON format only, as instructed."
            }, {
                "role": "user",
                "content": prompt
            }]
        )

        response_content = response.choices[0].message.content
        print("Raw response from OpenAI:", response_content)

        # Extract JSON block from the response
        json_match = re.search(r'```json\n(.*?)\n```', response_content, re.DOTALL)
        if json_match:
            cleaned_response = json_match.group(1)
        else:
            cleaned_response = response_content

        if not cleaned_response:
            print("Error: Empty response received.")
            return None

        try:
            investment_advice = json.loads(cleaned_response)
            return investment_advice
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON received from OpenAI. {e}")
            print(f"Raw response: {response_content}")  # Log raw response
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None
def calculate_investment_amount(investable_amount, return_rate, years):
    """
    Calculate the investment return amount based on the given investable amount,
    return rate (percentage), and duration in years.
    """
    if investable_amount is None:
        return 0  # Avoid NoneType errors

    investable_amount = float(investable_amount)  # Convert to float
    return_rate = float(return_rate)  # Convert to float

    # Apply compound interest formula: A = P(1 + r/100)^t
    final_amount = investable_amount * ((1 + return_rate / 100) ** years)

    return round(final_amount, 2)  # Return rounded amount


@app.route("/advise", methods=["GET", "POST"])
def advise():
    # Get session data (age, salary, expenses)
    age = session.get("age")
    salary = session.get("salary")
    Vacation = float(session.get("Vacation"))
    Entertainment = float(session.get("Entertainment"))
    Groceries = float(session.get("Groceries"))
    Medical = float(session.get("Medical"))
    Other = float(session.get("Other"))
    expenses= Medical + Entertainment+ Groceries + Vacation + Other
    

    # Set default risk level to "Medium" if not provided
    risk = request.form.get("risk", "Medium")  # Default to 'Medium' if not provided

    # Apply 50/30/20 budgeting rule
    needs = 0.50 * float(salary)
    wants = 0.30 * float(salary)
    savings = 0.20 * float(salary)  # 20% of salary allocated to savings

    # Fetch real-time inflation data (for display)
    inflation_rates = get_inflation_data()

    # Fetch AI-powered investment advice
    investment_data = get_ai_investment_advice(age, salary, expenses, risk, inflation_rates)

    if investment_data is None:
        return "Error: AI investment advice not available.", 500  # Server error

    # Ensure investment_data is a valid dictionary
    if not isinstance(investment_data, dict):
        return "Error: Invalid response format received from AI. Expected a dictionary.", 500  # Server error

    # Extract emergency fund recommendation
    emergency_fund = float(investment_data.get("emergency_fund").replace("₹", "")) # Default to ₹0 if key doesn't exist

    # Convert emergency fund to float if it contains the ₹ symbol
    if isinstance(emergency_fund, str):
        emergency_fund = float(emergency_fund.replace("₹", ""))  # Remove ₹ symbol
    else:
        emergency_fund = float(emergency_fund)  # If it's already a number, just use it

    # Extract investment data from the AI response (SIP, Mutual Funds, etc.)
    investments_breakdown = investment_data.get("investments", {})
    
    # Use AI-provided investment values or fall back to the calculated savings
    sip_amount = float(investments_breakdown.get("SIP", "0").replace("₹", "").replace("%", ""))
    mutual_funds_amount = float(investments_breakdown.get("Mutual Funds", "0").replace("₹", "").replace("%", ""))
    reits_amount = float(investments_breakdown.get("REITs", "0").replace("₹", "").replace("%", ""))
    # Assign the rest (e.g., Fixed Deposit, Gold) as 0 for now
    fixed_deposit_amount = float(investments_breakdown.get("Fixed Deposit", "0").replace("₹", "").replace("%", ""))

    gold_amount = float(investments_breakdown.get("Gold", "0").replace("₹", "").replace("%", ""))
    stocks_amount = float(investments_breakdown.get("Stocks", "0").replace("₹", "").replace("%", ""))
    crypto_amount = float(investments_breakdown.get("Crypto", "0").replace("₹", "").replace("%", ""))
    
    # Calculate total investments from the AI response
    total_investments = sip_amount + mutual_funds_amount + reits_amount + fixed_deposit_amount + gold_amount + stocks_amount + crypto_amount

    # Use the 50/30/20 rule for investments if AI data is not provided
    investments = savings if total_investments == 0 else total_investments
    investable_amount=investment_data.get("investable_amount")
    investable_amount=investable_amount.replace("₹", "")
    # Extract the investment breakdown based on the user's risk appetite

    investment_breakdown = investment_data.get("investments", {})

    # Calculate the number of investments (based on the current breakdown)

    # # Process investment details
    # investments_details = {}
    # for investment, amount in investment_breakdown.items():
    #     try:
    #         # Fetch amount from response and remove ₹ symbol if present
    #         return_r = float(amount.replace("₹", ""))
    #         x=calculate_investment_amount(investable_amount,return_r, years=1)# Remove ₹ symbol
    #         investments_details[investment] = {
    #             "amount": f"{x}",
    #             "returns": f"{return_r:,.2f}"  # Set returns as N/A or calculate if needed
    #         }
    #     except ValueError:
    #         investments_details[investment] = {
    #             "amount": "₹0.00",
    #             "returns": "₹0.00"
    #         }
              # Process investment details
    investments_details = {}
    for investment, amount in investment_breakdown.items():
        try:
        # Fetch amount and remove ₹ symbol
            return_r = float(amount)  

        # Calculate returns for 1, 3, and 5 years
            return_1_year = calculate_investment_amount(float(investable_amount), return_r, 1)
            return_3_years = calculate_investment_amount(float(investable_amount), return_r, 3)
            return_5_years = calculate_investment_amount(float(investable_amount), return_r, 5)

            investments_details[investment] = {
                "amount": f"₹{float(investable_amount):,.2f}",
                 "returns_1_year": f"₹{return_1_year:,.2f}",
                 "returns_3_years": f"₹{return_3_years:,.2f}",
                 "returns_5_years": f"₹{return_5_years:,.2f}"
         }
        except ValueError:
            investments_details[investment] = {
            "amount": "₹0.00",
            "returns_1_year": "₹0.00",
            "returns_3_years": "₹0.00",
            "returns_5_years": "₹0.00"
        }


    # Add Needs, Wants, and Investments breakdown
    investments_details["Needs"] = {"amount": f"₹{needs:,.2f}", "returns": "0.00%"}
    investments_details["Wants"] = {"amount": f"₹{wants:,.2f}", "returns": "0.00%"}
    investments_details["Investments"] = {"amount": f"₹{investments:,.2f}", "returns": "0.00%"}

    # Extract projected returns for 1, 3, and 5 years from AI response if available
    returns_projection = investment_data.get("returns", {
        "1_year": "N/A",
        "3_years": "N/A",
        "5_years": "N/A"
    })

    # Debugging Output
   # print("Processed Investment Data:", investments_details)
   # print("Projected Returns Extracted:", returns_projection)

    # Template mapping based on risk level
    template_map = {
        "low": "low.html",
        "medium": "medium.html",
        "high": "high.html"
    }

    # Render template with updated investment data
    return render_template(
        template_map.get(risk.lower(), "medium.html"),
        risk=risk,
        age=age,
        salary=salary,
        expenses=expenses,
        investments=investments_details,
        emergency_fund=emergency_fund,
        inflation=inflation_rates,
        expected_returns=returns_projection,
        investable_amount=investable_amount
    )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
