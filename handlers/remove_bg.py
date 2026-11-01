import os
import time
import uuid
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import VIP_IDS, CHANNEL_USERNAME
from tools.photo_tools.engine import process_remove_bg
from tools.photo_tools.cleaner import cleanup_photo_temp

TEMP_PHOTO_DIR = os.path.join(os.path.dirname(__file__), '..', 'tools', 'photo_tools', 'temp')

# Dictionary memori ringan untuk menyimpan waktu terakhir user (user_id: timestamp)
user_cooldowns = {}
COOLDOWN_SECONDS = 120  # Delay 2 menit (120 detik)

async def is_user_subscribed(bot, user_id):
    """Mengecek apakah user VIP atau sudah bergabung dengan channel."""
    # 1. Cek Jalur Tol (VIP)
    if user_id in VIP_IDS:
        return True
    
    # Jika channel tidak di-set di .env, loloskan semua
    if not CHANNEL_USERNAME:
        return True
        
    # 2. Cek keanggotaan Telegram Channel
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logging.warning(f"Gagal mengecek channel membership (Pastikan bot adalah Admin di Channel): {e}")
        return False

async def start_remove_bg_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback saat tombol 'Auto Remove BG' diklik."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # Cek Validasi Keanggotaan
    is_subscribed = await is_user_subscribed(context.bot, user_id)
    
    if not is_subscribed:
        channel_url = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        keyboard = [
            [InlineKeyboardButton("📢 Gabung Channel (Wajib)", url=channel_url)],
            [InlineKeyboardButton("🔄 Cek Status / Coba Lagi", callback_data="rmbg_check_sub")]
        ]
        await query.edit_message_text(
            "🔒 **Akses Terkunci**\n\n"
            "Fitur ini 100% Gratis! Tapi kamu **wajib bergabung** ke channel Telegram kami terlebih dahulu untuk menggunakannya.\n\n"
            "Silakan gabung lalu klik tombol 'Cek Status'.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    # Jika lolos validasi (VIP atau Subscribed)
    context.user_data['waiting_for_photo'] = True
    await query.edit_message_text(
        "✂️ **Auto Remove Background AI**\n\n"
        "Silakan **kirimkan foto** yang ingin dihapus background-nya!\n\n"
        "📌 *Tips: Kirim foto dengan resolusi baik agar hasil AI lebih rapi.*",
        parse_mode="Markdown"
    )

async def handle_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menerima dan memproses foto yang dikirim user."""
    if not context.user_data.get('waiting_for_photo'):
        return
        
    user_id = update.effective_user.id
    current_time = time.time()

    # --- PENGECEKAN COOLDOWN (ANTI-SPAM) ---
    # Jika bukan VIP, cek apakah ada cooldown yang berjalan
    if user_id not in VIP_IDS:
        last_used = user_cooldowns.get(user_id, 0)
        selisih_waktu = current_time - last_used
        
        if selisih_waktu < COOLDOWN_SECONDS:
            sisa_waktu = int(COOLDOWN_SECONDS - selisih_waktu)
            menit = sisa_waktu // 60
            detik = sisa_waktu % 60
            
            waktu_teks = f"{menit} menit {detik} detik" if menit > 0 else f"{detik} detik"
            
            await update.message.reply_text(
                f"⏳ **Sabar Dulu, Bang!**\n\n"
                f"Tunggu **{waktu_teks}** lagi sebelum mengirim foto baru.\n\n"
                f"*Masih Antri Hehe :)*",
                parse_mode="Markdown"
            )
            # Menghapus state menunggu foto agar user harus pencet menu ulang
            context.user_data.clear() 
            return

    # Memastikan user mengirim foto (ambil resolusi tertinggi [-1]) atau sebagai dokumen
    photo_file = None
    if update.message.photo:
        photo_file = update.message.photo[-1]
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        photo_file = update.message.document
    else:
        return

    os.makedirs(TEMP_PHOTO_DIR, exist_ok=True)
    pesan_proses = await update.message.reply_text("📥 Sedang mengunduh foto...")
    
    unique_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(TEMP_PHOTO_DIR, f"input_bg_{unique_id}.jpg")
    output_path = os.path.join(TEMP_PHOTO_DIR, f"output_bg_{unique_id}.png")
    
    try:
        # Download file
        file_obj = await context.bot.get_file(photo_file.file_id, read_timeout=120)
        await file_obj.download_to_drive(input_path, read_timeout=120)
        
        await pesan_proses.edit_text("⚡ AI sedang memotong background dengan presisi tinggi...\n*Tunggu sebentar ya!*", parse_mode="Markdown")
        
        # Eksekusi AI
        process_remove_bg(input_path, output_path)
        
        # Kirim hasil
        with open(output_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename="KiroBot_NoBG.png",
                caption=(
                    "🎉 **Selesai!**\nIni hasil foto transparan kamu (Format PNG).\n\n"
                    "💡 *Btw, bot ini jalan pake modal patungan server. Kalo lu ngerasa kebantu, gas nyawer kopi dikit biar Kiro ngga gampang tepar ☕:*\n"
                    "👉 https://sociabuzz.com/kyymedia/tribe"
                ),
                parse_mode="Markdown",
                read_timeout=120,
                write_timeout=120
            )
            
        await pesan_proses.delete()
        
        # --- UPDATE COOLDOWN JIKA SUKSES ---
        if user_id not in VIP_IDS:
            user_cooldowns[user_id] = time.time()
        
    except Exception as e:
        logging.error(f"Error Auto Remove BG: {e}")
        await pesan_proses.edit_text("❌ Terjadi kesalahan teknis saat memproses foto. Pastikan format foto benar atau coba lagi nanti.")
        
    finally:
        cleanup_photo_temp([input_path, output_path])
        context.user_data.clear()