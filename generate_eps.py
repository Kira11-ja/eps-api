# generate_eps.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from tqdm import tqdm
import json

# 要抓的股票代號清單
stock_ids = ['2330', '2317', '2303']

eps_cache = {}

for stock_id in tqdm(stock_ids, desc="抓取 EPS"):
    url = f"https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Cookie': 'IS_TOUCH_DEVICE=F; SCREEN_SIZE=WIDTH=2048&HEIGHT=1280;',
    }

    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'lxml')
        table_html = soup.select_one('#txtFinDetailData')

        if not table_html:
            print(f"⚠️ 找不到表格 for {stock_id}")
            continue

        dfs = pd.read_html(StringIO(table_html.prettify()))
        df = dfs[0]
        df.columns = df.columns.map(str)

        eps_data = []
        for _, row in df.iterrows():
            eps_data.append({
                "year": row.get("年度") or row.get("年/季"),
                "eps": row.get("EPS(元)") or row.get("稅後EPS(元)"),
                "yoy": row.get("年增(元)"),
                "pe": row.get("本益比"),
            })

        eps_cache[stock_id] = eps_data
        print(f"✅ 完成 {stock_id}（共 {len(eps_data)} 筆）")

    except Exception as e:
        print(f"❌ 失敗 {stock_id}: {e}")

# 寫入 JSON 快取檔案
with open("eps_data.json", "w", encoding="utf-8") as f:
    json.dump(eps_cache, f, indent=2, ensure_ascii=False)

print("📁 eps_data.json 儲存完成！")
