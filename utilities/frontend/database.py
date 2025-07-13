import pyodbc
import os
import dotenv
# database.py
from pymongo import MongoClient
# import os
# from dotenv import load_dotenv

# load_dotenv()

dotenv.load_dotenv()

server = 'railway-ml.database.windows.net'
database = 'Railways'
username = 'paweladmin@railway-ml'
sql_password = os.getenv('sql_password')

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};DATABASE={database};UID={username};PWD={sql_password};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=300;"
    )

def init_db():
    conn = get_connection()
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


def get_db():
    client = MongoClient(os.getenv("MONGODB_URI"))  # e.g., "mongodb+srv://<user>:<pass>@cluster0.mongodb.net/mydb"
    db = client["AgentLawDB"]
    return db
