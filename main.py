from sources.yahoo_finance.setup import YahooFinance
from sources.yahoo_finance.utils.constants import BASE_API

from sources.stockanalysis.ingestion import Ingestion
from sources.stockanalysis.early_analysis import Analysis
from sources.stockanalysis.end_analysis import EndAnalysis

import asyncio

async def main():
    finance_ingestion = Ingestion()
    response = finance_ingestion.get_financial_data()

    finance_analysis = await Analysis.create()

    top_etfs = EndAnalysis.create()

if __name__ == "__main__":
    asyncio.run(main())