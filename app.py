"""
Small Flask app: one page, one endpoint.
GET  /            -> the input form
POST /generate     -> prompt in, MP4 back
"""

import os
from dotenv import load_dotenv
load_dotenv()  # reads .env into environment variables before anything else runs

from flask import Flask, request, jsonify, send_file
from planner import make_plan
from render_pipeline import generate_video

app = Flask(__name__, static_folder="static")


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    prompt = (data or {}).get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Prompt is empty."}), 400

    try:
        plan = make_plan(prompt)
        video_path = generate_video(plan)
    except ValueError as e:
        # Bad LLM output - not the user's fault, but not a server crash either.
        return jsonify({"error": f"Could not plan the video: {e}"}), 502
    except RuntimeError as e:
        # HyperFrames itself failed to render.
        return jsonify({"error": f"Rendering failed: {e}"}), 500

    return send_file(video_path, mimetype="video/mp4")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
