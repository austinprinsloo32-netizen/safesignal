from flask import Flask, request, jsonify
from detector import analyze_text
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")

    result = analyze_text(text)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)