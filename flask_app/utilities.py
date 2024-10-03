import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def retrieve_mt5_data(login_id, password, server, symbol, timeframe=mt5.TIMEFRAME_H1, history_bars=64000):
    if not mt5.initialize():
        return {"error": f"initialize() failed, error code = {mt5.last_error()}"}

    authorized = mt5.login(login_id, password=password, server=server)
    if not authorized:
        return {"error": f"Failed to connect to login_id {login_id}, error code: {mt5.last_error()}"}
    
    data = mt5.copy_rates_from_pos(symbol, timeframe, 0, history_bars)
    if data is None or len(data) == 0:
        return {"error": "No data retrieved."}
    
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['tick_volume'] = df['tick_volume'].astype(float)
    df.sort_values('time', inplace=True)

    return df

def process_data(df):
    X_train_original = df.copy()
    
    df['RSI'] = ta.rsi(df['close'], length=9)
    df['EMAF'] = ta.ema(df['close'], length=10)
    df['EMAM'] = ta.ema(df['close'], length=26)
    df['EMAS'] = ta.ema(df['close'], length=50)
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=10)
    
    df['Adj Close'] = df['close']
    df['TargetNextClose'] = df['close'].shift(-1)
    df['target'] = df['TargetNextClose'] - df['close']
    df.drop(['tick_volume', 'spread', 'real_volume', 'close', 'time'], axis=1, inplace=True)
    df.dropna(inplace=True)

    
    # X_train_original = X_train_original.drop('TargetNextClose', axis=1)
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df.drop('target', axis=1))
    df_scaled = pd.DataFrame(scaled_data, columns=df.drop('target', axis=1).columns)

    X = np.array(df_scaled)
    y = np.array(df['target'])

    return X, y, scaler, df_scaled, X_train_original
