from datetime import datetime, timedelta

import yfinance as yf

from strategy import TickerData, Trade, run_all_strategies


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
                    f"Min Credit: {trade.min_credit}"
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


def backtest_strategy(ticker_data, trades):
    money = 0
    win = 0
    total = 0
    price_multiplier = []

    for trade in trades:
        expiration_date = datetime.strptime(trade.expiration_date, "%Y-%m-%d %H:%M:%S")
        date_alerted = datetime.strptime(trade.date_alerted, "%Y-%m-%d %H:%M:%S")
        sell_strike = int(trade.strike_prices)
        option_type = trade.option_type

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
                print(
                    f"{alerted_price} - {option_type} {expiration_date.strftime('%d %B %Y')} {int(sell_strike)} - {int(expiration_price)} - {sell_strike / alerted_price} - Passed"
                )
            else:
                money -= 100 - int(trade.min_credit)
                # trade.save_to_database(status="LOSE")
                print(
                    f"{alerted_price} - {option_type} {expiration_date.strftime('%d %B %Y')} {int(sell_strike)} - {int(expiration_price)} - {sell_strike / alerted_price} - Failed"
                )

    print(money)
    print(win)
    print(total)
    print(win / total * 100)
    if price_multiplier:
        print(sum(price_multiplier) / len(price_multiplier))


def main_backtest(type):
    file_name = "spy_all.txt"
    specific_date = datetime(2024, 1, 19)

    ticker_symbol = "QQQ"
    ticker_data = TickerData(ticker_symbol)

    if type == "create":
        all_trades = []
        for i in range(0, 8000):
            all_trades.append(
                run_all_strategies(ticker_data, specific_date - timedelta(days=i))
            )
        all_trades = [item for item in all_trades if item != []]
        write_trades_to_file(all_trades, file_name)
        # elif type == "verify":
        trades = read_trades_from_file("spy_all.txt")
        backtest_strategy(ticker_data, trades)
    elif type == "steal":
        file_name = "input.txt"
        output_data = process_trades(file_name)
        print(output_data)


if __name__ == "__main__":
    main_backtest("create")
