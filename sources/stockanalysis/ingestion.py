import requests
from sources.stockanalysis.utils.constants import ETF_BASE_URL
import json 
import re 

class Ingestion:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
     
    @classmethod
    def create(self):
        self.get_financial_data()
        self.parser()
        self.save_json()

    def get_financial_data(self):
        response=self.session.get(ETF_BASE_URL)
        if response.ok:
            self.parser(response.text)
        
    def parser(self, text):
        idx = text.find("count:")
        if idx == -1:
            print("count not found")
            return
        
        data_start = text.find("data:[", idx)
        if data_start == -1:
            print("data array not found")
            return
        
        array_start = data_start + len("data:")
        raw = text[array_start:]
        
        depth = 0
        end_idx = 0
        for i, char in enumerate(raw):
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        
        raw = raw[:end_idx]
        
        clean = re.sub(r'(\b\w+\b)(?=\s*:)', r'"\1"', raw)
        clean = re.sub(r':\.(\d+)', r':0.\1', clean)     
        clean = re.sub(r'-\.(\d+)', r'-0.\1', clean)      

        try:
            data = json.loads(clean)
            print(f"Successfully parsed {len(data)} ETFs")
            self.save_json(data)
        except json.JSONDecodeError as e:
            print(f"JSON error: {e}")
            print(clean[e.pos-50:e.pos+50])

    def save_json(self,text):
        with open("./sources/stockanalysis/results/ingested.json","w") as file:
            json.dump(text, file, indent=2)

        
    
