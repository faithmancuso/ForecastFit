from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
from dotenv import load_dotenv
import os
import sqlite3

# Initialize Flask app and load environment variables
app = Flask(__name__)
load_dotenv()

# Enable CORS for the specified domain
CORS(app, resources={r"/*": {"origins": "https://www.forecast-fit.com"}})

# API Keys
WEATHER_API_KEY = "3fc72f97a7404f9a8d0213532241211"
TEXTBELT_API_KEY = os.getenv('TEXTBELT_API_KEY')

if not TEXTBELT_API_KEY:
    print("Error: TEXTBELT_API_KEY is not set. SMS functionality will not work!")

# Helper Functions
def send_sms(phone, message):
    """
    Send SMS using Textbelt API.
    """
    response = requests.post('https://textbelt.com/text', {
        'phone': phone,
        'message': message,
        'key': TEXTBELT_API_KEY,
    })
    print(f"Textbelt Response: {response.json()}")  # Logs the API response
    return response.json()

def fetch_weather_data(zip_code, days, temp_unit='F'):
    """
    Fetch weather data for a specified number of days.
    """
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={zip_code}&days={days}"
    response = requests.get(url)
    data = response.json()

    # Convert temperatures if necessary
    if temp_unit == 'C':
        for day in data['forecast']['forecastday']:
            day['day']['maxtemp_c'] = (day['day']['maxtemp_f'] - 32) * 5 / 9
            day['day']['mintemp_c'] = (day['day']['mintemp_f'] - 32) * 5 / 9
            day['day']['avgtemp_c'] = (day['day']['avgtemp_f'] - 32) * 5 / 9
            for hour in day['hour']:
                hour['temp_c'] = (hour['temp_f'] - 32) * 5 / 9
                hour['feelslike_c'] = (hour['feelslike_f'] - 32) * 5 / 9

    return data

def get_clothing_recommendations(temperature, condition, temp_unit):
    """
    Generate clothing recommendations based on temperature and condition.
    """
    if temperature is None or condition is None:
        return ["Unable to provide clothing recommendations."]

    recommendations = []
    # Convert temperature to Celsius if it's in Fahrenheit
    if temp_unit == 'F':
        temperature = (temperature - 32) * 5 / 9

    # Temperature-based clothing recommendations
    if temperature < -18:
        recommendations.append("Wear a heavy insulated coat and fleece-lined pants. Consider layering with thermal underwear. Insulated boots and warm socks are essential.")
    elif -18 <= temperature <= 0:
        recommendations.append("Opt for a winter coat, a sweater or thermal layer, and thick pants like jeans paired with thermal leggings. Insulated boots and warm socks are essential.")
    elif 0 < temperature <= 10:
        recommendations.append("A light winter jacket or puffer coat, paired with a sweater or hoodie, is ideal. Wear jeans and closed-toe shoes.")
    elif 10 < temperature <= 18:
        recommendations.append("Choose a lightweight or denim jacket with a long-sleeve shirt or light sweater. Pants or leggings work well with any closed-toe shoes.")
    elif 18 < temperature <= 24:
        recommendations.append("Wear a T-shirt with a light jacket if needed. Pair with lightweight pants or shorts and casual shoes like sneakers or sandals.")
    elif 24 < temperature <= 29:
        recommendations.append("Stick to lightweight clothing like a T-shirt or tank top and shorts or a dress. Comfortable footwear like sandals or breathable sneakers is best.")
    elif 29 < temperature <= 35:
        recommendations.append("Opt for light cotton or linen clothing to stay cool, such as shorts or a flowy dress. Sandals or flip-flops are ideal. Consider carrying a water bottle to stay hydrated and don’t forget your sunscreen.")
    elif temperature > 35:
        recommendations.append("Opt for ultra-lightweight, breathable fabrics like linen or moisture-wicking materials. Wear sleeveless tops, shorts, or airy dresses. Stick to sandals or open-toe shoes to stay cool. Carry a water bottle to stay hydrated, and don’t forget your sunscreen.")

    # Weather condition-based accessories recommendations
    if "sun" in condition.lower():
        recommendations.append("Carry your sunglasses or a brimmed hat.")
    elif "rain" in condition.lower():
        recommendations.append("Wear a waterproof jacket or raincoat paired with waterproof boots. Carry an umbrella for convenience.")
    elif "snow" in condition.lower():
        recommendations.append("Make sure your boots are waterproof and wear a warm scarf.")
    elif "hail" in condition.lower():
        recommendations.append("Wear waterproof gloves and sturdy boots with good traction. For small hail, a sturdy umbrella can be useful.")
    elif "wind" in condition.lower():
        recommendations.append("A windbreaker or jacket is a good choice. A scarf or neck gaiter can protect against wind chill, and tie long hair back if needed.")
    elif "blizzard" in condition.lower():
        recommendations.append("Bundle up with a heavy-duty insulated coat, thermal pants, and layers to cover your face and extremities. Goggles can help protect your eyes from snow and wind.")

    return recommendations

# Routes
@app.route('/')
def home():
    """
    Serve the homepage.
    """
    return render_template('index.html')

@app.route('/test-env', methods=['GET'])
def test_env():
    """
    Test if environment variables are loaded properly.
    """
    return jsonify({
        "TEXTBELT_API_KEY": TEXTBELT_API_KEY is not None,
        "TEXTBELT_API_KEY (value)": TEXTBELT_API_KEY
    })

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """
    Handle subscription requests.
    """
    data = request.json
    phone = data.get('phone')
    time = data.get('time')
    zip_code = data.get('zip')

    if not phone or not time or not zip_code:
        print("Missing fields in subscription request.")
        return jsonify({"error": "All fields are required."}), 400

    print(f"Received subscription: Phone={phone}, Time={time}, Zip={zip_code}")

    # Save the subscription to the database
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO subscriptions (phone, time, zip_code) VALUES (?, ?, ?)', (phone, time, zip_code))
    conn.commit()
    conn.close()

    # Fetch weather data for the current day
    weather_data = fetch_weather_data(zip_code, 1)
    today_forecast = weather_data['forecast']['forecastday'][0]
    temp_unit = 'F'  # Assuming the default temperature unit is Fahrenheit

    # Get today's temperature and condition for recommendations
    today_temperature = today_forecast['day']['avgtemp_f']
    today_condition = today_forecast['day']['condition']['text']

    # Get clothing recommendations based on temperature and condition
    clothing_recommendations = get_clothing_recommendations(today_temperature, today_condition, temp_unit)

    # Prepare the SMS message
    sms_message = (
        f"Thank you for subscribing! Weather updates will be sent at {time}.\n"
        f"Today's Weather: Temp: {today_temperature}°F, Condition: {today_condition}\n"
        f"Clothing Recommendations: {', '.join(clothing_recommendations)}"
    )

    # Attempt to send SMS
    print("Attempting to send SMS...")
    sms_response = send_sms(phone, sms_message)
    print(f"SMS Response: {sms_response}")

    if not sms_response.get('success'):
        print(f"SMS failed with error: {sms_response.get('error')}")
        return jsonify({"error": "Subscription saved, but SMS failed to send."}), 500

    return jsonify({"message": "Subscription successful!"}), 200

@app.route('/subscriptions', methods=['GET'])
def view_subscriptions():
    """
    View all subscriptions.
    """
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subscriptions')
    rows = cursor.fetchall()
    conn.close()

    return jsonify({"subscriptions": rows}), 200

@app.route('/weather/today-hourly', methods=['GET'])
def today_hourly():
    """
    Get today's weather with hourly data for a specified zip code.
    """
    zip_code = request.args.get('zip', '44113')
    temp_unit = request.args.get('temp_unit', 'F')
    data = fetch_weather_data(zip_code, 1, temp_unit)
    return jsonify(data)

@app.route('/weather/3-day', methods=['GET'])
def three_day_forecast():
    """
    Get a 3-day weather forecast for a specified zip code.
    """
    zip_code = request.args.get('zip', '44113')
    temp_unit = request.args.get('temp_unit', 'F')
    data = fetch_weather_data(zip_code, 3, temp_unit)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)