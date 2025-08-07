from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# ✅ JSON 快取檔案的正確檔名（與 Colab 輸出一致）
CACHE_FILE = "eps_cache.json"

# ✅ 首頁路由（用來測試 Render 有無啟動成功）
@app.route('/')
def home():
    return '✅ EPS API is running (JSON cache loaded)'

# ✅ 查詢 EPS 資料的 API：/api/eps?stock_id=2330
@app.route('/api/eps')
def get_eps_data():
    stock_id = request.args.get('stock_id')
    if not stock_id:
        return jsonify({"error": "Missing stock_id parameter"}), 400

    # 檢查 JSON 快取檔是否存在
    if not os.path.exists(CACHE_FILE):
        return jsonify({"error": "Cache file not found"}), 500

    try:
        # 讀取 JSON 檔案
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # 查找指定 stock_id 的資料
    result = data.get(stock_id)
    if result is None:
        return jsonify({"error": "Stock ID not found in cache", "stock_id": stock_id}), 404

    return jsonify(result)

# ✅ 啟動 Flask 應用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
