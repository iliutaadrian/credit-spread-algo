```python
down_range = [-1, 3]
up_range = [3, 6]
days_range = [7, 15]

Strategy(
    "Trend Up",
    "put",
    {"up": 4, "down": 1},
    0.97,
    {"SPY": 98, "DIA": 89, "QQQ": 88},
    9,
),


down_range = [-3, 1]
up_range = [1, 3]
days_range = [7, 15]

Strategy(
    "Trend Sideways",
    "put",
    {"up": 1, "down": -1},
    0.98,
    {"SPY": 89, "DIA": 90, "QQQ": 87},
    14,
),


down_range = [-5, -3]
up_range = [-3, 0]
days_range = [7, 15]

Strategy(
    "Dip buy",
    "put",
    {"up": -2, "down": -10},
    0.987,
    {"SPY": 90, "DIA": 90, "QQQ": 90},
    8,
),


down_range = [1, 3]
up_range = [3, 6]
days_range = [7, 15]

Strategy(
    "Over Extended",
    "call",
    {"up": 4, "down": 2},
    1.022,
    {"SPY": 96, "DIA": 90, "QQQ": 90},
    10,
),


down_range = [-5, 5]
up_range = [-5, 5]
days_range = [7, 15]

Strategy(
    "LUX Trend Up",
    "put",
    {"up": 5, "down": -5},
    0.97,
    {"SPY": 98, "DIA": 89, "QQQ": 88},
    9,
),

down_range = [-5, 5]
up_range = [-5, 5]
days_range = [7, 15]

Strategy(
    "LUX Trend Down",
    "put",
    {"up": 5, "down": -5},
    0.97,
    {"SPY": 98, "DIA": 89, "QQQ": 88},
    9,
),

```
