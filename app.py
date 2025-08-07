from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ EPS API is running"

@app.route("/eps", methods=["GET"])
def get_eps():
    stock_id = request.args.get("stock_id")
    if not stock_id:
        return jsonify({"error": "Missing stock_id"})

    try:
        url = f"https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://goodinfo.tw/"
        }
        res = requests.get(url, headers=headers)
        res.encoding = "utf-8"

        soup = BeautifulSoup(res.text, "lxml")
        data = soup.select_one("#txtFinDetailData")
        if not data:
            return jsonify({"error": "No EPS data found"})

        dfs = pd.read_html(data.prettify())
        df = dfs[0]

        result = []
        for _, row in df.iterrows():
            year = row.get("年度")
            if not str(year).isdigit():
                continue
            result.append({
                "year": year,
                "eps": row.get("稅後EPS(元)", ""),
                "yoy": row.get("年增(元)", ""),
                "pe": row.get("本益比", ""),
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
