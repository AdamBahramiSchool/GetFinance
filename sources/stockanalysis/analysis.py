import json
from sources.stockanalysis.utils.constants import MIN_AUM, MIN_CHANGE, MIN_VOLUME, ETF_CHART_DATA_API
import asyncio
import aiohttp

class Analysis: 
    def __init__(self):
        self.data=None
        self.filtered=[]
        self.filtered_etf_signals=[]
        
    @classmethod
    def create(self):
        self.read_json()
        self.filter_etfs()
        asyncio.run(self.setup_async_requests())

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


    def save_filtered(self):
        with open("./sources/stockanalysis/results/filtered_etfs.json", "w") as file:
            json.dump(self.filtered,file,indent=2)
    
    async def get_more_etf_signals(self,session,ticker):
        async with session.get(ETF_CHART_DATA_API.format(ticker)) as response:
            self.filtered_etf_signals.append(response.json())
    
    async def setup_async_requests(self):
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                self.get_more_etf_signals(session=session, tickers=tickers['s']) for tickers in self.filtered
            ) 
