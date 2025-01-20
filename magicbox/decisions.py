import pandas as pd
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from magicbox import get_data as gd
import streamlit as st
import logging
import numpy as np
import matplotlib.pyplot as plt
from magicbox import data_base as db
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

def decision(data, prediction):
    
    model_name = 'decision_tree_model.joblib'
    loaded_clf = joblib.load(model_name)
    
    data = pd.DataFrame(data)
    data['LSTM_Prediction'] = prediction
     # Drop column by position (column 10 is the 11th column, as indexing starts at 0)
    data = data.drop(data.columns[10], axis=1).values
    X = data
    predictions = loaded_clf.predict(X)
    
    current_prediction = predictions[-1]
    return current_prediction
    

def train_decision_tree_model(login_id, server, password, symbol):
    BASE_URL = 'http://localhost:5000' 
    
    model_name = db.get_model_name(login_id, symbol)
    
    try:
        model = load_model(model_name)
        logging.info("Model %s loaded successfully", model_name)
    except Exception as e:
        logging.error("Failed to load model %s: %s", model_name, e)
        return
    
    X_new_data, current_price, original_data = gd.get_data(BASE_URL, login_id, server, password, symbol)
    
    X_new_data = np.reshape(X_new_data, (X_new_data.shape[0], 1, X_new_data.shape[1]))
    prediction = model.predict(X_new_data)
    
    original_data = pd.DataFrame(original_data)
    original_data['LSTM_Prediction'] = prediction
    data = calculate_pip_profit(original_data)
    data['Profitability'] = (data['Profit'] > 0).astype(int)
    X = data.drop(['Next_Close', 'Profit', 'Profitability', 10], axis=1).values
    y = data['Profitability'] 
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train a decision tree classifier
    clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    clf.fit(X_train, y_train)

    # Visualize the decision tree
    fig, ax = plt.subplots(figsize=(20, 10))
    plot_tree(clf, class_names=['Not Profitable', 'Profitable'], filled=True, fontsize=10, ax=ax)
    ax.set_title("Decision Tree for Avoiding Losses")
    
    # Display the graph in Streamlit
    st.pyplot(fig)
    
    # Evaluate the model
    accuracy = clf.score(X_test, y_test)
    st.write(f"Decision Tree Accuracy: {accuracy:.2f}")

    # Save the model
    model_filename = 'decision_tree_model.joblib'
    joblib.dump(clf, model_filename)

    st.write(f"Model saved as {model_filename}")
    
    
    
def calculate_pip_profit(data):
    # Ensure 'Close' is a pandas Series and shift it to create 'Next_Close'
    data['Next_Close'] = pd.Series(data[8]).shift(-1)
    
    # Define the profit calculation logic
    def profit_logic(row):
        if row['LSTM_Prediction'] > 0:  # BUY signal
            return (row['Next_Close'] - row[8]) * 0.5
        elif row['LSTM_Prediction'] < 0:  # SELL signal
            return (row[8] - row['Next_Close']) * 0.5
        else:
            return 0  # No trade

    # Apply the profit calculation logic
    data['Profit'] = data.apply(profit_logic, axis=1)
    
    # Fill NaN values in 'Profit' column for the last row
    data['Profit'] = data['Profit'].fillna(0)
    
    return data