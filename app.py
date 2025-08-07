from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# 設定 JSON 快取檔案路徑
CACHE_FILE = "eps_data.json"

@app.route('/')
def home():
    return '✅ EPS API is running (from JSON cache)!'

@app.route('/api/eps')
def get_eps_data():
    stock_id = request.args.get('stock_id')
    if not stock_id:
        return jsonify({"error": "Missing stock_id parameter"}), 400

    # 讀取快取檔
    if not os.path.exists(CACHE_FILE):
        return jsonify({"error": "Cache file not found"}), 500

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    result = data.get(stock_id)
    if result is None:
        return jsonify({"error": "Stock ID not found in cache", "stock_id": stock_id}), 404

    return jsonify(result)

if __name__ == '__main__':
    app.run()
