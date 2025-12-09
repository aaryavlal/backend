from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restful import Api, Resource
import time

app = Flask(__name__)
CORS(app, supports_credentials=True, origins='*')
api = Api(app)

# -------------------------------------------------------
# QUIZ ATTEMPT STORAGE (like your interactive activity)
# -------------------------------------------------------

RECENT_ATTEMPTS = []   # stores dicts of attempts


def summarize_attempts(attempts, max_items=5):
    """
    Summarize the last N attempts.
    """
    summary = []
    recent = attempts[-max_items:]

    for a in recent:
        label = ""
        pct = a["score"] / a["maxScore"]

        if pct == 1:
            label = "Perfect"
        elif pct >= 0.8:
            label = "Strong"
        elif pct >= 0.6:
            label = "OK"
        else:
            label = "Needs Practice"

        summary.append(f"{a['timestamp']} — {label} ({a['score']}/{a['maxScore']})")

    return summary


class AttemptAPI(Resource):
    def get(self):
        """Return all stored attempts."""
        return jsonify({
            "attempts": RECENT_ATTEMPTS,
            "summary": summarize_attempts(RECENT_ATTEMPTS)
        })

    def post(self):
        """
        Store a new attempt sent from the frontend.
        Expected JSON:
        {
            "score": number,
            "maxScore": number,
            "feedback": "text",
            "details": {...}
        }
        """
        attempt = request.get_json()

        if not attempt:
            return {"error": "No attempt data provided"}, 400

        # stamp with server timestamp
        attempt["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        RECENT_ATTEMPTS.append(attempt)

        return {
            "message": "Attempt stored",
            "attempt": attempt,
            "serverSummary": summarize_attempts(RECENT_ATTEMPTS)
        }, 201


# Register quiz attempt endpoint
api.add_resource(AttemptAPI, '/api/attempt')


# -------------------------------------------------------
# ORIGINAL DATA API (kept intact)
# -------------------------------------------------------

class InfoModel:
    def __init__(self):
        self.data = [
            {
                "FirstName": "John",
                "LastName": "Mortensen",
                "DOB": "October 21",
                "Residence": "San Diego",
                "Email": "jmortensen@powayusd.com",
                "Owns_Cars": ["2015-Fusion", "2011-Ranger", "2003-Excursion",
                              "1997-F350", "1969-Cadillac", "2015-Kuboto-3301"]
            },
            {
                "FirstName": "Shane",
                "LastName": "Lopez",
                "DOB": "February 27",
                "Residence": "San Diego",
                "Email": "slopez@powayusd.com",
                "Owns_Cars": ["2021-Insight"]
            }
        ]

    def read(self):
        return self.data

    def create(self, entry):
        self.data.append(entry)


info_model = InfoModel()


class DataAPI(Resource):
    def get(self):
        return jsonify(info_model.read())

    def post(self):
        entry = request.get_json()
        if not entry:
            return {"error": "No data provided"}, 400
        info_model.create(entry)
        return {"message": "Entry added", "entry": entry}, 201


api.add_resource(DataAPI, '/api/data')


@app.route('/')
def say_hello():
    return """
    <html>
    <head><title>Hello</title></head>
    <body><h2>Hello, World!</h2></body>
    </html>
    """


if __name__ == '__main__':
    app.run(port=5001)