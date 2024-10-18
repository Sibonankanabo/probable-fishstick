import numpy as np
import pandas as pd
import pandas_ta as ta
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import time
import requests
import logging
import mysql.connector
from mysql.connector import Error
import joblib  # For loading the scaler
import streamlit as st
from magicbox import decisions as dc

# Setup logging
logging.basicConfig(filename="traderbot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# API base URL
BASE_URL = "http://localhost:5000"

def traderbot(login_id, server, password, symbol, lot_size, risk_percentage):
    
    TIMEFRAME = "M15"  # Set timeframe string to use in API
    HISTORY_BARS = 100  # Number of bars to fetch
    
    # Fetch the model name from the database
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

            if result and 'model' in result:
                model_name = result['model']
            else:
                logging.error("Model not found in database for symbol: %s", symbol)
                return
    except Error as e:
        logging.error("Database connection error: %s", e)
        return
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    lot_size = float(lot_size)

    # Load the trained model
    try:
        model = load_model(model_name)
        logging.info("Model %s loaded successfully", model_name)
    except Exception as e:
        logging.error("Failed to load model %s: %s", model_name, e)
        return

    # Load the MinMaxScaler if saved during training
    try:
        scaler = MinMaxScaler() 
        logging.info("Scaler loaded successfully")
    except Exception as e:
        logging.error("Failed to load scaler: %s", e)
        scaler = None

    # Function to place orders via Flask API
    def place_order(order_type, price, sl_level, tp_level, predicted_diff):
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
                logging.info("Order placed: %s", response.json())
                return response.json()
            else:
                logging.error("Order placement failed: %s", response.json().get('message'))
                return None
        except Exception as e:
            logging.error("Error placing order: %s", e)
            return None

    # Function to close open positions via Flask API
    def close_positions(order_type):
        payload = {"login_id": login_id, "password": password, "server": server, "symbol": symbol, "order_type": order_type}
        try:
            response = requests.post(f"{BASE_URL}/close_position", json=payload)
            if response.status_code == 200:
                logging.info("Positions closed successfully.")
                return response.json()
            else:
                logging.error("Failed to close positions: %s", response.json().get('message'))
                return None
        except Exception as e:
            logging.error("Error closing positions: %s", e)
            return None
    # def trailing_stop_loss(login_id, password, server, symbol, trailing_distance):
    #     payload = {"login_id": login_id, "password": password, "server": server, "symbol": symbol, "trailing_distance": trailing_distance}
    #     try:
    #         response = requests.post(f"{BASE_URL}/close_position", json=payload)
    #         if response.status_code == 200:
    #             logging.info("Positions closed successfully.")
    #             return response.json()
    #         else:
    #             logging.error("Failed to close positions: %s", response.json().get('message'))
    #             return None
    #     except Exception as e:
    #         logging.error("Error closing positions: %s", e)
    #         return None

    # Streamlit setup for displaying info
    st.title("Forex Trader Bot")
    predicted_diff_placeholder = st.empty()  # Placeholder for predicted diff
    order_type_placeholder = st.empty()     # Placeholder for order type
    countdown_placeholder = st.empty()      # Placeholder for countdown timer

    def countdown_timer(minutes):
        """Shows a countdown timer in Streamlit."""
        for i in range(minutes * 60, 0, -1):
            mins, secs = divmod(i, 60)
            countdown_placeholder.write(f"Next prediction in: {mins:02d}:{secs:02d}")
            time.sleep(1)

    # Start continuous prediction
    try:
        while True:
            # Fetch the latest market data using Flask API
            api_url = f"{BASE_URL}/get_trading_data"
            payload = {
                "login_id": login_id,
                "password": password,
                "server": server,
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "history_bars": HISTORY_BARS,
            }

            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                data = response.json()

                # Extract necessary data
                X_new_data = np.array(data['X_new_data'])  # Features used for prediction
                current_price = np.array(data['current_price'])  # Current market price
                atr = np.array(data['atr'])  # Average True Range (ATR)
                scaled_features = np.array(data['scaled_features'])  # Other scaled features
                original_data = np.array(data['X_train_original'])

                # Reshape data if necessary for the model input
                X_new_data = np.reshape(X_new_data, (X_new_data.shape[0], 1, X_new_data.shape[1]))

                # Make predictions (scaled values)
                prediction_scaled = model.predict(X_new_data)
                
                # Assuming the predicted price is in the last column after inverse transform
                predicted_diff = prediction_scaled[-1, -1]

                # Display prediction in Streamlit
                predicted_diff_placeholder.write(f"Predicted Difference: {predicted_diff}")
                print(f"The predicted difference is: {predicted_diff}")

                stop_loss_pct = 0.005
                take_profit_pct = 0.009

                stop_loss_buy = current_price * (1 - stop_loss_pct)
                stop_loss_sell = current_price * (1 + stop_loss_pct)
                take_profit_buy = current_price * (1 + take_profit_pct)
                take_profit_sell = current_price * (1 - take_profit_pct)

                if predicted_diff > 7:
                    order_type = "buy"
                    sl_level = stop_loss_buy
                    tp_level = take_profit_buy
                elif predicted_diff < -7 :
                    order_type = "sell"
                    sl_level = stop_loss_sell
                    tp_level = take_profit_sell
                else:
                    order_type = "hold"

                # Display order type in Streamlit
                order_type_placeholder.write(f"Order Type: {order_type}")
                print(f"Order type: {order_type}")

                if order_type == "hold":
                    logging.info("No trade placed. Signal too weak to trade.")
                    # Sleep for 15 minutes before the next check if the signal is weak
                    countdown_timer(3)  # Countdown 15 minutes
                else:
                    # Close existing positions
                    close_positions(order_type)
                   
                    # Place the new order
                    price = float(current_price)
                    predicted_diff = float(predicted_diff)
                    result = place_order(order_type, price, sl_level, tp_level, predicted_diff)
                    
                    # trailing_stop_loss()

                    if result:
                        logging.info(f"{'Buy' if order_type == 'buy' else 'Sell'} order placed with result: {result}, Predicted diff: {predicted_diff}")
                        # Wait for 1 hour to allow the trade to take place
                        countdown_timer(60)  # Countdown 1 hour
                    else:
                        logging.error("Failed to place order")
            else:
                logging.error("Failed to fetch market data: %s", response.json().get('message'))

    except Exception as e:
        logging.error("Error occurred: %s", e)
        print(e)
