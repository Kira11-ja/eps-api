# generate_eps.py
import os, sys, json, time, random
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
from pathlib import Path

STOCK_IDS = ["2330", "2317", "2303"]
OUTFILE = "eps_cache.json"
DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(exist_ok=True)

BASE = "https://goodinfo.tw"
PATH = "/tw/StockBzPerformance.asp"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": f"{BASE}{PATH}",
}
# 這個站常看 Referer / UA，Cookie 不一定要，但加上可提高成功率
COOKIES = {
    "IS_TOUCH_DEVICE": "F",
    "SCREEN_SIZE": "WIDTH=2048&HEIGHT=1280",
}

def fetch_html(session: requests.Session, stock_id: str) -> str | None:
    url = f"{BASE}{PATH}?STOCK_ID={stock_id}"
    for i in range(3):
        try:
            r = session.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
            r.encoding = "utf-8"
            if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
                return r.text
        except Exception:
            pass
        time.sleep(1 + random.random())
    return None

def parse_table(html: str, stock_id: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    box = soup.select_one("#txtFinDetailData") or soup.select_one("table")
    if not box:
        return []

    dfs = pd.read_html(StringIO(box.prettify()))
    if not dfs:
        return []
    df = dfs[0]
    df.columns = [str(c).strip() for c in df.columns.map(str)]

    # 欄位偵測
    def find_col(cols, needles):
        for c in cols:
            cc = str(c)
            if any(n in cc for n in needles):
                return c
        return None

    year_col     = find_col(df.columns, ["年度", "年/季", "年季", "年季別"])
    eps_col      = find_col(df.columns, ["EPS"])
    roe_col      = find_col(df.columns, ["ROE"])
    priceavg_col = find_col(df.columns, ["平均"])

    rows = []
    for _, row in df.iterrows():
        # ✅ 不做正規化，直接用原始文字
        year = str(row.get(year_col, "")).strip() if year_col else ""
        if not year:
            continue

        rows.append({
            "year": year,                          # ← 原樣保留（可能是 25Q1、2024 年估…）
            "eps": "" if not eps_col else str(row.get(eps_col, "")).strip(),
            "ROE": "" if not roe_col else str(row.get(roe_col, "")).strip(),
            "priceavg": "" if not priceavg_col else str(row.get(priceavg_col, "")).strip(),
        })

    # 如果你不要排序，也可以拿掉這行
    # rows.sort(key=lambda r: r["year"], reverse=True)

    return rows


def main():
    out = {}
    total = 0

    with requests.Session() as s:
        for sid in STOCK_IDS:
            html = fetch_html(s, sid)
            # 存 raw HTML 便於你事後下載檢查
            (DEBUG_DIR / f"page_{sid}.html").write_text(html or "", encoding="utf-8")

            if not html:
                print(f"⚠️  {sid} 抓不到 HTML")
                out[sid] = []
                continue

            rows = parse_table(html, sid)
            # 也把欄位資訊存下來，幫你查欄位名是否變了
            if rows:
                # 給你一份 table 的前幾列 CSV
                try:
                    soup = BeautifulSoup(html, "lxml")
                    box = soup.select_one("#txtFinDetailData") or soup.select_one("table")
                    dfs = pd.read_html(StringIO(box.prettify()))
                    dfs[0].head(10).to_csv(DEBUG_DIR / f"table_head_{sid}.csv", index=False)
                except Exception:
                    pass

            out[sid] = rows
            total += len(rows)
            print(f"✅ {sid}：{len(rows)} 筆")

    # 先將結果寫到檔案（就算 0 筆，也讓你在 artifact 下載到），
    # 但「0 筆」時我們會用非 0 的 exit code 讓 workflow 失敗，避免把空資料 push 上 repo。
    with open(OUTFILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"📁 寫入 {OUTFILE} 完成（總共 {total} 筆）")

    # 若全部都 0，讓 workflow 失敗，並引導你下載 debug 檔
    if total == 0:
        print("❌ 全部股票皆為 0 筆，請到 Actions 下載 debug artifact 檢查 page_*.html / table_head_*.csv")
        sys.exit(2)

if __name__ == "__main__":
    main()



