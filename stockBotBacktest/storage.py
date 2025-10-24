# storage for functions that aren't used in the backtest 
# but that I want to keep access to in the future

import yfinance as yf
from config import top_gainers_lookback_days, number_of_top_gainers

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

# get_top_gainers looking hours behind
def get_top_gainers(data, input_date, symbols=None):
    """
    Returns a list of the top number_of_top_gainers gainers for input_date,
    using close price of input_date minus close price of top_gainers_lookback_days before input_date.
    """
    if symbols is None:
        symbols = data.columns.levels[0]
    # Find the index of input_date
    try:
        idx = data.index.get_loc(input_date)
    except KeyError:
        print(f"Date {input_date} not found in data.")
        return []
    lookback_idx = idx - top_gainers_lookback_days
    if lookback_idx < 0:
        print(f"Not enough lookback days before {input_date}.")
        return []
    gainers = []
    for symbol in symbols:
        try:
            close_today = data[symbol].iloc[idx]['Close']
            close_lookback = data[symbol].iloc[lookback_idx]['Close']
            gain = close_today - close_lookback
            gainers.append((symbol, gain))
        except Exception as e:
            continue
    # Sort by gain descending and return top N
    gainers.sort(key=lambda x: x[1], reverse=True)
    return [symbol for symbol, _ in gainers[:number_of_top_gainers]]