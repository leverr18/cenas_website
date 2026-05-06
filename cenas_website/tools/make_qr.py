# cenas_website/tools/make_qr.py
import os, qrcode

BASE = os.getenv("PUBLIC_BASE_URL", "https://cenaskitchen.com")  # or use your Render domain

for slug in ("tomball", "copperfield"):
    url = f"{BASE}/apply/{slug}"
    img = qrcode.make(url)
    os.makedirs("static/qr", exist_ok=True)
    img.save(f"static/qr/{slug}.png")
    print("Created", f"static/qr/{slug}.png", "->", url)
