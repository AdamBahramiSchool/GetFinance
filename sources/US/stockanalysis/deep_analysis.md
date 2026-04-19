# ETF Analysis Skill

## Goal
Build an `Analysis` class that takes filtered ETFs, their timeseries data, and extra signals, then scores and ranks them to find the best opportunities each day.

---

## Data Structures Available

### 1. filtered_etfs.json
List of pre-filtered ETF objects:
```json
{
  "s": "TQQQ",
  "n": "ProShares UltraPro QQQ",
  "assetClass": "Equity",
  "aum": 27886252011,
  "price": 58.59,
  "change": 1.23,
  "volume": 103559546,
  "holdings": 121
}
```

### 2. timeseries.json
List of historical daily close prices per ticker (3 months):
```json
{
  "status": 200,
  "ticker": "TQQQ",
  "currency": "",
  "data": [
    { "t": "2026-01-21T00:00:00.000Z", "c": 128.18 },
    { "t": "2026-01-22T00:00:00.000Z", "c": 131.57 }
  ]
}
```

### 3. extra_signals.json
Additional metadata per ticker scraped from the ETF detail page:
```json
{
  "ticker": "TQQQ",
  "Assets": "$27.89B",
  "Expense Ratio": "0.82%",
  "PE Ratio": "n/a",
  "Shares Out": "546.60M",
  "Dividend (ttm)": "$0.32",
  "Dividend Yield": "0.54%",
  "52-Week Low": "20.12",
  "52-Week High": "60.69",
  "Beta": "3.53",
  "Holdings": "121",
  "Inception Date": "Feb 9, 2010",
  "Previous Close": "56.43",
  "Open": "57.78"
}
```

---

## Class Structure to Build

```python
class Analysis:
    def __init__(self):
        self.etfs = []         # from filtered_etfs.json
        self.timeseries = {}   # dict keyed by ticker from timeseries.json
        self.signals = {}      # dict keyed by ticker from extra_signals.json
        self.scored = []       # final scored and ranked list

    def load_data(self): ...
    def build_lookups(self): ...
    def calculate_all(self): ...
    def score_etfs(self): ...
    def get_top(self, n=10): ...
    def save_results(self): ...
```

---

## Analysis Functions to Implement

### 1. Moving Averages (from timeseries)
Calculate 10-day, 20-day, 50-day simple moving averages from close prices.
- If current price > 50MA → bullish trend signal
- If 10MA > 20MA > 50MA → strong uptrend (golden alignment)

```python
def moving_average(closes, period):
    # closes is a list of floats, most recent last
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period
```

### 2. RSI - Relative Strength Index (from timeseries)
14-period RSI. Measures momentum — is the ETF overbought or oversold.
- RSI < 30 → oversold (potential buy opportunity)
- RSI 30-70 → neutral momentum zone (healthy trend)
- RSI > 70 → overbought (potentially overextended)

```python
def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
```

### 3. Price Position in 52-Week Range (from extra_signals)
Where is the current price relative to its 52-week high and low?
- Position near 52-week high = strong momentum
- Position near 52-week low = potential mean reversion play

```python
def week52_position(price, low_52, high_52):
    # returns 0.0 (at low) to 1.0 (at high)
    if high_52 == low_52:
        return 0.5
    return (price - low_52) / (high_52 - low_52)
```

### 4. Volume Surge (from filtered_etfs + timeseries)
Compare today's volume against the 20-day average volume.
- Ratio > 2.0 → significant unusual activity
- Ratio > 1.5 → elevated interest

```python
def volume_surge(today_volume, avg_volume):
    if avg_volume == 0:
        return 1.0
    return today_volume / avg_volume
```

Note: You need to calculate avg_volume from timeseries if available,
or use today's volume vs AUM as a proxy if not.

### 5. Momentum Score (from timeseries)
Percentage return over the last 1 month and 3 months.
- Strong positive momentum across both timeframes = strong signal

```python
def momentum(closes):
    if len(closes) < 2:
        return None
    month_1 = ((closes[-1] - closes[-20]) / closes[-20]) * 100 if len(closes) >= 20 else None
    month_3 = ((closes[-1] - closes[0]) / closes[0]) * 100
    return {"1m": month_1, "3m": month_3}
```

### 6. Expense Ratio Filter (from extra_signals)
Parse and filter out expensive ETFs. High fees eat returns.
- < 0.20% → excellent (broad market ETFs)
- 0.20-0.75% → acceptable
- > 0.75% → expensive (leveraged ETFs often fall here — flag but don't exclude)
- > 1.5% → exclude entirely

```python
def parse_expense_ratio(ratio_str):
    # "0.82%" → 0.82
    try:
        return float(ratio_str.replace("%", "").strip())
    except:
        return None
```

### 7. Beta Assessment (from extra_signals)
Beta measures volatility relative to the market (S&P 500 = 1.0).
- Beta < 0.8 → low volatility (defensive)
- Beta 0.8-1.2 → market-like movement
- Beta > 2.0 → highly volatile (leveraged ETFs like TQQQ=3.53, SOXL)
- Use beta to segment ETFs: conservative vs aggressive plays

```python
def parse_beta(beta_str):
    try:
        return float(beta_str)
    except:
        return None
```

### 8. Inception Date Filter (from extra_signals)
Exclude ETFs less than 1 year old — no track record.

```python
from datetime import datetime

def parse_inception(date_str):
    try:
        return datetime.strptime(date_str, "%b %d, %Y")
    except:
        return None

def is_established(date_str, min_years=1):
    inception = parse_inception(date_str)
    if not inception:
        return False
    age = (datetime.now() - inception).days / 365
    return age >= min_years
```

---

## Composite Scoring Function

Score each ETF 0-100 based on weighted signals. Adjust weights based on your strategy.

```python
def score_etf(etf, closes, signals):
    score = 0
    weights = {
        "momentum_today":  25,   # today's % change (already filtered >= 1.5%)
        "volume_surge":    20,   # unusual volume confirmation
        "rsi":             20,   # momentum health (favor 40-65 range)
        "trend":           20,   # price vs moving averages
        "week52_position": 15,   # position in 52-week range
    }

    # 1. Today's momentum (change already filtered >= 1.5)
    change = etf.get("change", 0)
    score += min(change / 10, 1.0) * weights["momentum_today"]

    # 2. Volume surge
    avg_vol = sum(volumes[-20:]) / 20  # need volume history or estimate
    surge = etf["volume"] / avg_vol if avg_vol > 0 else 1
    score += min(surge / 3, 1.0) * weights["volume_surge"]

    # 3. RSI — favor 40-65 (strong but not overbought)
    rsi = calculate_rsi(closes)
    if rsi:
        rsi_score = 1.0 if 40 <= rsi <= 65 else (0.5 if rsi < 40 else 0.2)
        score += rsi_score * weights["rsi"]

    # 4. Trend — price vs 50MA
    ma50 = moving_average(closes, 50)
    if ma50 and closes[-1] > ma50:
        score += weights["trend"]  # full points if above 50MA

    # 5. 52-week position
    try:
        low = float(signals.get("52-Week Low", 0))
        high = float(signals.get("52-Week High", 0))
        pos = week52_position(etf["price"], low, high)
        score += pos * weights["week52_position"]
    except:
        pass

    return round(score, 2)
```

---

## Segmentation Strategy

Don't rank leveraged ETFs against broad market ETFs — separate them:

```python
def segment_etfs(scored_etfs):
    leveraged = []   # beta > 2.0 or name contains "2X", "3X", "Ultra", "Bull"
    standard = []    # everything else

    for etf in scored_etfs:
        beta = etf.get("beta", 1.0)
        name = etf.get("n", "")
        if beta > 2.0 or any(x in name for x in ["2X", "3X", "Ultra", "Bull"]):
            leveraged.append(etf)
        else:
            standard.append(etf)

    return standard, leveraged
```

Leveraged ETFs (TQQQ, SOXL, TSLL) amplify gains AND losses — treat them as a
separate high-risk category, never mix them into the same ranking as IWM or XLK.

---

## Data Parsing Helpers

### Parse extra_signals currency strings
```python
def parse_currency(val):
    # "$27.89B" → 27890000000
    if val == "n/a" or not val:
        return None
    val = val.replace("$", "").replace(",", "").strip()
    multipliers = {"B": 1e9, "M": 1e6, "K": 1e3}
    for suffix, mult in multipliers.items():
        if val.endswith(suffix):
            return float(val[:-1]) * mult
    return float(val)

def parse_float(val):
    # "0.82%" → 0.82, "n/a" → None
    if val == "n/a" or not val:
        return None
    try:
        return float(val.replace("%", "").replace("$", "").replace(",", "").strip())
    except:
        return None
```

---

## Output Format

Save results as JSON with score and all relevant fields:
```json
[
  {
    "rank": 1,
    "ticker": "SOXL",
    "name": "Direxion Daily Semiconductor Bull 3X ETF",
    "score": 87.4,
    "change": 7.14,
    "volume": 67064954,
    "price": 94.68,
    "rsi": 58.2,
    "ma50": 88.3,
    "above_ma50": true,
    "week52_position": 0.82,
    "beta": 3.53,
    "expense_ratio": 0.89,
    "segment": "leveraged",
    "momentum_1m": 12.4,
    "momentum_3m": 28.1
  }
]
```

---

## Implementation Notes for Agent

1. Load all three JSON files at init
2. Build two lookup dicts: `timeseries[ticker]` and `signals[ticker]`
3. Extract closes list from timeseries: `[d["c"] for d in ticker_data["data"]]`
4. Run all calculations per ETF, handle missing data with `.get()` and `None` checks
5. Score each ETF, attach score to the ETF dict
6. Segment into leveraged vs standard
7. Sort each segment by score descending
8. Save top N from each segment to results JSON
9. All string fields from extra_signals need parsing before math — use parse_float() and parse_currency()
10. Never crash on missing data — wrap calculations in try/except and return None

---

## Expected Final Result

The final output should be **two ranked lists — top 5 standard ETFs and top 5 leveraged ETFs** — saved to `results.json`:

```json
{
  "date": "2026-04-18",
  "standard": [
    {
      "rank": 1,
      "ticker": "GDX",
      "name": "VanEck Gold Miners ETF",
      "score": 84.2,
      "change": 2.74,
      "price": 100.34,
      "volume": 21762711,
      "aum": 30923195907,
      "rsi": 61.3,
      "ma10": 97.2,
      "ma20": 94.8,
      "ma50": 89.1,
      "above_ma50": true,
      "momentum_1m": 8.4,
      "momentum_3m": 21.2,
      "week52_position": 0.88,
      "beta": 1.21,
      "expense_ratio": 0.51,
      "segment": "standard"
    },
    { "rank": 2, ... },
    { "rank": 3, ... },
    { "rank": 4, ... },
    { "rank": 5, ... }
  ],
  "leveraged": [
    {
      "rank": 1,
      "ticker": "SOXL",
      "name": "Direxion Daily Semiconductor Bull 3X ETF",
      "score": 91.5,
      "change": 7.14,
      "price": 94.68,
      "volume": 67064954,
      "aum": 13527958656,
      "rsi": 58.2,
      "ma10": 88.3,
      "ma20": 82.1,
      "ma50": 76.4,
      "above_ma50": true,
      "momentum_1m": 18.3,
      "momentum_3m": 34.7,
      "week52_position": 0.79,
      "beta": 3.45,
      "expense_ratio": 0.89,
      "segment": "leveraged"
    },
    { "rank": 2, ... },
    { "rank": 3, ... },
    { "rank": 4, ... },
    { "rank": 5, ... }
  ]
}
```

**Rules for the result:**
- Sorted by `score` descending within each segment (rank 1 = highest score)
- Every ETF object must contain all metrics listed above — no missing keys
- If a metric could not be calculated, set it to `null` not omit it
- `date` is today's date in YYYY-MM-DD format
- `week52_position` is a float 0.0 to 1.0 (0 = at 52-week low, 1 = at 52-week high)
- `above_ma50` is a boolean
- `segment` is either `"standard"` or `"leveraged"`
- All numeric fields should be rounded to 2 decimal places

- Save json to './sources/stockanalysis/results/top_etfs.json