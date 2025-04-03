from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv


app = Flask(__name__)
app.secret_key = "your_secret_key"

# MongoDB Setup
MONGO_URI = os.getenv('MONGO_URI', 'your-default-mongo-uri')
client = MongoClient(MONGO_URI)
db = client["toll_system"]
log_collection = db["logs"]
users_collection = db["users"]

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    return render_template("dashboard.html")


@app.route("/logs")
def get_logs():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 403

    logs = list(log_collection.find({}, {"_id": 0}).sort("time", -1)) 
    return jsonify(logs)

@app.route("/vehicles")
def get_vehicles():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 403

    vehicles = list(users_collection.find({}, {"_id": 0, "vehicle": 1}))  
    vehicle_list = [v["vehicle"] for v in vehicles if "vehicle" in v]

    return jsonify(vehicle_list)


@app.route("/user_logs/<vehicle>")
def get_user_logs(vehicle):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 403

    user = users_collection.find_one({"vehicle": vehicle}, {"logs": 1})  # No `_id`
    
    if user:
        # Convert ObjectId inside logs if needed
        for log in user["logs"]:
            log["_id"] = str(log["_id"]) if "_id" in log else None  

        return jsonify(user["logs"])

    return jsonify([])

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
