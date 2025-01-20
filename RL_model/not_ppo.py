import numpy as np
import pandas as pd
import os
import gymnasium as gym
import gym_anytrading
import gym_trading_env
from gym_anytrading.envs import TradingEnv, ForexEnv, StocksEnv, Actions, Positions
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback


def reward_function(history):
    """
    Reward is based on the portfolio valuation change after a trade.
    The goal is to maximize portfolio value incrementally after each step.
    """
    portfolio_valuation = history["portfolio_valuation"]  # Extract portfolio valuation from the history

    # Ensure we have enough data to calculate the reward
    if len(portfolio_valuation) < 2:
        return 0.0

    # Reward is the change in portfolio value between the last two steps
    delta_valuation = portfolio_valuation[-1] - portfolio_valuation[-2]

    # Reward based directly on portfolio valuation change
    return delta_valuation


# Define the model directory
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Load the dataset
data = pd.read_csv('cleaned_data.csv')

# Drop unnecessary features
data = data.drop(['Feature1', 'Feature2', 'Feature3', 'Feature4'], axis=1)

# Ensure proper column naming
if 'Close' in data.columns:
    data.rename(columns={'Close': 'close'}, inplace=True)
data.columns = data.columns.str.lower()


# Define the environment maker
env_maker = gym.make("TradingEnv", df=data, positions=[-1, 0, 1], initial_position=0,reward_function = reward_function)


class SaveBestModelCallback(BaseCallback):
    def __init__(self, save_path, verbose=1):
        super(SaveBestModelCallback, self).__init__(verbose)
        self.save_path = save_path
        self.best_mean_reward = -float('inf')
        self.episode_rewards = []

    def _on_step(self) -> bool:
        # Check if the 'rewards' key is available in the locals (from the rollout buffer)
        if 'rewards' in self.locals:
            rewards = self.locals['rewards']
            self.episode_rewards.append(rewards.sum())  # Sum of rewards for the episode

            # Calculate mean reward over the last 100 episodes
            if len(self.episode_rewards) >= 100:
                mean_reward = np.mean(self.episode_rewards[-100:])

                # Save the model if the mean reward improves
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    self.model.save(self.save_path)
                    if self.verbose > 0:
                        print(f"New best mean reward: {self.best_mean_reward:.2f}. Model saved!")

        return True


# Initialize the PPO model
model = PPO(
    "MlpPolicy", 
    env_maker, 
    learning_rate=2e-4, 
    gamma=0.99,
    gae_lambda=0.95, 
    clip_range=0.3, 
    n_steps=4096, 
    verbose=1, 
    ent_coef=0.2, 
    n_epochs=10, 
    vf_coef=0.8, 
    tensorboard_log="./ppo_trading_tensorboard/"
)

# Define callbacks
save_best_callback = SaveBestModelCallback(save_path=os.path.join(MODEL_DIR, "ppo_trading_best.zip"), verbose=1)

# Train the model
model.learn(total_timesteps=50000, callback=save_best_callback)

# Save the final model
model.save(os.path.join(MODEL_DIR, "ppo_trading_final"))
