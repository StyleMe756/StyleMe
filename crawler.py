# crawler.py

import requests
from bs4 import BeautifulSoup
import os
import uuid
import base64
import json
import time
import random

# === CONFIGURATION ===
FLASK_ANALYZE_URL = "http://127.0.0.1:5000/analyze"
DOWNLOAD_DIR = "crawled_images"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === HELPER FUNCTION: Download Image ===
def download_image(image_url, target_dir):
    """
    Downloads an image from a URL and returns its local path.
    Includes basic error handling and file extension inference.
    """
    try:
        # Send a GET request to the image URL with a timeout
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if 'jpeg' in content_type:
            ext = 'jpg'
        elif 'png' in content_type:
            ext = 'png'
        elif 'gif' in content_type:
            ext = 'gif'
        else:
            ext = 'jpg'

        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(target_dir, filename)

        with open(filepath, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        print(f"Downloaded: {image_url} to {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {image_url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        return None

# === MAIN CRAWLER FUNCTION ===
def crawl_and_analyze(start_url, max_images=5):
    """
    Crawls a given URL, finds images, downloads them,
    and sends them to your Flask /analyze endpoint for processing.
    Includes delays to be a "good citizen" when crawling.
    """
    try:
        print(f"Starting crawl for: {start_url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        
        response = requests.get(start_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        image_tags = soup.find_all('img', src=True)

        images_processed = 0
        for img_tag in image_tags:
            if images_processed >= max_images:
                break

            img_url = img_tag['src']
            
            # --- NEW CHECK: Skip Data URIs ---
            if img_url.startswith('data:'):
                print(f"Skipping Data URI image: {img_url[:50]}...") # Print first 50 chars for brevity
                continue # Skip to the next image tag

            # Convert relative URLs to absolute URLs
            if not img_url.startswith('http'):
                img_url = requests.compat.urljoin(start_url, img_url)

            if img_url:
                local_image_path = download_image(img_url, DOWNLOAD_DIR)
                if local_image_path:
                    try:
                        with open(local_image_path, 'rb') as img_file:
                            files = {'image': (os.path.basename(local_image_path), img_file, 'image/jpeg')}
                            
                            flask_response = requests.post(FLASK_ANALYZE_URL, files=files)
                            flask_response.raise_for_status()
                            
                            analysis_result = flask_response.json()
                            print(f"Analysis for {img_url}: {analysis_result.get('description', 'No description')}")
                            
                            if analysis_result.get('links'):
                                print("Product Links:")
                                for link in analysis_result['links']:
                                    print(f"  - {link}")
                            else:
                                print("  No product links found for this image.")

                            images_processed += 1
                    except requests.exceptions.RequestException as e:
                        print(f"Error sending image {local_image_path} to Flask API: {e}")
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON response from Flask API for {local_image_path}")
                    finally:
                        if os.path.exists(local_image_path):
                            os.remove(local_image_path)
                            print(f"Cleaned up {local_image_path}")

            time.sleep(random.uniform(2, 5))

    except requests.exceptions.RequestException as e:
        print(f"Error during crawl for {start_url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during crawling: {e}")

# === ENTRY POINT ===
if __name__ == "__main__":
    target_website = "https://www.nike.com/w/mens-shoes-nik1zy7ok"
    crawl_and_analyze(target_website, max_images=3)
