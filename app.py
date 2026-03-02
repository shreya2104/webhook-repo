from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import hashlib
import hmac
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["github_webhooks"]
collection = db["events"]

# webhook secret in env variable
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# GitHub Signature Verification
def verify_signature(req):
    if not WEBHOOK_SECRET:
        print("WEBHOOK_SECRET not configured")
        return False

    signature = req.headers.get("X-Hub-Signature-256")

    if not signature:
        return False

    try:
        sha_name, received_signature = signature.split("=")

        mac = hmac.new(
            WEBHOOK_SECRET.encode(),
            msg=req.data,
            digestmod=hashlib.sha256
        )

        expected_signature = mac.hexdigest()

        return hmac.compare_digest(expected_signature, received_signature)

    except Exception as e:
        print("Signature verification error:", e)
        return False

# Webhook Receiver
@app.route("/webhook", methods=["POST"])
def webhook():

    # GitHub signature Verification
    if not verify_signature(request):
        return jsonify({"error": "Invalid signature"}), 403

    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json

    if not payload:
        return jsonify({"error": "Empty payload"}), 400

    try:
        if event_type == "push":
            data = {
                "type": "PUSH",
                "author": payload["pusher"]["name"],
                "to_branch": payload["ref"].split("/")[-1],
                "timestamp": payload["head_commit"]["timestamp"]
            }
            collection.insert_one(data)

        elif event_type == "pull_request":
            pr = payload["pull_request"]

            # Detect MERGE
            if pr.get("merged") is True:
                event_name = "MERGE"
            else:
                event_name = "PULL_REQUEST"

            data = {
                "type": event_name,
                "author": pr["user"]["login"],
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": pr["updated_at"]
            }

            collection.insert_one(data)

        else:
            return jsonify({"message": "Event ignored"}), 200

        return jsonify({"message": "Webhook received"}), 200

    except Exception as e:
        print("Webhook processing error:", e)
        return jsonify({"error": str(e)}), 500

# UI Polling API
@app.route("/events", methods=["GET"])
def get_events():
    try:
        events = list(collection.find().sort("timestamp", -1))

        for event in events:
            event["_id"] = str(event["_id"])

        return jsonify(events), 200

    except Exception as e:
        print("Events fetch error:", e)
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)