from flask import Flask
from backend import backend_bp
from register import register_bp

app = Flask(__name__)

app.secret_key = '616-083-942'

app.register_blueprint(backend_bp)
app.register_blueprint(register_bp)

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=9000, debug=True)