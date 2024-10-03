import numpy as np
import pandas as pd
import requests
import logging
from tensorflow.keras.models import load_model
from pages.backtesting import Backtest, Strategy
import matplotlib.pyplot as plt  # Add matplotlib for plotting
import streamlit as st

# Setup logging
logging.basicConfig(filename="traderbot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# API base URL
BASE_URL = "http://localhost:5000"

# Parameters
TIMEFRAME = "H4"
HISTORY_BARS = 1000  # Increase the history bars to use a larger dataset for backtesting
PREDICTION_INTERVAL = 150  # Make predictions at every 150 intervals

# Fetch historical data from your API
def get_historical_data(login_id, server, password, symbol):
    api_url = f"{BASE_URL}/get_trading_data"
    payload = {
        "login_id": login_id,
        "password": password,
        "server": server,
        "symbol": symbol,
        "timeframe": TIMEFRAME,
        "history_bars": HISTORY_BARS,
    }

    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        data = response.json()
        historical_data = pd.DataFrame(data['X_train_original'])
        X_new_data = pd.DataFrame(data['X_new_data'])

        # Drop the first column (timestamp) and columns 6, 7
        historical_data = historical_data.drop(columns=[0, 6, 7])

        # Rename columns to 'Open', 'High', 'Low', 'Close', 'Volume'
        historical_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        return historical_data, X_new_data
    else:
        logging.error("Failed to fetch historical data: %s", response.json().get('message'))
        return None, None

# Define trading strategy for backtesting
class TraderStrategy(Strategy):
    # X_new_data will be assigned before backtest run
    X_new_data = None  # Shared class attribute
    window_size = 2   # Number of bars to use in each prediction window

    def init(self):
        # Load the trained model
        self.model = load_model("5569074_Volatility 10 Index.h5")
        logging.info("Model loaded successfully.")
        self.counter = 0  # Track the interval for prediction

    def next(self):
        # Ensure we have enough data for the window and prediction is done at the right interval
        if TraderStrategy.X_new_data is not None and len(self.data) >= self.window_size and self.counter % PREDICTION_INTERVAL == 0:
            # Close any existing open position before opening a new one
            if self.position:
                self.position.close()  # Close existing trade

            # Get the current position in historical_data
            current_index = len(self.data)

            # Extract the rolling window from the current data for prediction
            X_new_data_window = TraderStrategy.X_new_data.iloc[current_index - self.window_size:current_index]
            X_new_data_window = np.array([X_new_data_window.values])  # Add batch dimension
            X_new_data_window = np.reshape(X_new_data_window, (1, self.window_size, X_new_data_window.shape[2]))

            # Plot the window data
            self.plot_data_window(X_new_data_window)

            # Predict price movement
            predicted_diff = self.model.predict(X_new_data_window)[0, -1]

            # Trading logic based on predicted price movement
            current_price = self.data.Close[-1]
            atr = 2 * (self.data.High[-1] - self.data.Low[-1])  # Simple ATR calculation

            # Define stop loss and take profit percentages
            stop_loss_pct = 0.02  # 2%
            take_profit_pct = 0.5  # 50%

            stop_loss_buy = current_price * (1 - stop_loss_pct)
            stop_loss_sell = current_price * (1 + stop_loss_pct)
            take_profit_buy = current_price * (1 + take_profit_pct)
            take_profit_sell = current_price * (1 - take_profit_pct)
            
            print(predicted_diff)

            # Execute the trade based on prediction
            if predicted_diff > 0:
                # Buy if predicted price is going up with stop loss and take profit
                self.buy(sl=stop_loss_buy, tp=take_profit_buy)
            elif predicted_diff < 0:
                # Sell if predicted price is going down with stop loss and take profit
                self.sell(sl=stop_loss_sell, tp=take_profit_sell)
        
        # Increment counter at each step
        self.counter += 1

    def plot_data_window(self, X_new_data_window):
        """
        Plot the sliding window of data used for predictions.
        :param X_new_data_window: The current window of data (numpy array) being used for predictions
        """
        window_size = X_new_data_window.shape[1]
        features = ['Open', 'High', 'Low', 'Close', 'Volume']

        # Squeeze the batch dimension
        X_new_data_window = X_new_data_window.squeeze()

        plt.figure(figsize=(10, 6))

        # Plot each feature in the window
        for i, feature in enumerate(features):
            plt.plot(X_new_data_window[:, i], label=feature)

        plt.title(f"Feature Values in Prediction Window (Last {window_size} Bars)")
        plt.xlabel("Bars")
        plt.ylabel("Value")
        plt.legend()
        plt.show()

# Main function to execute the backtest
def run_backtest(login_id, password, server, symbol):
    # Fetch historical data
    historical_data, X_new_data = get_historical_data(login_id, password, server, symbol)

    if historical_data is not None and isinstance(historical_data, pd.DataFrame):
        # Assign X_new_data to TraderStrategy class variable
        TraderStrategy.X_new_data = X_new_data

        # Run backtest using fetched data
        bt = Backtest(historical_data, TraderStrategy, cash=10000, commission=0.05)
        output = bt.run()
        print(output)  # Print performance metrics
        bt.plot()      # Plot the backtest results
    else:
        print("Failed to retrieve historical data.")

# Call the backtest function with your login credentials and trading parameters
run_backtest(login_id="5569074", password="6hPQkJsZ9@Wv3nr", server="Deriv-Demo", symbol="Volatility 10 Index")
