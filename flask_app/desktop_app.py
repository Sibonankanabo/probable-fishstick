import subprocess
import threading
import os
from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedTk
from tkinter import scrolledtext
from flask import Flask
from auth import auth_bp
from data import data_bp
from orders import orders_bp
from trend import trend_dp


class FlaskAppManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Flask App Manager")
        self.flask_process = None

        # Set theme
        self.root.set_theme("arc")

        # Header
        self.header_label = ttk.Label(self.root, text="Flask Application Control Panel", font=("Helvetica", 16))
        self.header_label.pack(pady=10)

        # Start Button
        self.start_button = ttk.Button(self.root, text="Start Flask App", command=self.start_flask_app)
        self.start_button.pack(pady=5)

        # Stop Button
        self.stop_button = ttk.Button(self.root, text="Stop Flask App", command=self.stop_flask_app)
        self.stop_button.pack(pady=5)

        # Console Output Area
        self.console_output = scrolledtext.ScrolledText(self.root, wrap=WORD, width=60, height=20, font=("Courier", 10))
        self.console_output.pack(pady=10)

        # Status Label
        self.status_label = ttk.Label(self.root, text="Status: Flask app is not running", foreground="red")
        self.status_label.pack(pady=5)

    def start_flask_app(self):
        if self.flask_process is None:
            # Start Flask app in a separate thread
            self.flask_thread = threading.Thread(target=self.run_flask_app, daemon=True)
            self.flask_thread.start()

            # Update status
            self.status_label.config(text="Status: Flask app is running", foreground="green")
            self.console_output.insert(END, "Starting Flask app...\n")

    def run_flask_app(self):
        # Run Flask app using subprocess
        app = Flask(__name__)

        # Register the blueprints
        app.register_blueprint(auth_bp)
        app.register_blueprint(data_bp)
        app.register_blueprint(orders_bp)
        app.register_blueprint(trend_dp)

        if __name__ == '__main__':
            app.run(host='0.0.0.0', port=5000)

        # Capture output and print to console
        for line in self.flask_process.stdout:
            self.console_output.insert(END, line)
            self.console_output.yview(END)  # Auto scroll to the end

        # Wait for the process to complete
        self.flask_process.wait()

    def stop_flask_app(self):
        if self.flask_process is not None:
            # Terminate the Flask app process
            self.flask_process.terminate()
            self.flask_process = None

            # Update status
            self.status_label.config(text="Status: Flask app is not running", foreground="red")
            self.console_output.insert(END, "Flask app stopped.\n")


# Create and launch the app
if __name__ == "__main__":
    root = ThemedTk(theme="arc")  # Using ttkthemes for a better look
    app = FlaskAppManager(root)
    root.geometry("600x500")
    root.mainloop()
