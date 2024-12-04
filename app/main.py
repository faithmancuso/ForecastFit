from flask import Flask, jsonify, request, render_template
import requests
from flask_cors import CORS
import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import sqlite3

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://www.forecast-fit.com"}})
load_dotenv()

API_KEY = os.getenv('TEXTBELT_API_KEY')
WEATHER_API_KEY = "3fc72f97a7404f9a8d0213532241211"
subscriptions = []
scheduler = BackgroundScheduler()
scheduler.start()

# SQLite database setup
DB_PATH = 'subscribers.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zip_code TEXT NOT NULL,
            phone TEXT NOT NULL,
            notification_time TEXT NOT NULL,
            consent BOOLEAN NOT NULL
        )
        """)
        conn.commit()

def send_sms(phone_number, message):
    response = requests.post('https://textbelt.com/text', {
        'phone': phone_number,
        'message': message,
        'key': API_KEY,
    })
    return response.json()

def notify_users():
    for user in subscriptions:
        send_sms(user['phone'], 'Your daily weather notification.')

scheduler.add_job(func=notify_users, trigger="interval", hours=24)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    zip_code = data.get("zip")
    phone = data.get("phone")
    time = data.get("time")
    consent = data.get("consent")

    if not zip_code or not phone or not time or not consent:
        return jsonify({"error": "All fields are required"}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            query = """
            INSERT INTO subscribers (zip_code, phone, notification_time, consent)
            VALUES (?, ?, ?, ?)
            """
            cursor.execute(query, (zip_code, phone, time, consent))
            conn.commit()
            return jsonify({"message": "Subscription successful"}), 200
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return jsonify({"error": "Database error occurred"}), 500

def fetch_weather_data(zip_code, days, temp_unit='F'):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={zip_code}&days={days}"
    response = requests.get(url)
    data = response.json()

    if temp_unit == 'C':
        for day in data['forecast']['forecastday']:
            day['day']['maxtemp_c'] = (day['day']['maxtemp_f'] - 32) * 5 / 9
            day['day']['mintemp_c'] = (day['day']['mintemp_f'] - 32) * 5 / 9
            day['day']['avgtemp_c'] = (day['day']['avgtemp_f'] - 32) * 5 / 9
            for hour in day['hour']:
                hour['temp_c'] = (hour['temp_f'] - 32) * 5 / 9
                hour['feelslike_c'] = (hour['feelslike_f'] - 32) * 5 / 9

    return data

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/weather/today-hourly', methods=['GET'])
def today_hourly():
    zip_code = request.args.get('zip', '44113')
    temp_unit = request.args.get('temp_unit', 'F')
    data = fetch_weather_data(zip_code, 1, temp_unit)
    return jsonify(data)

@app.route('/weather/3-day', methods=['GET'])
def three_day_forecast():
    zip_code = request.args.get('zip', '44113')
    temp_unit = request.args.get('temp_unit', 'F')
    data = fetch_weather_data(zip_code, 3, temp_unit)
    return jsonify(data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)