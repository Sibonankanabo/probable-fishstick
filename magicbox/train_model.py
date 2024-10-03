import streamlit as st
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import mysql.connector
from mysql.connector import Error
from sklearn.metrics import mean_squared_error


# Function to train the LSTM model
def train(login_id, server, password, symbol):
    st.write("Fetching data from API...")

    # API call to get data
    api_url = "http://localhost:5000/get_data"
    payload = {
        "login_id": login_id,
        "server": server,
        "password": password,
        "symbol": symbol
    }
    response = requests.post(api_url, json=payload)
    
    if response.status_code == 200:  # Successful response
        data = response.json()
        X_train = np.array(data['X_train'])  # Convert to NumPy arrays
        X_test = np.array(data['X_test'])
        y_train = np.array(data['y_train'])
        y_test = np.array(data['y_test'])
        original_data = np.array(data['X_train_original'])  # Not used, but kept for consistency
        
        st.write("Data shapes:")
        st.write(f"X_train shape: {X_train.shape}")
        st.write(f"X_test shape: {X_test.shape}")
        st.write(f"y_train shape: {y_train.shape}")
        st.write(f"y_test shape: {y_test.shape}")
    else:
        st.error(f"Failed to get data from API. Status code: {response.status_code}")
        return
     
    # No scaling is applied as data is already scaled
    # Reshape X_train and X_test to 3D shape for LSTM (assume already scaled)
    X_train = np.reshape(X_train, (X_train.shape[0], 1, X_train.shape[1]))  # (samples, 1, features)
    X_test = np.reshape(X_test, (X_test.shape[0], 1, X_test.shape[1]))  

    # Reshape y_train and y_test if needed (keeping them as 2D arrays for LSTM)
    y_train = y_train.reshape(-1, 1)
    y_test = y_test.reshape(-1, 1)

    st.write("Building and training the LSTM model...")

    # Build the LSTM model
    model = Sequential([
        LSTM(150, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
        Dropout(0.2),
        LSTM(150, return_sequences=False),
        Dropout(0.2),
        Dense(50, activation='relu'),  # Optional, adding more neurons for better performance
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')

    # Train the model with a progress spinner
    with st.spinner('Training the model...'):
        model.fit(X_train, y_train, batch_size=32, epochs=150, validation_data=(X_test, y_test))

    # Predict using the test data
    predictions = model.predict(X_test)

    # No need for inverse scaling as the data is already scaled in the background
    # Directly compare predictions with the actual values
    predictions = predictions.reshape(-1, 1)  # Reshape to (n_samples, 1) if needed

    # Plotting the results
    plt.figure(figsize=(14, 7))
    plt.plot(y_test, label='Actual', color='blue')  # Plot actual y_test values
    plt.plot(predictions, label='Predicted', linestyle='--', color='red')  # Plot predicted values
    plt.title('LSTM Predictions vs Actual Values')
    plt.xlabel('Time Steps')
    plt.ylabel('Next Close')
    plt.legend()
    plt.grid(True)

    st.pyplot(plt.gcf())  # Display the plot in Streamlit
  
    # Display the actual values and predicted values
    

    results = pd.DataFrame({'Actual': y_test.flatten(), 'Predicted': predictions.flatten()})
    
    mse = mean_squared_error(y_test, predictions)
    st.write(f"Mean Squared Error: {mse:.4f}")
    st.write(results)
    
    # Save the model to a file
    model_name = f'{login_id}_{symbol}.h5'
    model.save(model_name)
    st.write(f"Model saved as {model_name}")

    # Save the model name in the database
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='CMLTB_DB',
            user='root',
            password=''
        )

        if connection.is_connected():
            cursor = connection.cursor()
            update_query = """
            UPDATE parameters 
            SET model = %s 
            WHERE login_id = %s AND symbol = %s
            """
            cursor.execute(update_query, (model_name, login_id, symbol))
            connection.commit()
            st.success(f"Model {model_name} saved to database.")

    except Error as e:
        st.error(f"Error: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
