import os
from datetime import datetime, timedelta
import yfinance as yf
import math
from strategy import (
    Strategy,
    TickerData,
    Trade,
    run_all_strategies,
    strategies,
)
from db import save_trade_to_db, create_table

def backtest_and_populate_db(ticker_data, trades):
    for trade in trades:
        date_alerted = trade.date_alerted
        expiration_date = trade.expiration_date
        sell_strike = math.floor(float(trade.strike_price))  # Round down to nearest integer
        trade.sell_strike = sell_strike
        option_type = trade.option_type

        if expiration_date > datetime.now().date() or expiration_date.weekday() >= 5 or date_alerted.weekday() >= 5:
            continue

        expiration_price = ticker_data.get_date_price(expiration_date)
        if expiration_price is None:
            continue  # Skip this trade if we can't find a valid expiration price

        if (option_type == "put" and sell_strike < expiration_price) or (
            option_type == "call" and sell_strike > float(expiration_price)
        ):
            status = "win"
        else:
            status = "loss"

        save_trade_to_db(trade, status)

def populate_historical_trades():
    tickers = ["IWM", "VTI", "QQQ", "SPY"]
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=9000)

    for ticker_symbol in tickers:
        print(f"Processing {ticker_symbol}...")
        ticker_data = TickerData(ticker_symbol)

        all_trades = []
        current_date = start_date
        while current_date <= end_date:
            trades = run_all_strategies(ticker_data, current_date, duplicate_filter=True)
            if trades:  # Only extend if there are trades
                all_trades.extend(trades)
            current_date += timedelta(days=1)


        if all_trades:  # Only process if we have trades
            print(f"Found {len(all_trades)} trades for {ticker_symbol}")
            backtest_and_populate_db(ticker_data, all_trades)
        else:
            print(f"No trades found for {ticker_symbol}")

        print(f"Finished processing {ticker_symbol}")

    print("Database population complete.")

if __name__ == "__main__":
    populate_historical_trades()
