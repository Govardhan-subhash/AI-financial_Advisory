import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
from openai import OpenAI
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import joblib
from inflation import get_inflation_data
import json
from investment import get_investment_recommendations
# Load environment variables
load_dotenv()

app = Flask(__name__)




# Load trained model and preprocessing tools
model = joblib.load("risk_prediction_model.pkl")
scaler = joblib.load("scaler.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# Use .env variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")  # Example: postgresql://user:password@host:port/database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        # Get user input
        age = int(request.form["age"])
        salary = float(request.form["salary"])
        expenses = float(request.form["expenses"])
        
        # session
        session['age'] = age
        session['salary'] = salary
        session['expenses'] = expenses

        # Preprocess input
        input_data = np.array([[age, salary, expenses]])
        input_scaled = scaler.transform(input_data)  # Apply scaling

        # Predict risk category
        prediction = model.predict(input_scaled)
        risk_category = label_encoder.inverse_transform(prediction)[0]  # Convert back to label
        inflation_rates = get_inflation_data()

        # Define investment data
        investment_data = {
            "SIP": 12,  # Base rate for SIP
            "Fixed Deposit (FD)": 7,  # Base rate for FD
            "Mutual Funds": 15,  # Base rate for Mutual Funds
            "Gold Investment": 8  # Base rate for Gold
        }
        countries = ["Austria", "Germany", "Belgium"]

        # Get dynamically adjusted investment returns based on inflation data
        investments = get_investment_recommendations(investment_data,countries)

        # Render the result page
        return render_template("result.html", risk=risk_category, age=age, salary=salary, expenses=expenses, inflation=inflation_rates, investments=investments)

    return render_template("input.html")
# Function to get AI-generated investment advice
def get_investment_advice(age, salary, expenses, risk, inflation_rates):
    prompt = f"""
    Given a user with:
    - Age: {age} years
    - Salary: ₹{salary}
    - Monthly Expenses: ₹{expenses}
    - Risk Appetite: {risk} (Low, Medium, or High)
    - Inflation Rates: Austria: {inflation_rates['Austria']}%, Germany: {inflation_rates['Germany']}%, Belgium: {inflation_rates['Belgium']}%
  Suggest an investment strategy with:
    - Diversified investment options (FDs, SIPs, Mutual Funds, Gold, etc.)
    - Estimated returns for each investment over 1, 3, and 5 years for remaining money 
    - Safe vs Risky investments based on risk level
    - Emergency fund recommendation amount in rupees 
    Provide a JSON response with:
    {{
        "investments": {{
            "Fixed Deposit": {{"1_year": "₹...", "3_years": "₹...", "5_years": "₹..."}},
            "SIP": {{"1_year": "₹...", "3_years": "₹...", "5_years": "₹..."}},
            "Mutual Funds": {{"1_year": "₹...", "3_years": "₹...", "5_years": "₹..."}},
            "Gold": {{"1_year": "₹...", "3_years": "₹...", "5_years": "₹..."}}
        }},
        "returns": {{
            "1_year": "₹...",
            "3_years": "₹...",
            "5_years": "₹..."
        }},
       
        "emergency_fund": {{
        "months": 6,
        "amount": "₹{{ expenses * 6 }}"
    }}
    }}

    Return **only valid JSON** without additional text.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a financial advisor. Provide responses in JSON format only."},
            {"role": "user", "content": prompt}
        ]
    )

    try:
        return json.loads(response.choices[0].message.content)  # Ensure valid JSON
    except json.JSONDecodeError:
        return {"error": "Invalid JSON received from OpenAI"}
@app.route("/advise", methods=["GET","POST"])
def advise():
    # Get stored data from session
    age = session.get("age")
    salary = session.get("salary")
    expenses = session.get("expenses")

    # Get user-inputted risk level
    risk = request.form["risk"]

    # Get real-time inflation rates
    inflation_rates = get_inflation_data()

    # Get AI-generated recommendations
    investment_data = get_investment_advice(age, salary, expenses, risk, inflation_rates)
    print(investment_data["returns"])
    return render_template(
        "advise.html",
        risk=risk,
        age=age,
        salary=salary,
        expenses=expenses,
        investments=investment_data["investments"],
        returns=investment_data["returns"],
        emergency_fund=investment_data["emergency_fund"],
        inflation=inflation_rates  # Pass dynamic inflation rates to the template
    )
# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
