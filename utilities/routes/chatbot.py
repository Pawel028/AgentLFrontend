from flask import Blueprint, render_template, request, session, redirect, url_for
import os
from werkzeug.utils import secure_filename

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/main', methods=['GET', 'POST'])
def main():
    if 'user' not in session:
        return redirect(url_for('login'))

    if 'chat_history' not in session:
        session['chat_history'] = []

    chat_history = session['chat_history']

    if request.method == 'POST':
        if 'delete_history' in request.form:
            session['chat_history'] = []
        else:
            user_msg = request.form.get('user_input')
            if user_msg:
                bot_msg = f"You said: {user_msg}"
                chat_history.append(("User", user_msg))
                chat_history.append(("Bot", bot_msg))
                session['chat_history'] = chat_history  # 🔁 This is key
    print(session['chat_history'])
    return render_template('chatbot_main.html', chat_history=session['chat_history'])