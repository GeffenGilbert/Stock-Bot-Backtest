# python3 graph.py

import pandas as pd
import matplotlib.pyplot as plt

# Read the trade logs
df = pd.read_csv('trade_logs.csv')

df['profit_loss_pct'] = ((df['sell_price'] - df['buy_price']) / df['buy_price']) * 100

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

df['cumulative_pct'] = df['profit_loss_pct'].cumsum()

# Toggle: Set to True for compounded, False for simple cumulative
use_compounded = True

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Trading Performance Analysis', fontsize=16)

# Calculate compounded cumulative return (reinvesting gains)
compounded = (1 + df['profit_loss_pct'] / 100).cumprod() - 1
compounded_pct = compounded * 100

if use_compounded:
    axes[0, 0].plot(df['date'], compounded_pct, marker='.', linewidth=2, markersize=2, label='Cumulative % (Compounded)')
else:
    axes[0, 0].plot(df['date'], df['cumulative_pct'], marker='o', linewidth=2, markersize=1, label='Cumulative % (Simple)')

axes[0, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[0, 0].set_title('Cumulative Profit/Loss Percent Over Time')
axes[0, 0].set_xlabel('Date')
axes[0, 0].set_ylabel('Cumulative P&L (%)')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].tick_params(axis='x', rotation=45)
axes[0, 0].legend()

colors = ['green' if x > 0 else 'red' for x in df['profit_loss_pct']]
axes[0, 1].bar(range(len(df)), df['profit_loss_pct'], color=colors, alpha=0.7)
axes[0, 1].axhline(y=0, color='black', linewidth=0.8)
axes[0, 1].set_title('Individual Trade Profit/Loss (%)')
axes[0, 1].set_xlabel('Trade Number')
axes[0, 1].set_ylabel('P&L (%)')
axes[0, 1].grid(True, alpha=0.3, axis='y')

# 3. Win rate by sell reason
sell_reason_stats = df.groupby('sell_reason').agg({
    'profit_loss_pct': ['count', lambda x: (x > 0).sum()]
}).reset_index()
sell_reason_stats.columns = ['sell_reason', 'total', 'wins']
sell_reason_stats['win_rate'] = (sell_reason_stats['wins'] / sell_reason_stats['total']) * 100

axes[1, 0].bar(sell_reason_stats['sell_reason'], sell_reason_stats['win_rate'], color='skyblue', alpha=0.7)
axes[1, 0].set_title('Win Rate by Exit Reason')
axes[1, 0].set_xlabel('Exit Reason')
axes[1, 0].set_ylabel('Win Rate (%)')
axes[1, 0].grid(True, alpha=0.3, axis='y')

axes[1, 1].hist(df['profit_loss_pct'], bins=20, color='purple', alpha=0.7, edgecolor='black')
axes[1, 1].axvline(x=0, color='red', linestyle='--', linewidth=2)
axes[1, 1].set_title('Profit/Loss Percent Distribution')
axes[1, 1].set_xlabel('P&L (%)')
axes[1, 1].set_ylabel('Frequency')
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('trading_performance.png', dpi=300, bbox_inches='tight')
print("Graph saved as 'trading_performance.png'")

# Print summary statistics
print("\n=== Trading Performance Summary ===")
print(f"Total Trades: {len(df)}")
print(f"Winning Trades: {(df['profit_loss_pct'] > 0).sum()}")
print(f"Losing Trades: {(df['profit_loss_pct'] < 0).sum()}")
print(f"Win Rate: {(df['profit_loss_pct'] > 0).sum() / len(df) * 100:.2f}%")
print(f"\nSum of P&L %: {df['profit_loss_pct'].sum():.2f}%")
print(f"Average P&L % per Trade: {df['profit_loss_pct'].mean():.2f}%")
print(f"Best Trade: {df['profit_loss_pct'].max():.2f}%")
print(f"Worst Trade: {df['profit_loss_pct'].min():.2f}%")
print("\n=== Exit Reason Breakdown ===")
print(df['sell_reason'].value_counts())

plt.show()
