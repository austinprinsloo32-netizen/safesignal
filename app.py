from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from detector import analyze_text, analyze_single_url, analyze_email, analyze_image_file
import os

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    mode = request.form.get("mode") or (request.get_json(silent=True) or {}).get("mode", "text")

    if mode == "image":
        image = request.files.get("image")
        if not image:
            return jsonify({
                "risk": "Invalid Input",
                "score": 0,
                "reasons": ["No image was uploaded."],
                "insights": [],
                "advice": "Upload a screenshot to analyze."
            }), 400

        result = analyze_image_file(image)

    else:
        data = request.get_json()

        if mode == "url":
            url = data.get("url", "")
            result = analyze_single_url(url)

        elif mode == "email":
            sender = data.get("sender", "")
            subject = data.get("subject", "")
            body = data.get("body", "")
            result = analyze_email(sender, subject, body)

        else:
            text = data.get("text", "")
            result = analyze_text(text)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)