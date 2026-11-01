import json
import os
from datetime import datetime

# Ambil data VIP_IDS dari config.py di folder utama (root)
from config import VIP_IDS

# File json bakal otomatis terbuat di folder tools/
DATA_FILE = os.path.join(os.path.dirname(__file__), "limit_data.json")

def load_data() -> dict:
    """Membaca data dari file JSON."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data: dict):
    """Menyimpan data kembali ke file JSON."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[LIMITER ERROR] Gagal menyimpan data: {e}")

def check_limit(user_id: int, tool_name: str, max_limit: int = 3) -> tuple[bool, int]:
    """
    Ngecek apakah user masih punya kuota untuk fitur (tool) tertentu hari ini.
    """
    # 1. VIP Bypass: Kalau ID lu, langsung loss tanpa batas!
    if user_id in VIP_IDS:
        return True, 9999

    today = datetime.now().strftime("%Y-%m-%d")
    data = load_data()

    # 2. Fitur Auto-Reset: Kalo hari udah berganti, hapus semua catatan kemarin
    if data.get("date") != today:
        data = {"date": today, "users": {}}
        save_data(data)

    users = data.get("users", {})
    user_str = str(user_id) # Ubah ID Telegram ke format teks biar bisa masuk JSON

    # 3. Kalau user ini belum pernah pakai sama sekali hari ini, buatin brankasnya
    if user_str not in users:
        users[user_str] = {}

    # 4. Ambil catatan pemakaian khusus untuk tool_name (misal: "upscale")
    used = users[user_str].get(tool_name, 0)

    # 5. Validasi: Hitung sisa atau tolak kalau udah limit
    if used < max_limit:
        sisa = max_limit - used
        return True, sisa
    else:
        return False, 0

def increment_limit(user_id: int, tool_name: str):
    """
    Nambahin pemakaian (+1) setelah user BERHASIL pakai fitur.
    """
    # VIP nggak usah dicatet
    if user_id in VIP_IDS:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    data = load_data()

    # Jaga-jaga kalau pas nambahin limit pas banget jam 00:00 ganti hari
    if data.get("date") != today:
        data = {"date": today, "users": {}}

    users = data.get("users", {})
    user_str = str(user_id)

    if user_str not in users:
        users[user_str] = {}

    # Tambah angka pemakaian +1 cuma buat fitur yang lagi dipakai
    users[user_str][tool_name] = users[user_str].get(tool_name, 0) + 1
    data["users"] = users

    save_data(data)