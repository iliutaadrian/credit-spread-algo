from itertools import product
import numpy as np
from db import get_all_trades
from collections import defaultdict

def calculate_optimal_position_test(bankroll, win_rate, credit, kelly_fraction):
    """Modified position sizing calculator for testing different parameters"""
    p = win_rate / 100
    q = 1 - p
    
    win_amount = credit * 100 
    loss_amount = (5 - credit) * 100
    
    b = win_amount / loss_amount
    kelly = p - (q / b)
    kelly = max(0, kelly) * kelly_fraction
    
    optimal_risk = bankroll * kelly
    num_spreads = int(optimal_risk / loss_amount)
    num_spreads = max(1, min(num_spreads, 1000))
    
    return {
        'credit': credit,
        'num_spreads': num_spreads,
        'potential_profit': num_spreads * (credit * 100 - 1),
        'max_loss': num_spreads * (loss_amount + 1),
        'risk_amount': optimal_risk,
        'risk_percentage': kelly * 100
    }

def backtest_parameters(initial_capital=20000):
    """Run backtest with different parameter combinations"""
    # Define parameter ranges
    win_rates = np.arange(90, 92, 0.5)
    credits = np.arange(0.30, 0.55, 0.05)
    kelly_fractions = np.arange(0.3, 0.85, 0.05)
    
    # Get historical trades
    trades = get_all_trades(["QQQ"])

    results = []
    
    # Test all combinations
    for win_rate, credit, kelly_fraction in product(win_rates, credits, kelly_fractions):
        running_capital = initial_capital
        peak_capital = initial_capital
        trades_taken = 0
        
        waiting_for_win = False
        
        for trade in trades:
            if waiting_for_win:
                if trade[8] == 'win':
                    waiting_for_win = False
                else:
                    continue
            
            position = calculate_optimal_position_test(
                running_capital, 
                win_rate,
                credit,
                kelly_fraction
            )
            
            trades_taken += 1
            
            if trade[8] == 'win':
                running_capital += position['potential_profit']
            else:
                running_capital -= position['max_loss']
                waiting_for_win = True
        
        # Calculate metrics
        total_return = ((running_capital - initial_capital) / initial_capital) * 100
        
        results.append({
            'win_rate': win_rate,
            'credit': credit,
            'kelly_fraction': kelly_fraction,
            'final_capital': running_capital,
            'total_return_pct': total_return,
            'trades_taken': trades_taken
        })
    
    # Sort results by final capital
    results.sort(key=lambda x: x['final_capital'], reverse=True)
    
    return results

def print_top_results(results, top_n=20):
    """Print top N results with formatting"""
    print("\n=== Top Position Sizing Strategies ===")
    print(f"{'Rank':4} {'Win Rate':8} {'Credit':8} {'Kelly %':8} {'Final $':12} {'Return %':9} {'Trades':6}")
    print("-" * 70)
    
    for i, result in enumerate(results[:top_n], 1):
        print(f"{i:4d} {result['win_rate']:8.1f} {result['credit']:8.2f} "
              f"{result['kelly_fraction']:8.1f} {result['final_capital']:12,.0f} "
              f"{result['total_return_pct']:9.1f}"
              f"{result['trades_taken']:6d}")

def main():
    print("Starting backtest of position sizing parameters...")
    results = backtest_parameters()
    print_top_results(results)

if __name__ == "__main__":
    main()
