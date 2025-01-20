import pandas as pd

# Load the dataset
file_path = "cleaned_data.csv"  # Update with the actual path if needed
data = pd.read_csv(file_path)

# Ensure that the data['Close'] is a pandas Series before shifting
def calculate_pip_profit(data):
    # Ensure 'Close' is a pandas Series and shift it to create 'Next_Close'
    data['Next_Close'] = pd.Series(data['Close']).shift(-1)
    
    # Define the profit calculation logic
    def profit_logic(row):
        if row['signal'] == 1:  # BUY signal
            return (row['Next_Close'] - row['Close']) * 0.5
        elif row['signal'] == 0:  # SELL signal
            return (row['Close'] - row['Next_Close']) * 0.5
        else:
            return 0  # No trade

    # Apply the profit calculation logic
    data['Profit'] = data.apply(profit_logic, axis=1)
    
    # Fill NaN values in 'Profit' column for the last row
    data['Profit'] = data['Profit'].fillna(0)
    
    return data

# Apply the profit calculation
data = calculate_pip_profit(data)

# Save the updated dataset to a new file
output_path = "cleaned_data_with_pip_profit_conditions.csv"
data.to_csv(output_path, index=False)

print(f"Updated dataset with 'Profit' column saved to {output_path}")
