import time
from datetime import datetime, timedelta

import numpy as np
import yfinance as yf
from strategy import (
    Strategy,
    TickerData,
    Trade,
    run_all_strategies,
    run_each_strategy,
    strategies,
)


def write_trades_to_file(daily_trades, output_file):
    trade_data_list = []
    with open(output_file, "w") as file:
        for daily_trade in daily_trades:
            for trade in daily_trade:
                trade_output = (
                    f"Ticker: {trade.ticker}\n"
                    f"Strategy Name: {trade.strategy_name}\n"
                    f"Current Price: {trade.current_price}\n"
                    f"MA/STD: {trade.ma_std}\n"
                    f"Date Alerted: {trade.date_alerted}\n"
                    f"Expiration Date: {trade.expiration_date}\n"
                    f"Option Type: {trade.option_type}\n"
                    f"Strike Prices: {trade.strike_prices}\n"
                    f"Min Credit: {trade.min_credit}\n"
                    f"Win Rate: {trade.win_rate}"
                )

                trade_data_list.append(trade_output)

        trade_data = "\n---\n".join(trade_data_list)
        file.write(trade_data)


def read_trades_from_file(file_name):
    trades = []

    with open(file_name, "r") as file:
        trade_data = file.read().split("---\n")

        for trade_entry in trade_data:
            trade_lines = trade_entry.strip().split("\n")

            # Create a dictionary to store trade fields
            trade_fields = {}

            for line in trade_lines:
                field_name, field_value = line.split(": ", 1)
                trade_fields[field_name] = field_value

            trade_instance = Trade(
                ticker=trade_fields.get("Ticker", ""),
                strategy_name=trade_fields.get("Strategy Name", ""),
                current_price=trade_fields.get("Current Price", ""),
                ma_std=trade_fields.get("MA/STD", ""),
                date_alerted=trade_fields.get("Date Alerted", ""),
                expiration_date=trade_fields.get("Expiration Date", ""),
                option_type=trade_fields.get("Option Type", ""),
                strike_prices=trade_fields.get("Strike Prices", ""),
                min_credit=trade_fields.get("Min Credit", ""),
                win_rate=trade_fields.get("Win Rate", ""),
            )

            trades.append(trade_instance)

    return trades


def process_trades(file_name):
    with open(file_name, "r") as file:
        lines = file.readlines()

    output = ""
    for line in lines:
        parts = line.strip().split("\t")
        expiration_info = parts[1].split(", ")
        expiration_date = f"{expiration_info[0].split(' : ')[1]} {expiration_info[1]}"
        expiration_date = datetime.strptime(expiration_date, "%b %d %Y")

        spread_info = expiration_info[2].split(": ")[1].split(" / ")

        output += f"Ticker: SPY\n"
        output += f"Strategy Name: Trend Up\n"
        output += f"Current Price: 0\n"
        output += f"MA/STD: 0\n"
        output += f"Date Alerted: {parts[0]}\n"
        output += f"Expiration Date: {expiration_date}\n"
        output += f"Option Type: put\n"
        output += f"Strike Prices: {spread_info[0].replace('$', '')}\n"
        output += "---\n"

    return output


def backtest_strategy(ticker_data, trades, verbose=False):
    money = 0
    win = 0
    total = 0
    price_multiplier = []

    if trades is None:
        return

    for trade in trades:
        expiration_date = datetime.strptime(trade.expiration_date, "%Y-%m-%d %H:%M:%S")
        date_alerted = datetime.strptime(trade.date_alerted, "%Y-%m-%d %H:%M:%S")
        sell_strike = int(trade.strike_prices)
        option_type = trade.option_type

        # expiration_date = trade.expiration_date
        # date_alerted = trade.date_alerted
        # sell_strike = int(trade.strike_prices)
        # option_type = trade.option_type

        if (
            expiration_date > datetime.now()
            or expiration_date.weekday() >= 5
            or date_alerted.weekday() >= 5
        ):
            continue
        else:
            alerted_price = ticker_data.get_date_price(date_alerted)
            if alerted_price is None:
                continue

            expiration_price = ticker_data.get_date_price(expiration_date)
            i = 0
            while expiration_price is None:
                expiration_price = ticker_data.get_date_price(
                    expiration_date - timedelta(days=i)
                )
                i += 1

            price_multiplier.append(sell_strike / alerted_price)
            total += 1
            if (option_type == "put" and sell_strike < expiration_price) or (
                option_type == "call" and sell_strike > int(expiration_price)
            ):
                money += int(trade.min_credit)
                win += 1
                # trade.save_to_database(status="WIN")
                if verbose:
                    print(
                        f"{alerted_price} - {option_type} {expiration_date.strftime('%d %B %Y')} {int(sell_strike)} - {int(expiration_price)} - {sell_strike / alerted_price} - Passed"
                    )
            else:
                money -= 100 - int(trade.min_credit)
                # trade.save_to_database(status="LOSE")
                if verbose:
                    print(
                        f"{alerted_price} - {option_type} {expiration_date.strftime('%d %B %Y')} {int(sell_strike)} - {int(expiration_price)} - {sell_strike / alerted_price} - Failed"
                    )

    if verbose:
        print(money)
        print(win)
        print(total)
        print(win / total * 100)
        if price_multiplier:
            print(sum(price_multiplier) / len(price_multiplier))

    if total == 0:
        return 0, 0, 0

    return win / total * 100, win, total


def backtrack_strategy():
    # Define ranges
    down_range = [0, 3]
    up_range = [3, 6]
    days_range = [7, 15]

    strategies_backtest = []

    # Iterate through all combinations of ranges
    for down in np.arange(down_range[0], down_range[1], 0.5):
        for up in np.arange(up_range[0], up_range[1], 0.5):
            for days in range(days_range[0], days_range[1] + 1):
                if down >= up:
                    continue
                # Create a new Strategy object for each combination
                strategy = Strategy(
                    "Trend Up",
                    "put",
                    {"up": up, "down": down},
                    0.98,
                    {"SPY": 92, "QQQ": 89},
                    days,
                )
                strategies_backtest.append(strategy)

    return strategies_backtest


def main_backtest(type):
    var = 0
    options = ["SPY", "QQQ"]

    file_name = f"{options[var]}.txt"
    specific_date = datetime(2024, 2, 8)

    ticker_symbol = options[var]
    ticker_data = TickerData(ticker_symbol)

    if type == "all_strategies":
        all_trades = []
        for i in range(0, 9000):
            all_trades.append(
                run_all_strategies(ticker_data, specific_date - timedelta(days=i))
            )
        all_trades = [item for item in all_trades if item != []]
        write_trades_to_file(all_trades, file_name)
        # elif type == "verify":
        trades = read_trades_from_file(file_name)
        backtest_strategy(ticker_data, trades, verbose=True)
    elif type == "each_strategy":
        strategy_results = []
        generated_strategies = backtrack_strategy()

        strategy_num = 0

        for strategy in generated_strategies:
            start_time = time.time()
            strategy_num += 1

            trades = []

            for i in range(0, 7000):
                trades.append(
                    run_each_strategy(
                        ticker_data, specific_date - timedelta(days=i), strategy
                    )
                )
            trades = [item for item in trades if item != []]

            if len(trades) == 0:
                strategy_results.append(
                    {"strategy": strategy, "win_rate": 0, "win": 0, "total": 0}
                )
                continue

            parsed_trades = []

            for daily_trade in trades:
                for trade in daily_trade:
                    parsed_trades.append(trade)

            # write_trades_to_file(trades, file_name)
            #
            # trades = read_trades_from_file(file_name)
            win_rate, win, total = backtest_strategy(ticker_data, parsed_trades)
            strategy_results.append(
                {"strategy": strategy, "win_rate": win_rate, "win": win, "total": total}
            )

            end_time = time.time()
            print(
                f"{options[var]} -- {strategy_num}/{len(generated_strategies)} -- {end_time - start_time}"
            )

            if strategy_num % 100 == 0:
                strategy_results = sorted(
                    strategy_results, key=lambda x: x["win"], reverse=True
                )
                for result in strategy_results[:1]:
                    print(f"{result['win']}/{result['total']}")
                    print(result["win_rate"])
                    print(result["strategy"].print_strategy())

        print("Top 3 Win:")
        strategy_results = sorted(
            strategy_results, key=lambda x: x["win"], reverse=True
        )
        for result in strategy_results[:10]:
            print(f"{result['win']}/{result['total']}")
            print(result["win_rate"])
            print(result["strategy"].print_strategy())

        print("Top 3 Win %:")
        strategy_results = sorted(
            strategy_results, key=lambda x: x["win_rate"], reverse=True
        )
        for result in strategy_results[:10]:
            print(f"{result['win']}/{result['total']}")
            print(result["win_rate"])
            print(result["strategy"].print_strategy())


if __name__ == "__main__":
    main_backtest("all_strategies")
