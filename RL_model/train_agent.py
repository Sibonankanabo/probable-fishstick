import streamlit as st
import requests
import numpy as np
import pandas as pd
import logging
from tensorflow.keras.models import load_model
import mysql.connector
from mysql.connector import Error
from RL_model import trading_env  # assuming it's in a file named trading_env.py


BASE_URL = "http://localhost:5000"
TIMEFRAME = "M15"  # Set timeframe string to use in API
HISTORY_BARS = 100

logging.basicConfig(filename="traderbot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Function to train and predict with the LSTM model
def reifroced(login_id, server, password, symbol):
    
    def get_trend(login_id, password, server, symbol):
        payload = {"login_id": login_id, "password": password, "server": server, "symbol": symbol}
        try:
            response = requests.post(f"{BASE_URL}/get_trend", json=payload)
            if response.status_code == 200:
                logging.info("Market trend data fetched successfully.")
                return response.json()
            else:
                logging.error("Failed to fetch market trend: %s", response.json().get('message'))
                return None
        except Exception as e:
            logging.error("Error fetching market trend: %s", e)
            return None

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
            
    try:
        model = load_model(model_name)
        logging.info("Model %s loaded successfully", model_name)
    except Exception as e:
        logging.error("Failed to load model %s: %s", model_name, e)
        return

    st.write("Fetching data from API...")

    # API call to get data
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
        st.dataframe(X_new_data)
         

        env = trading_env(X_new_data, model)
        obs = env.reset()

        for _ in range(len(X_new_data) - 1):
            action = env.action_space.sample()  # Replace this with a policy later
            obs, reward, done, info = env.step(action)
            env.render()
            if done:
                break


