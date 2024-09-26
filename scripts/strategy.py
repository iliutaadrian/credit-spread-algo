import math
import os
from datetime import datetime, timedelta

import telebot
import yfinance as yf
from dotenv import load_dotenv
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
environment = os.environ.get("ENV")
Base = declarative_base()


def get_db_url():
    return f"postgresql://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}/{os.environ.get('POSTGRES_DATABASE')}"


def get_database_session():
    engine = create_engine(get_db_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


class Strategy:
    def __init__(
        self,
        name,
        option_type,
        deviation,
        price_multiplier,
        win_rate,
        expiration_date_round,
    ):
        self.name = name
        self.option_type = option_type
        self.deviation = deviation
        self.price_multiplier = price_multiplier
        self.win_rate = win_rate
        self.expiration_date_round = expiration_date_round

    def print_strategy(self):
        output = (
            f"{self.name}\n"
            f"Option Type: {self.option_type}\n"
            f"Deviation: {self.deviation}\n"
            f"Price Multiplier: {self.price_multiplier}\n"
            f"Win Rate: {self.win_rate}\n"
            f"Expiration Date Round: {self.expiration_date_round}\n"
        )
        return output


strategies = [
    Strategy(
        "Trend Up",
        "put",
        {"up": 3.5, "down": -5},
        0.98,
        {"SPY": 83, "VTI": 86},
        8,
    ),
    Strategy(
        "LUX Trend Up",
        "put",
        {"up": 3.5, "down": 2},
        0.98,
        {"SPY": 82, "QQQ": 71, "VTI": 91},
        10,
    ),
]


class TickerData:
    def __init__(self, ticker):
        self.ticker = ticker
        self.ticker_data = yf.download(ticker)

    def get_last_price(self):
        return self.ticker_data["Close"][-1]

    def get_date_price(self, date):
        try:
            return self.ticker_data.loc[date.strftime("%Y-%m-%d")]["Close"]
        except KeyError:
            return None

    def calculate_ma_std(self, date):
        try:
            rolling_data = self.ticker_data["Close"].loc[:date].rolling(window=200)
            ma = rolling_data.mean().iloc[-1]
            std = rolling_data.std().iloc[-1]
            return ma, std
        except (KeyError, IndexError):
            return None, None


class Trade():
    id = Column(Integer, primary_key=True)
    ticker = Column(String(255), nullable=False)
    strategy_name = Column(String(255), nullable=False)
    current_price = Column(Float, nullable=False)
    ma_std = Column(String(255), nullable=False)
    date_alerted = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    option_type = Column(String(255), nullable=False)
    strike_prices = Column(Float, nullable=False)
    min_credit = Column(Float, nullable=False)
    status = Column(String(255))

    def __init__(
        self,
        ticker,
        strategy_name,
        current_price,
        ma_std,
        date_alerted,
        expiration_date,
        option_type,
        strike_prices,
        min_credit,
        win_rate,
        status=None,
    ):
        self.ticker = ticker
        self.strategy_name = strategy_name
        self.current_price = current_price
        self.ma_std = ma_std
        self.date_alerted = date_alerted
        self.expiration_date = expiration_date
        self.option_type = option_type
        self.strike_prices = strike_prices
        self.min_credit = min_credit
        self.win_rate = win_rate
        self.status = status

    def print_and_generate_output(self):
        output = (
            f"Date Alerted: {self.date_alerted.strftime('%d %B %Y')}\n"
            f"{self.ticker} - {self.strategy_name} {self.win_rate}%\n"
            f"Trade: {self.option_type} {self.strike_prices}\n"
            f"Expiration: {self.expiration_date.strftime('%d %B %Y')}\n"
            f"Minimum credit: ${self.min_credit}\n"
        )
        return output

    def save_to_database(self):
        return self.print_and_generate_output()


def check_strategy(ticker, specific_date, strategy):
    trades = []
    for i in range(5):
        date_alerted = specific_date - timedelta(days=i)
        if date_alerted.weekday() >= 5:
            continue

        current_price = ticker.get_date_price(date_alerted)
        if current_price is None:
            continue

        ma, std = ticker.calculate_ma_std(date_alerted)

        upper_boundary = ma + strategy.deviation["up"] * std
        lower_boundary = ma + strategy.deviation["down"] * std

        if lower_boundary <= current_price <= upper_boundary:
            strike_price = current_price * strategy.price_multiplier
            expiration_date = date_alerted + timedelta(
                days=strategy.expiration_date_round
            )
            while expiration_date.weekday() != 4:  # 4 represents Friday
                expiration_date += timedelta(days=1)

            trade = Trade(
                ticker=ticker.ticker,
                strategy_name=f"{strategy.name}",
                win_rate=strategy.win_rate[ticker.ticker],
                current_price=int(current_price),
                ma_std=f"{ma}/{std}",
                date_alerted=date_alerted,
                expiration_date=expiration_date,
                option_type=strategy.option_type,
                strike_prices=int(strike_price),
                min_credit=calculate_credit(strategy.win_rate[ticker.ticker]),
            )
            trades.append(trade)

    return trades


# calculate based on Long Term Expectancy
def calculate_credit(win_rate):
    return math.ceil(55 - 0.5 * win_rate + 1)


def remove_duplicates(trades, date_limit):
    oldest_trade = None
    for trade in trades:
        if not oldest_trade:
            oldest_trade = trade
        elif (
            trade.expiration_date == oldest_trade.expiration_date
            and trade.option_type == oldest_trade.option_type
        ):
            initial_price = int(oldest_trade.strike_prices)
            aux_price = int(trade.strike_prices)

            if abs(initial_price - aux_price) > 20:
                break

            if trade.date_alerted < oldest_trade.date_alerted:
                oldest_trade = trade

    if oldest_trade and oldest_trade.date_alerted != date_limit:
        oldest_trade = None

    return oldest_trade


def run_all_strategies(ticker_data, specific_date, duplicate_filter=True):
    global environment
    all_trades = []
    filtered_trades = []

    for strategy in strategies:
        trade_ideas = check_strategy(ticker_data, specific_date, strategy)

        if duplicate_filter:
            filtered_trades = remove_duplicates(trade_ideas, specific_date)
            if filtered_trades:
                all_trades.append(filtered_trades)
        else:
            for trade_idea in trade_ideas:
                if trade_idea.date_alerted == specific_date:
                    all_trades.append(trade_idea)

    all_trades = sorted(all_trades, key=lambda x: x.win_rate, reverse=True)
    return all_trades


def run_each_strategy(ticker_data, specific_date, strategy):
    global environment
    all_trades = []

    trade_ideas = check_strategy(ticker_data, specific_date, strategy)

    filtered_trades = remove_duplicates(trade_ideas, specific_date)
    if filtered_trades:
        all_trades.append(filtered_trades)

    return all_trades


def generate_notifications(trades):
    output = ""
    for trade in trades:
        output += trade.save_to_database()
    print(output)

    if output and environment == "PROD":
        bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
        bot.send_message(os.environ.get("TELEGRAM_CHAT_ID"), output)


def main():
    tickers = [
        "VTI",
        # "SPY",
        # "QQQ",
    ]
    specific_date = datetime.now().date()
    # specific_date = datetime(2002, 5, 5)

    print("--------------------")
    print(specific_date.strftime("%d %B %Y"))

    for ticker_name in tickers:
        ticker = TickerData(ticker_name)
        trades = run_all_strategies(ticker, specific_date, duplicate_filter=False)
        generate_notifications(trades)


if __name__ == "__main__":
    main()
