# generate_eps.py
import json
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

STOCK_IDS = ["2330", "2317", "2303"]

# 加強一點 Header（含 Referer），另外帶上一些 cookie（不一定每次都要，但在 CI 比較容易成功）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://goodinfo.tw/tw/index.asp",
    "Cookie": "IS_TOUCH_DEVICE=F; SCREEN_SIZE=WIDTH=2048&HEIGHT=1280;",
}

def fetch_eps(stock_id: str, debug_dir: Path) -> list[dict]:
    url = f"https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}"
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    r.encoding = "utf-8"

    # 存原始頁面，方便在 Actions 下載檢查
    (debug_dir / f"page_{stock_id}.html").write_text(r.text, "utf-8")

    soup = BeautifulSoup(r.text, "lxml")
    container = soup.select_one("#txtFinDetailData")
    if not container:
        print(f"⚠️ 找不到外層 #txtFinDetailData for {stock_id}")
        return []

    # 取內層真正的 table（有些情況 container 裡不止一層）
    table = container.find("table")
    if not table:
        print(f"⚠️ 找不到內層 <table> for {stock_id}")
        return []

    (debug_dir / f"table_{stock_id}.html").write_text(str(table), "utf-8")

    # 用 StringIO 包 table 給 pandas 讀
    dfs = pd.read_html(StringIO(str(table)))
    if not dfs:
        print(f"⚠️ pandas.read_html 讀不到表 for {stock_id}")
        return []

    df = dfs[0]
    # 把多層欄位壓平，避免 MultiIndex 或奇怪空白
    df.columns = [str(c).strip().replace("\n", "").replace(" ", "") for c in df.columns]

    # 偵錯：輸出欄位名稱與前幾列
    (debug_dir / f"df_cols_{stock_id}.txt").write_text("\n".join(df.columns), "utf-8")
    try:
        (debug_dir / f"df_head_{stock_id}.csv").write_text(df.head(10).to_csv(index=False), "utf-8")
    except Exception:
        pass

    # 嘗試用幾種可能的欄位名
    year_keys = ["年度", "年/季", "年/季度", "年季"]
    eps_keys  = ["EPS(元)", "稅後EPS(元)", "每股盈餘(元)"]
    yoy_keys  = ["年增(元)", "年增率(%)", "年增率"]
    pe_keys   = ["本益比", "本益比(倍)"]

    def pick(row, keys):
        for k in keys:
            k_norm = k.replace(" ", "").replace("\n", "")
            if k_norm in row:
                val = row.get(k_norm)
                if pd.notna(val):
                    return str(val)
        return ""

    rows = []
    for _, row in df.iterrows():
        # 將索引轉 dict，並把 key 正規化後查找
        rdict = {str(k).strip().replace("\n", "").replace(" ", ""): row[k] for k in df.columns if k in row}
        item = {
            "year": pick(rdict, year_keys),
            "eps":  pick(rdict, eps_keys),
            "yoy":  pick(rdict, yoy_keys),
            "pe":   pick(rdict, pe_keys),
        }
        # 過濾完全空白的列
        if any(item.values()):
            rows.append(item)

    return rows

def main():
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)

    cache = {}
    for sid in STOCK_IDS:
        try:
            data = fetch_eps(sid, debug_dir=debug_dir)
            cache[sid] = data
            print(f"✅ 完成 {sid}（共 {len(data)} 筆）")
        except Exception as e:
            print(f"❌ 失敗 {sid}: {e}")
            cache[sid] = []

    Path("eps_cache.json").write_text(json.dumps(cache, ensure_ascii=False, indent=2), "utf-8")
    print("📁 eps_cache.json 儲存完成！")

if __name__ == "__main__":
    main()
