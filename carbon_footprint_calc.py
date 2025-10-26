from flask import Flask, render_template_string, request, jsonify
import json

app = Flask(__name__)

# Emission factors (kg CO2 per unit)
EMISSION_FACTORS = {
    'car_petrol': 0.192,      # per km
    'car_diesel': 0.171,      # per km
    'car_electric': 0.053,    # per km
    'bus': 0.089,             # per km
    'train': 0.041,           # per km
    'flight_short': 0.255,    # per km (< 1500km)
    'flight_long': 0.195,     # per km (> 1500km)
    'electricity': 0.5,       # per kWh
    'natural_gas': 2.03,      # per m³
    'meat_high': 7.26,        # per day
    'meat_medium': 5.63,      # per day
    'meat_low': 4.67,         # per day
    'vegetarian': 3.91,       # per day
    'vegan': 2.89,            # per day
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carbon Footprint Calculator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 30px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 15px;
            border-left: 5px solid #11998e;
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        
        input[type="number"], select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        input[type="number"]:focus, select:focus {
            outline: none;
            border-color: #11998e;
        }
        
        .btn {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 50px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(17, 153, 142, 0.3);
        }
        
        .result {
            display: none;
            margin-top: 30px;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            color: white;
            text-align: center;
        }
        
        .result.show {
            display: block;
            animation: slideIn 0.5s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .result h3 {
            font-size: 2em;
            margin-bottom: 15px;
        }
        
        .result .total {
            font-size: 3em;
            font-weight: bold;
            margin: 20px 0;
        }
        
        .result .comparison {
            font-size: 1.1em;
            opacity: 0.95;
            margin-top: 15px;
        }
        
        .breakdown {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 25px;
        }
        
        .breakdown-item {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
        }
        
        .breakdown-item h4 {
            font-size: 0.9em;
            margin-bottom: 5px;
            opacity: 0.9;
        }
        
        .breakdown-item p {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .tips {
            margin-top: 30px;
            padding: 20px;
            background: #fff3cd;
            border-radius: 10px;
            border-left: 5px solid #ffc107;
        }
        
        .tips h3 {
            color: #856404;
            margin-bottom: 15px;
        }
        
        .tips ul {
            color: #856404;
            padding-left: 20px;
        }
        
        .tips li {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 Carbon Footprint Calculator</h1>
            <p>Calculate your annual carbon emissions</p>
        </div>
        
        <div class="content">
            <form id="carbonForm">
                <div class="section">
                    <h2>🚗 Transportation</h2>
                    
                    <div class="form-group">
                        <label for="car_type">Car Type:</label>
                        <select id="car_type" name="car_type">
                            <option value="none">No car</option>
                            <option value="car_petrol">Petrol</option>
                            <option value="car_diesel">Diesel</option>
                            <option value="car_electric">Electric</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="car_km">Kilometers driven per year:</label>
                        <input type="number" id="car_km" name="car_km" value="0" min="0">
                    </div>
                    
                    <div class="form-group">
                        <label for="public_transport_km">Public transport (bus/train) per week (km):</label>
                        <input type="number" id="public_transport_km" name="public_transport_km" value="0" min="0">
                    </div>
                    
                    <div class="form-group">
                        <label for="flights_short">Short-haul flights (&lt;1500km) per year:</label>
                        <input type="number" id="flights_short" name="flights_short" value="0" min="0">
                    </div>
                    
                    <div class="form-group">
                        <label for="flights_long">Long-haul flights (&gt;1500km) per year:</label>
                        <input type="number" id="flights_long" name="flights_long" value="0" min="0">
                    </div>
                </div>
                
                <div class="section">
                    <h2>⚡ Energy Use</h2>
                    
                    <div class="form-group">
                        <label for="electricity">Electricity usage per month (kWh):</label>
                        <input type="number" id="electricity" name="electricity" value="0" min="0">
                    </div>
                    
                    <div class="form-group">
                        <label for="natural_gas">Natural gas usage per month (m³):</label>
                        <input type="number" id="natural_gas" name="natural_gas" value="0" min="0">
                    </div>
                </div>
                
                <div class="section">
                    <h2>🍽️ Diet</h2>
                    
                    <div class="form-group">
                        <label for="diet">Diet type:</label>
                        <select id="diet" name="diet">
                            <option value="meat_high">High meat consumption (daily)</option>
                            <option value="meat_medium">Medium meat consumption (3-4 times/week)</option>
                            <option value="meat_low">Low meat consumption (1-2 times/week)</option>
                            <option value="vegetarian">Vegetarian</option>
                            <option value="vegan">Vegan</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" class="btn">Calculate My Footprint</button>
            </form>
            
            <div class="result" id="result">
                <h3>Your Annual Carbon Footprint</h3>
                <div class="total" id="totalEmissions">0</div>
                <p class="comparison" id="comparison"></p>
                
                <div class="breakdown">
                    <div class="breakdown-item">
                        <h4>Transportation</h4>
                        <p id="transportEmissions">0 kg</p>
                    </div>
                    <div class="breakdown-item">
                        <h4>Energy</h4>
                        <p id="energyEmissions">0 kg</p>
                    </div>
                    <div class="breakdown-item">
                        <h4>Food</h4>
                        <p id="foodEmissions">0 kg</p>
                    </div>
                </div>
            </div>
            
            <div class="tips">
                <h3>💡 Tips to Reduce Your Carbon Footprint</h3>
                <ul>
                    <li>Use public transportation, bike, or walk when possible</li>
                    <li>Switch to renewable energy sources for your home</li>
                    <li>Reduce meat consumption and eat more plant-based meals</li>
                    <li>Improve home insulation to reduce heating/cooling needs</li>
                    <li>Choose video calls over business flights when possible</li>
                    <li>Buy local and seasonal products</li>
                    <li>Reduce, reuse, and recycle to minimize waste</li>
                </ul>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('carbonForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            fetch('/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                document.getElementById('totalEmissions').textContent = 
                    result.total.toFixed(0) + ' kg CO₂';
                document.getElementById('transportEmissions').textContent = 
                    result.breakdown.transport.toFixed(0) + ' kg';
                document.getElementById('energyEmissions').textContent = 
                    result.breakdown.energy.toFixed(0) + ' kg';
                document.getElementById('foodEmissions').textContent = 
                    result.breakdown.food.toFixed(0) + ' kg';
                document.getElementById('comparison').textContent = result.comparison;
                
                document.getElementById('result').classList.add('show');
                document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    
    # Transportation emissions
    transport_emissions = 0
    
    # Car emissions
    car_type = data.get('car_type', 'none')
    if car_type != 'none':
        car_km = float(data.get('car_km', 0))
        transport_emissions += car_km * EMISSION_FACTORS[car_type]
    
    # Public transport (weekly to yearly)
    public_km = float(data.get('public_transport_km', 0)) * 52
    transport_emissions += public_km * (EMISSION_FACTORS['bus'] + EMISSION_FACTORS['train']) / 2
    
    # Flights
    flights_short = float(data.get('flights_short', 0))
    flights_long = float(data.get('flights_long', 0))
    transport_emissions += flights_short * 800 * EMISSION_FACTORS['flight_short']  # avg 800km per short flight
    transport_emissions += flights_long * 4000 * EMISSION_FACTORS['flight_long']  # avg 4000km per long flight
    
    # Energy emissions (monthly to yearly)
    energy_emissions = 0
    electricity = float(data.get('electricity', 0)) * 12
    natural_gas = float(data.get('natural_gas', 0)) * 12
    energy_emissions += electricity * EMISSION_FACTORS['electricity']
    energy_emissions += natural_gas * EMISSION_FACTORS['natural_gas']
    
    # Food emissions (daily to yearly)
    diet = data.get('diet', 'meat_medium')
    food_emissions = EMISSION_FACTORS[diet] * 365
    
    # Total emissions
    total_emissions = transport_emissions + energy_emissions + food_emissions
    
    # Comparison (global average is about 4 tons per person)
    global_avg = 4000  # kg
    if total_emissions < global_avg * 0.75:
        comparison = "Great! You're below the global average! 🌱"
    elif total_emissions < global_avg * 1.25:
        comparison = "You're around the global average. Room for improvement! 🌍"
    else:
        comparison = "Your footprint is above average. Consider making changes! 🌏"
    
    return jsonify({
        'total': total_emissions,
        'breakdown': {
            'transport': transport_emissions,
            'energy': energy_emissions,
            'food': food_emissions
        },
        'comparison': comparison
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
