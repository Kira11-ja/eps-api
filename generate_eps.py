# generate_eps.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from tqdm import tqdm
import json
import math


# 要抓的股票代號清單
stock_ids = ['2330', '2317', '2303']

# ===== 輸出檔名（跟 workflow 保持一致）=====
OUTFILE = "eps_cache.json"

def pick(row: pd.Series, candidates):
    """在多個可能欄名中，挑第一個存在且非空的值，回傳乾淨的字串"""
    for c in candidates:
        if c in row:
            v = row[c]
            # pandas 可能回傳 NaN/None 或 Series
            if isinstance(v, pd.Series):
                v = v.iloc[0] if len(v) else None
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                s = str(v).strip()
                if s != "":
                    return s
    return ""

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
     # 讀表
        dfs = pd.read_html(StringIO(table_html.prettify()))
        if not dfs:
            print(f"⚠️ 讀不到表格 for {stock_id}")
            continue

       
        df = dfs[0]
    # 保險：把欄名轉成字串
        df.columns = df.columns.map(str)

        eps_data = []
        for _, row in df.iterrows():
            year = pick(row, ["年度", "年/季"])
            if year == "":
                # 跳過沒有年份的列
                continue

            item = {
                "year": year,
                "eps": pick(row, ["稅後EPS(元)", "EPS(元)"]),
                "yoy": pick(row, ["年增(元)", "年增"]),
                "pe": pick(row, ["本益比", "PE"]),
            }
            eps_data.append(item)


        eps_cache[stock_id] = eps_data
        print(f"✅ 完成 {stock_id}（共 {len(eps_data)} 筆）")

    except Exception as e:
        print(f"❌ 失敗 {stock_id}: {e}")

# 寫入 JSON 快取檔案
with open(OUTFILE, "w", encoding="utf-8") as f:
    json.dump(eps_cache, f, ensure_ascii=False, indent=2)

print(f"📁 {OUTFILE} 儲存完成！")

