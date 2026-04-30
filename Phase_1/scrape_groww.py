import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
]

script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(script_dir, "chroma_db", "documents.json")
def scrape():
    docs = {}
    doc_id = 1
    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for url in URLS:
        print(f"Scraping {url}...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            script = soup.find('script', id='__NEXT_DATA__')
            
            if not script:
                print(f"No Next.js data found for {url}")
                continue
                
            data = json.loads(script.string)
            mf_data = data.get('props', {}).get('pageProps', {}).get('mfServerSideData', {})
            
            if not mf_data:
                print(f"No mfServerSideData found for {url}")
                continue
                
            name = mf_data.get('scheme_name', 'Unknown Scheme')
            nav = mf_data.get('nav', 'N/A')
            nav_date = mf_data.get('nav_date', 'N/A')
            expense_ratio = mf_data.get('expense_ratio', 'N/A')
            exit_load = mf_data.get('exit_load', 'N/A')
            min_sip = mf_data.get('min_sip_investment', 'N/A')
            aum = mf_data.get('aum', 'N/A')
            benchmark = mf_data.get('benchmark_name', 'N/A')
            lock_in = mf_data.get('lock_in', 'N/A')
            
            content = f"""
# {name}
- NAV: {nav} as of {nav_date}
- Expense Ratio: {expense_ratio}%
- Exit Load: {exit_load}
- Minimum SIP: {min_sip}
- AUM: {aum}
- Benchmark: {benchmark}
- Lock-in: {lock_in}
- Scheme Description: {mf_data.get('description', '')}
            """
            
            docs[str(doc_id)] = {
                "content": content,
                "metadata": {
                    "source_url": url,
                    "scheme_name": name,
                    "last_updated": scrape_time
                }
            }
            doc_id += 1
            
        except Exception as e:
            print(f"Failed to process {url}: {e}")
            
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f:
        json.dump(docs, f, indent=4)
        
    print(f"Successfully scraped {len(docs)} funds into {DB_PATH}")

if __name__ == "__main__":
    scrape()
