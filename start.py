import subprocess
import time
import os

# Function to run Streamlit app
def run_streamlit_app():
    subprocess.Popen(['streamlit', 'run', 'login.py'])

# Function to run Flask app from flask_app directory
def run_flask_app():
    flask_app_path = os.path.join('flask_app', 'desktop_app.py')  # Ensure correct path to flask app
    subprocess.Popen(['python', flask_app_path])

if __name__ == "__main__":
    # Run Streamlit app
    print("Starting Streamlit app...")
    run_streamlit_app()

    # Sleep for a bit to ensure the Streamlit app is up before Flask
    time.sleep(1)

    # Run Flask app
    print("Starting Flask app...")
    run_flask_app()

    # Keep the script running to keep the subprocesses alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Terminating both apps.")
