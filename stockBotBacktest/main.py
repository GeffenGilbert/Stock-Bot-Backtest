# python3 main.py

# stock = yf.Ticker(ticker)
# data = stock.history(
#     start=start_date,
#     end=end_date,
#     interval=interval,
#     auto_adjust=True,
#     prepost=True
# )

import yfinance as yf
from datetime import date, timedelta
from config import top_gainers_lookback_days, number_of_top_gainers

def main():
    # # Example usage:
    # current_price = get_price('AAPL', '2025-10-15')
    # print(current_price)

    # # Example usage for get_day_bars
    # bars = get_day_bars('AAPL', '2025-10-15', current_price)
    # print(bars)
    
    # # Example usage for get_hourly_bars
    # hourly_bars = get_hourly_bars('AAPL', '2025-10-15', current_price)
    # print(hourly_bars)

    symbols = get_symbols()
    # print(symbols)

    top_gainers = get_top_gainers(symbols, '2025-10-15')
    print(top_gainers)

# it was correct for AAPL 2025-10-15
def get_price(symbol, input_date):
    # Get the price of the stock at 3:59pm on the given date.
    # Args:
    #     symbol (str): Stock ticker symbol (e.g., 'AAPL')
    #     input_date (str): Date in 'YYYY-MM-DD' format
    # Returns:
    #     float or None: Price at 3:59pm, or None if not found

    # Download 1-minute interval data for the given date
    start_date = date.fromisoformat(input_date)
    end_date = start_date + timedelta(days=1)
    data = yf.download(symbol, start=start_date, end=end_date, interval='1m', progress=False, auto_adjust=False)
    if data.empty:
        return None

    # specific fields
    close_2nd_last = data['Close'][symbol].iloc[-2]

    return float(close_2nd_last) # get the price at the time of 3:58pm

def get_day_bars(symbol, input_date, current_price):
    # Get the last top_gainers_lookback_days close values for the symbol, including input_date.
    # Uses get_price for the current day's close.
    # Returns a list of close values.
    end_date = date.fromisoformat(input_date)
    # Download extra days to ensure we cover non-trading days (weekends/holidays)
    extra_days = top_gainers_lookback_days * 2
    start_date = end_date - timedelta(days=extra_days)
    # Download daily bars for the range (excluding today)
    data = yf.download(symbol, start=start_date, end=end_date, interval='1d', progress=False, auto_adjust=False)
    # Get last top_gainers_lookback_days closes (actual trading days)
    closes = data['Close'][symbol].dropna().tolist()[-top_gainers_lookback_days:]
    closes.append(current_price)
    return closes

def get_hourly_bars(symbol, input_date, current_price):
    # Returns the last 5 hourly close prices for the given symbol on input_date.
    # Uses get_price for the most recent hour bar (close at 3:59pm).
    start_date = date.fromisoformat(input_date)
    end_date = start_date + timedelta(days=1)
    # Download hourly bars for the date
    data = yf.download(symbol, start=start_date, end=end_date, interval='60m', progress=False, auto_adjust=False)
    if data.empty:
        return []
    # Get last 4 closes from hourly bars (excluding the last, which may be incomplete)
    closes = data['Close'][symbol].dropna().tolist()[-5:-1]
    # Get the most recent close using get_price (close at 3:59pm)
    closes.append(current_price)
    return closes

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

def get_top_gainers(symbols, input_date):
    """
    Loops through the symbols and returns an array of the number_of_top_gainers top gaining stocks
    in the last top_gainers_lookback_days (uses get_day_bars for data retrieval).
    """
    gainers = []
    for symbol in symbols:
        try:
            # Get current price (for today)
            current_price = get_price(symbol, input_date)
            if current_price is None:
                continue
            bars = get_day_bars(symbol, input_date, current_price)
            if len(bars) < 2:
                continue
            pct_gain = (bars[-1] - bars[0]) / bars[0] if bars[0] != 0 else 0
            gainers.append((symbol, pct_gain))
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
    # Sort by percent gain descending and return top N symbols
    gainers.sort(key=lambda x: x[1], reverse=True)
    return [symbol for symbol, _ in gainers[:number_of_top_gainers]]

if __name__ == "__main__":
    main()