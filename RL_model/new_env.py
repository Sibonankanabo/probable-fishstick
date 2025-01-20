import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class TradingEnv(gym.Env):
    """
    Custom Gym environment for trading with reinforcement learning.
    Refined reward function and enhanced trading metrics.
    """

    def __init__(self, data_path, initial_cash=10000, commission=0.002, max_loss_threshold=0.05):
        super(TradingEnv, self).__init__()

        # Load historical data
        self.data_path = data_path
        self.data = None  # Placeholder for loaded data
        self.current_step = 0

        # Trading parameters
        self.initial_cash = initial_cash
        self.commission = commission
        self.max_loss_threshold = max_loss_threshold  # Maximum threshold for unrealized loss
        self.holding = False  # Whether a position is held
        self.purchase_price = 0.0
        self.position = 0  # 0 = No position, 1 = Long, -1 = Short
        self.entry_step = 0  # Step at which the trade was entered

        # Action and observation spaces
        self.action_space = spaces.Discrete(3)  # 0: Hold, 1: Buy, 2: Sell
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )

        # State and episode flags
        self.done = False
        self.reward = 0.0
        self.observation = np.zeros(10, dtype=np.float32)  # Initialize with zeros

    def fetch_historical_data(self):
        """
        Load historical data from the CSV file once.
        """
        self.data = pd.read_csv(self.data_path)
        if self.data.empty:
            raise ValueError("Historical data file is empty or missing.")
        self.num_steps = len(self.data)

    def reset(self, seed=None):
        """
        Reset the environment for a new episode.
        """
        super().reset(seed=seed)
        if self.data is None:
            self.fetch_historical_data()

        self.current_step = 0
        self.holding = False
        self.purchase_price = 0.0
        self.position = 0
        self.entry_step = 0
        self.done = False
        self.observation = self.data.iloc[self.current_step].values.astype(np.float32)

        return self.observation, {}

    def step(self, action):
        """
        Perform a single step in the trading environment.
        
        Args:
            action (int): The action to take (0 = Hold, 1 = Buy, 2 = Sell).
        
        Returns:
            observation (np.ndarray): The current state of the environment.
            reward (float): The reward for the taken action.
            terminated (bool): Whether the episode is terminated.
            truncated (bool): Whether the episode is truncated.
            info (dict): Additional information for debugging.
        """
        # Initialize trading parameters
        stop_loss_pct = 0.005  # 0.5%
        take_profit_pct = 0.01  # 1%

        df = pd.DataFrame(self.data)

        # Process actions
        if action == 1:  # Buy action
            if not self.holding:  # Buy only if not already holding
                self.purchase_price = df['Open'].iloc[self.current_step]
                self.position = 1  # Long position
                self.entry_step = self.current_step
                self.holding = True
        elif action == 2:  # Sell action
            if self.holding:  # Sell only if holding a position
                sell_price = df['Open'].iloc[self.current_step]
                self.reward = self.calculate_profit_or_loss(sell_price)
                self.holding = False
                self.position = 0  # Close position
        elif action == 0:  # Hold action
            # Holding means we continue without making a trade
            self.reward = 0.0  # No reward for holding

        # Risk management: Penalize if unrealized loss exceeds max threshold
        if self.holding and (df['Close'].iloc[self.current_step] - self.purchase_price) / self.purchase_price < -self.max_loss_threshold:
            self.reward -= 0.05  # Penalty for excessive loss

        # Update portfolio value for continuous reward shaping
        if self.holding:
            current_price = df['Close'].iloc[self.current_step]
            portfolio_value = self.initial_cash + (self.position * (current_price - self.purchase_price))
            self.reward += (portfolio_value - self.initial_cash) / self.initial_cash  # Reward for portfolio growth

        # End episode if no more data
        self.current_step += 1
        terminated = self.current_step >= len(self.data)
        truncated = False  # Define truncation logic if needed

        # Set the observation for the next step
        if not terminated:
            observation = self.data.iloc[self.current_step].values.astype(np.float32)
        else:
            observation = np.zeros(self.observation_space.shape, dtype=np.float32)

        return observation, self.reward, terminated, truncated, {}

    def calculate_profit_or_loss(self, sell_price):
        """
        Calculate the profit or loss for a completed trade.
        """
        if self.position == 1:  # Selling a long position
            profit_or_loss = sell_price - self.purchase_price
        elif self.position == -1:  # Selling a short position (if supported)
            profit_or_loss = self.purchase_price - sell_price
        else:
            profit_or_loss = 0
        return profit_or_loss

    def render(self):
        """
        Render the current state.
        """
        if not self.done:
            print(f"Step: {self.current_step}, Price: {self.data.iloc[self.current_step, 0]}")
        else:
            print("Episode finished.")

    def close(self):
        """
        Clean up resources.
        """
        print("Environment closed.")

