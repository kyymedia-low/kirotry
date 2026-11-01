from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import datetime, timezone, timedelta

# --- KONFIGURASI DATA OWNER & ADMIN ---
ADMIN_GROUP_ID = -1004493597594
OWNER_USERNAME = "kionlyy"

async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan menu Bantuan (CS) dengan Inline Keyboard."""
    keyboard = [
        [InlineKeyboardButton("🐛 Lapor Bug", callback_data="help_lapor_bug")],
        [InlineKeyboardButton("🤖 Info Kiro", callback_data="help_info_kiro")],
        [InlineKeyboardButton("☕ Request Tools (via Sociabuzz)", url="https://sociabuzz.com/kyymedia/tribe")],
        [InlineKeyboardButton("🌐 All Sosmed KyyMedia", callback_data="help_sosmed")],
        [InlineKeyboardButton("💼 Chat Owner (Collab)", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    pesan = "Ada yang bisa dibantu bro? Pilih menu di bawah yak, santai aja Kiro siap dengerin. 🛠️"
    
    if update.message:
        await update.message.reply_text(pesan, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(pesan, reply_markup=reply_markup)

async def handle_help_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani klik pada tombol-tombol di dalam menu Bantuan & Grup Admin."""
    query = update.callback_query
    data = query.data

    if data == "help_info_kiro":
        await query.answer()
        pesan_info = (
            "🤖 **Tentang Kiro Bot**\n\n"
            "Kiro ini asisten digital serba bisa yang dirakit khusus buat ngebantu produktivitas lu sehari-hari. "
            "Mulai dari bikin subtitle otomatis ala CapCut, ngehapus background foto pake AI, sampe ngatur alokasi gaji bulanan (Smart Budgeting).\n\n"
            "Simpel, sat-set, dan 100% gratis! Lu cuma perlu join channel kita sebagai tiket masuknya 🎫.\n\n"
            "*Created with ☕ by KyyMedia.*"
        )
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="help_back")]]
        await query.edit_message_text(pesan_info, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "help_sosmed":
        await query.answer()
        pesan_sosmed = (
            "🌐 **Ekosistem KyyMedia**\n\n"
            "Jangan lupa mampir & support KyyMedia di platform lain yak:\n"
            "📌 **Channel Telegram:** [Klik di sini](https://t.me/kyymediaupdate)\n"
            "📌 **Channel WA:** [Klik di sini](https://whatsapp.com/channel/0029VbDSrel2ER6b9D5jRx2c)\n"
            "📌 **YouTube:** [Klik di sini](https://youtube.com/@vanguardsminds?si=whqq3Bv9TSfJH7bZ)\n"
            "*(Sosmed lain *coming soon*)*"
        )
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="help_back")]]
        await query.edit_message_text(
            pesan_sosmed, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
   

    elif data == "help_lapor_bug":
        await query.answer()
        context.user_data['waiting_for_bug_report'] = True
        pesan_lapor = (
            "🐛 **Lapor Bug / Error**\n\n"
            "Kiro lagi ngadat di bagian mana nih? Ketik aja keluhan lu di bawah, "
            "nanti pesannya langsung diterbangin ke meja owner biar cepet difix 🛠️\n\n"
            "*(Ketik pesan lu sekarang...)*"
        )
        keyboard = [[InlineKeyboardButton("❌ Batal", callback_data="help_back")]]
        await query.edit_message_text(pesan_lapor, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "help_back":
        await query.answer()
        context.user_data.pop('waiting_for_bug_report', None)
        await show_help_menu(update, context)

    # --- LOGIKA TOMBOL "SUDAH DI-FIX" DI GRUP ADMIN ---
    elif data.startswith("help_fixbug_"):
        # Ambil ID user pelapor dari data callback (contoh data: help_fixbug_6828530851)
        pelapor_id = data.split("_")[2]
        
        # 1. Hapus Pesan Laporan di Grup
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Gagal menghapus pesan di grup: {e}")
            
        # 2. Kirim DM Notifikasi ke Pelapor
        pesan_notif = "✅ **Notifikasi Kiro Bot**\n\nHalo! Laporan bug yang lu kirim sebelumnya udah diperbaiki sama Owner ya. Makasih banget udah lapor dan bantu Kiro jadi lebih baik! 🚀"
        try:
            await context.bot.send_message(chat_id=pelapor_id, text=pesan_notif, parse_mode="Markdown")
        except Exception as e:
            print(f"Gagal mengirim DM ke user {pelapor_id} (Mungkin user memblokir bot): {e}")

        # Tampilkan pop-up notifikasi kecil di layar Admin
        await query.answer("Laporan berhasil dihapus & Pelapor telah dinotifikasi!", show_alert=False)

async def handle_bug_report_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangkap teks laporan bug dari user dan mem-forward ke Grup Admin."""
    if not context.user_data.get('waiting_for_bug_report'):
        return

    teks_laporan = update.message.text
    user_info = update.effective_user
    username_pengirim = f"@{user_info.username}" if user_info.username else user_info.first_name
    id_pengirim = user_info.id

    # Bikin format Waktu WIB (UTC+7)
    wib_timezone = timezone(timedelta(hours=7))
    waktu_sekarang = datetime.now(wib_timezone).strftime("%d %B %Y, %H:%M WIB")

    # Format pesan estetik buat di Grup Admin
    laporan_ke_admin = (
        f"🚨 **LAPORAN BUG BARU** 🚨\n\n"
        f"👤 **Dari:** {username_pengirim}\n"
        f"🆔 **ID User:** `{id_pengirim}`\n"
        f"📅 **Waktu:** {waktu_sekarang}\n\n"
        f"💬 **Pesan Laporan:**\n"
        f"_{teks_laporan}_"
    )

    # Tambahin tombol Fix di bawah pesan yang ke grup
    keyboard_admin = [
        [InlineKeyboardButton("✅ Sudah di-Fix (Hapus)", callback_data=f"help_fixbug_{id_pengirim}")]
    ]
    reply_markup_admin = InlineKeyboardMarkup(keyboard_admin)

    try:
        # Kirim laporan ke Grup Admin
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID, 
            text=laporan_ke_admin, 
            reply_markup=reply_markup_admin,
            parse_mode="Markdown"
        )
        
        # Balas ke user
        await update.message.reply_text("✅ Sip, laporan lu udah masuk bengkel KyyMedia! Nanti kalau udah fix bakal diinfoin ya. Thanks bro!")
    except Exception as e:
        print(f"Gagal ngirim laporan bug ke grup: {e}")
        await update.message.reply_text("❌ Waduh, sistem lagi sibuk nih. Coba laporin manual via Chat Owner ya.")
    
    # Hapus state setelah selesai
    context.user_data.pop('waiting_for_bug_report', None)