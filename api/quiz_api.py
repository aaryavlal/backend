"""
Quiz API
Endpoints to list quizzes, get quiz, submit attempts, view attempts and leaderboard
"""
from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from __init__ import db
from model.quiz import Quiz, Question, Choice, Attempt, init_quizzes
from model.user import User
import jwt
import json
from datetime import datetime


quiz_api = Blueprint('quiz_api', __name__, url_prefix='/api/quiz')
api = Api(quiz_api)


def _get_current_user_from_token():
    token = request.cookies.get(current_app.config.get('JWT_TOKEN_NAME'))
    if not token:
        return None
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.filter_by(_uid=data.get('_uid')).first()
        return user
    except Exception:
        return None


class QuizListAPI(Resource):
    def get(self):
        quizzes = Quiz.get_all()
        return [q.read(include_answers=False) for q in quizzes], 200


class QuizDetailAPI(Resource):
    def get(self, quiz_id):
        quiz = Quiz.get_by_id(quiz_id)
        if not quiz:
            return {'message': 'Quiz not found'}, 404
        # include choices but not correct flags
        return quiz.read(include_answers=False), 200


class SubmitAttemptAPI(Resource):
    def post(self):
        data = request.get_json() or {}
        quiz_id = data.get('quizId')
        answers = data.get('answers') or []  # list of {questionId, choiceId}
        user_id = data.get('userId')
        # allow manual score submission (for leaderboard additions)
        manual_score = data.get('score')
        manual_total = data.get('total')

        # try to resolve user from token if not provided
        user = None
        if not user_id:
            user = _get_current_user_from_token()
            if user:
                user_id = user.id

        # Development convenience: if still no user_id, prefer the configured admin user
        # (this repo seeds an admin by default). If not found, fall back to first user or create a dev user.
        if not user_id:
            # If config allows anonymous submissions, use or create a shared anonymous user.
            if current_app.config.get('ALLOW_ANONYMOUS_SUBMIT'):
                anon_uid = current_app.config.get('ANONYMOUS_UID') or 'guest'
                anon_name = current_app.config.get('ANONYMOUS_NAME') or 'Guest User'
                anon_user = User.query.filter_by(_uid=anon_uid).first()
                if anon_user:
                    user_id = anon_user.id
                else:
                    # create anonymous user (dev only)
                    try:
                        pwd = current_app.config.get('DEFAULT_PASSWORD') or 'password'
                        new_user = User(anon_name, anon_uid, password=pwd)
                        created = new_user.create()
                        if created:
                            user_id = created.id
                        else:
                            # fallback to first existing user
                            default_user = User.query.first()
                            user_id = default_user.id if default_user else None
                    except Exception:
                        default_user = User.query.first()
                        user_id = default_user.id if default_user else None
            else:
                # Not allowed: require auth or explicit userId
                return {'message': 'userId missing and no valid auth token present'}, 401

        quiz = Quiz.get_by_id(quiz_id)
        if not quiz:
            return {'message': 'Quiz not found'}, 404

        # calculate score or accept manual values when provided
        if manual_score is not None and manual_total is not None:
            # use provided manual score/total (useful for adding leaderboard entries)
            score = float(manual_score)
            total_points = float(manual_total)
        else:
            total_points = 0
            score = 0
            # Build a map of question -> correct choice id(s)
            correct_map = {}
            for q in quiz.questions.all():
                total_points += q.points
                correct_choices = [c.id for c in q.choices.filter_by(is_correct=True).all()]
                correct_map[q.id] = correct_choices

            # Score answers
            for a in answers:
                qid = a.get('questionId')
                cid = a.get('choiceId')
                if qid in correct_map and cid in correct_map[qid]:
                    # find question points
                    q_obj = Question.query.get(qid)
                    score += (q_obj.points if q_obj else 1)

        # Create Attempt (store answers as provided)
        attempt = Attempt(user_id=user_id, quiz_id=quiz_id, score=score, total=total_points, answers=answers)
        created = attempt.create()
        return created.read(), 201


class UserAttemptsAPI(Resource):
    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404
        attempts = Attempt.get_by_user(user_id)
        return [a.read() for a in attempts], 200


class LeaderboardAPI(Resource):
    def get(self, quiz_id):
        quiz = Quiz.get_by_id(quiz_id)
        if not quiz:
            return {'message': 'Quiz not found'}, 404
        attempts = Attempt.get_by_quiz(quiz_id)
        # aggregate best score per user
        best_by_user = {}
        for a in attempts:
            uid = a.user_id
            if uid not in best_by_user or a.score > best_by_user[uid].score:
                best_by_user[uid] = a

        leaderboard = [best_by_user[uid].read() for uid in best_by_user]
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        return leaderboard, 200


# Register routes
api.add_resource(QuizListAPI, '/all')
api.add_resource(QuizDetailAPI, '/<int:quiz_id>')
api.add_resource(SubmitAttemptAPI, '/attempt')
api.add_resource(UserAttemptsAPI, '/attempts/user/<int:user_id>')
api.add_resource(LeaderboardAPI, '/leaderboard/<int:quiz_id>')


# Note: do not run DB initialization at import time here (needs app context).
