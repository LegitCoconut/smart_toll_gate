from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime


app = Flask(__name__)
app.secret_key = "x230887898af"

# MongoDB Setup
MONGO_URI = os.getenv('MONGO_URI', 'your-default-mongo-uri')
client = MongoClient(MONGO_URI)
db = client["toll_system"]
log_collection = db["logs"]
users_collection = db["users"]

# Admin Credentials
ADMIN_USERNAME = os.getenv('USER_NAME', 'your-default-usr')
ADMIN_PASSWORD = os.getenv('PASSWORD', 'def_pass')

#@app.route("/login", methods=["GET", "POST"])
#def login():
#    if request.method == "POST":
#        username = request.form.get("username")
#        password = request.form.get("password")
#
#        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
#            session["logged_in"] = True
#            return redirect(url_for("dashboard"))
#        else:
#            return render_template("login.html", error="Invalid credentials")
#a
#    return render_template("login.html")


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/logs")
def get_logs():
    logs = list(log_collection.find({}, {"_id": 0}).sort("time", -1)) 
    return jsonify(logs)

@app.route("/vehicles")
def get_vehicles():
    vehicles = list(users_collection.find({}, {"_id": 0, "vehicle": 1}))  
    vehicle_list = [v["vehicle"] for v in vehicles if "vehicle" in v]

    return jsonify(vehicle_list)


@app.route("/user_logs/<vehicle>")
def get_user_logs(vehicle):
    user = users_collection.find_one({"vehicle": vehicle}, {"logs": 1, "balance": 1})

    if user:
        logs = user.get("logs", [])
        for log in logs:
            log["_id"] = str(log["_id"]) if "_id" in log else None
            # Parse time if it's a string
            if isinstance(log.get("time"), str):
                try:
                    log["time"] = datetime.strptime(log["time"], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    log["time"] = datetime.min  # fallback if parse fails

        logs.sort(key=lambda x: x.get("time", datetime.min), reverse=True)

        # Convert datetime back to string for sending to frontend
        for log in logs:
            if isinstance(log.get("time"), datetime):
                log["time"] = log["time"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({
            "logs": logs,
            "balance": user.get("balance", 0)
        })

    return jsonify({"logs": [], "balance": 0})


@app.route("/update_balance", methods=["POST"])
def update_balance():

    data = request.get_json()
    vehicle = data.get("vehicle")
    amount = data.get("balance")

    if not vehicle or amount is None:
        return jsonify({"error": "Invalid input"}), 400

    user = users_collection.find_one({"vehicle": vehicle})
    if not user:
        return jsonify({"error": "Vehicle not found"}), 404

    # Increment balance
    new_balance = user.get("balance", 0) + amount
    users_collection.update_one({"vehicle": vehicle}, {
        "$set": {"balance": new_balance}
    })

    # Create log entry
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "time": now,
        "event": f"Balance updated: ₹{amount:.2f} added. New Balance: ₹{new_balance:.2f}"
    }

    # Insert in personal log
    users_collection.update_one({"vehicle": vehicle}, {
        "$push": {"logs": log_entry}
    })

    # Insert in global log
    log_collection.insert_one(log_entry)

    return jsonify({"message": "Recgarge successfully", "new_balance": new_balance})


if __name__ == "__main__":
    app.run()
