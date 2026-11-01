# ==========================================
# [AREA ATAS] : IMPORT & KONFIGURASI
# ==========================================
import os
import sys
import time         # Tambahan untuk jeda Bigjpg
import httpx
import requests     # Tambahan untuk nembak API Bigjpg
import cloudinary   # Tambahan untuk Cloudinary
import cloudinary.uploader

# Tambahan variabel API dari config.py
from config import (
    PHOTOROOM_API_KEY,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
    BIGJPG_API_KEY
)

# Kunci Pintu Masuk Cloudinary (Otomatis jalan saat file dipanggil)
cloudinary.config( 
  cloud_name = CLOUDINARY_CLOUD_NAME, 
  api_key = CLOUDINARY_API_KEY, 
  api_secret = CLOUDINARY_API_SECRET
)

# ==========================================
# [AREA TENGAH] : KODE LAMA (TIDAK DIUBAH SAMA SEKALI)
# ==========================================
def update_console(msg, status="info"):
    colors = {
        "info": "\033[96m",
        "success": "\033[92m",
        "warning": "\033[93m",
        "error": "\033[91m",
        "reset": "\033[0m"
    }
    color = colors.get(status, colors["reset"])
    sys.stdout.write(f"\r\033[K{color}✦ {msg}{colors['reset']}\n") # Ditambah \n biar log terminal lebih rapi ke bawah
    sys.stdout.flush()

def process_remove_bg(input_path, output_path):
    try:
        if not PHOTOROOM_API_KEY:
            raise ValueError("PHOTOROOM_API_KEY belum diisi di file .env!")

        # Mendukung fitur Multi-Key
        api_keys = [k.strip() for k in PHOTOROOM_API_KEY.split(",") if k.strip()]
        
        with open(input_path, "rb") as f:
            image_bytes = f.read()

        for index, current_key in enumerate(api_keys):
            try:
                if len(api_keys) > 1:
                    update_console(f"Mengirim foto ke Photoroom API (Kunci {index + 1}/{len(api_keys)})...", "info")
                else:
                    update_console("Mengirim foto ke Photoroom API...", "info")
                
                headers = {"x-api-key": current_key}
                files = {"image_file": (os.path.basename(input_path), image_bytes, "image/jpeg")}

                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        "https://sdk.photoroom.com/v1/segment",
                        headers=headers,
                        files=files
                    )

                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    update_console("Proses Remove BG Sukses! Hasil Premium Photoroom.", "success")
                    return output_path
                elif response.status_code in [402, 403, 429]:
                    update_console(f"Kunci ke-{index + 1} Limit/Habis. Cek kunci berikutnya...", "warning")
                    continue
                else:
                    raise Exception(f"API Error ({response.status_code}): {response.text}")
            except Exception as e:
                if index == len(api_keys) - 1:
                    raise e
                else:
                    continue
        raise Exception("LIMIT_HABIS")
    except Exception as e:
        update_console(f"Error Remove BG Photoroom: {e}", "error")
        raise e

# ==========================================
# [AREA BAWAH] : KAMAR BARU (FUNGSI UPSCALE CLOUDINARY)
# ==========================================
def upscale_cloudinary_real(input_path: str) -> str:
    """Mesin HD Khusus Foto Real/Wajah (Cloudinary)"""
    try:
        update_console("Mengirim foto real ke Cloudinary untuk di-HD-kan...", "info")
        upload_result = cloudinary.uploader.upload(input_path)
        raw_url = upload_result.get("secure_url")
        
        # e_improve: auto-enhance resmi Cloudinary + c_scale,w_2.0: perbesar 2x
        hd_url = raw_url.replace("/upload/", "/upload/e_improve/c_scale,w_2.0/")
        
        update_console("Proses HD Real Foto Sukses!", "success")
        return hd_url
    except Exception as e:
        update_console(f"Error Cloudinary (Real): {e}", "error")
        return None

def upscale_cloudinary_anime(input_path: str) -> str:
    """Mesin HD Khusus Anime/Art (Cloudinary)"""
    try:
        update_console("Mengirim gambar anime ke Cloudinary untuk di-HD-kan...", "info")
        upload_result = cloudinary.uploader.upload(input_path)
        raw_url = upload_result.get("secure_url")
        
        # Perbesar 2x lipat tanpa filter eksperimental yang bikin error 400
        hd_url = raw_url.replace("/upload/", "/upload/c_scale,w_2.0/")
        
        update_console("Proses HD Anime Sukses!", "success")
        return hd_url
    except Exception as e:
        update_console(f"Error Cloudinary (Anime): {e}", "error")
        return None