from flask import Flask, jsonify, request, render_template
import requests
from flask_cors import CORS
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
import datetime

app = Flask(__name__)
# Explicitly allow requests from your live domain
CORS(app, resources={r"/*": {"origins": "https://www.forecast-fit.com"}})
WEATHER_API_KEY = "3fc72f97a7404f9a8d0213532241211"

# Load environment variables
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Create Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms(to, body):
    message = client.messages.create(
        body=body,
        from_=TWILIO_PHONE_NUMBER,
        to=to
    )
    return message.sid

# In-memory storage for subscriptions
subscriptions = []

# Route to handle user subscription
@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    phone = data.get('phone')
    time = data.get('time')
    zip_code = data.get('zip')

    if not phone or not time or not zip_code:
        return jsonify({"error": "All fields are required."}), 400

    # Save subscription data
    subscriptions.append({
        "phone": phone,
        "time": time,
        "zip": zip_code
    })

    return jsonify({"message": "Subscription successful!"}), 200

# Function to send SMS
def send_sms(phone, message):
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        print(f"SMS sent to {phone}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

# Function to send daily notifications
def send_daily_notifications():
    current_time = datetime.datetime.now().strftime('%H:%M')
    for subscription in subscriptions:
        if subscription['time'] == current_time:
            # Generate a weather message (use a real API in production)
            message = f"Good morning! Here’s your daily weather update for zip code {subscription['zip']}."
            send_sms(subscription['phone'], message)

# Set up the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_notifications, 'interval', minutes=1)  # Check every minute
scheduler.start()

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
