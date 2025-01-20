import joblib
import pandas as pd

model_filename = 'decision_tree_model.joblib'
# Load the model from the file
loaded_clf = joblib.load(model_filename)

file_path = "cleaned_data_with_pip_profit_conditions.csv"  # Update with the actual path
data = pd.read_csv(file_path)

# Create target variable for profitability
data['Profitability'] = (data['Profit'] > 0).astype(int)

# Select features and target
features = ['Open', 'High', 'Low', 'Close', 'Volume', 'Feature1', 'Feature2', 'Feature3', 'Feature4', 'LSTM_Prediction']
X_test = data[features]
y_test = data['Profitability']

# Use the loaded model for predictions or evaluations
accuracy = loaded_clf.score(X_test, y_test)
print(f"Loaded Model Accuracy: {accuracy:.2f}")
