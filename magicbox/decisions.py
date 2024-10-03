import pandas as pd
import joblib

# Load the trained model from the file
clf = joblib.load('decision_tree_model.pkl')

predicted_diff = 17.783323287963867
current_price = 6595.211695776594
# Prepare new data (ensure it's in the same format as the training data)
def prepare_data(predicted_diff,current_price):
    
    
    new_data = pd.DataFrame()
    new_data['price_current'] = current_price
    # Add 'comment' column based on the predicted difference
    new_data['comment'] = predicted_diff
    # Calculate the 'order_type' column:
    # Positive 'predicted_diff' -> Buy (0), Negative 'predicted_diff' -> Sell (1)
    new_data['order_type'] = new_data['comment'].apply(lambda x: 1 if x < 0 else 0)
    

    # Ensure DataFrame is not empty and remove constant columns
    if not new_data.empty:
        new_data = new_data.loc[:, (new_data != new_data.iloc[0]).any()]

    # Return the prepared data (without 'time_taken')
    return new_data

# Function to make predictions
def predict_diff(predicted_diff,current_price):
    # Prepare the new data
    X_new = prepare_data(predicted_diff,current_price)

    # Use the model to predict outcomes (e.g., Buy, Sell, Hold)
    # predictions = clf.predict(X_new)

    # Display the predictions
    # print("Predictions:", predictions)
    print(X_new)

# Assuming you have actual new data and predicted differences:
# new_data = pd.read_csv('your_real_data.csv')  # Load your actual new data
# predicted_diff = some_model_or_function_that_predicts_diff(new_data)  # Provide your predicted differences

# Example call to predict_diff (replace with your actual new_data and predicted_diff)
# predict_diff(new_data, predicted_diff)
predict_diff(predicted_diff,current_price)