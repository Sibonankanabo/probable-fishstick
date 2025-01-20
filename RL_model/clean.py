import pandas as pd

# Load the data
df = pd.read_csv("X_train_original_with_predictions.csv")

# Rename specific numbered columns
df = df.rename(columns={
    '0': 'Open',
    '1': 'High',
    '2': 'Low',
    '3': 'Feature3',
    '4': 'Volume',
    '5': 'Feature1',
    '6': 'Feature2',
    '7': 'Feature4',
    '8': 'Close',
    '9': 'LSTM_Prediction'
})

# Add the signal column based on LSTM_Prediction
df['signal'] = df['LSTM_Prediction'].apply(lambda x: 1 if x > 8 else (-1 if x < -8 else 0))

# Ensure correct column order
df = df[['Open', 'High', 'Low', 'Close', 'Volume', 'Feature1', 'Feature2', 'Feature3', 'Feature4', 'LSTM_Prediction','signal']]



# Save the cleaned DataFrame to a CSV file
df.to_csv("cleaned_data.csv", index=False)
