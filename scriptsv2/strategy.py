import os
from datetime import datetime, timedelta
import telebot
import yfinance as yf
from dotenv import load_dotenv
import math
import pandas as pd

load_dotenv()
environment = os.environ.get("ENV")
from db import save_trade_to_db, get_trades_for_streak

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
        self.ticker_data = yf.download(ticker)
        self.ticker_data.index = self.ticker_data.index.tz_localize(None)

    def get_date_price(self, date):
        try:
            date_str = date.strftime("%Y-%m-%d")
            return self.ticker_data.loc[date_str]["Close"]
        except KeyError:
            return None

    def calculate_ma_std(self, date):
        try:
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

        if isinstance(current_price, (pd.Series, pd.DataFrame)):
            current_price = float(current_price)

        ma, std = ticker.calculate_ma_std(date_alerted)
        if ma is None or std is None:
            continue

        upper_boundary = float(ma + strategy.deviation["up"] * std)
        lower_boundary = float(ma + strategy.deviation["down"] * std)

        if lower_boundary <= current_price <= upper_boundary:
            strike_price = current_price * strategy.price_multiplier
            sell_strike = math.floor(strike_price/5)*5 

            expiration_date = date_alerted + timedelta(days=strategy.expiration_date_round)
            while expiration_date.weekday() != 4:  # Find next Friday
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

def get_trading_status(date_str):
    print(date_str)
    trades = get_trades_for_streak(date_str)
    if not trades:
        return False, "Active", None
        
    win_streak_start = None
    for trade_date, status in trades:
        print(trade_date, status)
        if status is not None:
            if status == 'loss':
                return True, "Inactive", None
            elif win_streak_start is None:
                win_streak_start = trade_date
    
    return False, "Active", win_streak_start

def calculate_optimal_position(bankroll, win_rate=92.0):
    p = win_rate / 100
    q = 1 - p
    
    credit = 0.55
    win_amount = credit * 100 
    loss_amount = (5 - credit) * 100
    
    b = win_amount / loss_amount
    kelly = p - (q / b)
    kelly = max(0, kelly) * 0.5
    
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

def check_winning_streak(check_date_str):
    """
    Check if we should be trading based on streak status
    Returns:
    - (True, None) if we can trade (last trade was a win)
    - (False, last_win_date) if we shouldn't trade (in a losing streak)
    """
    trades = get_trades_for_streak(check_date_str)
    
    if not trades:
        return True, None  # No trades means we can trade
        
    # Get most recent trade status
    last_trade_status = trades[0][1]  # trades[0] is most recent since ordered DESC
    
    # If last trade was a win, we can trade
    if last_trade_status == 'win':
        return True, None
        
    # If last trade was a loss, we need to wait
    return False, trades[0][0]

def calculate_current_year_winrate(current_year=datetime.now().year):
    """Calculate win rate for current year"""
    year_start = f"{current_year}-01-01"
    trades = get_trades_for_streak(datetime.now().strftime('%Y-%m-%d'))
    
    if not trades:
        return None
        
    current_year_trades = [t for t in trades if t[0].startswith(str(current_year))]
    
    if not current_year_trades:
        return None
        
    wins = sum(1 for t in current_year_trades if t[1] == 'win')
    total = len(current_year_trades)
    
    return f"Year {current_year}: {(wins / total * 100):.2f}%: {wins}/{total}" if total > 0 else None

def generate_alert(trades, current_year, bankroll=5000, is_active=True):
    """
    Generate trade alert with position sizing recommendations and active status
    """
    if not trades:
        return
        
    position = calculate_optimal_position(bankroll)
    
    output = ""
    for trade in trades:
        status = "Active" if is_active else f"Inactive {trade.expiration_date.strftime('%d %B %Y')}"
        output += (
            f"{trade.ticker} | {trade.strategy_name} | {status}\n"
            f"{trade.option_type.upper()} {trade.strike_price} - {trade.expiration_date.strftime('%d %B %Y')}\n"
            f"P/L: +${position['potential_profit']:.2f}/-${position['max_loss']:.2f}\n"
            f"Risk: ${position['risk_amount']:.2f}/{bankroll} ({position['risk_percentage']:.2f}%)\n"
            f"Credit: ${position['credit']:.2f} × {position['num_spreads']} $5 spreads\n"
            f"{current_year}"
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
    bankroll = 20000

    specific_date = datetime.now().date()
    # specific_date = datetime(2022, 10, 7)

    # Get current year win rate
    current_year_winrate = calculate_current_year_winrate(specific_date.year)
    
    for ticker_name in tickers:
        ticker = TickerData(ticker_name)
        
        # Check if we can trade based on streak
        can_trade, last_trade_date = check_winning_streak(specific_date.strftime('%Y-%m-%d'))
        
        # First save filtered trades to DB
        filtered_trades = run_all_strategies(ticker, specific_date, duplicate_filter=True)
        if filtered_trades:
            for trade in filtered_trades:
                save_trade_to_db(trade, None)  # Save with null status for later update
        
        # Then generate alerts for all possible trades
        trades = run_all_strategies(ticker, specific_date, duplicate_filter=False)
        
        generate_alert(trades, current_year_winrate, bankroll, is_active=can_trade)

if __name__ == "__main__":
    main()
