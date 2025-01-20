from new_env import TradingEnv  # Replace with your module name
import numpy as np

# Define parameters for testing
max_steps = 10  # Limit the number of steps in the episode for testing

# Instantiate the environment
data_path = "cleaned_data.csv"  # Path to your data file
env = TradingEnv(data_path=data_path)

# Reset the environment and get the initial observation
observation, info = env.reset()
done = False
total_reward = 0
step_count = 0

print("=== Starting Environment Test ===")

# Run the episode loop
while not done and step_count < max_steps:
    # Sample a random action
    action = env.action_space.sample()  # Randomly select Hold, Sell, or Buy
    
    # Take a step in the environment
    step_result = env.step(action)
    
    # Handle Gymnasium vs. older Gym step result structure
    if len(step_result) == 5:  # Gymnasium format
        observation, reward, done, truncated, info = step_result
    else:  # Gym format (if truncated is not returned)
        observation, reward, done, info = step_result
        truncated = False  # Default value
    
    # Print step details for debugging
    print(f"Step {step_count + 1}:")
    print(f"  Action: {action} (0=Hold, 1=Sell, 2=Buy)")
    print(f"  Reward: {reward}")
    print(f"  Done: {done}")
    print(f"  Observation: {observation}")
    
    # Accumulate reward
    total_reward += reward
    
    # Increment step count
    step_count += 1
    
    # Render the environment state
    env.render()

# Print results after the episode ends
print("\n=== Test Complete ===")
print(f"Total Steps: {step_count}")
print(f"Total Reward: {total_reward}")

# Close the environment
env.close()
