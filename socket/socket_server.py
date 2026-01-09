# imports from flask
import os
import sys

from flask import Flask
from flask_socketio import SocketIO, emit, send

# Import rustism
backend_path = os.path.join(os.path.dirname(__file__), "..")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from model.compute import get_concurrent, get_sequential

app = Flask(__name__)

socketio = SocketIO(
    app,
    cors_allowed_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:4600",
        "http://127.0.0.1:4600",
        "https://hardwarehavoc.github.io",
        "https://pages.hardwarehavoc.com",
        "https://aaryavlal.github.io",  # deployed site
    ],
)


players = []  # Keep a list of players and scores


@socketio.on("player_join")
def handle_player_join(data):
    name = data.get("name")
    if name:
        players.append({"name": name, "score": 0})
        emit("player_joined", {"name": name}, broadcast=True)


@socketio.on("player_score")
def handle_player_score(data):
    name = data.get("name")
    score = data.get("score", 0)
    for p in players:
        if p["name"] == name:
            p["score"] = score
            break
    # Sort and broadcast leaderboard
    leaderboard = sorted(players, key=lambda x: x["score"], reverse=True)
    emit("leaderboard_update", leaderboard, broadcast=True)


@socketio.on("clear_leaderboard")
def handle_clear_leaderboard():
    global players
    players = []
    emit("leaderboard_update", players, broadcast=True)


@socketio.on("get_leaderboard")
def handle_get_leaderboard():
    # Sort and emit current leaderboard
    leaderboard = sorted(players, key=lambda x: x["score"], reverse=True)
    emit("leaderboard_update", leaderboard)


# COMPUTE WebSocket Events
@socketio.on("compute_sequential")
def handle_compute_sequential(data=None):
    """
    Handle request for sequential task execution
    Emits the result back to the requesting client

    Args:
        data: Optional dict with keys: width, height, tile_w, tile_h, max_iter
    """
    try:
        # Extract parameters with defaults
        params = data or {}
        width = params.get("width", 800)
        height = params.get("height", 600)
        tile_w = params.get("tile_w", 64)
        tile_h = params.get("tile_h", 64)
        max_iter = params.get("max_iter", 256)
        time_limit_ms = params.get("time_limit_ms", 2000)

        # Execute without streaming
        records = get_sequential(
            width=width,
            height=height,
            tile_w=tile_w,
            tile_h=tile_h,
            max_iter=max_iter,
            time_limit_ms=time_limit_ms,
        )

        emit(
            "compute_sequential_result",
            {
                "success": True,
                "data": records,
                "message": "Sequential tasks executed successfully",
            },
        )
    except Exception as e:
        import traceback

        print(f"ERROR: {e}")
        print(traceback.format_exc())
        emit(
            "compute_sequential_error",
            {
                "success": False,
                "error": str(e),
                "message": "Error executing sequential tasks",
            },
        )


@socketio.on("compute_sequential_stream")
def handle_compute_sequential_stream(data=None):
    """
    Handle request for streaming sequential task execution
    Emits progress updates in real-time as tasks complete

    Args:
        data: Optional dict with keys: width, height, tile_w, tile_h, max_iter
    """
    try:
        # Extract parameters with defaults
        params = data or {}
        width = params.get("width", 800)
        height = params.get("height", 600)
        tile_w = params.get("tile_w", 64)
        tile_h = params.get("tile_h", 64)
        max_iter = params.get("max_iter", 256)
        time_limit_ms = params.get("time_limit_ms", 2000)

        # Calculate total tasks for progress tracking
        total_tasks = (height // tile_h + (1 if height % tile_h else 0)) * (
            width // tile_w + (1 if width % tile_w else 0)
        )

        # Define callback to emit each tile as it completes
        def emit_tile_update(tile):
            emit(
                "compute_task_update",
                {
                    "task": tile,
                    "progress": {"current": tile["task_id"] + 1, "total": total_tasks},
                },
            )

        # Execute with streaming callback
        records = get_sequential(
            width=width,
            height=height,
            tile_w=tile_w,
            tile_h=tile_h,
            max_iter=max_iter,
            emit_callback=emit_tile_update,
            time_limit_ms=time_limit_ms,
        )

        # Final completion event
        completed = len(records)
        was_limited = completed < total_tasks

        emit(
            "compute_sequential_complete",
            {
                "success": True,
                "total_tasks": total_tasks,
                "completed_tasks": completed,
                "was_time_limited": was_limited,
                "message": f"Completed {completed}/{total_tasks} tiles"
                + (" (time limit reached)" if was_limited else ""),
            },
        )
    except Exception as e:
        emit(
            "compute_sequential_error",
            {
                "success": False,
                "error": str(e),
                "message": "Error executing sequential tasks",
            },
        )


@socketio.on("compute_concurrent_stream")
def handle_compute_concurrent_stream(data=None):
    """
    Handle requests for streaming concurrent Mandelbrot tasks
    Emits progress updates

    Args:
        data: Optional dict with keys: width, height, tile_w, tile_h, max_iter, time_limit_ms, num_threads
    """
    try:
        # Extract parameters with defaults
        # Prob redundant since the compute.py already passes defaults
        params = data or {}
        width = params.get("width", 800)
        height = params.get("height", 600)
        tile_w = params.get("tile_w", 64)
        tile_h = params.get("tile_h", 64)
        max_iter = params.get("max_iter", 256)
        time_limit_ms = params.get("time_limit_ms", 2000)
        num_threads = params.get("num_threads", 4)

        # Calculate the total tasks for progress tracking
        total_tasks = (height // tile_h + (1 if height % tile_h != 0 else 0)) * (
            width // tile_w + (1 if width % tile_w != 0 else 0)
        )

        # Define callback to emit each tile as it completes
        def emit_tile_update(tile):
            emit(
                "compute_task_update",
                {
                    "task": tile,
                    "progress": {"current": tile["task_id"] + 1, "total": total_tasks},
                },
            )

        # Execute with streaming callback
        records = get_concurrent(
            width=width,
            height=height,
            tile_w=tile_w,
            tile_h=tile_h,
            max_iter=max_iter,
            emit_callback=emit_tile_update,
            time_limit_ms=time_limit_ms,
            num_threads=num_threads,
        )

        # Final completion event
        completed = len(records)
        was_limited = completed < total_tasks

        emit(
            "compute_concurrent_complete",
            {
                "success": True,
                "total_tasks": total_tasks,
                "completed_tasks": completed,
                "was_time_limited": was_limited,
                "num_threads": num_threads,
                "message": f"Completed {completed}/{total_tasks} tiles with {num_threads} threads"
                + (" (time limit reached)" if was_limited else ""),
            },
        )
    except Exception as e:
        import traceback

        print(f"ERROR: {e}")
        print(traceback.format_exc())
        emit(
            "compute_concurrent_error",
            {
                "success": False,
                "error": str(e),
                "message": "Error executing concurrent tasks",
            },
        )


# this runs the flask application on the development server
if __name__ == "__main__":
    # change name for testing
    socketio.run(app, debug=False, host="0.0.0.0", port=8500)
