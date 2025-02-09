from flask import Blueprint, request, jsonify
import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime

orders_bp = Blueprint('orders', __name__)



@orders_bp.route('/close_position', methods=['POST'])
def close_position():
    data = request.json
    login_id = data.get('login_id')
    password = data.get('password')
    server = data.get('server')
    symbol = data.get('symbol')

    if not all([login_id, password, server, symbol]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 200

    positions = mt5.positions_get(symbol=symbol)
      
    if not positions:
        return jsonify({"status": "error", "message": "No open positions found."}), 200
    
    
    results = []

    for position in positions:
        order_type = mt5.ORDER_TYPE_BUY if position.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "magic": position.magic,
            "comment": "LSTM Close Position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(close_request)
        results.append(result._asdict())

    # Save the positions data to CSV
    # create_csv(symbol, positions)

    return jsonify({"status": "success", "message": "Positions closed successfully.", "results": results})


@orders_bp.route('/place_order', methods=['POST'])
def place_order():
    data = request.json
    login_id = data.get('login_id')
    password = data.get('password')
    server = data.get('server')
    symbol = data.get('symbol')
    volume = data.get('volume')
    order_type = data.get('order_type')
    price = data.get('price')
    sl = data.get('sl')
    tp = data.get('tp')
    predicted_diff = data.get('predicted_diff')
    
    # sl = float(sl)
    # tp = float(tp)
    # price = float(price) 
    
    # print(sl,type(sl),tp,type(tp),price,type(price))  
    # print(predicted_diff,sl,tp)
    print(data)
    if not all([login_id, password, server, symbol, volume, order_type, price, sl]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 404
    tp = tp + predicted_diff
    predicted_diff = str(predicted_diff)
    order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type.lower() == 'buy' else mt5.ORDER_TYPE_SELL
    order_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": 1.0,
        "type": order_type_mt5,
        "price": price,
        "sl": sl,
        "tp":tp,
        "magic": 0,
        "comment": predicted_diff,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(order_request)
   
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        # print(mt5.last_error())
        # print(result.retcode,order_type_mt5)
        # print(predicted_diff,sl,tp)
        return jsonify({"status": "error", "message": f"Failed to place order: {result.retcode}"}), 500
        
    
    # print(mt5.last_error())
    return jsonify({"status": "success", "message": "Order placed successfully.", "result": result._asdict()})

@orders_bp.route('/update_trailing_stop_loss', methods=['POST'])
def update_trailing_stop_loss():
    data = request.json
    login_id = data.get('login_id')
    password = data.get('password')
    server = data.get('server')
    symbol = data.get('symbol')
    trailing_distance = data.get('trailing_distance')

    if not all([login_id, password, server, symbol, trailing_distance]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 404

    # Ensure trailing distance is numeric
    try:
        trailing_distance = float(trailing_distance)
    except ValueError:
        return jsonify({"status": "error", "message": "Trailing distance must be a number."}), 400

    # Call the trailing stop loss function
    result = trailing_stop_loss(login_id, password, server, symbol, trailing_distance)
    
    return jsonify(result)


def trailing_stop_loss(login_id, password, server, symbol, trailing_distance):
    # Ensure all required fields are present
    if not all([login_id, password, server, symbol]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 200

    # Retrieve current open positions for the given symbol
    positions = mt5.positions_get(symbol=symbol)
    
    if not positions:
        return jsonify({"status": "error", "message": "No open positions found."}), 200

    # Get current market price for the symbol
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return jsonify({"status": "error", "message": "Unable to get current price."}), 500

    # List to store the results of updating stop losses
    results = []

    for position in positions:
        # Get current stop loss and position type (buy or sell)
        current_stop_loss = position.sl
        position_type = position.type

        # For BUY positions, we calculate the new stop loss to be trailing below the current ask price
        if position_type == mt5.ORDER_TYPE_BUY:
            current_price = tick.ask
            new_stop_loss = current_price - trailing_distance

            # Update the stop loss only if the new stop loss is higher than the current one
            if new_stop_loss > current_stop_loss:
                change_stop_loss_request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "position": position.ticket,  # The unique position identifier (ticket)
                    "sl": new_stop_loss,          # Set new trailing stop loss value
                    "tp": position.tp,            # Keep the current take profit as it is
                    "magic": position.magic,      # Preserve the magic number
                    "comment": "Trailing SL update", # Optional: Comment for the trade
                }

                # Send the request to modify the stop loss
                result = mt5.order_send(change_stop_loss_request)
                results.append(result._asdict())

        # For SELL positions, we calculate the new stop loss to be trailing above the current bid price
        elif position_type == mt5.ORDER_TYPE_SELL:
            current_price = tick.bid
            new_stop_loss = current_price + trailing_distance

            # Update the stop loss only if the new stop loss is lower than the current one
            if new_stop_loss < current_stop_loss:
                change_stop_loss_request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "position": position.ticket,  # The unique position identifier (ticket)
                    "sl": new_stop_loss,          # Set new trailing stop loss value
                    "tp": position.tp,            # Keep the current take profit as it is
                    "magic": position.magic,      # Preserve the magic number
                    "comment": "Trailing SL update", # Optional: Comment for the trade
                }

                # Send the request to modify the stop loss
                result = mt5.order_send(change_stop_loss_request)
                results.append(result._asdict())

    return jsonify({"status": "success", "message": "Trailing stop loss updated successfully.", "results": results})

