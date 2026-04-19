import json
from datetime import datetime, date


class EndAnalysis:
    def __init__(self):
        self.etfs = []
        self.timeseries = {}
        self.signals = {}
        self.scored = []

    @classmethod
    def create(cls):
        self = cls()
        self.load_data()
        self.calculate_all()
        self.save_results()
        return self

    def load_data(self):
        with open('./sources/stockanalysis/results/filtered_etfs.json') as f:
            self.etfs = json.load(f)
        with open('./sources/stockanalysis/results/timeseries.json') as f:
            self.timeseries = {item['ticker']: item for item in json.load(f)}
        with open('./sources/stockanalysis/results/extra_signals.json') as f:
            self.signals = {item['ticker']: item for item in json.load(f)}

    # --- Calculation helpers ---

    def moving_average(self, closes, period):
        if len(closes) < period:
            return None
        return round(sum(closes[-period:]) / period, 2)

    def calculate_rsi(self, closes, period=14):
        if len(closes) < period + 1:
            return None
        deltas = [closes[i + 1] - closes[i] for i in range(len(closes) - 1)]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    def week52_position(self, price, low_52, high_52):
        if high_52 == low_52:
            return 0.5
        return round((price - low_52) / (high_52 - low_52), 2)

    def momentum(self, closes):
        if len(closes) < 2:
            return None, None
        month_1 = round(((closes[-1] - closes[-20]) / closes[-20]) * 100, 2) if len(closes) >= 20 else None
        month_3 = round(((closes[-1] - closes[0]) / closes[0]) * 100, 2)
        return month_1, month_3

    def parse_float(self, val):
        if not val or val == "n/a":
            return None
        try:
            return float(str(val).replace("%", "").replace("$", "").replace(",", "").strip())
        except:
            return None

    def is_established(self, date_str, min_years=1):
        if not date_str or date_str == "n/a":
            return False
        try:
            inception = datetime.strptime(date_str, "%b %d, %Y")
            return (datetime.now() - inception).days / 365 >= min_years
        except:
            return False

    def score_etf(self, etf, closes, sig):
        score = 0
        weights = {
            "momentum_today":  25,
            "volume_surge":    20,
            "rsi":             20,
            "trend":           20,
            "week52_position": 15,
        }

        change = etf.get("change") or 0
        score += min(change / 10, 1.0) * weights["momentum_today"]

        aum = etf.get("aum") or 0
        price = etf.get("price") or 1
        avg_vol = (aum / price) * 0.01
        today_vol = etf.get("volume") or 0
        surge = today_vol / avg_vol if avg_vol > 0 else 1.0
        score += min(surge / 3, 1.0) * weights["volume_surge"]

        if closes:
            rsi = self.calculate_rsi(closes)
            if rsi is not None:
                rsi_score = 1.0 if 40 <= rsi <= 65 else (0.5 if rsi < 40 else 0.2)
                score += rsi_score * weights["rsi"]

            ma50 = self.moving_average(closes, 50)
            if ma50 is not None and closes[-1] > ma50:
                score += weights["trend"]

        try:
            low = self.parse_float(sig.get("52-Week Low"))
            high = self.parse_float(sig.get("52-Week High"))
            if low is not None and high is not None:
                pos = self.week52_position(etf.get("price", 0), low, high)
                score += pos * weights["week52_position"]
        except:
            pass

        return round(score, 2)

    def calculate_all(self):
        for etf in self.etfs:
            ticker = etf.get("s")
            sig = self.signals.get(ticker, {})

            expense_ratio = self.parse_float(sig.get("Expense Ratio"))
            if expense_ratio is not None and expense_ratio > 1.5:
                continue
            if not self.is_established(sig.get("Inception Date")):
                continue

            ts = self.timeseries.get(ticker, {})
            closes = [d["c"] for d in ts.get("data", []) if d.get("c") is not None]

            ma10 = self.moving_average(closes, 10)
            ma20 = self.moving_average(closes, 20)
            ma50 = self.moving_average(closes, 50)
            rsi = self.calculate_rsi(closes)
            mom_1m, mom_3m = self.momentum(closes)
            beta = self.parse_float(sig.get("Beta"))

            try:
                low = self.parse_float(sig.get("52-Week Low"))
                high = self.parse_float(sig.get("52-Week High"))
                w52_pos = self.week52_position(etf.get("price", 0), low, high) if low is not None and high is not None else None
            except:
                w52_pos = None

            name = etf.get("n", "")
            is_leveraged = (beta or 0) > 2.0 or any(x in name for x in ["2X", "3X", "Ultra", "Bull"])

            self.scored.append({
                "ticker": ticker,
                "name": name,
                "score": self.score_etf(etf, closes, sig),
                "change": round(etf.get("change") or 0, 2),
                "volume": etf.get("volume"),
                "price": etf.get("price"),
                "aum": etf.get("aum"),
                "rsi": rsi,
                "ma10": ma10,
                "ma20": ma20,
                "ma50": ma50,
                "above_ma50": (closes[-1] > ma50) if (closes and ma50 is not None) else None,
                "momentum_1m": mom_1m,
                "momentum_3m": mom_3m,
                "week52_position": w52_pos,
                "beta": beta,
                "expense_ratio": expense_ratio,
                "segment": "leveraged" if is_leveraged else "standard",
            })

    def get_top(self, n=5):
        standard = sorted(
            [e for e in self.scored if e["segment"] == "standard"],
            key=lambda x: x["score"], reverse=True
        )[:n]
        leveraged = sorted(
            [e for e in self.scored if e["segment"] == "leveraged"],
            key=lambda x: x["score"], reverse=True
        )[:n]

        for i, etf in enumerate(standard, 1):
            etf["rank"] = i
        for i, etf in enumerate(leveraged, 1):
            etf["rank"] = i

        return standard, leveraged

    def save_results(self):
        path = "./sources/stockanalysis/results/top_etfs.json"
        today = date.today().isoformat()

        try:
            with open(path) as f:
                data = json.load(f)
            history = data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        standard, leveraged = self.get_top()
        entry = {"date": today, "standard": standard, "leveraged": leveraged}

        for i, record in enumerate(history):
            if record.get("date") == today:
                history[i] = entry
                break
        else:
            history.append(entry)

        with open(path, "w") as f:
            json.dump(history, f, indent=2)
