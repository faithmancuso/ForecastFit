# Main application code to run the server

# Importing necessary Flask components
from flask import Flask, render_template, request

# Create an instance of the Flask application
app = Flask(__name__)

# Define the route for the home page
@app.route("/")  # This tells Flask that this function should run when someone visits "/"
def home():
    # Render the "index.html" template when the home page is accessed
    return render_template("index.html")

# Define a route to handle form submissions from "index.html"
@app.route("/subscribe", methods=["POST"])
def subscribe():
    # Extract data from the form submission
    location = request.form.get("location")
    phone = request.form.get("phone")
    time = request.form.get("time")

    # TEST: just print the data to the console to confirm it's working (delete later)
    print(f"Location: {location}, Phone: {phone}, Time: {time}")

    # Add further processing here, like saving data or sending SMS 

    # Return a success message to show the form was submitted
    return "Subscription successful! We have saved your preferences."

if __name__ == "__main__":
    app.run(debug=True)