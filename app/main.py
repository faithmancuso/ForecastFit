from flask import Flask, jsonify, request, render_template
import requests
from flask_cors import CORS
import requests
from dotenv import load_dotenv
import os


app = Flask(__name__)
load_dotenv()
# Explicitly allow requests from our live domain
CORS(app, resources={r"/*": {"origins": "https://www.forecast-fit.com"}})
WEATHER_API_KEY = "3fc72f97a7404f9a8d0213532241211"
TEXTBELT_API_KEY = os.getenv('TEXTBELT_API_KEY')

if not TEXTBELT_API_KEY:
    print("Error: TEXTBELT_API_KEY is not set. SMS functionality will not work!")

def send_sms(phone, message):
    response = requests.post('https://textbelt.com/text', {
        'phone': phone,
        'message': message,
        'key': TEXTBELT_API_KEY,
    })
    print(f"Textbelt Response: {response.json()}")  # Logs the API response
    return response.json()

subscriptions = []

import sqlite3

@app.route('/subscribe', methods=['POST'])
def subscribe():
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

    # Attempt to send SMS
    print("Attempting to send SMS...")
    sms_response = send_sms(phone, f"Thank you for subscribing! Weather updates will be sent at {time}.")
    print(f"SMS Response: {sms_response}")

    if not sms_response.get('success'):
        print(f"SMS failed with error: {sms_response.get('error')}")
        return jsonify({"error": "Subscription saved, but SMS failed to send."}), 500

    return jsonify({"message": "Subscription successful!"}), 200



@app.route('/test-env', methods=['GET'])
def test_env():
    """
    Test if environment variables are loaded properly.
    """
    return jsonify({
        "TEXTBELT_API_KEY": TEXTBELT_API_KEY is not None,
        "TEXTBELT_API_KEY (value)": TEXTBELT_API_KEY
    })


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

@app.route('/subscriptions', methods=['GET'])
def view_subscriptions():
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subscriptions')
    rows = cursor.fetchall()
    conn.close()

    return jsonify({"subscriptions": rows}), 200

@app.route('/')
def home():
    """
    Serve the homepage.
    """
    return render_template('index.html')

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