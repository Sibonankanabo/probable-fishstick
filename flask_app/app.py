from flask import Flask
from auth import auth_bp
from data import data_bp
from orders import orders_bp
from trend import trend_dp
from  trailing import trailing_dp

app = Flask(__name__)

# Register the blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(data_bp)
app.register_blueprint(trend_dp)
app.register_blueprint(orders_bp)
app.register_blueprint(trailing_dp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
