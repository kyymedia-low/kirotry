import logging
import asyncio
import sys
import warnings

# Sembunyikan pesan DeprecationWarning dari asyncio di Windows
warnings.filterwarnings("ignore", category=DeprecationWarning)

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.request import HTTPXRequest
from config import BOT_TOKEN
from handlers.menu import show_main_menu, handle_menu_click
from handlers.auto_subtitle import (
    start_subtitle_flow,
    handle_video_upload,
    handle_style_selection,
    handle_color_selection
)
from handlers.remove_bg import (
    start_remove_bg_flow,
    handle_photo_upload
)

# --- IMPORT RANDOM TOOLS (SMART BUDGETING) ---
from handlers.random_tools import start_smart_budget_flow, handle_budget_preset

# --- IMPORT BARU MENU BANTUAN (CS) ---
from handlers.help_cs import handle_help_callbacks

# ==========================================
# [ TAMBAHAN IMPORT: UPSCALE / HD FOTO ]
# ==========================================
from handlers.upscale_photo import (
    handle_hd_menu_start,
    handle_hd_photo_input,
    handle_hd_engine_selection
)

from handlers.auto_edit import (
    handle_autoedit_start,
    handle_autoedit_inputs,
    handle_autoedit_toggle
)

# Logging Setup: Set level ke WARNING supaya info spam dari library tidak muncul
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING 
)

# Sembunyikan log spesifik dari library bawaan biar terminal benar-benar bersih
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("faster_whisper").setLevel(logging.WARNING)

def print_banner():
    """Menampilkan banner estetik saat bot mulai berjalan"""
    banner = """\033[96m
╔══════════════════════════════════════╗
║     KIRO BOT IS ONLINE & STANDBY     ║
╚══════════════════════════════════════╝\033[0m
"""
    sys.stdout.write(banner)
    sys.stdout.flush()

def main():
    # Mengatur timeout global hingga 120 detik agar koneksi tidak mudah putus
    request_config = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=120.0,
        write_timeout=120.0,
        pool_timeout=60.0
    )

    app = ApplicationBuilder().token(BOT_TOKEN).request(request_config).build()

    # Command Handler (/start)
    app.add_handler(CommandHandler("start", show_main_menu))

    # Callback Query Handlers (Untuk Tombol Inline Auto Subtitle)
    app.add_handler(CallbackQueryHandler(start_subtitle_flow, pattern="^sub_start$"))
    app.add_handler(CallbackQueryHandler(handle_style_selection, pattern="^set_style_"))
    app.add_handler(CallbackQueryHandler(handle_color_selection, pattern="^set_color_"))

    # Callback Query Handlers (Remove BG)
    app.add_handler(CallbackQueryHandler(start_remove_bg_flow, pattern="^rmbg_start$"))
    app.add_handler(CallbackQueryHandler(start_remove_bg_flow, pattern="^rmbg_check_sub$")) 
    
    # Callback Query Handlers (Smart Budgeting)
    app.add_handler(CallbackQueryHandler(start_smart_budget_flow, pattern="^budget_start$"))
    app.add_handler(CallbackQueryHandler(handle_budget_preset, pattern="^budget_preset_"))

    # --- CALLBACK QUERY BARU (MENU BANTUAN CS) ---
    app.add_handler(CallbackQueryHandler(handle_help_callbacks, pattern="^help_"))

    # ==========================================
    # [ TAMBAHAN HANDLER TOMBOL: UPSCALE FOTO ]
    # ==========================================
    app.add_handler(CallbackQueryHandler(handle_hd_menu_start, pattern="^hd_menu_start$"))
    app.add_handler(CallbackQueryHandler(handle_hd_engine_selection, pattern="^hd_engine_"))

    # Message Handlers Utama (Grup Default / 0)
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video_upload))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo_upload)) # Penangkap Foto Remove BG
    
    # ==========================================
    # [ TAMBAHAN HANDLER FOTO: UPSCALE FOTO ]
    # (Pakai group=1 biar gak tabrakan sama Remove BG)
    # ==========================================
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_hd_photo_input), group=1)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_click))

    # ==========================================
    # [ TAMBAHAN HANDLER: AUTO EDIT AFFILIATE ]
    # ==========================================
    app.add_handler(CallbackQueryHandler(handle_autoedit_start, pattern="^autoedit_start$"))
    app.add_handler(CallbackQueryHandler(handle_autoedit_toggle, pattern="^aedit_toggle_"))
    app.add_handler(CallbackQueryHandler(handle_autoedit_toggle, pattern="^aedit_process$"))
    
    # Penangkap file/link khusus Auto Edit (wajib group=2 biar gak tabrakan sama RemoveBG/Upscale)
    # Penangkap bahan Auto Edit (Video, Teks, Audio, Voice)
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO | filters.TEXT | filters.VOICE | filters.AUDIO, handle_autoedit_inputs), group=2)

    # Panggil banner estetik
    print_banner()
    app.run_polling()

if __name__ == "__main__":
    # Mengatur event loop secara manual khusus untuk Python versi terbaru di Windows
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    main()