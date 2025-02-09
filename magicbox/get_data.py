import requests
import numpy as np
import logging


BASE_URL = 'http://localhost:5000' 


def get_data(BASE_URL,login_id,server,password,symbol):
            
            print(f"login: {login_id}, server: {server}, password: {password}, symbol: {symbol}")

    # Fetch the latest market data using Flask API
            api_url = f"{BASE_URL}/get_trading_data"
            payload = {
                "login_id": login_id,
                "password": password,
                "server": server,
                "symbol": symbol,
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
                
                print(f"login: {login_id}, server: {server}, password: {password}, symbol: {symbol}")

                return X_new_data,current_price,original_data

# Function to place orders via Flask API
def place_order(login_id,server,password,symbol,order_type, price, sl_level, tp_level, predicted_diff,volume):
        
        payload = {
            "login_id": login_id,
            "password": password,
            "server": server,
            "symbol": symbol,
            "order_type": order_type,
            "volume":volume,
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
def close_positions(login_id,server,password,symbol,order_type):
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
    
def get_trend(login_id, password, server, symbol):
        payload = {"login_id": login_id, "password": password, "server": server, "symbol": symbol}
        try:
            response = requests.post(f"{BASE_URL}/get_trend", json=payload)
            if response.status_code == 200:
                logging.info("Positions closed successfully.")
                return response.json()
            else:
                logging.error("Failed to close positions: %s", response.json().get('message'))
                return None
        except Exception as e:
            logging.error("Error closing positions: %s", e)
            return None

def get_streak(login_id, password, server, symbol):
        payload = {"login_id": login_id, "password": password, "server": server, "symbol": symbol}
        try:
            response = requests.post(f"{BASE_URL}/streak", json=payload)
            if response.status_code == 200:
                logging.info("Positions closed successfully.")
                return response.json()
            else:
                logging.error("Failed to close positions: %s", response.json().get('message'))
                return None
        except Exception as e:
            logging.error("Error closing positions: %s", e)
            return None