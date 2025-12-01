# Import the test data
import sqlite3
import os
from flask import abort
from werkzeug.security import check_password_hash, generate_password_hash

# This defines which functions are available for import when using 'from db.db import *'
__all__ = [
    "create_user",
    "validate_login",
    "get_user_by_username",
    "get_user_by_id",
]

# Establish connection to the SQLite database
def get_db_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
    DB_PATH = os.path.join(BASE_DIR, 'database.db') # Construct the full path to the database file
    conn = sqlite3.connect(DB_PATH)                 # Connect to the database
    conn.row_factory = sqlite3.Row                  # Enable dictionary-like access to rows
    return conn

# Authentication functions
# =========================================================
# Insert a new user (Register)
def create_user(username, password):
    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()

# Validate user exists with password (Login)
def validate_login(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user['password'], password):
        return user
    return None

# Check if a user exists
def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

# Get user by ID
def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user is None:
        abort(404)
    return user

