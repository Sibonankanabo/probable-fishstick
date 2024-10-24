import MetaTrader5 as mt5
import time
from flask import Blueprint, request, jsonify

trailing_dp = Blueprint('trailing', __name__)

@trailing_dp.route('/start_trailing', methods=['POST'])
def trailing_stop_loss_route():
    data = request.json
    ACCOUNT_NUMBER = data.get('login_id')
    PASSWORD = data.get('password')
    SERVER = data.get('server')
    SYMBOL = data.get('symbol')
    TRAILING_STOP_DISTANCE = 4050

    # Initialize and log in to MetaTrader 5 terminal
    def initialize_mt5():
        if not mt5.initialize():
            return {"message": "MT5 initialization failed"}, 500
        
        # Try to log in to the MT5 account
        login_status = mt5.login(ACCOUNT_NUMBER, password=PASSWORD, server=SERVER)
        if not login_status:
            return {"message": f"Login failed, error: {mt5.last_error()}"}, 401
        
        return {"message": f"Login successful: {mt5.account_info().name}"}, 200

    # Get all active positions for trailing stop
    def get_active_positions():
        positions = mt5.positions_get()
        if positions is None:
            return None, {"message": "No active positions found"}, 404
        return positions, None

    # Modify the stop loss for an active position
    def modify_stop_loss(order, new_stop_loss):
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": order.symbol,
            "position": order.ticket,
            "sl": new_stop_loss,
            "tp": order.tp,
            "type": order.type
        }
        
        # Send the request to modify the stop loss
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"message": f"Failed to modify stop loss for order {order.ticket}. Error: {result.retcode}"}, 500
        return {"message": f"Stop loss updated for order {order.ticket}"}, 200

    # Perform trailing stop loss on all active positions
    def trailing_stop_loss():
        positions, error_response = get_active_positions()
        if error_response:  # Return error if no active positions
            return error_response, 404
        
        updated_orders = []
        for order in positions:
            # Get the current market price of the symbol
            symbol_info = mt5.symbol_info_tick(order.symbol)
            if not symbol_info:
                return {"message": f"Failed to get symbol info for {order.symbol}"}, 400
            
            price = symbol_info.bid if order.type == mt5.ORDER_TYPE_BUY else symbol_info.ask

            # Calculate new stop loss based on trailing stop distance
            new_stop_loss = price - TRAILING_STOP_DISTANCE * mt5.symbol_info(order.symbol).point if order.type == mt5.ORDER_TYPE_BUY else price + TRAILING_STOP_DISTANCE * mt5.symbol_info(order.symbol).point

            # Check if the new stop loss is better than the current one (further in profit direction)
            if (order.type == mt5.ORDER_TYPE_BUY and new_stop_loss > order.sl) or (order.type == mt5.ORDER_TYPE_SELL and new_stop_loss < order.sl):
                update_result, status_code = modify_stop_loss(order, new_stop_loss)
                if status_code == 200:  # Only add successful updates
                    updated_orders.append(update_result)

        if not updated_orders:
            return {"message": "No stop loss modifications were made."}, 200
        return {"updated_orders": updated_orders}, 200

    # Main logic starts here
    initialize_result, init_status_code = initialize_mt5()
    if init_status_code != 200:  # Check if initialization or login failed
        return jsonify(initialize_result), init_status_code
    
    # Start trailing stop loss process
    trailing_result, trailing_status_code = trailing_stop_loss()
    return jsonify(trailing_result), trailing_status_code
