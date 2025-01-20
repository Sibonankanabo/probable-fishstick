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

logging.basicConfig(filename='mainlogs',level=logging.INFO, format="%(asctime)s - %(message)s")

BASE_URL = 'http://localhost:5000' 
def main(login_id,server,password,symbol):
    
    model_name = db.get_model_name(login_id,symbol)
    
    try:
        model = load_model(model_name)
        logging.info("Model %s loaded successfully", model_name)
    except Exception as e:
        logging.error("Failed to load model %s: %s", model_name, e)
        return
    
    X_new_data,current_price,original_data = gd.get_data(BASE_URL,login_id,server,password,symbol)
    
    X_new_data = np.reshape(X_new_data, (X_new_data.shape[0], 1, X_new_data.shape[1]))
    
    # original_data = np.reshape(original_data, (original_data.shape[0], 1, original_data.shape[1])) 
    
    prediction_scaled = model.predict(X_new_data)
    
    prediction_scaled = prediction_scaled[-1,-1]
    
    # prediction_scaled = prediction_scaled[-1]    
    action = dc.decision(original_data,prediction_scaled)
    
    # Place the new order
    price = float(current_price)
    predicted_diff = float(prediction_scaled)
    stop_loss_pct = 0.005
    take_profit_pct = 0.009

    stop_loss_buy = current_price * (1 - stop_loss_pct)
    stop_loss_sell = current_price * (1 + stop_loss_pct)
    take_profit_buy = current_price * (1 + take_profit_pct)
    take_profit_sell = current_price * (1 - take_profit_pct)   
    if predicted_diff > 0:
        order_type = "buy"
        sl_level = stop_loss_buy
        tp_level = take_profit_buy
    elif predicted_diff < 0 :
        order_type = "sell"
        sl_level = stop_loss_sell
        tp_level = take_profit_sell
    else:
                    order_type = "hold"
    
    if action == 1:
        
        gd.close_positions(login_id,server,password,symbol,order_type)
        result = gd.place_order(login_id,server,password,symbol,order_type, price, sl_level, tp_level, predicted_diff)
    
        st.write(result)
    # st.write(original_data)
    