from flask import Flask, request, jsonify, render_template, Blueprint, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import re
import bcrypt

# Flask app and Blueprint setup
app = Flask(__name__)
# app.secret_key = 'your_secret_key'
register_bp = Blueprint('register', __name__)

# MySQL connection
def create_connection():
    return mysql.connector.connect(
        host='localhost',
        database='CMLTB_DB',
        user='root',
        password=''
    )

# Route to render the registration form
@register_bp.route('/register')
def register():
    # Get message from query string (if any)
    message = request.args.get('message')
    return render_template('register.html', message=message)

# Route to create a new user
@register_bp.route('/create_user', methods=['POST'])
def create_user():
    conn = create_connection()

    # Extract form data
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    fname = request.form.get('fname')
    lname = request.form.get('lname')

    # Validate email format
    email_regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if not re.match(email_regex, email):
        message = 'Invalid email format'
        return render_template('register.html', message=message)
        # return jsonify({'error': 'Invalid email format'}), 400

    # Hash the password
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=15)
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    cursor = conn.cursor()

    # Check if email is already registered
    cursor.execute("SELECT * FROM USERS WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        message = 'Email already registered'
        return render_template('register.html', message=message)
        # return jsonify({'error': 'Email already registered'}), 409

    # Insert user data into the database
    cursor.execute("INSERT INTO USERS (email, password, phone, f_name, l_name) VALUES (%s, %s, %s, %s, %s)",
                   (email, hashed_password, phone, fname, lname))

    conn.commit()
    cursor.close()
    conn.close()

    # Redirect to login page with a success message
    return redirect(url_for('backend.login_page', message='User registered successfully'))
