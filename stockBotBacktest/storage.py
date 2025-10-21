import yfinance as yf
from config import top_gainers_lookback_days, number_of_top_gainers

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