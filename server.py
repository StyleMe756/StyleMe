import time
import os
import uuid
import json
import requests
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from PIL import Image
import google.generativeai as genai

# === CONFIG ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA00gYwZwiDXLc-zSGzYuD__aBCLastKno")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "f486e9ee6f9955c5aa876ad7eac18a2b5f328891a09e6a7a2eb9c163c2f143fa")

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
LOG_FILE = "debug_log.txt"

# === Logging Helper ===
def log_to_file(message):
    try:
        with open(LOG_FILE, "a", encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except Exception as log_err:
        print(f"ERROR: Could not write to log file: {log_err} - Message: {message}")

# === Gemini Setup ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# === SerpAPI Product Search ===
def search_products_with_serpapi(query, max_results=5):
    log_to_file(f"Using SerpAPI to search for: {query}")
    serp_url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query,
        "tbm": "shop",
        "api_key": SERPAPI_KEY
    }

    try:
        response = requests.get(serp_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("shopping_results", [])[:max_results]:
            raw_link = item.get("link") or item.get("product_link") or item.get("serpapi_link") or ""
            if raw_link and not raw_link.startswith("http"):
                raw_link = "https://" + raw_link.lstrip("/")
            results.append({
                "title": item.get("title"),
                "price": item.get("price"),
                "source": item.get("source"),
                "link": raw_link,
                "thumbnail": item.get("thumbnail")
            })

        log_to_file(f"✅ Found {len(results)} products via SerpAPI.")
        return results

    except Exception as e:
        log_to_file(f"❌ Error using SerpAPI: {str(e)}")
        return []

# === ROUTES ===

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/analyze", methods=["POST"])
def analyze():
    log_to_file("--- ANALYZE FUNCTION STARTED ---")
    description = "No description generated."
    links = []
    path = None

    try:
        if 'image' not in request.files:
            return jsonify({"description": "No image uploaded.", "links": []})

        image_file = request.files["image"]
        if image_file.filename == '':
            return jsonify({"description": "Empty filename.", "links": []})

        filename = f"{uuid.uuid4()}.jpg"
        path = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(path)
        log_to_file(f"📷 Image saved: {path}")

        with Image.open(path) as img:
            response = model.generate_content([
                "Describe the outfit in this image in detail, focusing on specific clothing items...",
                img
            ])
            description = response.text.strip()
            log_to_file(f"📄 Gemini Description: {description}")

        if "cannot describe the outfit" in description.lower():
            description += "\n\n(Please provide an actual image of an outfit for product search.)"
            links = []
        else:
            search_query = "white t-shirt"
            if "*" in description:
                lines = [line.strip("* ").strip() for line in description.split("\n") if line.strip().startswith("*")]
                if lines:
                    search_query = lines[0]
            log_to_file(f"🧠 Search Query: {search_query}")
            links = search_products_with_serpapi(search_query)

            if not links:
                description += "\n\n(No matching products found. Try a clearer outfit image.)"

        return jsonify({"description": description, "links": links})

    except Exception as e:
        log_to_file(f"❌ Error: {str(e)}")
        return jsonify({"description": f"Error: {str(e)}", "links": []})

    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                log_to_file(f"⚠️ Cleanup error: {str(e)}")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": "Please enter a message."})

        response = model.generate_content(user_message)
        return jsonify({"reply": response.text.strip()})

    except Exception as e:
        log_to_file(f"❌ Chat error: {str(e)}")
        return jsonify({"reply": "Something went wrong."})

# === RUN SERVER ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
