from flask import Flask, jsonify, request, render_template
import requests
import os

app = Flask(__name__)

# Retrieve the API key from environment variables in vercel
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

def fetch_weather_data(zip_code, days):
    """
    Fetch weather data for a specified number of days.
    """
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={zip_code}&days={days}"
    response = requests.get(url)
    return response.json()

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
    zip_code = request.args.get('zip', '44113')  # Default to zip code 44113 if not provided
    data = fetch_weather_data(zip_code, 1)
    return jsonify(data)

@app.route('/weather/3-day', methods=['GET'])
def three_day_forecast():
    """
    Get a 3-day weather forecast for a specified zip code.
    """
    zip_code = request.args.get('zip', '44113')  # Default to zip code 44113 if not provided
    data = fetch_weather_data(zip_code, 3)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)