from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

CACHE_FILE = "eps_cache.json"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def home():
    return "✅ EPS API is running (JSON cache loaded)"

# 方式一：/api/eps?stock_id=2330
@app.route("/api/eps")
def get_eps_query():
    stock_id = request.args.get("stock_id")
    if not stock_id:
        return jsonify({"error": "Missing stock_id parameter"}), 400
    data = load_cache()
    if data is None:
        return jsonify({"error": "Cache file not found"}), 500
    result = data.get(str(stock_id))
    if result is None:
        return jsonify({"error": "Stock ID not found in cache", "stock_id": stock_id}), 404
    return jsonify(result), 200

# 方式二：/api/eps/2330
@app.route("/api/eps/<stock_id>")
def get_eps_path(stock_id):
    data = load_cache()
    if data is None:
        return jsonify({"error": "Cache file not found"}), 500
    result = data.get(str(stock_id))
    if result is None:
        return jsonify({"error": "Stock ID not found in cache", "stock_id": stock_id}), 404
    return jsonify(result), 200

# 可選：給 n8n 或手動叫來重新讀取檔案（目前是每次請求都讀，所以可不加）
@app.route("/admin/reload", methods=["POST", "GET"])
def reload_cache():
    ok = os.path.exists(CACHE_FILE)
    return jsonify({"reloaded": ok}), (200 if ok else 500)

if __name__ == "__main__":
    # 本地測試用；Render 會用 gunicorn 啟動
    app.run(host="0.0.0.0", port=5000)
