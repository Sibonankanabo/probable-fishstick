import streamlit as st
import requests
import mysql.connector
from mysql.connector import Error

# Check if user is logged in
if 'logged_in' in st.session_state and st.session_state['logged_in']:
    st.write('Logged in')
else:
    st.warning("Please log in to access this page.")
    st.stop()

# Function to save data to MySQL
def save_to_mysql(login_id, server, password, symbol, lot_size, risk_percentage):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='CMLTB_DB',
            user='root',
            password=''
        )
        
        user_id = st.session_state['user_id']
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Check if login_id already exists
            cursor.execute("SELECT * FROM `account_data` WHERE `login_id` = %s", (login_id,))
            account_exists = cursor.fetchone()

            if account_exists:
                st.write(f"Account with Login ID {login_id} already exists. Adding new parameters.")
                
                # Save parameters only
                cursor.execute(
                    "INSERT INTO `parameters` (`login_id`, `symbol`, `lot_size`, `risk_percentage`) VALUES (%s, %s, %s, %s)",
                    (login_id, symbol, lot_size, risk_percentage)
                )
            else:
                st.write(f"New account. Saving account data and parameters.")
                
                # Save account data
                cursor.execute(
                    "INSERT INTO `account_data` (`login_id`, `user_id`,`server`, `password`) VALUES (%s, %s, %s, %s)",
                    (login_id,user_id, server, password)
                )

                # Save parameters
                cursor.execute(
                    "INSERT INTO `parameters` (`login_id`, `symbol`, `lot_size`, `risk_percentage`) VALUES (%s, %s, %s, %s)",
                    (login_id, symbol, lot_size, risk_percentage)
                )

            connection.commit()
            st.write("Data saved to MySQL database successfully.")
    except Error as e:
        st.write(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            st.write("MySQL connection is closed.")

# Streamlit form for user input
with st.form("my_form"):
    st.write("Login to your account")
    login_id = st.text_input("Login ID")
    server = st.text_input("Server")
    password = st.text_input("Password", type='password')
    
    submitted = st.form_submit_button("Submit")
    if submitted:
        # Check if all required fields are filled
        if not login_id or not server or not password:
            st.write("Please fill in all fields.")
        else:
            # Call the login API
            response = requests.post('http://localhost:5000/login', json={
                'login_id': login_id,
                'server': server,
                'password': password
            })

            if response.status_code == 200:
                st.write("You have logged in successfully. Continue.")
                
                # Get symbols from the API
                symbols_response = requests.get('http://localhost:5000/symbols')
                if symbols_response.status_code == 200:
                    symbols = symbols_response.json()
                    selected_symbol = st.selectbox("Choose symbol", symbols, index=0)
                    lot_size = st.text_input("Lot size")
                    risk_percentage = st.text_input("Risk percentage")

                    if not lot_size or not risk_percentage:
                        st.write("Please enter the lot size and risk percentage.")
                    else:
                        save_to_mysql(login_id, server, password, selected_symbol, lot_size, risk_percentage)
                else:
                    st.write("Failed to get symbols.")
            else:
                st.write(response.json()['message'])
