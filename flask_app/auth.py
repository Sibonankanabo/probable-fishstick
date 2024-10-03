from flask import Blueprint, request, jsonify
import MetaTrader5 as mt5

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    login_id = int(data.get('login_id'))
    password = data.get('password')
    server = data.get('server')

    if mt5.initialize():
        authorized = mt5.login(login_id, password=password, server=server)
        if authorized:
            return jsonify({"status": "success", "message": "Logged in successfully."})
        else:
            return jsonify({"status": "error", "message": "Wrong credentials."}), 401
    else:
        return jsonify({"status": "error", "message": "Failed to initialize MetaTrader5."}), 500
