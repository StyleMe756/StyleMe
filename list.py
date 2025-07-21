import requests

res = requests.get("https://openrouter.ai/api/v1/models", headers={
    "Authorization": "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"
})
data = res.json()["data"]

# Print model IDs that accept images
vision_models = [
    m for m in data
    if "image" in m["architecture"]["input_modalities"]
]
print("✅ Vision-capable models:")
for m in vision_models:
    print(m["id"])
