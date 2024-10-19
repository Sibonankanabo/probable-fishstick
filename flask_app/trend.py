import numpy as np
from utilities import retrieve_mt5_data
from flask import Blueprint, request, jsonify
import pandas_ta as ta

trend_dp = Blueprint('trend', __name__)

SYMBOL = "Volatility 10 Index"
ACCOUNT_NUMBER = 5569074
PASSWORD = "6hPQkJsZ9@Wv3nr"
SERVER = "Deriv-Demo"

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
