import MetaTrader5 as mt5
import time

# Constants
TRAILING_STOP_DISTANCE = 4050  # Distance in points for the trailing stop
SYMBOL = "Volatility 10 Index"            # Replace with the symbol you are trading

# MetaTrader 5 Account Information (Replace with your account details)
ACCOUNT_NUMBER = 5569074    # Your MT5 account number
PASSWORD = "6hPQkJsZ9@Wv3nr"   # Your MT5 account password
SERVER = "Deriv-Demo" # Your broker's MT5 server

# Initialize and log in to MetaTrader 5 terminal
def initialize_mt5():
    if not mt5.initialize():
        print("MT5 initialization failed")
        return False
    
    # Try to log in to the MT5 account
    login_status = mt5.login(ACCOUNT_NUMBER, password=PASSWORD, server=SERVER)
    if not login_status:
        print(f"Login failed, error: {mt5.last_error()}")
        return False
    
    print(f"Login successful: {mt5.account_info().name}")
    return True

# Get all active orders
def get_active_orders():
    return mt5.positions_get()

# Modify the stop loss for an active order
def modify_stop_loss(order, new_stop_loss):
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": order.symbol,
        "position": order.ticket,
        "sl": new_stop_loss,
        "tp": order.tp,
        "type": order.type
    }
    
    # Send the request to modify the stop loss
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to modify stop loss for order {order.ticket}. Error: {result.retcode}")
    else:
        print(f"Stop loss updated for order {order.ticket}")

# Perform trailing stop loss on all active orders
def trailing_stop_loss():
    orders = get_active_orders()
    if orders is None or len(orders) == 0:
        print("No active orders found.")
        return

    for order in orders:
        # Get the current market price of the symbol
        price = mt5.symbol_info_tick(order.symbol).bid if order.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(order.symbol).ask

        # Calculate new stop loss based on trailing stop distance
        new_stop_loss = price - TRAILING_STOP_DISTANCE * mt5.symbol_info(order.symbol).point if order.type == mt5.ORDER_TYPE_BUY else price + TRAILING_STOP_DISTANCE * mt5.symbol_info(order.symbol).point

        # Check if the new stop loss is better than the current one (further in profit direction)
        if (order.type == mt5.ORDER_TYPE_BUY and new_stop_loss > order.sl) or (order.type == mt5.ORDER_TYPE_SELL and new_stop_loss < order.sl):
            modify_stop_loss(order, new_stop_loss)

if __name__ == "__main__":
    if initialize_mt5():
        try:
            while True:
                trailing_stop_loss()
                time.sleep(60)  # Wait for a minute before checking again
        except KeyboardInterrupt:
            print("Script terminated by user.")
        finally:
            mt5.shutdown()
