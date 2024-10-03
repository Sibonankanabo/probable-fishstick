from flask import Blueprint, request,jsonify
from utilities import retrieve_mt5_data, process_data
import MetaTrader5 as mt5

data_bp = Blueprint('data', __name__)

@data_bp.route('/get_data', methods=['POST'])
def api_get_data():
    login_id = request.json.get('login_id')
    server = request.json.get('server')
    password = request.json.get('password')
    symbol = request.json.get('symbol')
    
    if not all([login_id, server, password, symbol]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    df = retrieve_mt5_data(login_id, password, server, symbol)
    if "error" in df:
        return jsonify(df), 500
    
    X, y, scaler, df_scaled, X_train_original = process_data(df)
    split_index = int(0.8 * len(X))
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    response_data = {
        'X_data':X.tolist(),
        'X_train': X_train.tolist(),
        'X_test': X_test.tolist(),
        'y_train': y_train.tolist(),
        'y_test': y_test.tolist(),
        'X_train_original': X_train_original.values.tolist(),
    }

    return jsonify(response_data)

@data_bp.route('/get_trading_data', methods=['POST'])
def get_trading_data():
    data = request.json
    login_id = data.get('login_id')
    server = data.get('server')
    password = data.get('password')
    symbol = data.get('symbol')
    
    if not all([login_id, server, password, symbol]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    df = retrieve_mt5_data(login_id, password, server, symbol)
    if "error" in df:
        return jsonify(df), 500

    X_new_data, _, scaler, df_scaled, X_train_original = process_data(df)

    current_price = df['EMAF'].iloc[-1]
    atr = df['ATR'].iloc[-1]

    response_data = {
        'X_new_data': X_new_data.tolist(),
        'current_price': current_price,
        'atr': atr,
        'scaled_features': df_scaled.iloc[-1].tolist(),
        'X_train_original': X_train_original.values.tolist(),
    }

    return jsonify(response_data)

@data_bp.route('/symbols', methods=['GET'])
def get_symbols():
    if not mt5.initialize():
        return jsonify({"status": "error", "message": "Failed to initialize MetaTrader5."}), 500
    
    symbols = mt5.symbols_get()
    symbol_names = [s.name for s in symbols]
    return jsonify(symbol_names)

