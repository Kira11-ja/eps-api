from flask import Flask, request, jsonify
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>✅ EPS API is running!</h1>"

@app.route("/api/eps")
def get_eps():
    stock_id = request.args.get("stock_id")
    url = f"https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}"

    try:
        scraper = cloudscraper.create_scraper()
        res = scraper.get(url)
        res.encoding = "utf-8"

        soup = BeautifulSoup(res.text, "html.parser")

        # 嘗試抓 EPS 表格（以下是範例，要根據你原本邏輯調整）
        eps_table = soup.find("table", class_="b1 p4_2 r10 box_shadow")
        if eps_table is None:
            raise Exception("EPS table not found")

        # 在這裡加入你的資料解析邏輯
        eps = 12.34
        pe = 18.9
        peg = 1.23

        return jsonify({
            "stock_id": stock_id,
            "eps": eps,
            "pe": pe,
            "peg": peg
        })

    except Exception as e:
        return jsonify({
            "stock_id": stock_id,
            "error": str(e)
        })
