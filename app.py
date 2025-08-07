from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ EPS API is running!"

@app.route("/api/eps", methods=["GET"])
def get_eps():
    stock_id = request.args.get("stock_id", "2330")
    # 模擬一個假回傳
    return jsonify({
        "stock_id": stock_id,
        "eps": 12.34,
        "pe": 18.9,
        "peg": 1.23
    })
