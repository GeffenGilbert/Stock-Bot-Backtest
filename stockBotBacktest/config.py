lookback_days = 15
top_gainers_lookback_days = 5
number_of_top_gainers = 20

velocity_lookback = 2
acceleration_lookback = 2
velocity_sma = 5
acceleration_sma = 5

# Signal thresholds
velocity_threshold_min = -0.5
velocity_threshold_max = 0.0
acceleration_threshold = 0.2

# Risk management
stop_loss_pct = 0.05  # 5% stop-loss
profit_target_pct = 0.04  # 4% profit target
use_trailing_stop = True  # Enable trailing stop
trailing_stop_pct = 0.02  # 2% trailing stop

# Time (hour) to stop checking for sell signals in the morning (e.g., 11 for 11am)
morning_sell_time = 11

max_concurrent_positions = 10  # Maximum number of simultaneous positions