import gym
from gym import spaces
import numpy as np

class TradingEnv(gym.Env):
    def __init__(self, data, model, initial_balance=1000, history_bars=100):
        super(TradingEnv, self).__init__()
        
        # Define initial parameters
        self.data = data
        self.model = model
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = None  # None means no position, 'long' or 'short' for active positions
        self.history_bars = history_bars
        self.current_step = 0
        self.profit = 0

        # Define action and observation space
        # Actions: 0 = hold, 1 = buy, 2 = sell
        self.action_space = spaces.Discrete(3)
        # Observations include trading features (price data, indicators) and account status
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(data.shape[1] + 2,), dtype=np.float32
        )

    def reset(self):
        # Reset environment to initial state
        self.balance = self.initial_balance
        self.position = None
        self.current_step = 0
        self.profit = 0
        return self._next_observation()

    def _next_observation(self):
        # Get the current data slice plus account information
        obs = np.concatenate([self.data[self.current_step], [self.balance, self.profit]])
        return obs

    def step(self, action):
        # Execute the action
        self._take_action(action)
        
        # Move to the next step
        self.current_step += 1

        # Calculate the reward and check if the episode is done
        reward = self.profit
        done = self.current_step >= len(self.data) - 1
        
        obs = self._next_observation()
        return obs, reward, done, {}

    def _take_action(self, action):
        current_price = self.data[self.current_step][0]  # Assuming the first column is price
        
        if action == 1 and not self.position:  # Buy
            self.position = 'long'
            self.entry_price = current_price
        elif action == 2 and not self.position:  # Sell
            self.position = 'short'
            self.entry_price = current_price
        elif action == 0 and self.position:  # Close position
            if self.position == 'long':
                self.profit += (current_price - self.entry_price)
            elif self.position == 'short':
                self.profit += (self.entry_price - current_price)
            self.position = None

        self.balance += self.profit  # Update balance based on profit

    def render(self, mode='human'):
        print(f'Step: {self.current_step}, Balance: {self.balance}, Profit: {self.profit}')

