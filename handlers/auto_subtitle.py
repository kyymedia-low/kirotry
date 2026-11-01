import os
import uuid
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from tools.auto_subtitle.engine import process_video_subtitle
from tools.auto_subtitle.cleaner import cleanup_temp_files

# --- IMPORT TAMBAHAN UNTUK SECURITY (FORCE SUBSCRIBE) ---
from config import CHANNEL_USERNAME
from handlers.remove_bg import is_user_subscribed

TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'tools', 'auto_subtitle', 'temp')

async def start_subtitle_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback saat tombol 'Auto Subtitle' diklik."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    # --- PENGECEKAN KEANGGOTAAN CHANNEL ---
    is_subscribed = await is_user_subscribed(context.bot, user_id)
    if not is_subscribed:
        channel_url = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        keyboard = [
            [InlineKeyboardButton("📢 Gabung Channel (Wajib)", url=channel_url)],
            [InlineKeyboardButton("🔄 Cek Status / Coba Lagi", callback_data="sub_start")]
        ]
        await query.edit_message_text(
            "🔒 **Akses Terkunci**\n\n"
            "Fitur ini 100% Gratis! Tapi kamu **wajib bergabung** ke channel Telegram kami terlebih dahulu untuk menggunakannya.\n\n"
            "Silakan gabung lalu klik tombol 'Cek Status'.",
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown"
        )
        return
    
    # Tandai user sedang dalam mode menunggu kiriman video (Jika lolos)
    context.user_data['waiting_for_video'] = True
    
    await query.edit_message_text(
        "🎬 **Auto Subtitle ala CapCut**\n\n"
        "Silakan **kirimkan video** yang ingin kamu beri subtitle otomatis!\n\n"
        "📌 *Ketentuan: Durasi maksimal 120 detik (2 menit).*",
        parse_mode="Markdown"
    )

async def handle_video_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menerima dan memproses video yang dikirim user."""
    # Pastikan user memang sedang dalam alur Auto Subtitle
    if not context.user_data.get('waiting_for_video'):
        return

    video = update.message.video or update.message.document
    if not video:
        return

    # 1. Cek Durasi (Maksimal 120 Detik)
    duration = getattr(video, 'duration', 0)
    if duration > 120:
        await update.message.reply_text("❌ **Video Terlalu Panjang!**\nDurasi maksimal video adalah 120 detik (2 menit). Silakan potong video kamu terlebih dahulu.", parse_mode="Markdown")
        return

    # Buat direktori temp jika belum ada
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    pesan_download = await update.message.reply_text("📥 Menyiapkan video...")
    
    # 2. Download Video ke folder temp (ditambah timeout 120 detik)
    unique_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(TEMP_DIR, f"input_{unique_id}.mp4")
    
    file_obj = await context.bot.get_file(video.file_id, read_timeout=120)
    await file_obj.download_to_drive(input_path, read_timeout=120)
    
    # Simpan path file di session user
    context.user_data['subtitle_input_path'] = input_path
    context.user_data['waiting_for_video'] = False
    
    # 3. Tampilkan Pilihan Style
    keyboard = [
        [InlineKeyboardButton("✨ Style 1 (Pop Standard)", callback_data="set_style_style1")],
        [InlineKeyboardButton("📦 Style 2 (Boxed Shadow)", callback_data="set_style_style2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await pesan_download.edit_text(
        "✅ **Video Berhasil Diunggah!**\n\nPilih **Style Animasi Subtitle** yang kamu inginkan:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menyimpan pilihan style dan menampilkan pilihan warna."""
    query = update.callback_query
    await query.answer()
    
    selected_style = query.data.replace("set_style_", "")
    context.user_data['subtitle_style'] = selected_style
    
    # Tampilkan Pilihan Warna Highlight
    keyboard = [
        [
            InlineKeyboardButton("💛 Kuning", callback_data="set_color_kuning"),
            InlineKeyboardButton("🩵 Cyan", callback_data="set_color_cyan")
        ],
        [
            InlineKeyboardButton("💚 Hijau", callback_data="set_color_hijau"),
            InlineKeyboardButton("❤️ Merah", callback_data="set_color_merah")
        ],
        [
            InlineKeyboardButton("🤍 Putih", callback_data="set_color_putih")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎨 **Pilih Warna Highlight Kata:**\nKata yang sedang diucapkan akan menyala dengan warna pilihanmu.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_color_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menyimpan warna dan mengeksekusi AI & FFmpeg Render."""
    query = update.callback_query
    await query.answer()
    
    selected_color = query.data.replace("set_color_", "")
    style = context.user_data.get('subtitle_style', 'style1')
    input_path = context.user_data.get('subtitle_input_path')
    
    if not input_path or not os.path.exists(input_path):
        await query.edit_message_text("❌ File video tidak ditemukan / telah kadaluarsa. Silakan coba lagi.")
        return

    await query.edit_message_text("⚡ **Sedang Memproses Subtitle AI & Render HD...**\nMohon tunggu 1-3 menit (tergantung durasi video).", parse_mode="Markdown")
    
    unique_id = os.path.basename(input_path).replace("input_", "").replace(".mp4", "")
    output_path = os.path.join(TEMP_DIR, f"output_{unique_id}.mp4")
    
    try:
        # Eksekusi Mesin Auto Subtitle
        process_video_subtitle(
            input_video_path=input_path,
            output_video_path=output_path,
            style=style,
            color=selected_color
        )
        
        # Kirim Video HD ke User (ditambah read & write timeout 120 detik)
        with open(output_path, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=(
                    "🎉 **Auto Subtitle Berhasil Dipasang!**\nKualitas HD Near-Lossless.\n\n"
                    "💡 *Btw, render beginian itu berat cuy dan server Kiro idup dari patungan. Kalo hasil ini ngebantu lu, gas traktir kopi dikit biar Kiro ngga gampang tepar ☕:*\n"
                    "👉 https://sociabuzz.com/kyymedia/tribe"
                ),
                parse_mode="Markdown",
                read_timeout=120,
                write_timeout=120
            )
            
    except Exception as e:
        logging.error(f"Error pada handler auto subtitle: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Terjadi kesalahan teknis saat memproses video. Silakan coba lagi nanti."
        )
        
    finally:
        # Hapus file mentah dan file hasil di temp
        cleanup_temp_files([input_path, output_path])
        # Reset session user
        context.user_data.clear()