"""
Quiz Model
Defines Quiz, Question, Choice, and Attempt models
"""
from __init__ import db
from datetime import datetime
import json


class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', backref=db.backref('quiz'), lazy='dynamic')

    def __init__(self, title, description=None):
        self.title = title
        self.description = description
        self.created_at = datetime.utcnow()

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def read(self, include_answers=False):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'questions': [q.read(include_answers=include_answers) for q in self.questions.order_by(Question.id).all()]
        }

    @staticmethod
    def get_by_id(quiz_id):
        return Quiz.query.get(quiz_id)

    @staticmethod
    def get_all():
        return Quiz.query.order_by(Quiz.created_at.desc()).all()


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, default=1)

    choices = db.relationship('Choice', backref=db.backref('question'), lazy='dynamic')

    def __init__(self, quiz_id, text, points=1):
        self.quiz_id = quiz_id
        self.text = text
        self.points = points

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def read(self, include_answers=False):
        return {
            'id': self.id,
            'quizId': self.quiz_id,
            'text': self.text,
            'points': self.points,
            'choices': [c.read(include_answers=include_answers) for c in self.choices.order_by(Choice.id).all()]
        }


class Choice(db.Model):
    __tablename__ = 'choices'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    def __init__(self, question_id, text, is_correct=False):
        self.question_id = question_id
        self.text = text
        self.is_correct = is_correct

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def read(self, include_answers=False):
        data = {
            'id': self.id,
            'questionId': self.question_id,
            'text': self.text,
        }
        if include_answers:
            data['isCorrect'] = bool(self.is_correct)
        return data


class Attempt(db.Model):
    __tablename__ = 'attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    answers = db.Column(db.Text, nullable=True)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    quiz = db.relationship('Quiz', foreign_keys=[quiz_id])

    def __init__(self, user_id, quiz_id, score, total, answers=None):
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.score = score
        self.total = total
        self.answers = json.dumps(answers or [])
        self.timestamp = datetime.utcnow()

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def read(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'userName': self.user.name if self.user else None,
            'quizId': self.quiz_id,
            'score': self.score,
            'total': self.total,
            'answers': json.loads(self.answers) if self.answers else [],
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    @staticmethod
    def get_by_user(user_id):
        return Attempt.query.filter_by(user_id=user_id).order_by(Attempt.timestamp.desc()).all()

    @staticmethod
    def get_by_quiz(quiz_id):
        return Attempt.query.filter_by(quiz_id=quiz_id).order_by(Attempt.score.desc()).all()


def init_quizzes():
    with db.session.begin():
        existing = Quiz.query.first()
        if existing:
            return
        # create a sample quiz
        q = Quiz(title='Sample Quiz: Python Basics', description='A short quiz about Python basics')
        db.session.add(q)
        db.session.flush()

        q1 = Question(quiz_id=q.id, text='What is the output of: print(1+1)?', points=1)
        db.session.add(q1)
        db.session.flush()
        c1 = Choice(question_id=q1.id, text='1', is_correct=False)
        c2 = Choice(question_id=q1.id, text='2', is_correct=True)
        c3 = Choice(question_id=q1.id, text='11', is_correct=False)
        db.session.add_all([c1, c2, c3])

        q2 = Question(quiz_id=q.id, text='Which keyword defines a function in Python?', points=1)
        db.session.add(q2)
        db.session.flush()
        c4 = Choice(question_id=q2.id, text='func', is_correct=False)
        c5 = Choice(question_id=q2.id, text='def', is_correct=True)
        c6 = Choice(question_id=q2.id, text='function', is_correct=False)
        db.session.add_all([c4, c5, c6])

        db.session.commit()
