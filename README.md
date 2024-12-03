# Credit Spreads Algo

This algo is designed to provide simple trade alerts with a backtested method. Developed in Python and seamlessly integrated with telebot and yfinance, Credit Spreads Platform delivers actionable insights to elevate your trading experience.

#### Key Strategies:

#### Trend Up

- **Option Type:** Put
- **Deviation from 200ma:** +4
- **Price Multiplier:** 0.98
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
   Ticker: QQQ
   Strategy Name: Over Extended
   Current Price: 421
   MA/STD: 365.57/26.19
   Date Alerted: 2024-01-19
   Expiration Date: 2024-02-02
   Option Type: Call
   Strike Prices: 429
  ```
#### How to use
docker compose up --build
docker run -v ~/Sites/lux_credit_spreads_python/script_brain:/app credit_spreads_image 

## Kelly Criterion Backtest
win_rates = np.arange(90, 92, 0.5)
credits = np.arange(0.40, 0.55, 0.05)
kelly_fractions = np.arange(0.3, 0.85, 0.05)


=== Top Position Sizing Strategies ===
Rank Win Rate Credit   Kelly %  Final $      Return %  DrawDown% Trades
----------------------------------------------------------------------
   1     91.5     0.55      0.8   10,963,716   54718.6      16.9   1147
   2     91.5     0.55      0.7   10,294,628   51373.1      17.8   1147
   3     91.5     0.55      0.7    9,444,354   47121.8      19.2   1147
   4     91.5     0.55      0.6    8,418,980   41994.9      21.0   1147
   5     91.0     0.55      0.8    8,095,856   40379.3      21.7   1147
   6     91.0     0.55      0.7    7,077,530   35287.7      24.1   1147
   7     91.5     0.55      0.6    7,077,530   35287.7      24.1   1147
   8     91.0     0.55      0.7    6,056,298   30181.5      27.1   1147
   9     91.5     0.55      0.5    5,635,304   28076.5      28.6   1147
  10     91.0     0.55      0.6    4,492,240   22361.2      33.5   1147
  11     91.5     0.55      0.5    3,830,834   19054.2      37.2   1147
  12     90.5     0.55      0.8    2,746,680   13633.4      46.4   1147
  13     91.0     0.55      0.6    2,746,680   13633.4      46.4   1147
  14     90.5     0.55      0.7    1,867,212    9236.1      48.3   1147
  15     91.5     0.55      0.4    1,867,212    9236.1      48.3   1147
  16     91.0     0.55      0.5    1,676,626    8283.1      47.3   1147
  17     90.5     0.55      0.7    1,337,382    6586.9      45.4   1147
  18     91.0     0.55      0.5    1,138,214    5591.1      43.3   1147
  19     91.5     0.55      0.4    1,138,214    5591.1      43.3   1147
  20     90.5     0.55      0.6    1,067,260    5236.3      42.3   1147


### IWM
Total Trades Taken: 1147
Total Trades Skipped: 53
Total Available Trades: 1200
Win Rate: 93.1%

### VTI
Total Trades Taken: 1114
Total Trades Skipped: 34
Total Available Trades: 1148
Win Rate: 94.9%


### QQQ
Total Trades Taken: 1201
Total Trades Skipped: 71
Total Available Trades: 1272
Win Rate: 92.8%

### SPY
Total Trades Taken: 1216
Total Trades Skipped: 53
Total Available Trades: 1269
Win Rate: 93.0%


## 2 weeks
QQQ 0.54 - IV 8%
VTI 0.32 - IV 9%
IWM 0.78 - IV 21%
SPY 0.30 - IV 5%

## 11 days
QQQ 0.67 - IV 14%
VTI 0.32 - IV 9%
IWM 0.78 - IV 22.5%
SPY 0.35 - IV 10%


VTI $299.62 | Active
PUT 290 13.12 (-3.2%)
P/L: +$324/-$2676
Risk: $2727.27/20k (14%)
Year 2024: 82.61%: 38/46

IWM $241.99 | Active
PUT 235 13.12 (-2.9%)
P/L: +$324/-$2676
Risk: $2727.27/20k (14%)
Year 2024: 82.61%: 38/46

SPY $601.56 | Active
PUT 585 13.12 (-2.8%)
P/L: +$324/-$2676
Risk: $2727.27/20k (14%)
Year 2024: 82.61%: 38/46

QQQ $508.99 | Active
PUT 495 13.12 (-2.7%)
P/L: +$324/-$2676
Risk: $2727.27/20k (14%)
Year 2024: 82.61%: 38/46


