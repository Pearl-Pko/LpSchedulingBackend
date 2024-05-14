from flask import Flask, request, jsonify, abort
from flask_cors import CORS 
import pulp

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return jsonify({"status": "success", "message": "Server is up and running"}), 200

# Define parameters
num_days = 6  # Number of days in a week (Monday to Saturday)
num_shifts = 3  # Number of shifts per day (morning, afternoon, evening)
num_rest_days = 2

@app.route("/allocate-shifts", methods=["POST"])
def get_timetable():
    num_employees = request.json["num_employees"]
    
    # Create a new ILP problem
    prob = pulp.LpProblem("Hospital_Shift_Management", pulp.LpMaximize)

    # Define decision variables
    x = [[[pulp.LpVariable(f"x_{i}_{j}_{k}", cat=pulp.LpBinary) for k in range(num_days)] for j in range(num_shifts)] for i in range(num_employees)]

    # Define objective function
    prob += pulp.lpSum(x[i][j][k] for k in range(num_days) for j in range(num_shifts) for i in range(num_employees))

    # Single Shift per Day Constraint
    for i in range(num_employees):
        for k in range(num_days):
            prob += pulp.lpSum(x[i][j][k] for j in range(num_shifts)) <= 1

    # Minimum Employees per Shift Constraint
    for j in range(num_shifts):
        for k in range(num_days):
            prob += pulp.lpSum(x[i][j][k] for i in range(num_employees))  >= int(((num_days - num_rest_days) / num_days) * (num_employees / num_shifts))   
            prob += pulp.lpSum(x[i][j][k] for i in range(num_employees)) <= int(num_employees / num_shifts)
    
    # maximum shits in a week for a given
    for i in range(num_employees):
        prob += pulp.lpSum(x[i][j][k] for j in range(num_shifts) for k in range(num_days)) == (num_days - num_rest_days)
            
    status = prob.solve()
    
    res = format_response(x, num_employees)
    
    return jsonify({'status': pulp.LpStatus[status], "res": res}), 200

def format_response(x, num_employees):
    result = []
    
    for i in range(num_employees):
        for j in range(num_shifts):
            for k in range(num_days):
                if pulp.value(x[i][j][k]):
                    result.append(f"x_{i}_{j}_{k}")
                    
    return result
                    

@app.errorhandler(Exception)
def handle_exception(error):
    # Log the exception
    app.logger.error(f'An error occurred: {str(error)}')

    # Return a JSON response with error message
    return jsonify({"status": "error", 'message': 'Internal Server Error'}), 500

app.run(debug=True)