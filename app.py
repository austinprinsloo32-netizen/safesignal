from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from detector import analyze_text

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")

    result = analyze_text(text)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)