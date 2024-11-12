# Main application code to run the server

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/subscribe", methods=["POST"])
def subscribe():
    # Extract form data (location, phone, time)
    location = request.form.get("location")
    phone = request.form.get("phone")
    time = request.form.get("time")
    
    # Log or process the data as needed
    print(f"Received subscription: Location={location}, Phone={phone}, Time={time}")
    
    # Return a JSON response with the success message
    return jsonify(message="Subscription successful!")

if __name__ == "__main__":
    app.run(debug=True)