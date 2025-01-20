import gym_anytrading
from stable_baselines3 import PPO
import gymnasium as gym
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from gym_trading_env.renderer import Renderer
import numpy as np
import gym_anytrading
import gym_trading_env
from gym_anytrading.envs import TradingEnv, ForexEnv, StocksEnv, Actions, Positions

# Reload the trained model
model_path = "models/ppo_trading_final.zip"
model = PPO.load(model_path)

# Load the data
data = pd.read_csv('cleaned_data.csv')

data = data.drop(['Feature1', 'Feature2', 'Feature3', 'Feature4'], axis=1)

# Ensure proper column naming
if 'Close' in data.columns:
    data.rename(columns={'Close': 'close'}, inplace=True)

# Convert all column names to lowercase
data.columns = data.columns.str.lower()

# # Add the 'position_signal' column based on 'lstm_prediction'
# if 'lstm_prediction' in data.columns:
#     data['position_signal'] = np.where(data['lstm_prediction'] > 0, 1, -1)
# else:
#     raise KeyError("The column 'lstm_prediction' is missing from the dataset.")


# Add a 'time' column with 1-hour intervals starting from 7 years ago
hours_in_7_years = len(data)  # Number of rows determines the number of intervals
start_time = datetime.now() - timedelta(days=7*365)  # Start time: 7 years ago
time_range = [start_time + timedelta(hours=i) for i in range(hours_in_7_years)]
data['strftime'] = time_range

# Ensure the 'time' column is set as the index
data.set_index('strftime', inplace=True)

# Create a testing environment
test_env = gym.make("TradingEnv", df=data, positions=[-1, 0, 1], initial_position=1)

# Correctly reset the environment for testing
obs, info = test_env.reset()

# Evaluate the model
while True:
    # Use only `obs` for prediction
    action, _states = model.predict(obs)
    obs, reward, terminated, truncated, info = test_env.step(action)
    done = terminated or truncated
    if done:
        break

# Visualize the trading results
# At the end of the episode you want to render
test_env.unwrapped.save_for_render(dir="render_logs")
renderer = Renderer(render_logs_dir="render_logs")
renderer.run()
