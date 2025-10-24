# python3 main.py

# bias's to be aware of: 
# due to limited minute data the backtest uses data at the close of the day, in real time I will only be able to use data at 3:58pm, two minute discrepancy
# if a stock hits the take profit and then the stop loss within one hour then it will assume the stop loss was triggered (slight bias against the strategy)

# decide whether dividing by close price or velocity when calculating acceleration
# check which is better in the backtest (leaning torwards dividing by velocity)

import yfinance as yf
import pandas as pd
import csv
from datetime import date, timedelta
import pytz
from config import *

positions = {}

def main():
    import time
    start_time = time.time()

    symbols = get_symbols()
    data = get_data(symbols)
    # print("data: ")
    # print(sorted(set(data.index.date)))

    # buy('NVTS', data, '2025-10-17')
    # print("positions: ", positions)

    # check_sell('NVTS', data, '2025-10-20')

    loop_through_days(data)

    print("Program Completed.")

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\nProgram took {elapsed:.2f} seconds.")

    # # Example usage:
    # current_price = get_price('AAPL', '2025-10-15')
    # print(current_price)

def get_symbols():
    # Reads symbols from yahoo_screener_symbols.csv and returns them as a list of strings.
    symbols = []
    try:
        with open('yahoo_screener_symbols.csv', 'r') as f:
            next(f)  # skip header
            for line in f:
                parts = line.strip().split(',')
                if parts and parts[0]:
                    symbols.append(parts[0])
    except Exception as e:
        print(f"Error reading symbols: {e}")
    return symbols

def get_data(symbols):
    # Gets historical bars for each symbol in the array symbols from lookback_days ago to today.
    # Returns a DataFrame of historical data.
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)
    print("Downloading data...")
    try:
        data = yf.download(symbols, start=start_date, end=end_date + timedelta(days=1), interval='60m', progress=False, auto_adjust=False, group_by='ticker')
        print(f"Downloaded data for {len(symbols)} symbols.")
    except Exception as e:
        print(f"Error retrieving data for symbols: {e}")
        data = None
    return data

def filter_valid_symbols(data, symbols):
    # Filters out symbols with no data and returns valid_symbols, missing_symbols.
    valid_symbols = []
    missing_symbols = []
    if isinstance(data, dict):
        for symbol in symbols:
            df = data.get(symbol)
            if df is not None and not df.empty:
                valid_symbols.append(symbol)
            else:
                missing_symbols.append(symbol)
    else:
        for symbol in symbols:
            try:
                df = data[symbol]
                if df is not None and not df.dropna(how='all').empty:
                    valid_symbols.append(symbol)
                else:
                    missing_symbols.append(symbol)
            except (KeyError, AttributeError):
                missing_symbols.append(symbol)
    return valid_symbols, missing_symbols

def get_top_gainers(data, input_date):
    # Returns a list of the top number_of_top_gainers gainers for input_date,
    # using daily close price of input_date minus close price of top_gainers_lookback_days before input_date.
    symbols = data.columns.levels[0]
    # Build a sorted list of unique dates (days) from the index
    all_dates = sorted(set(pd.to_datetime(data.index).date))
    input_date = pd.to_datetime(input_date).date()
    # Find the index of input_date in the list of days
    try:
        idx = all_dates.index(input_date)
    except ValueError:
        print(f"Date {input_date} not found in data.")
        return []
    lookback_idx = idx - top_gainers_lookback_days
    if lookback_idx < 0:
        print(f"Not enough lookback days before {input_date}.")
        return []
    # Get the actual timestamps for the last bar of each day
    def close_price_for_day(df, day):
        day_bars = df.loc[pd.to_datetime(df.index).date == day]
        if not day_bars.empty:
            return day_bars.iloc[-1]['Close']
        return None
    gainers = []
    for symbol in symbols:
        try:
            df = data[symbol]
            close_today = close_price_for_day(df, all_dates[idx])
            close_lookback = close_price_for_day(df, all_dates[lookback_idx])
            if close_today is not None and close_lookback is not None:
                gain = (close_today - close_lookback) / close_today
                gainers.append((symbol, gain))
        except Exception:
            continue
    gainers.sort(key=lambda x: x[1], reverse=True)
    return [symbol for symbol, _ in gainers[:number_of_top_gainers]]

def calculate_vel_acc(symbol, data, input_date):
    # Calculates velocity and acceleration SMA for a stock symbol at input_date (hour bars).
    # Returns (velocity_sma_value, acceleration_sma_value) for the last bar of input_date.

    df = data[symbol]
    # Calculate velocity for each bar
    close = df['Close']
    velocity = 100 * (close - close.shift(velocity_lookback)) / close
    # Calculate acceleration for each bar
    prev_close = close.shift(acceleration_lookback)
    prev_close_vel_lookback = close.shift(acceleration_lookback + velocity_lookback)
    prev_velocity = 100 * (prev_close - prev_close_vel_lookback) / prev_close
    acceleration = (velocity - prev_velocity) / velocity
    # Calculate SMA for velocity and acceleration
    velocity_sma_series = velocity.rolling(window=velocity_sma).mean()
    acceleration_sma_series = acceleration.rolling(window=acceleration_sma).mean()

    # Get all bars for the input_date
    input_date = pd.to_datetime(input_date).date()
    day_bars = df.loc[pd.to_datetime(df.index).date == input_date]
    if day_bars.empty:
        print("NO bars for day, ", input_date, ", cannot calculate velocity/acceleration SMA.")
        return None, None
    # Use the last bar of the day
    idx = day_bars.index[-1]
    velocity_sma_value = velocity_sma_series.loc[idx]
    acceleration_sma_value = acceleration_sma_series.loc[idx]
    return float(velocity_sma_value), float(acceleration_sma_value)

def check_buy(symbol, data, input_date):
    velocity, acceleration = calculate_vel_acc(symbol, data, input_date)
    if velocity_threshold_min < velocity and velocity < velocity_threshold_max and acceleration > acceleration_threshold:
        buy(symbol, data, input_date, velocity, acceleration)

def buy(symbol, data, input_date, velocity, acceleration):
    buy_price = data[symbol]['Close'].loc[pd.to_datetime(data.index).date == pd.to_datetime(input_date).date()].iloc[-1]
    
    positions[symbol] = {
        'buy_date': input_date, 
        'buy_price': float(buy_price), 
        'velocity': velocity, 
        'acceleration': acceleration
    }

# Checks for sell signals for a symbol on input_date up to morning_sell_time.
def check_sell(symbol, data, input_date):
    # Check if symbol exists in positions
    if symbol not in positions:
        print("Error: trying to sell a stock without it being in positions.")
        return

    # Get all bars for the input_date
    df = data[symbol]
    input_date = pd.to_datetime(input_date).date()
    day_bars = df.loc[pd.to_datetime(df.index).date == input_date]
    if day_bars.empty:
        return

    # print("Day bars:", day_bars)

    # Get buy price from positions
    buy_price = positions[symbol]['buy_price']
    take_profit_price = buy_price * (1 + profit_target_pct)
    trailing_stop_loss_price = buy_price * (1 - trailing_stop_pct)

    # Loop through hour bars for the day until morning_sell_time
    for idx, row in day_bars.iterrows():
        bar_time = pd.to_datetime(idx)
        close = row['Close']
        high = row['High']
        low = row['Low']
        
        est = pytz.timezone('US/Eastern')
        bar_time_est = bar_time.astimezone(est)
        # print(bar_time_est.hour)
        if bar_time_est.hour >= morning_sell_time:
            sell(symbol, close, "MorningExit")
            return
        
        # Update trailing stop loss if current high allows for a higher stop
        trailing_stop_loss_price = max(trailing_stop_loss_price, high * (1 - trailing_stop_pct))
        # if a stock hits the take profit and then the stop loss within one hour then it will assume the stop loss was triggered (slight bias against the strategy)
        if high >= take_profit_price:
            sell(symbol, take_profit_price, "TakeProfit")
            return
        if low <= trailing_stop_loss_price:
            sell(symbol, trailing_stop_loss_price, "StopLoss")
            return
    
    print(f"ERROR: For symbol {symbol}, on date {str(input_date)}, checked sell for the day but did not sell (this should not be happening).")

# Sells a position for a symbol at a given price and time
def sell(symbol, sell_price, sell_reason):
    # print(f"SELL {symbol} at {sell_price} on {sell_time}")
    buy_date = positions[symbol]['buy_date']
    buy_price = positions[symbol]['buy_price']
    velocity = positions[symbol]['velocity']
    acceleration = positions[symbol]['acceleration']

    with open("trade_logs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([symbol, buy_date, buy_price, sell_price, velocity, acceleration, sell_reason])

    del positions[symbol]

def loop_through_days(data):
    header = ["symbol", "date", "buy_price", "sell_price", "velocity", "acceleration", "sell_reason"]
    # Create or clear the trade_logs.csv file and write the header
    with open("trade_logs.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)

    # Loops through all days (rows) in the data and prints each date.
    all_dates = sorted(set(pd.to_datetime(data.index).date))
    for current_date in all_dates[top_gainers_lookback_days:]:
        for symbol in list(positions.keys()):
            check_sell(symbol, data, current_date)
            # Process each symbol in positions
        
        top_gainers = get_top_gainers(data, current_date)
        for symbol in top_gainers:
            check_buy(symbol, data, current_date)

        # Add counter and progress tracking
        if 'day_counter' not in locals():
            day_counter = 0
            total_days = len(set(data.index.date))
        day_counter += 1
        if day_counter % 50 == 0:
            print(f"Looped through {day_counter} days / {total_days} days")

if __name__ == "__main__":
    main()
