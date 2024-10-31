import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import yfinance as yf
import pandas as pd
import numpy as np
from db import get_all_trades
import statistics


def calculate_portfolio_metrics(trades, initial_capital=5000, risk_percentage=0.10):
    """Calculate portfolio metrics with dynamic position sizing"""
    current_capital = initial_capital
    portfolio_values = []
    contracts_per_trade = []
    
    # Risk and reward per contract
    risk_per_contract = 90  # $450/5 contracts = $90 per contract
    profit_per_contract = 10  # $50/5 contracts = $10 per contract
    
    for trade in trades:
        trade_date = datetime.strptime(trade[4], '%Y-%m-%d')
        
        # Calculate position size
        max_risk = current_capital * risk_percentage
        num_contracts = int(max_risk / risk_per_contract)
        num_contracts = max(1, min(num_contracts, 20))  # Min 1, max 20 contracts
        contracts_per_trade.append(num_contracts)
        
        # Update portfolio value
        if trade[8] == 'win':
            trade_profit = (num_contracts * profit_per_contract) - 1
            current_capital += trade_profit
        else:
            trade_loss = (num_contracts * risk_per_contract) + 1
            current_capital -= trade_loss
            
        portfolio_values.append((trade_date, current_capital))
    
    return {
        'final_capital': current_capital,
        'total_return_pct': ((current_capital - initial_capital) / initial_capital) * 100,
        'portfolio_values': portfolio_values,
        'contracts_history': contracts_per_trade,
        'avg_contracts': sum(contracts_per_trade) / len(contracts_per_trade) if contracts_per_trade else 0,
        'max_contracts': max(contracts_per_trade) if contracts_per_trade else 0,
        'min_contracts': min(contracts_per_trade) if contracts_per_trade else 0
    }


def calculate_statistics(trades, initial_capital=5000):
    """
    Calculate comprehensive trading statistics from trade data.
    """
    # Basic counts
    total_trades = len(trades)
    wins = sum(1 for trade in trades if trade[8] == 'win')
    losses = total_trades - wins
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

    # Financial calculations
    total_profit = wins * 50  # $50 profit for each winning trade
    total_loss = losses * 450  # $450 loss for each losing trade
    total_commission = total_trades * 1  # $1 commission per trade
    gross_profit = total_profit - total_loss - total_commission
    tax = max(0, gross_profit * 0.10)  # 10% tax on positive profits only
    net_profit = gross_profit - tax

    # Initialize tracking variables
    current_streak = 0
    max_win_streak = 0
    max_loss_streak = 0
    streaks = []
    consecutive_losses = 0
    max_consecutive_losses = 0
    
    # Time-based analysis
    monthly_trade_counts = defaultdict(int)
    monthly_win_rates = defaultdict(lambda: {'wins': 0, 'total': 0})
    yearly_trade_counts = defaultdict(int)
    yearly_win_rates = defaultdict(lambda: {'wins': 0, 'total': 0})
    yearly_profits = defaultdict(float)
    yearly_returns = defaultdict(float)
    weekday_distribution = defaultdict(int)
    win_trade_durations = []
    loss_trade_durations = []
    
    # Profitability tracking
    running_profit = 0
    max_running_profit = 0
    max_drawdown = 0
    current_drawdown = 0
    monthly_returns = defaultdict(float)
    profit_factor_monthly = defaultdict(lambda: {'profit': 0, 'loss': 0})

    # Calculate portfolio metrics
    portfolio_metrics = calculate_portfolio_metrics(trades, initial_capital)

    for trade in trades:
        # Date handling
        trade_date = datetime.strptime(trade[4], '%Y-%m-%d')
        expiry_date = datetime.strptime(trade[5], '%Y-%m-%d')
        month = trade_date.strftime('%Y-%m')
        year = trade_date.strftime('%Y')
        weekday = trade_date.weekday()

        # Duration calculations
        trade_duration = (expiry_date - trade_date).days
        
        # Monthly and yearly statistics
        monthly_trade_counts[month] += 1
        monthly_win_rates[month]['total'] += 1
        yearly_trade_counts[year] += 1
        yearly_win_rates[year]['total'] += 1
        weekday_distribution[weekday] += 1

        # Streak and profit calculations
        if trade[8] == 'win':
            monthly_win_rates[month]['wins'] += 1
            yearly_win_rates[year]['wins'] += 1
            
            if current_streak > 0:
                current_streak += 1
            else:
                streaks.append(current_streak)
                current_streak = 1
                
            win_trade_durations.append(trade_duration)
            consecutive_losses = 0
            running_profit += 50 - 1  # Win minus commission
            profit_factor_monthly[month]['profit'] += 50
            yearly_returns[year] += 50 - 1
            yearly_profits[year] += 50
        else:
            if current_streak < 0:
                current_streak -= 1
            else:
                streaks.append(current_streak)
                current_streak = -1
                
            loss_trade_durations.append(trade_duration)
            consecutive_losses += 1
            running_profit -= 450 + 1  # Loss plus commission
            profit_factor_monthly[month]['loss'] += 450
            yearly_returns[year] -= 450 + 1
            yearly_profits[year] -= 450

        # Update maximum values
        max_win_streak = max(max_win_streak, current_streak)
        max_loss_streak = min(max_loss_streak, current_streak)
        max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)

        # Drawdown calculations
        if running_profit > max_running_profit:
            max_running_profit = running_profit
            current_drawdown = 0
        else:
            current_drawdown = max_running_profit - running_profit
            max_drawdown = max(max_drawdown, current_drawdown)

        # Monthly returns
        monthly_returns[month] -= 1  # Commission
        if trade[8] == 'win':
            monthly_returns[month] += 50
        else:
            monthly_returns[month] -= 450

    # Calculate streak averages
    streaks.append(current_streak)
    avg_win_streak = sum(streak for streak in streaks if streak > 0) / len([streak for streak in streaks if streak > 0]) if len([streak for streak in streaks if streak > 0]) > 0 else 0
    avg_loss_streak = sum(abs(streak) for streak in streaks if streak < 0) / len([streak for streak in streaks if streak < 0]) if len([streak for streak in streaks if streak < 0]) > 0 else 0

    # Calculate advanced metrics
    avg_monthly_trades = sum(monthly_trade_counts.values()) / len(monthly_trade_counts)
    monthly_win_rate_stats = {month: stats['wins'] / stats['total'] * 100 for month, stats in monthly_win_rates.items()}
    avg_win_duration = sum(win_trade_durations) / len(win_trade_durations) if win_trade_durations else 0
    avg_loss_duration = sum(loss_trade_durations) / len(loss_trade_durations) if loss_trade_durations else 0

    # Calculate yearly statistics
    yearly_win_rate_stats = {
        year: {
            'win_rate': (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0,
            'trades': stats['total'],
            'wins': stats['wins'],
            'losses': stats['total'] - stats['wins'],
            'net_return': yearly_returns[year],
            'avg_return_per_trade': yearly_returns[year] / stats['total'] if stats['total'] > 0 else 0
        }
        for year, stats in yearly_win_rates.items()
    }

    # Calculate profit factors
    total_profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
    monthly_profit_factors = {
        month: pnl['profit'] / pnl['loss'] if pnl['loss'] != 0 else float('inf')
        for month, pnl in profit_factor_monthly.items()
    }

    # Apply monthly tax
    for month in monthly_returns:
        if monthly_returns[month] > 0:
            monthly_returns[month] *= 0.9  # 10% tax on profitable months

    # Calculate Sharpe Ratio (assuming risk-free rate of 2% annually)
    monthly_returns_series = pd.Series(monthly_returns)
    monthly_return_mean = monthly_returns_series.mean()
    monthly_return_std = monthly_returns_series.std()
    annual_sharpe = (monthly_return_mean * 12 - 0.02) / (monthly_return_std * np.sqrt(12)) if monthly_return_std != 0 else 0

    # Handle edge case where there's only one month of trades
    try:
        trade_freq_stdev = statistics.stdev(list(monthly_trade_counts.values()))
    except statistics.StatisticsError:
        trade_freq_stdev = 0

    stats_dict = {
        # Basic statistics
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,

        # Financial results
        'gross_profit': gross_profit,
        'total_commission': total_commission,
        'tax_paid': tax,
        'net_profit': net_profit,
        'profit_per_trade': net_profit / total_trades if total_trades > 0 else 0,
        'profit_factor': total_profit_factor,
        'monthly_profit_factors': monthly_profit_factors,

        # Streak analysis
        'max_win_streak': max_win_streak,
        'max_loss_streak': abs(max_loss_streak),
        'avg_win_streak': avg_win_streak,
        'avg_loss_streak': avg_loss_streak,
        'max_consecutive_losses': max_consecutive_losses,

        # Time-based metrics
        'avg_monthly_trades': avg_monthly_trades,
        'monthly_win_rates': monthly_win_rate_stats,
        'weekday_distribution': dict(weekday_distribution),
        'max_drawdown': max_drawdown,
        'monthly_returns': monthly_returns,

        # Yearly metrics
        'yearly_stats': yearly_win_rate_stats,
        'yearly_trade_counts': dict(yearly_trade_counts),
        'yearly_profits': dict(yearly_profits),

        # Duration metrics
        'avg_win_duration': avg_win_duration,
        'avg_loss_duration': avg_loss_duration,

        # Risk metrics
        'risk_reward_ratio': 450/50,  # Maximum loss / Average win
        'sharpe_ratio': annual_sharpe,

        # Consistency metrics
        'monthly_trade_counts': dict(monthly_trade_counts),
        'trade_frequency_stdev': trade_freq_stdev,
        
        # Portfolio metrics
        'initial_capital': initial_capital,
        'final_capital': portfolio_metrics['final_capital'],
        'total_return_pct': portfolio_metrics['total_return_pct'],
        'portfolio_values': portfolio_metrics['portfolio_values'],
        'avg_contracts': portfolio_metrics['avg_contracts'],
        'max_contracts': portfolio_metrics['max_contracts'],
        'min_contracts': portfolio_metrics['min_contracts']
    }

    return stats_dict


def print_statistics(stats):
    print("\n=== Trading Statistics ===")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Wins: {stats['wins']}")
    print(f"Losses: {stats['losses']}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    
    print(f"\n=== Portfolio Performance ===")
    print(f"Initial Capital: ${stats['initial_capital']:,.2f}")
    print(f"Final Capital: ${stats['final_capital']:,.2f}")
    print(f"Total Return: {stats['total_return_pct']:,.2f}%")
    print(f"Average Contracts: {stats['avg_contracts']:.1f}")
    print(f"Maximum Contracts: {stats['max_contracts']}")
    print(f"Minimum Contracts: {stats['min_contracts']}")
    
    print(f"\n=== Financial Results ===")
    print(f"Gross Profit: ${stats['gross_profit']:,.2f}")
    print(f"Total Commissions: ${stats['total_commission']:,.2f}")
    print(f"Tax Paid: ${stats['tax_paid']:,.2f}")
    print(f"Net Profit: ${stats['net_profit']:,.2f}")
    print(f"Average Profit per Trade: ${stats['profit_per_trade']:.2f}")
    print(f"Maximum Drawdown: ${stats['max_drawdown']:,.2f}")
    
    print(f"\n=== Streak Analysis ===")
    print(f"Max Win Streak: {stats['max_win_streak']}")
    print(f"Max Loss Streak: {stats['max_loss_streak']}")
    print(f"Average Win Streak: {stats['avg_win_streak']:.2f}")
    print(f"Average Loss Streak: {stats['avg_loss_streak']:.2f}")
    print(f"Maximum Consecutive Losses: {stats['max_consecutive_losses']}")
    
    print("\n=== Yearly Performance ===")
    for year, year_stats in sorted(stats['yearly_stats'].items()):
        print(f"\nYear {year}:")
        print(f"  Trades: {year_stats['trades']} " 
              f"(Wins: {year_stats['wins']}, Losses: {year_stats['losses']})")
        print(f"  Win Rate: {year_stats['win_rate']:.2f}%")
        print(f"  Net Return: ${year_stats['net_return']:,.2f}")
        print(f"  Average Return per Trade: ${year_stats['avg_return_per_trade']:.2f}")
    
    print("\n=== Monthly Analysis ===")
    print(f"Average Monthly Trades: {stats['avg_monthly_trades']:.2f}")
    print("\nWin Rate by Month:")
    for month, rate in sorted(stats['monthly_win_rates'].items()):
        print(f"{month}: {rate:.1f}%")
    
    print("\nMonthly Profit Factors:")
    for month, factor in sorted(stats['monthly_profit_factors'].items()):
        if factor != float('inf'):
            print(f"{month}: {factor:.2f}")
        else:
            print(f"{month}: ∞")
    
    print("\n=== Risk Metrics ===")
    print(f"Risk-Reward Ratio: 1:{stats['risk_reward_ratio']:.2f}")
    print(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
    
    print("\n=== Trade Duration Analysis ===")
    print(f"Average Winning Trade Duration: {stats['avg_win_duration']:.1f} days")
    print(f"Average Losing Trade Duration: {stats['avg_loss_duration']:.1f} days")
    
    print("\n=== Trading Pattern Analysis ===")
    print("Trade Distribution by Weekday:")
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for day_num, count in sorted(stats['weekday_distribution'].items()):
        percentage = (count / stats['total_trades']) * 100
        print(f"{days[day_num]}: {count} trades ({percentage:.1f}%)")
    
    print(f"\nTrade Frequency Consistency:")
    print(f"Monthly Trade Count Std Dev: {stats['trade_frequency_stdev']:.2f}")
    
    # Year-over-Year Analysis
    years = sorted(stats['yearly_stats'].keys())
    if len(years) > 1:
        print("\n=== Year-over-Year Changes ===")
        for i in range(1, len(years)):
            current_year = years[i]
            prev_year = years[i-1]
            win_rate_change = stats['yearly_stats'][current_year]['win_rate'] - \
                            stats['yearly_stats'][prev_year]['win_rate']
            trade_count_change = stats['yearly_stats'][current_year]['trades'] - \
                               stats['yearly_stats'][prev_year]['trades']
            return_change = stats['yearly_stats'][current_year]['net_return'] - \
                          stats['yearly_stats'][prev_year]['net_return']
            
            print(f"\n{prev_year} → {current_year}:")
            print(f"  Win Rate Change: {win_rate_change:+.2f}%")
            print(f"  Trade Volume Change: {trade_count_change:+d} trades")
            print(f"  Net Return Change: ${return_change:+,.2f}")
    
    # Best/Worst Performance
    if years:
        print("\n=== Performance Extremes ===")
        best_year = max(years, key=lambda y: stats['yearly_stats'][y]['net_return'])
        worst_year = min(years, key=lambda y: stats['yearly_stats'][y]['net_return'])
        
        print(f"Best Year: {best_year}")
        print(f"  Net Return: ${stats['yearly_stats'][best_year]['net_return']:,.2f}")
        print(f"  Win Rate: {stats['yearly_stats'][best_year]['win_rate']:.2f}%")
        print(f"  Total Trades: {stats['yearly_stats'][best_year]['trades']}")
        
        print(f"\nWorst Year: {worst_year}")
        print(f"  Net Return: ${stats['yearly_stats'][worst_year]['net_return']:,.2f}")
        print(f"  Win Rate: {stats['yearly_stats'][worst_year]['win_rate']:.2f}%")
        print(f"  Total Trades: {stats['yearly_stats'][worst_year]['trades']}")

    # Portfolio Growth Analysis
    print("\n=== Portfolio Growth Analysis ===")
    portfolio_values = stats['portfolio_values']
    if portfolio_values:
        first_date = portfolio_values[0][0]
        last_date = portfolio_values[-1][0]
        days = (last_date - first_date).days
        years = days / 365.25
        cagr = (((stats['final_capital'] / stats['initial_capital']) ** (1/years)) - 1) * 100 if years > 0 else 0
        
        print(f"Trading Period: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
        print(f"Days Traded: {days}")
        print(f"CAGR: {cagr:.2f}%")
        
        # Calculate monthly returns
        monthly_returns = defaultdict(float)
        prev_month = None
        prev_value = stats['initial_capital']
        
        for date, value in portfolio_values:
            month = date.strftime('%Y-%m')
            if month != prev_month:
                if prev_month:
                    monthly_returns[prev_month] = ((value - prev_value) / prev_value) * 100
                prev_month = month
                prev_value = value
        
        print("\nMonthly Returns:")
        for month, ret in sorted(monthly_returns.items()):
            print(f"{month}: {ret:+.2f}%")


def main():
    trades = get_all_trades()
    stats = calculate_statistics(trades)
    print_statistics(stats)


if __name__ == "__main__":
    main()
