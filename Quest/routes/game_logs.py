from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
from datetime import datetime

game_logs_bp = Blueprint('game_logs', __name__, url_prefix='/api/game-logs')

# Get logs directory from app config or use default
def get_logs_dir():
    from flask import current_app
    return current_app.config.get('LOGS_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'logs'))

@game_logs_bp.route('/gpu-simulator', methods=['POST'])
def log_gpu_simulator():
    """Log GPU simulator game data"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['stage', 'gpusCompleted', 'timeElapsed', 'avgTime', 'throughput']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create logs directory if it doesn't exist
        logs_dir = get_logs_dir()
        os.makedirs(logs_dir, exist_ok=True)

        # Create log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'stage': data['stage'],
            'gpusCompleted': data['gpusCompleted'],
            'timeElapsed': data['timeElapsed'],
            'avgTime': data['avgTime'],
            'throughput': data['throughput'],
            'achievements': data.get('achievements', []),
            'userAgent': request.headers.get('User-Agent', 'Unknown'),
            'sessionId': data.get('sessionId')
        }

        # Append to daily log file
        log_file = os.path.join(logs_dir, f'gpu_simulator_{datetime.utcnow().strftime("%Y%m%d")}.jsonl')

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        return jsonify({
            'message': 'Game data logged successfully',
            'timestamp': log_entry['timestamp']
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@game_logs_bp.route('/gpu-simulator/stats', methods=['GET'])
def get_gpu_simulator_stats():
    """Get aggregated stats from GPU simulator logs"""
    try:
        logs_dir = get_logs_dir()

        if not os.path.exists(logs_dir):
            return jsonify({
                'totalGames': 0,
                'avgByStage': {},
                'message': 'No data yet'
            })

        # Read all log files
        all_logs = []
        for filename in os.listdir(logs_dir):
            if filename.startswith('gpu_simulator_') and filename.endswith('.jsonl'):
                filepath = os.path.join(logs_dir, filename)
                with open(filepath, 'r') as f:
                    for line in f:
                        try:
                            all_logs.append(json.loads(line.strip()))
                        except:
                            continue

        if not all_logs:
            return jsonify({
                'totalGames': 0,
                'avgByStage': {},
                'message': 'No data yet'
            })

        # Calculate stats by stage
        stage_stats = {1: [], 2: [], 3: []}
        for log in all_logs:
            stage = log['stage']
            if stage in stage_stats:
                stage_stats[stage].append({
                    'avgTime': log['avgTime'],
                    'throughput': log['throughput'],
                    'gpus': log['gpusCompleted']
                })

        # Aggregate
        result = {
            'totalGames': len(all_logs),
            'avgByStage': {}
        }

        for stage, games in stage_stats.items():
            if games:
                result['avgByStage'][stage] = {
                    'gamesPlayed': len(games),
                    'avgTimePerGPU': sum(g['avgTime'] for g in games) / len(games),
                    'avgThroughput': sum(g['throughput'] for g in games) / len(games),
                    'totalGPUs': sum(g['gpus'] for g in games)
                }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@game_logs_bp.route('/gpu-simulator/recent', methods=['GET'])
def get_recent_games():
    """Get recent game sessions"""
    try:
        limit = int(request.args.get('limit', 10))
        logs_dir = get_logs_dir()

        if not os.path.exists(logs_dir):
            return jsonify({'games': []})

        # Read recent logs
        all_logs = []
        log_files = sorted([f for f in os.listdir(logs_dir) if f.startswith('gpu_simulator_')], reverse=True)

        for filename in log_files[:3]:  # Check last 3 days
            filepath = os.path.join(logs_dir, filename)
            with open(filepath, 'r') as f:
                for line in f:
                    try:
                        all_logs.append(json.loads(line.strip()))
                    except:
                        continue

        # Sort by timestamp and limit
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        recent = all_logs[:limit]

        return jsonify({'games': recent, 'count': len(recent)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
