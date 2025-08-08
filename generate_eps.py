# generate_eps.py
import json
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup

# 你要抓的股票清單
STOCK_IDS = ["2330", "2317", "2303"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Cookie": "IS_TOUCH_DEVICE=F; SCREEN_SIZE=WIDTH=2048&HEIGHT=1280;",
}

def fetch_eps(stock_id: str):
    """抓取單一股票 EPS 表格並回傳 list[dict]"""
    url = f"https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "lxml")
    table = soup.select_one("#txtFinDetailData")
    if not table:
        print(f"⚠️ 找不到表格 for {stock_id}")
        return []

    # 用 StringIO 包起來避免 pandas 的 FutureWarning
    dfs = pd.read_html(StringIO(str(table)))
    if not dfs:
        print(f"⚠️ 讀表失敗 for {stock_id}")
        return []

    df = dfs[0]
    df.columns = df.columns.map(str)

    rows = []
    for _, row in df.iterrows():
        rows.append({
            "year": row.get("年度") or row.get("年/季") or "",
            "eps": row.get("EPS(元)") or row.get("稅後EPS(元)") or "",
            "yoy": row.get("年增(元)") or "",
            "pe":  row.get("本益比") or "",
        })
    return rows

def main():
    cache = {}
    for sid in STOCK_IDS:
        try:
            data = fetch_eps(sid)
            cache[sid] = data
            print(f"✅ 完成 {sid}（共 {len(data)} 筆）")
        except Exception as e:
            print(f"❌ 失敗 {sid}: {e}")
            cache[sid] = []

    with open("eps_cache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print("📁 eps_cache.json 儲存完成！")

if __name__ == "__main__":
    main()
