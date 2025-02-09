import numpy as np
from utilities import retrieve_mt5_data
from flask import Blueprint, request, jsonify
import pandas_ta as ta
import MetaTrader5 as mt5
from datetime import datetime

trend_dp = Blueprint('trend', __name__)

SYMBOL = "Volatility 10 Index"
ACCOUNT_NUMBER = 40401208
PASSWORD = "6hPQkJsZ9@Wv3nr"
SERVER = "Deriv-Demo"
highest_profit = 0  

@trend_dp.route('/get_trend', methods=['POST'])
def get_trend():
    # Hardcoded values for testing
    login_id = ACCOUNT_NUMBER
    server = SERVER
    password = PASSWORD
    symbol = SYMBOL

    if not all([login_id, server, password, symbol]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    df = retrieve_mt5_data(login_id, password, server, symbol)
    if "error" in df:
        return jsonify(df), 500

    # Calculate essential indicators for market behavior classification
    df['RSI'] = ta.rsi(df['close'], length=9)
    df['ADX'] = ta.adx(df['high'], df['low'], df['close'], length=14)['ADX_14']
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=10)

    # Calculate Bollinger Bands
    bbands_df = ta.bbands(df['close'], length=20)
    df['Bollinger_Upper'] = bbands_df['BBU_20_2.0']
    df['Bollinger_Lower'] = bbands_df['BBL_20_2.0']

    # Precompute the rolling mean of ATR
    df['ATR_Rolling_Mean'] = df['ATR'].rolling(window=10).mean()

    # Market Behavior Classification
    def classify_market(row):
        # Trending Market
        if row['ADX'] > 25:
            if row['RSI'] > 70:
                return 'Uptrend'
            elif row['RSI'] < 30:
                return 'Downtrend'

        # Choppy Market (Range-Bound)
        if row['ADX'] < 20 and abs(row['RSI'] - 50) < 5:
            return 'Choppy'

        # Volatile Market
        if row['ATR'] > row['ATR_Rolling_Mean']:
            return 'Volatile'

        # Breakout Market
        if row['close'] > row['Bollinger_Upper']:
            return 'Breakout'

        # Breakdown Market
        if row['close'] < row['Bollinger_Lower']:
            return 'Breakdown'

        return 'Unknown'

    df['Market_Behavior'] = df.apply(classify_market, axis=1)

    # Return only the latest market behavior
    latest_behavior = df['Market_Behavior'].iloc[-1]

    return jsonify({"status": "success", "latest_behavior": latest_behavior}), 200

@trend_dp.route('/streak', methods=['POST'])
def streak():
    global highest_profit 
    
    # data = request.json
    # login_id = data.get('login_id')
    # password = data.get('password')
    # server = data.get('server')
    # symbol = data.get('symbol')
    
    login_id = ACCOUNT_NUMBER
    server = SERVER
    password = PASSWORD
    symbol = SYMBOL
    
    # Establish connection to MetaTrader 5 terminal
    if not mt5.initialize():
        return jsonify({"error": "Failed to initialize MT5", "code": mt5.last_error()}), 500

    authorized = mt5.login(login_id, password=password, server=server)
    if not authorized:
        return jsonify({"error": f"Failed to connect to {login_id}, error: {mt5.last_error()}"}), 500

    # Get open positions
    orders = mt5.positions_get()
    if orders is None:
        return jsonify({"status": "error", "message": "No open positions or error occurred", "code": mt5.last_error()}), 500
    elif len(orders) == 0:
        return jsonify({"status": "success", "message": "No running trades", "profit": 0}), 200

    # Calculate total profit from all open positions
    current_profit = sum(order.profit for order in orders)

    # Update highest recorded profit
    if current_profit > highest_profit:
        highest_profit = current_profit

    # Check last 3 trades in history
    from_date = datetime(2020, 1, 1)
    to_date = datetime.now()
    history_orders = mt5.history_deals_get(from_date, to_date)

    if history_orders is None:
        return jsonify({"status": "error", "message": "Failed to retrieve trading history"}), 500

    # Convert history orders to a list of closed trades
    closed_trades = [order for order in history_orders if order.profit is not None]

    if len(closed_trades) < 3:
        return jsonify({"status": "success", "message": "Not enough trade history to check for streak"}), 200

    # Get last 3 trades
    last_3_trades = closed_trades[-30:]
    
    filtered_trades = [trade for trade in last_3_trades if trade[13] != 0.0]
    
    past_profit = sum(trade[13] for trade in filtered_trades)
    
    # print(past_profit)
    # return jsonify(past_profit), 200
    # Check if last 3 trades are losses
    # losing_streak = all(trade.profit < 0 for trade in last_3_trades)
    
    balance = mt5.account_info().balance
    # Detect losing streak (profit drops below 80% of peak profit)
    loss_threshold = balance * 0.0005
    if past_profit < 0:
        diff = past_profit
    else:
        diff = current_profit - past_profit
    if  diff < 0 and abs(diff) > loss_threshold:  
        return jsonify({
            "status": "warning",
            "message": "Losing streak detected!",
            "current_profit": current_profit,
            "highest_profit": highest_profit,
            "last_3_trades": filtered_trades,
            "loss_threshold": loss_threshold,
            "diff": diff
        }), 200

    return jsonify({
        "status": "success",
        "current_profit": current_profit,
        "highest_profit": highest_profit,
        "loss_threshold": loss_threshold,
        "diff": diff
    }), 200