import requests
from sources.stockanalysis.utils.constants import ETF_BASE_URL
import json 
import re 
class StockAnalysis:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
     
    def get_raw_text(self):
        response=self.session.get(ETF_BASE_URL)
        if response.ok:
            self.parser(response.text)
        
    def parser(self, text):
        idx = text.find("count:")
        if idx == -1:
            print("count not found")
            return
        
        # extract everything from the data array onwards
        data_start = text.find("data:[", idx)
        if data_start == -1:
            print("data array not found")
            return
        
        # move past "data:" to get to the raw array
        array_start = data_start + len("data:")
        raw = text[array_start:]
        
        # find the closing bracket of the array
        # count brackets to find the matching close
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
        
        # convert JS to valid JSON
        # convert JS to valid JSON
        clean = re.sub(r'(\b\w+\b)(?=\s*:)', r'"\1"', raw)
        clean = re.sub(r':\.(\d+)', r':0.\1', clean)      # :.82 → :0.82
        clean = re.sub(r'-\.(\d+)', r'-0.\1', clean)       # -.41 → -0.41

        try:
            data = json.loads(clean)
            print(f"Successfully parsed {len(data)} ETFs")
            self.save_json(data)
        except json.JSONDecodeError as e:
            print(f"JSON error: {e}")
            print(clean[e.pos-50:e.pos+50])

    def save_json(self,text):
        with open("./sources/stockanalysis/data.json","w") as file:
            json.dump(text, file, indent=2)

        
    
