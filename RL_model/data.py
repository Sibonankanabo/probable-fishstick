import requests
import numpy as np
import pandas as pd

BASE_URL = "http://localhost:5000"
SYMBOL = "Volatility 10 Index"
ACCOUNT_NUMBER = 5569074
PASSWORD = "6hPQkJsZ9@Wv3nr"
SERVER = "Deriv-Demo"

api_url = f"{BASE_URL}/get_trading_data"
payload = {
    "login_id": ACCOUNT_NUMBER,
    "password": PASSWORD,
    "server": SERVER,
    "symbol": SYMBOL,
    "timeframe": 15,
    "history_bars": 6400,
}

response = requests.post(api_url, json=payload)
if response.status_code == 200:
    data = response.json()
    
    # Convert 'X_new_data' to a DataFrame and save it
    X_new_data = np.array(data['X_new_data'])
    df_new = pd.DataFrame(X_new_data)
    df_new.to_csv('X_new_data.csv', index=False)  # Saves 'X_new_data' in a CSV file
    print("X_new_data saved to X_new_data.csv")
    
    # Convert 'X_train_original' to a DataFrame and save it
    if 'X_train_original' in data:
        X_train_original = np.array(data['X_train_original'])
        df_train = pd.DataFrame(X_train_original)
        df_train.to_csv('X_train_original.csv', index=False)  # Saves 'X_train_original' in a CSV file
        print("X_train_original saved to X_train_original.csv")
    else:
        print("'X_train_original' field not found in the response data.")
else:
    print("No data")
