# python3 main.py

# decide whether dividing by close price or velocity when calculating acceleration
# check which is better in the backtest (leaning torwards dividing by velocity)

import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from config import *

positions = []

def main():
    import time
    start_time = time.time()

    symbols = get_symbols()
    data = get_data(symbols)
    print("data: ")
    print(sorted(set(data.index.date)))

    # print(get_top_gainers(data, '2025-10-17'))
    # print(calculate_vel_acc('NVTS', data, '2025-10-17'))
    buy('NVTS', data, '2025-10-17')
    print("positions: ", positions)

    # loop_through_days(data)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\nProgram took {elapsed:.2f} seconds.")

    # # Example usage:
    # current_price = get_price('AAPL', '2025-10-15')
    # print(current_price)

# it was correct for AAPL 2025-10-15
def get_price(symbol, input_date):
    # Get the price of the stock at 3:59pm on the given date.

    # Download 1-minute interval data for the given date
    start_date = date.fromisoformat(input_date)
    end_date = start_date + timedelta(days=1)
    data = yf.download(symbol, start=start_date, end=end_date, interval='1m', progress=False, auto_adjust=False)
    if data.empty:
        return None

    # specific fields
    close_2nd_last = data['Close'][symbol].iloc[-2]

    return float(close_2nd_last) # get the price at the time of 3:58pm

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
    acceleration = 100 * (velocity - prev_velocity) / close
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
    if velocity_threshold_min < velocity and velocity < velocity_threshold_max and acceleration > acceleration_lookback:
        buy(symbol, data, input_date)

def buy(symbol, data, input_date):
    buy_price = data[symbol]['Close'].loc[pd.to_datetime(data.index).date == pd.to_datetime(input_date).date()].iloc[-1]

    positions.append({
        "symbol": symbol, 
        "buy_price": float(buy_price)
    })

def loop_through_days(data):
    # Loops through all days (rows) in the data and prints each date.
    for current_date in data.index:
        for position in positions:
            symbol = position["symbol"]
            # check_sell(symbol, data, current_date)
            # Process each symbol in positions
        
        top_gainers = get_top_gainers(data, current_date)
        for symbol in top_gainers:
            check_buy(symbol, data, current_date)
        
        # for symbol in top_gainers:
        #     check_buy(symbol, current_date)

        # Add counter and progress tracking
        if 'day_counter' not in locals():
            day_counter = 0
            total_days = len(set(data.index.date))
        day_counter += 1
        if day_counter % 100 == 0:
            print(f"Looped through {day_counter} days / {total_days} days")

if __name__ == "__main__":
    main()
