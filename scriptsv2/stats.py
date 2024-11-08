import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np
from db import get_all_trades
from strategy import calculate_optimal_position

def calculate_yearly_stats(trades, initial_capital=5000):
    """Calculate yearly statistics with Kelly position sizing and skip-after-loss logic"""
    yearly_stats = defaultdict(lambda: {
        'trades': 0, 'wins': 0, 'losses': 0, 
        'net_return': 0, 'skipped_trades': 0
    })
    
    running_capital = initial_capital
    waiting_for_win = False  # Flag to track if we're waiting for a win
    
    for trade in trades:
        year = datetime.strptime(trade[4], '%Y-%m-%d').strftime('%Y')
        
        if waiting_for_win:
            if trade[8] == 'win':
                waiting_for_win = False  # Reset the flag on a win
            else:
                yearly_stats[year]['skipped_trades'] += 1
                continue  # Skip this trade
                
        # Calculate position size based on current capital
        position = calculate_optimal_position(running_capital)
        yearly_stats[year]['trades'] += 1
        
        if trade[8] == 'win':
            yearly_stats[year]['wins'] += 1
            profit = position['potential_profit']
            yearly_stats[year]['net_return'] += profit
            running_capital += profit
        else:
            yearly_stats[year]['losses'] += 1
            loss = position['max_loss']
            yearly_stats[year]['net_return'] -= loss
            running_capital -= loss
            waiting_for_win = True  # Set the flag after a loss
        
        # Store end-of-year capital
        yearly_stats[year]['year_end_capital'] = running_capital
    
    # Calculate win rates and other metrics
    for year_stats in yearly_stats.values():
        total_actual_trades = year_stats['wins'] + year_stats['losses']
        year_stats['win_rate'] = (year_stats['wins'] / total_actual_trades * 100) \
            if total_actual_trades > 0 else 0
        year_stats['total_trades_available'] = total_actual_trades + year_stats['skipped_trades']
    
    return yearly_stats, running_capital

def calculate_statistics(trades, initial_capital=5000):
    """Calculate statistics with Kelly position sizing and skip-after-loss logic"""
    # Calculate yearly stats and final capital
    yearly_stats, final_capital = calculate_yearly_stats(trades, initial_capital)
    
    # Calculate overall statistics
    total_trades = sum(year['trades'] for year in yearly_stats.values())
    total_wins = sum(year['wins'] for year in yearly_stats.values())
    total_skipped = sum(year['skipped_trades'] for year in yearly_stats.values())
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    # Calculate max drawdown with skip-after-loss logic
    peak_capital = initial_capital
    max_drawdown = 0
    running_capital = initial_capital
    waiting_for_win = False
    
    for trade in trades:
        if waiting_for_win:
            if trade[8] == 'win':
                waiting_for_win = False
            else:
                continue
                
        position = calculate_optimal_position(running_capital)
        
        if trade[8] == 'win':
            running_capital += position['potential_profit']
        else:
            running_capital -= position['max_loss']
            waiting_for_win = True
            
        peak_capital = max(peak_capital, running_capital)
        drawdown = peak_capital - running_capital
        max_drawdown = max(max_drawdown, drawdown)
    
    return {
        'total_trades': total_trades,
        'total_trades_available': total_trades + total_skipped,
        'total_skipped': total_skipped,
        'win_rate': win_rate,
        'yearly_stats': yearly_stats,
        'initial_capital': initial_capital,
        'final_capital': final_capital,
        'total_return_pct': ((final_capital - initial_capital) / initial_capital) * 100,
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': (max_drawdown / peak_capital) * 100 if peak_capital > 0 else 0,
        'current_optimal_position': calculate_optimal_position(final_capital)
    }

def print_statistics(stats):
    """Print statistics with skip-after-loss details"""
    print("\n=== Trading Performance Summary ===")
    print(f"Total Trades Taken: {stats['total_trades']}")
    print(f"Total Trades Skipped: {stats['total_skipped']}")
    print(f"Total Available Trades: {stats['total_trades_available']}")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    
    print(f"\nPortfolio Growth Summary")
    print(f"Initial Capital: ${stats['initial_capital']:,.2f}")
    print(f"Final Capital: ${stats['final_capital']:,.2f}")
    print(f"Total Return: {stats['total_return_pct']:.1f}%")
    print(f"Maximum Drawdown: ${stats['max_drawdown']:,.2f} ({stats['max_drawdown_pct']:.1f}%)")
    
    print("\n=== Yearly Performance ===")
    print("Year\t\tTrades\tSkipped\tWin Rate\tCapital\t\tYearly Change")
    print("-" * 80)
    
    prev_capital = stats['initial_capital']
    
    for year in sorted(stats['yearly_stats'].keys()):
        year_stats = stats['yearly_stats'][year]
        yearly_change = year_stats['net_return']
        year_end_capital = year_stats['year_end_capital']
        
        print(f"{year}\t\t{year_stats['trades']}\t"
              f"{year_stats['skipped_trades']}\t"
              f"{year_stats['win_rate']:>6.1f}%\t"
              f"${year_end_capital:>11,.0f}\t"
              f"${yearly_change:>+11,.0f}")
        
        prev_capital = year_end_capital
    
    current_position = stats['current_optimal_position']
    print("\n=== Current Optimal Position ===")
    print(f"Recommended Spreads: {current_position['num_spreads']}")
    print(f"Credit: ${current_position['credit']:.2f}")
    print(f"Risk Percentage: {current_position['risk_percentage']:.1f}%")
    print(f"Risk Amount: ${current_position['risk_amount']:,.2f}")
    print(f"Maximum Loss: ${current_position['max_loss']:,.2f}")
    print(f"Potential Profit: ${current_position['potential_profit']:,.2f}")

def main():
    trades = get_all_trades()
    stats = calculate_statistics(trades)
    print_statistics(stats)

if __name__ == "__main__":
    main()