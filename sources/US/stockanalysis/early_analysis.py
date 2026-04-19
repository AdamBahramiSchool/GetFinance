import json
import re
from sources.stockanalysis.utils.constants import MIN_AUM, MIN_CHANGE, MIN_VOLUME, ETF_CHART_DATA_API, ETF_CLIENTSIDE_CHART_DATA
import asyncio
import aiohttp
from datetime import datetime, timezone

class Analysis: 
    def __init__(self):
        self.data=None
        self.filtered=[]
        self.filtered_etf_signals=[]
        self.etf_clientside_chart_data=[]
        
    @classmethod
    async def create(cls):
        self = cls()
        self.read_json()
        self.filter_etfs()
        await self.setup_async_requests(self.get_timeseries_market_prices)
        self.save_etf_timeseries_prices()
        await self.setup_async_requests(self.extract_etf_html)
        self.save_etf_clientside_chart_data()
        return self

    def read_json(self):
        with open('./sources/stockanalysis/results/ingested.json','r') as file:
            self.data=json.load(file)
        
    def filter_etfs(self):
        self.filtered=sorted([
            etf for etf in self.data 
            if etf.get("assetClass") == "Equity"
            and (etf.get("change") or 0) >= MIN_CHANGE
            and (etf.get("aum") or 0) >= MIN_AUM
            and (etf.get("volume") or 0) > MIN_VOLUME
        ]
        , key=lambda x: x["change"] * x["volume"]/1000000, reverse=True)
        self.save_filtered()
    
    async def get_timeseries_market_prices(self, session, etf):
        ticker = etf['s']
        async with session.get(ETF_CHART_DATA_API.format(ticker)) as response:
            raw = await response.json()
            self.filtered_etf_signals.append({
                "status": raw.get("status"),
                "ticker": ticker,
                "currency": etf.get("currency", ""),
                "data": [
                    {
                        "t": self.unix_to_utc_datetime(point["t"]).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                        "c": point.get("c")
                    }
                    for point in raw.get("data", [])
                ]
            })

    async def setup_async_requests(self, function):
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                *[function(session=session, etf=etf) for etf in self.filtered]
            )

    def save_filtered(self):
        with open("./sources/stockanalysis/results/filtered_etfs.json", "w") as file:
            json.dump(self.filtered, file, indent=2)

    def save_etf_timeseries_prices(self):
        with open("./sources/stockanalysis/results/timeseries.json", "w") as file:
            json.dump(self.filtered_etf_signals, file, indent=2)

    def save_etf_clientside_chart_data(self):
        with open("./sources/stockanalysis/results/extra_signals.json", "w") as file:
            json.dump(self.etf_clientside_chart_data, file, indent=2)

    def unix_to_utc_datetime(self, unix_time):
        return datetime.fromtimestamp(unix_time, timezone.utc)

    async def extract_etf_html(self, session, etf):
        ticker = etf['s']
        async with session.get(ETF_CLIENTSIDE_CHART_DATA.format(ticker)) as response:
            html = await response.text()
            self.etf_clientside_chart_data.append({
                "ticker": ticker,
                **self.parser(html)
            })

    def parser(self, html):
        pairs = re.findall(r'<td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td>', html)
        return {label.strip(): value.strip() for label, value in pairs}