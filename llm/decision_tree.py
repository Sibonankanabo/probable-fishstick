import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
import matplotlib.pyplot as plt
import joblib

# Load dataset
file_path = "cleaned_data_with_pip_profit_conditions.csv"  # Update with the actual path
data = pd.read_csv(file_path)

# Create target variable for profitability
data['Profitability'] = (data['Profit'] > 0).astype(int)

# Select features and target
features = ['Open', 'High', 'Low', 'Close', 'Volume', 'Feature1', 'Feature2', 'Feature3', 'Feature4', 'LSTM_Prediction']
X = data[features]
y = data['Profitability']

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a decision tree classifier
clf = DecisionTreeClassifier(max_depth=5, random_state=42)
clf.fit(X_train, y_train)

# Print decision tree rules
tree_rules = export_text(clf, feature_names=features)
# print("Decision Tree Rules:\n", tree_rules)

# Visualize the decision tree
plt.figure(figsize=(20, 10))
plot_tree(clf, feature_names=features, class_names=['Not Profitable', 'Profitable'], filled=True, fontsize=10)
plt.title("Decision Tree for Avoiding Losses")
plt.show()

# Evaluate the model
accuracy = clf.score(X_test, y_test)
print(f"Decision Tree Accuracy: {accuracy:.2f}")

model_filename = 'decision_tree_model.joblib'
joblib.dump(clf, model_filename)

print(f"Model saved as {model_filename}")