from sources.yahoo_finance.setup import YahooFinance
from sources.yahoo_finance.utils.constants import BASE_API

from sources.stockanalysis.ingestion import Ingestion
from sources.stockanalysis.analysis import Analysis

if __name__ == "__main__":
    finance_ingestion = Ingestion()
    response= finance_ingestion.get_financial_data()
    
    finance_analysis=Analysis()
    finance_analysis.create()