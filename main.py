from sources.yahoo_finance.setup import YahooFinance
from sources.yahoo_finance.utils.constants import BASE_API

from sources.stockanalysis.setup import StockAnalysis

if __name__ == "__main__":
    finance = StockAnalysis()
    response= finance.get_raw_text()
    