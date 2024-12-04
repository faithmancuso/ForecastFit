import sqlite3
import requests

# SQLite database path
DB_PATH = 'subscribers.db'

# Function to initialize the SQLite database
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

# Function to add a subscriber to the database
def add_subscriber(phone, zip_code, time):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = "INSERT INTO subscribers (phone, zip_code, notification_time, consent) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (phone, zip_code, time, True))  # Assuming consent is always True
        conn.commit()
    print(f"Subscriber added: Phone={phone}, Zip={zip_code}, Time={time}")

# Function to fetch all subscribers from the database
def fetch_subscribers():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subscribers")
        data = cursor.fetchall()
    return data  # Returns a list of tuples

# Function to delete a subscriber by ID
def delete_subscriber(subscriber_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = "DELETE FROM subscribers WHERE id = ?"
        cursor.execute(query, (subscriber_id,))
        conn.commit()
    print(f"Subscriber with ID {subscriber_id} deleted.")

# Function to get weather information from the API
def get_weather(zip_code):
    # Replace with your weather API endpoint and key
    api_key = '3fc72f97a7404f9a8d0213532241211'
    url = f'http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={zip_code}&days=1'
    try:
        response = requests.get(url)
        response.raise_for_status()
        weather_data = response.json()
        return weather_data.get('current', {}).get('condition', {}).get('text', 'Unknown Weather')
    except requests.RequestException as e:
        print(f"Error fetching weather: {e}")
        return "Error"

# Example Usage
if __name__ == "__main__":
    # Uncomment the following line if you need to initialize the database
    # init_db()

    # Add a sample subscriber
    add_subscriber(phone="1234567890", zip_code="44113", time="07:00")

    # Fetch all subscribers
    subscribers = fetch_subscribers()
    print("All Subscribers:")
    for subscriber in subscribers:
        print(subscriber)

    # Delete a subscriber (example ID: 1)
    delete_subscriber(subscriber_id=1)

    # Fetch all subscribers again to confirm deletion
    subscribers = fetch_subscribers()
    print("Subscribers After Deletion:")
    for subscriber in subscribers:
        print(subscriber)

    # Example: Get weather for a zip code
    weather = get_weather(zip_code="44113")
    print(f"Weather for 44113: {weather}")