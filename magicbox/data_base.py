import mysql.connector
from mysql.connector import Error
import logging

def get_model_name(login_id,symbol):
     try:
        connection = mysql.connector.connect(
            host='localhost',
            database='CMLTB_DB',
            user='root',
            password=''
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = "SELECT model FROM parameters WHERE login_id = %s AND symbol = %s"
            cursor.execute(query, (login_id, symbol))
            result = cursor.fetchone()

            if result and 'model' in result:
                model_name = result['model']
                
                return model_name
            else:
                logging.error("Model not found in database for symbol: %s", symbol)
                return
     except Error as e:
        logging.error("Database connection error: %s", e)
        return
     finally:
        if connection.is_connected():
            cursor.close()
            connection.close()