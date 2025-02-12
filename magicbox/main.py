from magicbox import decisions as dc
import requests
import logging
import pandas as pd
import numpy as np
from magicbox import data_base as db
from magicbox import get_data as gd
from tensorflow.keras.models import load_model
import streamlit as st
from magicbox import decisions as dc
import threading
import time

logging.basicConfig(filename='mainlogs',level=logging.INFO, format="%(asctime)s - %(message)s")
cooldown_active = False 

BASE_URL = 'http://localhost:5000' 
def main(login_id, server, password, symbol):
    model_name = db.get_model_name(login_id, symbol)
    
    try:
        model = load_model(model_name)
        logging.info("Model %s loaded successfully", model_name)
    except Exception as e:
        logging.error("Failed to load model %s: %s", model_name, e)
        return 500  # Return error status code
    
    X_new_data, current_price, original_data = gd.get_data(BASE_URL, login_id, server, password, symbol)
    volume = original_data[-1][4]
    X_new_data = np.reshape(X_new_data, (X_new_data.shape[0], 1, X_new_data.shape[1]))
    
    prediction_scaled = model.predict(X_new_data)
    prediction_scaled = prediction_scaled[-1, -1]
    action = dc.decision(original_data, prediction_scaled)
    
    price = float(current_price)
    predicted_diff = float(prediction_scaled)
    
    
    if predicted_diff > 0:
        order_type = "buy"
        sl_level = price - (3 * predicted_diff)
        tp_level = price + predicted_diff
    elif predicted_diff < 0:
        order_type = "sell"
        sl_level = price - (3 * predicted_diff)
        tp_level = price + predicted_diff
    else:
        order_type = "hold"
    
    if action == 1:
        # gd.close_positions(login_id, server, password, symbol, order_type)
        result = gd.place_order(login_id, server, password, symbol, order_type, price, sl_level, tp_level, predicted_diff, volume)
        
        st.write(tp_level, price, predicted_diff, result)
        if result:
            if result["status"] == 'success':  # Assuming result has a 'status' field
                st.write(tp_level, price, predicted_diff, result)
                return 200
            else:
                return 500  # Return failure status if no status code present
        else:
            return 500
    else:
        st.write("error  unknown")
        return 500  # Return failure status to retry

def trigger_main_with_interval(login_id, server, password, symbol):
    global cooldown_active
    
    while True:
        if cooldown_active:
            logging.warning("Cooldown active. Waiting 1 hour before resuming operations.")
            time.sleep(60 * 60)  # Wait 1 hour
            cooldown_active = False  # Reset cooldown flag

        status = main(login_id, server, password, symbol)
        
        if status == 200:
            logging.info("Main function executed successfully. Waiting 30 minutes for the next run.")
            time.sleep(60 * 30)  
        else:
            logging.warning("Main function failed. Retrying in 25 seconds.")
            time.sleep(25)  

def trailing_stop_loss(login_id, password, server, symbol):   
    trailing_distance = 0
    trailing_stop_loss_placeholder = st.empty()
    payload = {
        "login_id": login_id,
        "password": password,
        "server": server,
        "symbol": symbol,
        "trailing_distance": trailing_distance
    }

    def trigger_trailing_stop_loss():
        try:
            response = requests.post(f"{BASE_URL}/start_trailing", json=payload)
            if response.status_code == 200:
                logging.info("Trailing Stop Loss Triggered successfully.")
                trailing_stop_loss_placeholder.write(f"Trailing Stop Loss Triggered: {response.json()}")
            else:
                logging.error(f"Failed to trigger trailing stop loss: {response.json().get('message')}")
                trailing_stop_loss_placeholder.write(f"Trailing Stop Loss Error: {response.json().get('message')}")
        except Exception as e:
            logging.error(f"Error in trailing stop loss: {str(e)}")
            trailing_stop_loss_placeholder.write(f"Error in Trailing Stop Loss: {str(e)}")
        
        threading.Timer(25, trigger_trailing_stop_loss).start()  

    trigger_trailing_stop_loss()
    
def streak_monitor(login_id, password, server, symbol):
        global cooldown_active
        
        while True:
            if cooldown_active:
                logging.warning("Cooldown active. Streak monitor is paused.")
                time.sleep(60*30)  # Wait 1 hour
                continue  

            result = gd.get_streak(login_id, password, server, symbol)
            
            if result.get('status') == 'warning':
                logging.warning("Losing streak detected! Stopping all operations for 1 hour.")
                # gd.close_positions(login_id, password, server, symbol, 'sell')
                cooldown_active = True  
            else:
                logging.info("No losing streak detected.")

            time.sleep(25)  

        
        
def start_thread(login_id, server, password, symbol):
    threading.Thread(target=trigger_main_with_interval, args=(login_id, server, password, symbol), daemon=True).start()
    threading.Thread(target=trailing_stop_loss, args=(login_id, password, server, symbol), daemon=True).start()
    threading.Thread(target=streak_monitor, args=(login_id,password,server,symbol), daemon=True).start()