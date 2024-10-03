import streamlit as st
import mysql.connector
import bcrypt

# MySQL connection
def create_connection():
    return mysql.connector.connect(
        host='localhost',
        database='CMLTB_DB',
        user='root',
        password=''
    )

# Streamlit app
st.title("Login Page")

# Input fields for login
email = st.text_input("Email")
password = st.text_input("Password", type="password")

# When the "Login" button is clicked
if st.button("Login"):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    # Check if user exists
    if user:
        # Get the stored hashed password from the database
        stored_password = user['password'].encode('utf-8')  # Convert stored password to bytes
        password_bytes = password.encode('utf-8')  # Convert entered password to bytes

        # Compare the entered password with the stored hashed password
        if bcrypt.checkpw(password_bytes, stored_password):
            st.success("Login successful!")
            st.session_state['logged_in'] = True
            st.session_state['email'] = email
            st.session_state['user_id'] = user['user_id']  # Store user ID if needed
            # Redirect or rerun the app to load the main page
            # st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    else:
        st.error("User not found")

# Display user information if logged in
if 'logged_in' in st.session_state and st.session_state['logged_in']:
    st.write(f"Logged in as {st.session_state['email']}")
