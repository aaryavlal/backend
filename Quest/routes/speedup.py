from flask import Blueprint, request, jsonify

speedup_bp = Blueprint('speedup', __name__, url_prefix='/api/speedup')

def serial_sort(numbers):
    arr = numbers[:]
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def parallel_sort(numbers):
    mid = max(1, len(numbers) // 2)
    left = sorted(numbers[:mid])
    right = sorted(numbers[mid:])
    return sorted(left + right)

QUIZ_QUESTIONS = [
    {"q": "If serial time = 100s and parallel time = 25s, what is speedup?", "a": "4"},
    {"q": "If speedup = 1, what does that mean?", "a": "No improvement"},
    {"q": "True/False: Speedup can be less than 1", "a": "True"},
]

LEADERBOARD = []

@speedup_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@speedup_bp.route("/quiz", methods=["POST"])
def take_quiz():
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", [])
    score = 0
    for i, ans in enumerate(answers[:len(QUIZ_QUESTIONS)]):
        if str(ans).strip().lower() == str(QUIZ_QUESTIONS[i]["a"]).strip().lower():
            score += 1
    result = {"score": score, "total": len(QUIZ_QUESTIONS), "answers": answers}
    LEADERBOARD.append(result)
    return jsonify(result)

@speedup_bp.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    return jsonify(LEADERBOARD[-10:])

@speedup_bp.route("/sort", methods=["POST"])
def sort_game():
    data = request.get_json(silent=True) or {}
    numbers = data.get("numbers", [])
    mode = (data.get("mode") or "serial").lower()
    result = parallel_sort(numbers) if mode == "parallel" else serial_sort(numbers)
    return jsonify({"sorted": result})
