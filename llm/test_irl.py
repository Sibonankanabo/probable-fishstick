import numpy as np
import pandas as pd
import pandas_ta as ta
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from sklearn.tree import DecisionTreeClassifier
import joblib
import time
import requests
import logging
import mysql.connector
from mysql.connector import Error
import threading
import streamlit as st

# Setup logging
logging.basicConfig(filename="traderbot.log", level=logging.INFO, format="%(asctime)s - %(message)s")
lot_size =0.5
# API Base URL
BASE_URL = "http://localhost:5000"

def load_resources():
    """Loads model, scaler, and other resources."""
    try:
        # Load LSTM model
        lstm_model = load_model('lstm_model.h5')
        logging.info("LSTM model loaded successfully.")
        
        # Load Decision Tree model
        decision_tree_model = joblib.load('decision_tree_model.joblib')
        logging.info("Decision tree model loaded successfully.")
        
        # Load scaler (if applicable)
        scaler = MinMaxScaler()
        logging.info("Scaler loaded successfully.")
        
        return lstm_model, decision_tree_model, scaler
    except Exception as e:
        logging.error(f"Failed to load resources: {e}")
        raise

def fetch_model_from_db(login_id, symbol):
    """Fetches model name from the database."""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='CMLTB_DB',
            user='root',
            password=''
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = "SELECT model FROM parameters WHERE login_id = %s AND symbol = %s"
            cursor.execute(query, (login_id, symbol))
            result = cursor.fetchone()
            return result['model'] if result and 'model' in result else None
    except Error as e:
        logging.error(f"Database connection error: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_market_data(login_id, password, server, symbol, timeframe, history_bars):
    """Fetches market data via Flask API."""
    payload = {
        "login_id": login_id,
        "password": password,
        "server": server,
        "symbol": symbol,
        "timeframe": timeframe,
        "history_bars": history_bars
    }
    try:
        response = requests.post(f"{BASE_URL}/get_trading_data", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Market data fetch failed: {response.json().get('message')}")
            return None
    except Exception as e:
        logging.error(f"Error fetching market data: {e}")
        return None

def place_order(order_type, price, sl_level, tp_level, predicted_diff, login_id, password, server, symbol):
    """Places an order via Flask API."""
    payload = {
        "login_id": login_id,
        "password": password,
        "server": server,
        "symbol": symbol,
        "volume": lot_size,
        "order_type": order_type,
        "price": price,
        "sl": sl_level,
        "tp": tp_level,
        "predicted_diff": predicted_diff
    }
    try:
        response = requests.post(f"{BASE_URL}/place_order", json=payload)
        if response.status_code == 200:
            logging.info(f"Order placed: {response.json()}")
            return response.json()
        else:
            logging.error(f"Order placement failed: {response.json().get('message')}")
            return None
    except Exception as e:
        logging.error(f"Error placing order: {e}")
        return None

def close_positions(login_id, password, server, symbol, order_type):
    """Closes open positions via Flask API."""
    payload = {"login_id": login_id, "password": password, "server": server, "symbol": symbol, "order_type": order_type}
    try:
        response = requests.post(f"{BASE_URL}/close_position", json=payload)
        if response.status_code == 200:
            logging.info("Positions closed successfully.")
            return response.json()
        else:
            logging.error(f"Failed to close positions: {response.json().get('message')}")
            return None
    except Exception as e:
        logging.error(f"Error closing positions: {e}")
        return None

def traderbot(login_id, password, server, symbol):
    """Main trader bot logic."""
    # Configuration
    TIMEFRAME = "M15"
    HISTORY_BARS = 100
    lot_size = 0.5
    stop_loss_pct = 0.005
    take_profit_pct = 0.009

    # Load models and scaler
    lstm_model, decision_tree_model, scaler = load_resources()

    # Streamlit placeholders
    st.title("Forex Trader Bot")
    predicted_diff_placeholder = st.empty()
    order_type_placeholder = st.empty()
    market_behavior_placeholder = st.empty()
    countdown_placeholder = st.empty()

    # Continuous trading loop
    while True:
        try:
            # Fetch market data
            market_data = fetch_market_data(login_id, password, server, symbol, TIMEFRAME, HISTORY_BARS)
            if not market_data:
                countdown_placeholder.write("Retrying in 60 seconds...")
                time.sleep(60)
                continue

            # Extract features and price
            X_new_data = np.array(market_data['X_new_data'])
            current_price = market_data['current_price']

            # Prepare data for prediction
            X_new_data = np.reshape(X_new_data, (X_new_data.shape[0], 1, X_new_data.shape[1]))
            lstm_prediction = lstm_model.predict(X_new_data)[-1, -1]
            
            # Prepare features for decision tree
            features_for_decision_tree = ['Open', 'High', 'Low', 'Close', 'Volume', 'Feature1', 'Feature2', 'Feature3', 'Feature4', 'LSTM_Prediction']
            X = pd.DataFrame(market_data['original_data'], columns=features_for_decision_tree)
            X['LSTM_Prediction'] = lstm_prediction
            decision_tree_prediction = decision_tree_model.predict(X)[-1]

            # Determine order type
            if decision_tree_prediction == 1:
                order_type = "buy"
                sl_level = current_price * (1 - stop_loss_pct)
                tp_level = current_price * (1 + take_profit_pct)
            elif decision_tree_prediction == -1:
                order_type = "sell"
                sl_level = current_price * (1 + stop_loss_pct)
                tp_level = current_price * (1 - take_profit_pct)
            else:
                order_type = "hold"

            # Streamlit updates
            predicted_diff_placeholder.write(f"LSTM Predicted Diff: {lstm_prediction:.2f}")
            order_type_placeholder.write(f"Order Type: {order_type}")
            market_behavior_placeholder.write(f"Decision Tree Prediction: {decision_tree_prediction} (1=Buy, -1=Sell, 0=Hold)")

            # Execute trades
            if order_type != "hold":
                close_positions(login_id, password, server, symbol, order_type)
                place_order(order_type, current_price, sl_level, tp_level, lstm_prediction, login_id, password, server, symbol, lot_size)
                countdown_placeholder.write("Waiting for next trade cycle...")
                time.sleep(60 * 15)  # Wait 15 minutes
            else:
                logging.info("No trade placed. Holding position.")
                countdown_placeholder.write("Holding position. Checking again in 5 minutes...")
                time.sleep(60 * 5)  # Wait 5 minutes

        except Exception as e:
            logging.error(f"Error in trading loop: {e}")
            st.error(f"Error in trading loop: {e}")
            time.sleep(60)

def start_traderbot():
    st.sidebar.title("Bot Configuration")
    login_id = st.sidebar.text_input("Login ID")
    password = st.sidebar.text_input("Password", type="password")
    server = st.sidebar.text_input("Server")
    symbol = st.sidebar.text_input("Symbol", value="EURUSD")
    lot_size = st.sidebar.text_input("Lot Size", value="0.1")
    risk_percentage = st.sidebar.text_input("Risk Percentage", value="2")

    if st.sidebar.button("Start Bot"):
        threading.Thread(target=traderbot, args=(login_id, password, server, symbol, lot_size, risk_percentage)).start()

if __name__ == "__main__":
    start_traderbot()
