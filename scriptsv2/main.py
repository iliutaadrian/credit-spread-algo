import argparse
from datetime import datetime
from populate_db import populate_historical_trades
from stats import main as run_statistics
from strategy import main as run_strategy 
from db import create_table

def parse_args():
    parser = argparse.ArgumentParser(description="Trading application command-line interface")
    parser.add_argument("action", choices=["backtest", "run", "stats"],
                        help="Action to perform: 'backtest' for historical data, 'run' for current day's strategy, 'stats' to view statistics")
    return parser.parse_args()

def backtest():
    print("Starting backtest process...")
    print("1. Creating database table if not exists...")
    create_table()
    print("2. Populating database with historical trades...")
    populate_historical_trades()
    print("3. Generating trading statistics...")
    run_statistics()
    print("Backtest process completed.")

def main():
    args = parse_args()
    
    if args.action == "backtest":
        backtest()
    elif args.action == "run":
        run_strategy()
        print("\n")
    elif args.action == "stats":
        run_statistics()

if __name__ == "__main__":
    main()
