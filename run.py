from flask import Flask, render_template, request, redirect, url_for, session
import os
import dotenv
import pyodbc
import bcrypt
import re
import secrets
from flask_mail import Mail, Message

dotenv.load_dotenv()
from werkzeug.utils import secure_filename
import mimetypes

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


# SQL Server config
server = 'railway-ml.database.windows.net'
database = 'Railways'
sql_username = 'paweladmin@railway-ml'
sql_password = os.getenv('sql_password')

# Flask app config
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Email config
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('EMAIL_USER'),  # Gmail
    MAIL_PASSWORD=os.getenv('EMAIL_PASS')   # App Password
)
mail = Mail(app)

# In-memory token store for password reset
reset_tokens = {}

# Common connection string
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={sql_username};"
    f"PWD={sql_password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Password utilities ---
def is_strong_password(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
    return re.match(pattern, password)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- DB Setup ---
def init_db():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute('''
        IF NOT EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo' 
              AND TABLE_NAME = 'AgentLaw_UserDB'
        )
        BEGIN
            CREATE TABLE dbo.AgentLaw_UserDB (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(100) UNIQUE NOT NULL,
                email NVARCHAR(100) UNIQUE NOT NULL,
                password NVARCHAR(100) NOT NULL
            );
        END
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not is_strong_password(password):
            return "Password too weak. Must have 8+ chars, upper/lowercase, digit & special char."

        hashed_pw = hash_password(password)

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO dbo.AgentLaw_UserDB (username, email, password) VALUES (?, ?, ?)',
                           (username, email, hashed_pw))
            conn.commit()
            return redirect(url_for('login'))
        except pyodbc.IntegrityError:
            return "Email or username already exists"
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM dbo.AgentLaw_UserDB WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password(password, user[0]):
            session['user'] = email
            return redirect(url_for('main'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        token = secrets.token_urlsafe(16)
        reset_tokens[email] = token

        msg = Message("Password Reset",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        link = url_for('reset_password', email=email, token=token, _external=True)
        msg.body = f"Click the link to reset your password:\n{link}"
        mail.send(msg)
        return "Password reset email sent!"
    return render_template('forgot_password.html')

@app.route('/reset/<email>/<token>', methods=['GET', 'POST'])
def reset_password(email, token):
    if email not in reset_tokens or reset_tokens[email] != token:
        return "Invalid or expired token"

    if request.method == 'POST':
        new_password = request.form['new_password']
        if not is_strong_password(new_password):
            return "Password too weak. Try again."

        hashed_pw = hash_password(new_password)
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute('UPDATE dbo.AgentLaw_UserDB SET password = ? WHERE email = ?', (hashed_pw, email))
        conn.commit()
        conn.close()
        reset_tokens.pop(email)
        return redirect(url_for('login'))

    return render_template('reset_password.html')



@app.route('/main', methods=['GET', 'POST'])
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




@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
