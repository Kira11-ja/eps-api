from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ EPS API is running!"

@app.route("/api/eps", methods=["GET"])
def get_eps():
    stock_id = request.args.get("stock_id", "2330")

    url = f"https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}"
    headers = {
        "user-agent": "Mozilla/5.0",
        "referer": "https://goodinfo.tw/"
    }

    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'lxml')

    try:
        # 找表格中最新一行的 EPS、YoY（可擴充取 PE PEG）
        table = soup.find("table", class_="b1 p4_2 r10 box_shadow")
        rows = table.find_all("tr")
        header = [td.get_text(strip=True) for td in rows[0].find_all("td")]
        latest = [td.get_text(strip=True) for td in rows[1].find_all("td")]

        eps = float(latest[header.index("EPS")])
        pe = float(latest[header.index("本益比")])
        peg = round(pe / eps, 2) if eps > 0 else None

        return jsonify({
            "stock_id": stock_id,
            "eps": eps,
            "pe": pe,
            "peg": peg
        })

    except Exception as e:
        return jsonify({"error": str(e), "stock_id": stock_id})

