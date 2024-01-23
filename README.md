# Credit Spreads Algo

This algo is designed to provide simple trade alerts with a backtested method. Developed in Python and seamlessly integrated with telebot and yfinance, Credit Spreads Platform delivers actionable insights to elevate your trading experience.

#### Key Strategies:

#### Trend Up
   - **Option Type:** Put
   - **Deviation from 200ma:** +4
   - **Price Multiplier:** 0.97
   - **Expiration Date Round:** 9

   **Explanation:** Identifies stocks with a current price 4 units higher than their 200-day Moving Average, suggesting an upward trend.

   **Trade Example:** If a stock's 200-day MA is 300, the algorithm would identify potential trades if the current price is 304 or higher.

#### Trend Sideways
   - **Option Type:** Put
   - **Deviation:** ±1
   - **Price Multiplier:** 0.98
   - **Expiration Date Round:** 14

   **Explanation:** Looks for stocks with a relatively small deviation from the 200-day MA, signaling a sideways trend. The algorithm considers both slight upward and downward deviations.

   **Trade Example:** If a stock's 200-day MA is 250, the algorithm would identify potential trades if the current price is between 249 and 251.

#### Dip Buy
   - **Option Type:** Put
   - **Deviation from 200ma:** -2
   - **Price Multiplier:** 0.987
   - **Expiration Date Round:** 8

   **Explanation:** Focuses on buying during dips. A deviation of -2 from the 200-day MA implies the algorithm is seeking stocks with prices 2 units lower than the average, anticipating a potential rebound.

   **Trade Example:** If a stock's 200-day MA is 180, the algorithm would identify potential trades if the current price is 178 or lower.

#### Over Extended
   - **Option Type:** Call
   - **Deviation from 200ma:** +2 - +10
   - **Price Multiplier:** 1.019
   - **Expiration Date Round:** 9

   **Explanation:** For the "Over Extended" strategy, a deviation of 10 from the 200-day MA indicates the algorithm is seeking stocks with a current price 10 units higher than their 200-day MA, suggesting a potentially over-extended trend.

   **Trade Example:** If a stock's 200-day MA is 400, the algorithm would identify potential trades if the current price is 410 or higher.

#### Backtesting Details:


## Backtesting Details:
- Backtested with SPY and QQQ.
- Backtested with SPY and QQQ from 2002 for a 93% Winrate
- Example of Telegram Notification:
  ```
  - **Ticker:** QQQ
  - **Strategy Name:** Over Extended
  - **Current Price:** 421
  - **MA/STD:** 365.57/26.19
  - **Date Alerted:** 2024-01-19
  - **Expiration Date:** 2024-02-02
  - **Option Type:** Call
  - **Strike Prices:** 429
