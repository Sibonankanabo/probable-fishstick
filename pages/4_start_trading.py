import streamlit as st
import mysql.connector
from mysql.connector import Error
from magicbox import trade_bot as tb  # Assuming this contains both traderbot and trailing_stop_loss functions

# Ensure user is logged in
# if 'logged_in' in st.session_state and st.session_state['logged_in']:
#     st.write('logged in')
# else:
#     st.warning("Please log in to access this page.")
#     st.stop()

# Function to connect to MySQL database and fetch joined data
def fetch_joined_data():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='CMLTB_DB',
            user='root',
            password=''
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            # Fetch joined account data and parameters
            query = """
                SELECT 
                    account_data.login_id, 
                    account_data.server,
                    account_data.password,
                    parameters.symbol, 
                    parameters.lot_size, 
                    parameters.risk_percentage,
                    parameters.model
                FROM 
                    account_data 
                JOIN 
                    parameters 
                ON 
                    account_data.login_id = parameters.login_id
            """
            cursor.execute(query)
            joined_data = cursor.fetchall()
            return joined_data
    except Error as e:
        st.write(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Function to format the display in the dropdown list
def format_option(option):
    return f"Account ID: {option['login_id']} | Server: {option['server']} | Symbol: {option['symbol']}"

# Initialize session state for buttons
if 'trading_started' not in st.session_state:
    st.session_state['trading_started'] = False
if 'trailing_applied' not in st.session_state:
    st.session_state['trailing_applied'] = False

# Streamlit UI
st.title("Select Account and Parameters for Model Training and Trading")

# Fetch joined data from the database
joined_data = fetch_joined_data()

# Check if data is available
if joined_data:
    # Create a dropdown with formatted options
    selected_option = st.selectbox(
        "Choose Account and Parameters",
        joined_data,
        format_func=format_option
    )

    # Display selected data
    st.write("Selected Account and Parameters:")
    st.write(f"Login ID: {selected_option['login_id']}")
    st.write(f"Server: {selected_option['server']}")
    st.write(f"Symbol: {selected_option['symbol']}")
    st.write(f"Lot Size: {selected_option['lot_size']}")
    st.write(f"Risk Percentage: {selected_option['risk_percentage']}")
    
   
            
        # Button to start trading
    if st.button("Start Trading") or st.session_state['trading_started']:
        if not st.session_state['trading_started']:  # If the trading hasn't been started before
            tb.start_thread(
                selected_option['login_id'],      
                selected_option['password'], 
                selected_option['server'], 
                selected_option['symbol'], 
                selected_option['lot_size'], 
                selected_option['risk_percentage'],
                trailing_distance=0,
            )
            st.session_state['trading_started'] = True
        st.success("Trading started successfully.")

    # Button to apply Stop Loss (SL) Trailing
else:
    st.write("No data found.")
        