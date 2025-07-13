# auth.py
from flask import Blueprint, render_template, request, redirect, session, url_for, current_app
from utilities.frontend.database import get_db
from utilities.frontend.security import hash_password, check_password, is_strong_password
from flask_mail import Message
from utilities.frontend import mail
import secrets
import dotenv
import os

dotenv.load_dotenv()
auth_bp = Blueprint('auth', __name__)
reset_tokens = {}

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not is_strong_password(password):
            return "Password too weak. Must include 8+ chars, upper/lowercase, digit, and special char."

        hashed_pw = hash_password(password)
        db = get_db()
        existing_user = db.users.find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            return "Email or username already exists"

        db.users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_pw
        })
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        user = db.users.find_one({'email': email})
        if user and check_password(password, user['password']):
            session['user'] = email
            return redirect(url_for('chatbot.main'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        token = secrets.token_urlsafe(16)
        reset_tokens[email] = token

        msg = Message("Password Reset",
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[email])
        link = url_for('auth.reset_password', email=email, token=token, _external=True)
        msg.body = f"Click the link to reset your password:\n{link}"
        mail.send(msg)
        return "Password reset email sent!"
    return render_template('forgot_password.html')

@auth_bp.route('/reset/<email>/<token>', methods=['GET', 'POST'])
def reset_password(email, token):
    if email not in reset_tokens or reset_tokens[email] != token:
        return "Invalid or expired token"

    if request.method == 'POST':
        new_password = request.form['new_password']
        if not is_strong_password(new_password):
            return "Password too weak. Try again."

        hashed_pw = hash_password(new_password)
        db = get_db()
        db.users.update_one({'email': email}, {'$set': {'password': hashed_pw}})
        reset_tokens.pop(email)
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))
