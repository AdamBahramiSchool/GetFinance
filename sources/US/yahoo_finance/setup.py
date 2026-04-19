import requests
from sources.yahoo_finance.utils.constants import CRUMB_URL, FINANCE_CONSENT_URL, YAHOO_FINANCE_URL

class YahooFinance:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        self.crumb = None
        self.establish_session_consent()
        self.get_crumb()

    def get_crumb(self):
        response = self.session.get(CRUMB_URL)
        if response.ok:
            self.crumb = response.text
        else:
            print(f"Failed to get crumb: {response.status_code}")
        
    def get_extra_cookies(self) -> bool:
        try:
            response = self.session.get(YAHOO_FINANCE_URL)
            return response.ok
        except Exception as e:
            print("Invalid: ", e)
            return False

    def establish_session_consent(self) -> bool:
        try:
            response = self.session.get(FINANCE_CONSENT_URL)
        except Exception as e:
            print("Invalid: ", e)
            return False

        if response.ok:
            return self.get_extra_cookies()

        return False

    def get_data(self, url):
        return self.session.get(url, params={"crumb": self.crumb})