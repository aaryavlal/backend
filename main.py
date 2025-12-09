# imports from flask
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from flask import abort, redirect, render_template, request, send_from_directory, url_for, jsonify, current_app, g # import render_template from "public" flask libraries
from flask_login import current_user, login_user, logout_user
from flask.cli import AppGroup
from flask_login import current_user, login_required
from flask import current_app
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from api.jwt_authorize import token_required
import bcrypt
import sqlite3
import os
from flask_restful import Api, Resource
import json
import random
import os
import fcntl


# import "objects" from "this" project
from __init__ import app, db, login_manager  # Key Flask objects 
# API endpoints
from api.user import user_api 
from api.python_exec_api import python_exec_api
from api.javascript_exec_api import javascript_exec_api
from api.section import section_api
from api.pfp import pfp_api
from api.stock import stock_api
from api.analytics import analytics_api
from api.student import student_api
from api.groq_api import groq_api
from api.gemini_api import gemini_api
from api.microblog_api import microblog_api
from api.classroom_api import classroom_api
from hacks.joke import scenario_api  # Import the joke API blueprint
from api.post import post_api  # Import the social media post API
from api.quiz_api import quiz_api
#from api.announcement import announcement_api ##temporary revert

# Import Quest blueprints
import sys
quest_path = os.path.join(os.path.dirname(__file__), 'Quest')
if quest_path not in sys.path:
    sys.path.insert(0, quest_path)

from Quest.routes.auth import auth_bp
from Quest.routes.rooms import rooms_bp
from Quest.routes.progress import progress_bp
from Quest.routes.glossary import glossary_bp

# database Initialization functions
from model.user import User, initUsers
from model.user import Section;
from model.github import GitHubUser
from model.feedback import Feedback
from api.analytics import get_date_range
# from api.grade_api import grade_api
from api.study import study_api
from api.feedback_api import feedback_api
from model.study import Study, initStudies
from model.classroom import Classroom
from model.post import Post, init_posts
from model.microblog import MicroBlog, Topic, init_microblogs
from hacks.jokes import initScenarios 
from model.quiz import init_quizzes
# from model.announcement import Announcement ##temporary revert

# server only Views

import os
import requests

# Load environment variables
load_dotenv()

app.config['KASM_SERVER'] = os.getenv('KASM_SERVER')
app.config['KASM_API_KEY'] = os.getenv('KASM_API_KEY')
app.config['KASM_API_KEY_SECRET'] = os.getenv('KASM_API_KEY_SECRET')

# Quest database path
QUEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'Quest', 'database.db')

# JWT Configuration for Quest integration
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key_change_in_production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# Initialize JWT
jwt = JWTManager(app)

# Note: CORS is already configured in __init__.py
# This secondary configuration is commented out to avoid conflicts
# cors_config = {
#     "origins": os.environ.get('CORS_ORIGINS', '*').split(','),
#     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     "allow_headers": ["Content-Type", "Authorization"],
#     "expose_headers": ["Content-Type", "Authorization"],
#     "supports_credentials": True,
#     "max_age": 3600
# }
# CORS(app, resources={r"/api/*": cors_config})

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token required'}), 401



# register URIs for api endpoints
app.register_blueprint(python_exec_api)
app.register_blueprint(javascript_exec_api)
app.register_blueprint(user_api)
app.register_blueprint(section_api)
app.register_blueprint(pfp_api) 
app.register_blueprint(stock_api)
app.register_blueprint(groq_api)
app.register_blueprint(gemini_api)
app.register_blueprint(microblog_api)

app.register_blueprint(analytics_api)
app.register_blueprint(student_api)
# app.register_blueprint(grade_api)
app.register_blueprint(study_api)
app.register_blueprint(classroom_api)
app.register_blueprint(feedback_api)
app.register_blueprint(scenario_api)  # Register the joke API blueprint
app.register_blueprint(post_api)  # Register the social media post API
# app.register_blueprint(announcement_api) ##temporary revert
app.register_blueprint(quiz_api)

# Register Quest blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(glossary_bp)

# --- Jokes API Resources ---
api = Api(app)

class JokesAPI(Resource):
    def get(self):
        jokes_file = os.path.join(current_app.config['DATA_FOLDER'], 'jokes.json')
        if not os.path.exists(jokes_file):
            return jsonify([])
        with open(jokes_file, 'r') as f:
            jokes = json.load(f)
        return jsonify(jokes)

class JokeByIDAPI(Resource):
    def get(self, joke_id):
        jokes_file = os.path.join(current_app.config['DATA_FOLDER'], 'jokes.json')
        if not os.path.exists(jokes_file):
            return jsonify(None), 404
        with open(jokes_file, 'r') as f:
            jokes = json.load(f)
        if 0 <= joke_id < len(jokes):
            return jsonify(jokes[joke_id])
        return jsonify(None), 404

class RandomJokeAPI(Resource):
    def get(self):
        jokes_file = os.path.join(current_app.config['DATA_FOLDER'], 'jokes.json')
        if not os.path.exists(jokes_file):
            return jsonify(None), 404
        with open(jokes_file, 'r') as f:
            jokes = json.load(f)
        if jokes:
            return jsonify(random.choice(jokes))
        return jsonify(None), 404

class JokeCountAPI(Resource):
    def get(self):
        jokes_file = os.path.join(current_app.config['DATA_FOLDER'], 'jokes.json')
        if not os.path.exists(jokes_file):
            return jsonify({'count': 0})
        with open(jokes_file, 'r') as f:
            jokes = json.load(f)
        return jsonify({'count': len(jokes)})

class JokeHahaAPI(Resource):
    def put(self, joke_id):
        jokes_file = os.path.join(current_app.config['DATA_FOLDER'], 'jokes.json')
        if not os.path.exists(jokes_file):
            return jsonify(None), 404
        try:
            with open(jokes_file, 'r+') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    jokes = json.load(f)
                    if 0 <= joke_id < len(jokes):
                        jokes[joke_id]['haha'] = jokes[joke_id].get('haha', 0) + 1
                        f.seek(0)
                        json.dump(jokes, f, indent=2)
                        f.truncate()
                        result = jokes[joke_id]
                    else:
                        result = None
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
                if result:
                    return jsonify(result)
                return jsonify(None), 404
        except Exception as e:
            print(f'Error updating haha vote: {e}')
            return jsonify({'error': str(e)}), 500

class JokeBoohooAPI(Resource):
    def put(self, joke_id):
        jokes_file = os.path.join(current_app.config['DATA_FOLDER'], 'jokes.json')
        if not os.path.exists(jokes_file):
            return jsonify(None), 404
        try:
            with open(jokes_file, 'r+') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    jokes = json.load(f)
                    if 0 <= joke_id < len(jokes):
                        jokes[joke_id]['boohoo'] = jokes[joke_id].get('boohoo', 0) + 1
                        f.seek(0)
                        json.dump(jokes, f, indent=2)
                        f.truncate()
                        result = jokes[joke_id]
                    else:
                        result = None
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
                if result:
                    return jsonify(result)
                return jsonify(None), 404
        except Exception as e:
            print(f'Error updating boohoo vote: {e}')
            return jsonify({'error': str(e)}), 500

# Register jokes routes
api.add_resource(JokesAPI, '/api/jokes', '/api/jokes/')
api.add_resource(JokeByIDAPI, '/api/jokes/<int:joke_id>', '/api/jokes/<int:joke_id>/')
api.add_resource(RandomJokeAPI, '/api/jokes/random', '/api/jokes/random/')
api.add_resource(JokeCountAPI, '/api/jokes/count', '/api/jokes/count/')
api.add_resource(JokeHahaAPI, '/api/jokes/<int:joke_id>/haha', '/api/jokes/<int:joke_id>/haha/')
api.add_resource(JokeBoohooAPI, '/api/jokes/<int:joke_id>/boohoo', '/api/jokes/<int:joke_id>/boohoo/')

# Jokes file initialization
with app.app_context():
    initScenarios()
    try:
        init_quizzes()
    except Exception:
        # ignore if tables/migrations are not present yet
        pass

# Initialize Quest database
from Quest.database import init_db as init_quest_db
from Quest.models.room import Room

init_quest_db()
demo_room = Room.ensure_demo_room_exists()
print("✅ Quest database initialized")
print(f"✅ Demo room available: {Room.DEMO_ROOM_CODE}")

# Tell Flask-Login the view function name of your login route
login_manager.login_view = "login"

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login', next=request.path))

# register URIs for server pages
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Helper function to check if the URL is safe for redirects
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# Helper function to check Quest database for user
def check_quest_user(username, password):
    """Check if user exists in Quest database and validate password"""
    try:
        if not os.path.exists(QUEST_DB_PATH):
            return None

        conn = sqlite3.connect(QUEST_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        quest_user = cursor.fetchone()
        conn.close()

        if quest_user and bcrypt.checkpw(password.encode('utf-8'), quest_user['password'].encode('utf-8')):
            return dict(quest_user)
        return None
    except Exception as e:
        print(f"Error checking Quest database: {e}")
        return None

# Helper function to sync Quest user to main database
def sync_quest_user_to_main(quest_user, plain_password):
    """Sync a Quest user to the main SQLAlchemy database"""
    try:
        # Check if user already exists in main database
        existing_user = User.query.filter_by(_uid=quest_user['username']).first()

        if existing_user:
            # User exists, just return it (password is valid since we authenticated)
            return existing_user

        # Create new user in main database
        new_user = User(
            name=quest_user.get('username', quest_user['username']),
            uid=quest_user['username'],
            password=plain_password,  # Will be hashed by User.__init__
            role='User'
        )
        new_user._email = quest_user.get('email', '?')

        db.session.add(new_user)
        db.session.commit()
        return new_user
    except Exception as e:
        print(f"Error syncing Quest user: {e}")
        db.session.rollback()
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    next_page = request.args.get('next', '') or request.form.get('next', '')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # First, try to authenticate with the main database
        user = User.query.filter_by(_uid=username).first()

        if user and user.is_password(password):
            # Main database authentication successful
            login_user(user)
            if not is_safe_url(next_page):
                return abort(400)
            return redirect(next_page or url_for('index'))

        # If main database auth fails, check Quest database
        quest_user = check_quest_user(username, password)

        if quest_user:
            # Quest user found - sync to main database
            synced_user = sync_quest_user_to_main(quest_user, password)

            if synced_user:
                login_user(synced_user)
                if not is_safe_url(next_page):
                    return abort(400)
                return redirect(next_page or url_for('index'))
            else:
                error = 'Error syncing user account. Please try again.'
        else:
            error = 'Invalid username or password.'

    return render_template("login.html", error=error, next=next_page)

@app.route('/studytracker')  # route for the study tracker page
def studytracker():
    return render_template("studytracker.html")


@app.route('/quizzes')
def quizzes():
    return render_template('quizzes.html')


@app.route('/quiz/<int:quiz_id>')
def quiz_page(quiz_id):
    return render_template('quiz.html')


@app.route('/leaderboard/<int:quiz_id>')
def leaderboard_page(quiz_id):
    return render_template('leaderboard.html')
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.errorhandler(404)  # catch for URL not found
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.route('/')  # connects default URL to index() function
def index():
    print("Home:", current_user)
    return render_template("index.html")



@app.route('/users/table2')
@login_required
def u2table():
    users = User.query.all()
    return render_template("u2table.html", user_data=users)

@app.route('/sections/')
@login_required
def sections():
    sections = Section.query.all()
    return render_template("sections.html", sections=sections)

# Helper function to extract uploads for a user (ie PFP image)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
 
@app.route('/users/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.delete()
        return jsonify({'message': 'User deleted successfully'}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Set the new password
    if user.update({"password": app.config['DEFAULT_PASSWORD']}):
        return jsonify({'message': 'Password reset successfully'}), 200
    return jsonify({'error': 'Password reset failed'}), 500

@app.route('/kasm_users')
def kasm_users():
    # Fetch configuration details from environment or app config
    SERVER = current_app.config.get('KASM_SERVER')
    API_KEY = current_app.config.get('KASM_API_KEY')
    API_KEY_SECRET = current_app.config.get('KASM_API_KEY_SECRET')

    # Validate required configurations
    if not SERVER or not API_KEY or not API_KEY_SECRET:
        return render_template('error.html', message='KASM keys are missing'), 400

    try:
        # Prepare API request details
        url = f"{SERVER}/api/public/get_users"
        data = {
            "api_key": API_KEY,
            "api_key_secret": API_KEY_SECRET
        }

        # Perform the POST request
        response = requests.post(url, json=data, timeout=10)  # Added timeout for reliability

        # Validate the API response
        if response.status_code != 200:
            return render_template(
                'error.html', 
                message='Failed to get users', 
                code=response.status_code
            ), response.status_code

        # Parse the users list from the response
        users = response.json().get('users', [])

        # Process `last_session` and handle potential parsing issues
        for user in users:
            last_session = user.get('last_session')
            try:
                user['last_session'] = datetime.fromisoformat(last_session) if last_session else None
            except ValueError:
                user['last_session'] = None  # Fallback for invalid date formats

        # Sort users by `last_session`, treating `None` as the oldest date
        sorted_users = sorted(
            users, 
            key=lambda x: x['last_session'] or datetime.min, 
            reverse=True
        )

        # Render the sorted users in the template
        return render_template('kasm_users.html', users=sorted_users)

    except requests.RequestException as e:
        # Handle connection errors or other request exceptions
        return render_template(
            'error.html', 
            message=f"Error connecting to KASM API: {str(e)}"
        ), 500
        
        
@app.route('/delete_user/<user_id>', methods=['DELETE'])
def delete_user_kasm(user_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    SERVER = current_app.config.get('KASM_SERVER')
    API_KEY = current_app.config.get('KASM_API_KEY')
    API_KEY_SECRET = current_app.config.get('KASM_API_KEY_SECRET')

    if not SERVER or not API_KEY or not API_KEY_SECRET:
        return {'message': 'KASM keys are missing'}, 400

    try:
        # Kasm API to delete a user
        url = f"{SERVER}/api/public/delete_user"
        data = {
            "api_key": API_KEY,
            "api_key_secret": API_KEY_SECRET,
            "target_user": {"user_id": user_id},
            "force": False
        }
        response = requests.post(url, json=data)

        if response.status_code == 200:
            return {'message': 'User deleted successfully'}, 200
        else:
            return {'message': 'Failed to delete user'}, response.status_code

    except requests.RequestException as e:
        return {'message': 'Error connecting to KASM API', 'error': str(e)}, 500


@app.route('/update_user/<string:uid>', methods=['PUT'])
def update_user(uid):
    # Authorization check
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403

    # Get the JSON data from the request
    data = request.get_json()
    print(f"Request Data: {data}")  # Log the incoming data

    # Find the user in the database
    user = User.query.filter_by(_uid=uid).first()
    if user:
        print(f"Found user: {user.uid}")  # Log the found user's UID
        
        # Update the user using the provided data
        user.update(data)  # Assuming `user.update(data)` is a method on your User model
        
        # Save changes to the database
        return jsonify({"message": "User updated successfully."}), 200
    else:
        print("User not found.")  # Log when user is not found
        return jsonify({"message": "User not found."}), 404



    
# Create an AppGroup for custom commands
custom_cli = AppGroup('custom', help='Custom commands')

# Define a command to run the data generation functions
@custom_cli.command('generate_data')
def generate_data():
    initUsers()
    init_microblogs()

# Register the custom command group with the Flask application
app.cli.add_command(custom_cli)
        
# this runs the flask application on the development server
if __name__ == "__main__":
    host = "0.0.0.0"
    port = app.config['FLASK_PORT']
    print(f"** Server running: http://localhost:{port}")  # Pretty link
    app.run(debug=True, host=host, port=port, use_reloader=False)
