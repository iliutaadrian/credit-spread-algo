import os
import sqlite3
from datetime import datetime, timedelta
import telebot
import yfinance as yf
from dotenv import load_dotenv
import math
import pandas as pd

load_dotenv()
environment = os.environ.get("ENV")
from db import save_trade_to_db, create_table 


class Strategy:
    def __init__(
        self,
        name,
        option_type,
        deviation,
        price_multiplier,
        expiration_date_round,
    ):
        self.name = name
        self.option_type = option_type
        self.deviation = deviation
        self.price_multiplier = price_multiplier
        self.expiration_date_round = expiration_date_round

strategies = [
    Strategy(
        "Trend Up",
        "put",
        {"up": 3.5, "down": -5},
        0.98,
        8,
    ),
    # Strategy(
    #     "LUX Trend Up",
    #     "put",
    #     {"up": 3.5, "down": 2},
    #     0.98,
    #     10,
    # ),
]

class TickerData:
    def __init__(self, ticker):
        self.ticker = ticker
        # Download data and localize it to remove timezone information
        self.ticker_data = yf.download(ticker)
        self.ticker_data.index = self.ticker_data.index.tz_localize(None)

    def get_last_price(self):
        return self.ticker_data["Close"][-1]

    def get_date_price(self, date):
        try:
            # Convert date to string format for lookup
            date_str = date.strftime("%Y-%m-%d")
            return self.ticker_data.loc[date_str]["Close"]
        except KeyError:
            return None

    def calculate_ma_std(self, date):
        try:
            # Convert date to string format for slicing
            date_str = date.strftime("%Y-%m-%d")
            rolling_data = self.ticker_data["Close"].loc[:date_str].rolling(window=200)
            ma = rolling_data.mean().iloc[-1]
            std = rolling_data.std().iloc[-1]
            return ma, std
        except (KeyError, IndexError):
            return None, None

class Trade:
    def __init__(
        self,
        ticker,
        strategy_name,
        current_price,
        date_alerted,
        expiration_date,
        option_type,
        strike_price,
        status=None,
    ):
        self.ticker = ticker
        self.strategy_name = strategy_name
        self.current_price = current_price
        self.date_alerted = date_alerted
        self.expiration_date = expiration_date
        self.option_type = option_type
        self.strike_price = strike_price
        self.status = status


def check_strategy(ticker, specific_date, strategy):
    trades = []
    for i in range(5):
        date_alerted = specific_date - timedelta(days=i)
        if date_alerted.weekday() >= 5:
            continue

        current_price = ticker.get_date_price(date_alerted)
        if current_price is None:
            continue

        # Extract scalar values for comparison
        if isinstance(current_price, (pd.Series, pd.DataFrame)):
            current_price = float(current_price)

        ma, std = ticker.calculate_ma_std(date_alerted)
        if ma is None or std is None:
            continue

        # Calculate boundaries using scalar values
        upper_boundary = float(ma + strategy.deviation["up"] * std)
        lower_boundary = float(ma + strategy.deviation["down"] * std)

        # Compare scalar values
        if lower_boundary <= current_price <= upper_boundary:
            strike_price = current_price * strategy.price_multiplier
            sell_strike = math.floor(strike_price/5)*5 

            expiration_date = date_alerted + timedelta(
                days=strategy.expiration_date_round
            )
            while expiration_date.weekday() != 4:  # 4 represents Friday
                expiration_date += timedelta(days=1)

            trade = Trade(
                ticker=ticker.ticker,
                strategy_name=strategy.name,
                current_price=current_price,
                date_alerted=date_alerted,
                expiration_date=expiration_date,
                option_type=strategy.option_type,
                strike_price=sell_strike,
            )
            trades.append(trade)

    return trades

def run_all_strategies(ticker_data, specific_date, duplicate_filter=True):
    all_trades = []

    for strategy in strategies:
        trade_ideas = check_strategy(ticker_data, specific_date, strategy)

        if duplicate_filter:
            filtered_trade = remove_duplicates(trade_ideas, specific_date)
            if filtered_trade:
                all_trades.append(filtered_trade)
        else:
            for trade_idea in trade_ideas:
                if trade_idea.date_alerted == specific_date:
                    all_trades.append(trade_idea)

    return all_trades


def remove_duplicates(trades, date_limit):
    oldest_trade = None
    for trade in trades:
        if not oldest_trade:
            oldest_trade = trade
        elif (
            trade.expiration_date == oldest_trade.expiration_date
            and trade.option_type == oldest_trade.option_type
        ):
            initial_price = int(oldest_trade.strike_price)
            aux_price = int(trade.strike_price)

            if abs(initial_price - aux_price) > 10:
                break

            if trade.date_alerted < oldest_trade.date_alerted:
                oldest_trade = trade

    if oldest_trade and oldest_trade.date_alerted != date_limit:
        oldest_trade = None

    return oldest_trade


def calculate_optimal_position(bankroll, win_rate=92.0):
    """
    Calculate optimal position size and credit using Kelly Criterion
    
    Args:
        bankroll (float): Current portfolio value
        win_rate (float): Strategy win rate percentage (default 92%)
    
    Returns:
        dict: Position details including spreads and credit amount
    """
    # Convert win rate to probability
    p = win_rate / 100
    q = 1 - p
    
    credit = 0.50
    win_amount = 50
    loss_amount = 450
    
    # Calculate Kelly percentage
    b = win_amount / loss_amount  # Odds ratio
    kelly = p - (q / b)
    
    # Use half-Kelly for safety
    kelly = max(0, kelly) * 1
    
    # Calculate optimal risk amount
    optimal_risk = bankroll * kelly
    
    # Calculate number of spreads (rounded down)
    num_spreads = int(optimal_risk / loss_amount)
    num_spreads = max(1, min(num_spreads, 20))  # Cap between 1 and 20 spreads
    
    return {
        'credit': credit,
        'num_spreads': num_spreads,
        'potential_profit': num_spreads * (credit * 100 - 1),  # Subtract commission
        'max_loss': num_spreads * (loss_amount + 1),  # Add commission
        'risk_amount': optimal_risk,
        'risk_percentage': kelly * 100
    }

def generate_alert(trades, bankroll=5000):
    """
    Generate trade alert with position sizing recommendations
    
    Args:
        trades (list): List of trade opportunities
        bankroll (float): Current portfolio value
    """
    if not trades:
        return
        
    # Get position sizing for the strategy
    position = calculate_optimal_position(bankroll)
    
    output = ""
    for trade in trades:
        output += (
            f"{trade.ticker} - {trade.strategy_name}\n"
            f"Trade: {trade.option_type} {trade.strike_price}\n"
            f"Expiration: {trade.expiration_date.strftime('%d %B %Y')}\n"
            f"Position: {position['num_spreads']} * $5 spread \n"
            f"Credit: ${position['credit']:.2f} \n"
            f"P/L: ${position['potential_profit']:.2f}/${position['max_loss']:.2f} \n"
        )
        output += "\n" if len(trades) - 1 > 2 else ""
    
    print(output)
    
    if environment == "PROD":
        bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
        bot.send_message(os.environ.get("TELEGRAM_CHAT_ID"), output)

def main():
    tickers = [
        "VTI",
        # "SPY",
        # "QQQ",
    ]
    bankroll = 10000

    specific_date = datetime.now().date()
    # specific_date = datetime(2024, 10, 23)

    for ticker_name in tickers:
        ticker = TickerData(ticker_name)
        trades = run_all_strategies(ticker, specific_date, duplicate_filter=False)
        generate_alert(trades, bankroll)

if __name__ == "__main__":
    main()
