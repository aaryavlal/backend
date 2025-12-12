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
SAVED_RUNS = []       # stores saved runs from the frontend
SAVED_RUNS_PATH = 'instance/saved_runs.json'


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


def _ensure_saved_runs_file():
    """Ensure the saved runs file exists and load it."""
    try:
        import os, json
        if not os.path.isdir('instance'):
            os.makedirs('instance', exist_ok=True)
        if not os.path.exists(SAVED_RUNS_PATH):
            with open(SAVED_RUNS_PATH, 'w') as f:
                json.dump([], f)
        with open(SAVED_RUNS_PATH, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                global SAVED_RUNS
                SAVED_RUNS = data
    except Exception:
        # if anything goes wrong, keep an in-memory list
        pass


def _save_saved_runs_file():
    try:
        import json
        with open(SAVED_RUNS_PATH, 'w') as f:
            json.dump(SAVED_RUNS, f, indent=2)
    except Exception:
        # best-effort only
        pass


class SavedRunsAPI(Resource):
    def get(self):
        """Return list of saved runs."""
        # Always reload from file to get fresh data
        try:
            import json, os
            if os.path.exists(SAVED_RUNS_PATH):
                with open(SAVED_RUNS_PATH, 'r') as f:
                    runs = json.load(f)
                    return jsonify({'savedRuns': runs})
        except Exception as e:
            pass
        return jsonify({'savedRuns': []})

    def post(self):
        """Save a new run posted from the frontend.

        Expected JSON: { name, seriesBlocks, parallelBlocks, serialTime, parallelTime, speedup }
        """
        payload = request.get_json()
        if not payload:
            return {'error': 'No data provided'}, 400

        # minimal validation
        required = ['name', 'seriesBlocks', 'parallelBlocks', 'serialTime', 'parallelTime', 'speedup']
        for r in required:
            if r not in payload:
                return {'error': f'Missing field: {r}'}, 400

        # Load current runs from file to get accurate next ID
        import time, json, os
        runs = []
        try:
            if os.path.exists(SAVED_RUNS_PATH):
                with open(SAVED_RUNS_PATH, 'r') as f:
                    runs = json.load(f)
        except Exception:
            runs = []

        # add timestamp and id
        new_run = dict(payload)
        new_run['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        new_run['id'] = (runs[-1]['id'] + 1) if runs and isinstance(runs[-1].get('id'), int) else 1

        runs.append(new_run)
        
        # Save back to file
        try:
            if not os.path.isdir('instance'):
                os.makedirs('instance', exist_ok=True)
            with open(SAVED_RUNS_PATH, 'w') as f:
                json.dump(runs, f, indent=2)
        except Exception:
            pass

        return {'message': 'Run saved', 'run': new_run}, 201


class SavedRunItemAPI(Resource):
    def get(self, run_id):
        """Get a single saved run by ID."""
        try:
            import json, os
            if os.path.exists(SAVED_RUNS_PATH):
                with open(SAVED_RUNS_PATH, 'r') as f:
                    runs = json.load(f)
                    for r in runs:
                        if r.get('id') == run_id:
                            return jsonify(r)
        except Exception:
            pass
        return {'error': 'Not found'}, 404


api.add_resource(SavedRunsAPI, '/api/saved_runs')
api.add_resource(SavedRunItemAPI, '/api/saved_runs/<int:run_id>')


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


@app.route('/speedup')
def speedup_page():
    """Serve the speedup interactive page."""
    from flask import send_file
    return send_file('templates/speedup.html')


if __name__ == '__main__':
    app.run(port=5001, debug=True)