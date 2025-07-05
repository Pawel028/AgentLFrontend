import os

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv('EMAIL_USER')
MAIL_PASSWORD = os.getenv('EMAIL_PASS')
