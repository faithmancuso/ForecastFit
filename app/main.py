from flask import Flask, jsonify, request, render_template
import requests
from flask_cors import CORS
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://www.forecast-fit.com"}})
WEATHER_API_KEY = "3fc72f97a7404f9a8d0213532241211"

load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

subscriptions = []

def send_sms(to, body):
    message = client.messages.create(
        body=body,
        from_=TWILIO_PHONE_NUMBER,
        to=to
    )
    return message.sid

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    phone = data.get('phone')
    time = data.get('time')
    zip_code = data.get('zip')

    if not phone or not time or not zip_code:
        return jsonify({"error": "All fields are required."}), 400

    subscriptions.append({
        "phone": phone,
        "time": time,
        "zip": zip_code
    })

    return jsonify({"message": "Subscription successful!"}), 200

def fetch_weather(zip_code):
    url = f'http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={zip_code}'
    response = requests.get(url)
    data = response.json()
    return data['forecast']['forecastday'][0]['day']['condition']['text']

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

def send_daily_notifications():
    current_time = datetime.datetime.now().strftime('%H:%M')
    for subscription in subscriptions:
        if subscription['time'] == current_time:
            weather = fetch_weather(subscription['zip'])
            message = f"Good morning! Here’s your daily weather update for zip code {subscription['zip']}: {weather}."
            send_sms(subscription['phone'], message)

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_notifications, 'interval', minutes=1)
scheduler.start()

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
    app.run(debug=True)