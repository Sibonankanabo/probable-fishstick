from flask import Blueprint, Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
import bcrypt  # Use bcrypt for hashing
 
backend_bp = Blueprint('backend', __name__)

# MySQL connection
def create_connection():
    return mysql.connector.connect(
        host='localhost',
        database='CMLTB_DB',
        user='root',
        password=''
    )

# Route to render the login page

@backend_bp.route('/')
def login_page():
    # Get the message from the query string (if any)
    message = request.args.get('message')
    return render_template('index.html', message=message)

# Route to handle login logic
@backend_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        # Compare the plain password with the hashed password in the database
        stored_password = user['password'].encode('utf-8')  # Ensure the stored hash is in bytes
        password_bytes = password.encode('utf-8')  # Convert entered password to bytes
        
        if bcrypt.checkpw(password_bytes, stored_password):
            session['logged_in'] = True
            session['email'] = email
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Incorrect password'})
    else:
        return jsonify({'success': False, 'message': 'User not found'})

# Route for dashboard
@backend_bp.route('/dashboard')
def dashboard():
    if 'logged_in' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login_page'))

if __name__ == '__main__':
    backend_bp.run(debug=True)
