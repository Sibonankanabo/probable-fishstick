import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, classification_report
import joblib
import streamlit as st


symbol = 'Volatility 10 Index'

def train_decisions(symbol):
    # Load the data
    filename = f"{symbol}_trades.csv"
    
    data = pd.read_csv(filename)

    # Convert 'time' and 'time_update' to datetime for time difference calculation
    data['time'] = pd.to_datetime(data['time'])
    data['time_update'] = pd.to_datetime(data['time_update'])

    # Add 'order_type' column (negative values -> sell (1), positive -> buy (0))
    data['order_type'] = data['comment'].apply(lambda x: 1 if x < 0 else 0)

    # Add 'profit_status' column (greater than 0 -> profit (1), less than 0 -> loss (0))
    data['profit_status'] = data['profit'].apply(lambda x: 1 if x > 0 else 0)

    # Calculate the time difference between 'time' and 'time_update' in seconds
    data['time_taken'] = (data['time_update'] - data['time']).dt.total_seconds()

    # Drop irrelevant columns that don’t contribute to decision making
    columns_to_drop = ['ticket', 'time_msc', 'time_update_msc', 'magic', 'identifier', 'reason', 'symbol', 'external_id', 'time', 'time_update','profit','swap','type','price_open','sl','price_current','tp']
    data = data.drop(columns=columns_to_drop, axis=1)

    # Drop rows with missing or NaN values
    data = data.dropna()

    # Ensure DataFrame is not empty before proceeding
    if not data.empty:
        # Remove columns with constant values (if all rows in the column are the same)
        data = data.loc[:, (data != data.iloc[0]).any()]

    # Define the features (X) and the target (y)
    X = data.drop(columns=['profit_status', 'time_taken'])  # All columns except 'order_type' and 'time_taken'

    # Define the target as a combination of time_taken and order_type (buy/sell/hold decision)
    def classify_action(row):
        if row['time_taken'] > 60:  # Example threshold of 60 seconds for holding decision
            return 2  # Hold
        return row['profit_status']  # Buy (0) or Sell (1)

    # Apply the classification to create the 'y' target
    y = data.apply(classify_action, axis=1)
    
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a Decision Tree Classifier
    clf = DecisionTreeClassifier()
    clf.fit(X_train, y_train)

    # Print the accuracy on the test set
    accuracy = clf.score(X_test, y_test)
    print(f"Accuracy: {accuracy * 100:.2f}%")

    # Make predictions
    y_pred = clf.predict(X_test)

    # Compute the confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(cm)

    # Optionally, you can also print a detailed classification report
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save the model to a file
    joblib.dump(clf, 'decision_tree_model.pkl')

    # Display the cleaned dataset
    print(X.head())
    print(y.head())

    print(X_train)
    
train_decisions(symbol)