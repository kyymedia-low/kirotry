import os
import sys
import time

def update_console(msg, status="info"):
    colors = {
        "info": "\033[96m",
        "success": "\033[92m",
        "warning": "\033[93m",
        "error": "\033[91m",
        "reset": "\033[0m"
    }
    color = colors.get(status, colors["reset"])
    sys.stdout.write(f"\r\033[K{color}✦ {msg}{colors['reset']}")
    sys.stdout.flush()

def cleanup_photo_temp(file_paths):
    for path in file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                filename = os.path.basename(path)
                update_console(f"Cleaner: Berhasil menghapus {filename}", "success")
                time.sleep(0.5) 
            except Exception as e:
                update_console(f"Cleaner Error: Gagal menghapus {path} - {e}", "error")
                time.sleep(1.5)
                
    # Hapus jejak teks di terminal agar bersih total
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()