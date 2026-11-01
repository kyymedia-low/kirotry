import os
from dotenv import load_dotenv

# Membaca isi file .env
load_dotenv()

# Mengambil token bot dari environment
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Validasi sederhana: pastikan token ada dan tidak kosong
if not BOT_TOKEN or BOT_TOKEN == "7891234567:AAExxxxxxxxxxxxxxxxxxxxxxx":
    raise ValueError("Token Bot belum diisi dengan benar di file .env!")

# Ambil VIP_IDS dan ubah string berpisah koma menjadi list angka [123456789, 987654321]
raw_vip_ids = os.getenv("VIP_IDS", "")
VIP_IDS = [int(x.strip()) for x in raw_vip_ids.split(",") if x.strip().isdigit()]

# Ambil Username / ID Channel Telegram untuk Force Subscribe
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")

# Ambil API Key untuk PhotoRoom
PHOTOROOM_API_KEY = os.getenv("PHOTOROOM_API_KEY", "")

# Ambil Api Key Dan Data Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# Ambil Api Key Bigjpg
BIGJPG_API_KEY = os.getenv("BIGJPG_API_KEY", "")

# --- KONTAK OWNER (Bisa lebih dari 1) ---
raw_owners = os.getenv("OWNER_USERNAMES", "")
OWNER_USERNAMES = [u.strip() for u in raw_owners.split(",") if u.strip()]