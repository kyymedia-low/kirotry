import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import BadRequest

# Import konfigurasi dan mesin yang udah kita buat
from config import CHANNEL_USERNAME
from tools.limiter import check_limit, increment_limit

# [ PERUBAHAN IMPORT ]: Panggil 2 mesin Cloudinary yang baru
from tools.photo_tools.engine import upscale_cloudinary_real, upscale_cloudinary_anime

# ==========================================
# STAGE 1: PINTU MASUK DARI MENU INLINE
# ==========================================
async def handle_hd_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangkap klik tombol '🪄 HD-in Foto / Upscale' dari menu utama."""
    query = update.callback_query
    await query.answer()

    # Tandai bahwa user ini lagi mau ngirim foto buat di-HD-in
    context.user_data['waiting_for_hd_photo'] = True

    await query.message.reply_text(
        "📸 **Mode Upscale / HD-in Foto Aktif!**\n\n"
        "Silakan kirimkan foto yang mau lu bikin jernih ke sini.\n"
        "*(Kirim sebagai foto biasa ya, jangan sebagai file/dokumen)*",
        parse_mode="Markdown"
    )

# ==========================================
# STAGE 2 & 3: GATEKEEPER & TERIMA FOTO
# ==========================================
async def handle_hd_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangkap foto yang dikirim user, cek Force Sub, cek Limit, dan tawarkan Engine."""
    user_id = update.effective_user.id

    # Pastikan user emang lagi di jalur HD-in Foto (bukan lagi iseng ngirim foto)
    if not context.user_data.get('waiting_for_hd_photo'):
        return

    # --- 1. GATEKEEPER: CEK FORCE SUBSCRIBE ---
    if CHANNEL_USERNAME:
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
            if member.status in ['left', 'kicked']:
                keyboard = [[InlineKeyboardButton("📢 Join Saluran", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]]
                await update.message.reply_text(
                    "Eits, tahan dulu bosku! 🛑\n\n"
                    "Lu wajib gabung saluran Telegram kita dulu buat bisa pake fitur premium ini.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
        except BadRequest:
            # Error terjadi jika Bot belum diangkat jadi Admin di Channel tersebut
            print("[WARNING] Bot tidak bisa mengecek member. Pastikan Kiro Bot jadi Admin di Channel!")
            pass 

    # --- 2. GATEKEEPER: CEK LIMIT HARIAN ---
    is_allowed, sisa_kuota = check_limit(user_id, "upscale", max_limit=3)
    if not is_allowed:
        keyboard = [
            [InlineKeyboardButton("☕ Upgrade VIP (Sociabuzz)", url="https://sociabuzz.com/kyymedia/tribe")],
            [InlineKeyboardButton("👨‍💻 Hubungi Owner", url="https://t.me/iky_username")] # Ganti username lu ntar
        ]
        await update.message.reply_text(
            "Yah, kuota gratis HD-in foto lu hari ini udah abis (Limit: 3x/hari). 😭\n\n"
            "Tunggu reset jam 12 malem nanti, atau **Upgrade ke VIP** buat dapetin akses *Unlimited* tanpa batas!\n\n"
            "Dukung Iky patungan server lewat Sociabuzz 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        # Hapus state biar dia nggak nyangkut
        context.user_data.pop('waiting_for_hd_photo', None)
        return

    # --- 3. PROSES DOWNLOAD FOTO ---
    proses_msg = await update.message.reply_text("⏳ Bentar, lagi nge-download foto lu...")
    
    photo = update.message.photo[-1] # Ambil resolusi paling tinggi dari Telegram
    file = await context.bot.get_file(photo.file_id)
    
    # Bikin folder temp kalau belum ada
    if not os.path.exists("temp"):
        os.makedirs("temp")
    
    temp_path = f"temp/hd_{user_id}.jpg"
    await file.download_to_drive(temp_path)

    # Simpan lokasi file sementara buat dieksekusi di Stage 4
    context.user_data['temp_hd_path'] = temp_path
    
    # Hapus pesan loading
    await proses_msg.delete()

    # --- 4. PEMILIHAN ENGINE (Cloudinary Real vs Cloudinary Anime) ---
    keyboard = [
        [InlineKeyboardButton("📸 Foto Asli (Wajah/Real)", callback_data="hd_engine_cloudinary")],
        [InlineKeyboardButton("🎨 Gambar Anime / Kartun", callback_data="hd_engine_bigjpg")] # Callback tetep bigjpg biar gak usah ubah main.py
    ]
    await update.message.reply_text(
        "Fotonya udah Kiro terima! Sisa kuota lu hari ini: **{}x**\n\n"
        "Sekarang pilih tipe foto lu biar AI-nya nggak salah ngasih filter:\n\n"
        "📸 **Foto Asli:** Resolusi 2x + Pertajam Wajah & Pemandangan\n"
        "🎨 **Anime/Kartun:** Resolusi 2x + Haluskan Piksel Pecah + Saturasi Warna".format(sisa_kuota),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==========================================
# STAGE 4 & 5: EKSEKUSI MESIN & PENGIRIMAN HASIL
# ==========================================
async def handle_hd_engine_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengeksekusi foto berdasarkan mesin yang dipilih (Cloudinary Real / Cloudinary Anime)."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    pilihan_mesin = query.data

    temp_path = context.user_data.get('temp_hd_path')
    if not temp_path or not os.path.exists(temp_path):
        await query.message.edit_text("Sesi kedaluwarsa atau foto hilang. Silakan kirim ulang fotonya ya!")
        context.user_data.pop('waiting_for_hd_photo', None)
        return

    await query.message.edit_text("🪄 **Magic sedang bekerja...**\nJangan ngirim apa-apa dulu ya, prosesnya bisa makan waktu 10-30 detik tergantung server.", parse_mode="Markdown")

    hasil_url = None

    # [ PERUBAHAN EKSEKUSI ]: Keduanya sekarang pakai mesin Cloudinary yang ringan
    if pilihan_mesin == "hd_engine_cloudinary":
        hasil_url = upscale_cloudinary_real(temp_path)

    elif pilihan_mesin == "hd_engine_bigjpg":
        # Namanya tetep hd_engine_bigjpg dari callback, tapi yang dieksekusi mesin Cloudinary Anime!
        hasil_url = upscale_cloudinary_anime(temp_path)

    # --- PENGIRIMAN HASIL ---
    if hasil_url:
        caption_teks = (
            "✨ **TADAA! Foto lu udah jadi HD!** ✨\n\n"
            "Gimana? Lebih tajam dari omongan tetangga kan? 😎\n\n"
            "☕ *Kalo ngerasa Kiro ngebantu banget, bolehlah traktir Iky kopi dikit di Sociabuzz biar Kiro tetep idup!*\n"
            "👉 [Klik di sini buat dukung Kiro!](https://sociabuzz.com/kyymedia/tribe)"
        )
        try:
            # Kirim balik sebagai foto (Telegram otomatis nampilin gambarnya dari URL)
            await context.bot.send_photo(
                chat_id=user_id,
                photo=hasil_url,
                caption=caption_teks,
                parse_mode="Markdown"
            )
            # Karena sukses, kurangi kuota limit user
            increment_limit(user_id, "upscale")
            await query.message.delete() # Hapus pesan loading
        except Exception as e:
            await query.message.edit_text(f"Waduh, gagal ngirim foto ke lu: {e}")
    else:
        await query.message.edit_text("Yah, server AI-nya lagi sibuk atau error nih. Coba lagi nanti ya, Ky!")

    # --- BERSIH-BERSIH (CLEANUP) ---
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except:
        pass

    # Reset status user biar bisa milih menu lain
    context.user_data.pop('waiting_for_hd_photo', None)
    context.user_data.pop('temp_hd_path', None)