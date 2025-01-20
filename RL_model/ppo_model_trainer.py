from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback
from new_env import TradingEnv  # Import your custom environment
import os
import advance_reward as ar

def custom_reward_function(history):
    return ar.advanced_reward_function(
        history,
        enable_risk_management=True,
        enable_transaction_costs=True,
        enable_benchmark_comparison=True,
        enable_long_term_growth=True,
        enable_sharpe_ratio=True,
        enable_drawdown_penalty=True
    )

# Define the environment with the custom reward function

# Path to your data file
DATA_PATH = "cleaned_data.csv"

# Directory to save the model
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Create and initialize the environment
print("Initializing the trading environment...")
try:
    env = TradingEnv(data_path=DATA_PATH)
    env = Monitor(env)  # Use Monitor to log stats like rewards
except Exception as e:
    raise ValueError(f"Failed to initialize the environment. Error: {e}")

# Check if the environment adheres to OpenAI Gym API standards
print("Checking the environment for compatibility...")
try:
    check_env(env, warn=True)
    print("Environment is compatible with stable-baselines3.")
except Exception as e:
    raise ValueError(f"Environment check failed. Error: {e}")

# Initialize the PPO model with optimized hyperparameters
print("Initializing the PPO model...")
model = PPO(
    "MlpPolicy", 
    env, 
    learning_rate=3e-4,  # Updated learning rate
    gamma=0.99,          # Slightly higher discount factor
    gae_lambda=0.95,     # Keeps the GAE lambda at 0.95
    clip_range=0.3,      # Keep the clip range
    n_steps=2048,        # Larger steps per update for more stability
    verbose=1, 
    ent_coef=0.01,       # Keep the entropy coefficient
    n_epochs=10,         # Lower number of epochs for faster training
    vf_coef=0.8,         # Keep the value function coefficient
    tensorboard_log="./ppo_trading_tensorboard/"
)

# Create a checkpoint callback to save models during training
checkpoint_callback = CheckpointCallback(
    save_freq=1000,  # Save the model every 1000 steps for faster training
    save_path=MODEL_DIR,
    name_prefix="ppo_trading_model"
)

# Train the model
print("Starting training...")
try:
    model.learn(total_timesteps=9000000, callback=checkpoint_callback)  # Increased timesteps
    print("Training complete.")
except Exception as e:
    raise RuntimeError(f"Training failed. Error: {e}")

# Save the final trained model
model_path = os.path.join(MODEL_DIR, "ppo_trading_model_final")
model.save(model_path)
print(f"Final model saved to {model_path}.")
