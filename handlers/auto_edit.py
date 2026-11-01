import urllib.parse
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from tools.auto_edit_engine import run_auto_edit_pipeline
from config import VIP_IDS, OWNER_USERNAMES

# ==========================================
# 1. PINTU MASUK & GATEKEEPER VIP
# ==========================================
async def handle_autoedit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if user_id not in VIP_IDS:
        pesan_tanya = "Halo bos! Gua tertarik mau upgrade VIP Kiro Bot nih biar bisa pake pake fitur Auto Edit Affiliate. Gimana caranya?"
        pesan_url = urllib.parse.quote(pesan_tanya)
        
        keyboard = []
        daftar_owner = OWNER_USERNAMES if OWNER_USERNAMES else ["username_iky_cadangan"] 
        
        for idx, owner in enumerate(daftar_owner):
            owner_bersih = owner.replace('@', '').strip()
            link_tele = f"https://t.me/{owner_bersih}?text={pesan_url}"
            nama_admin = "Iky" if idx == 0 else f"Admin {idx+1}"
            keyboard.append([InlineKeyboardButton(f"👑 Chat {nama_admin} (Upgrade VIP)", url=link_tele)])
            
        await query.message.edit_text(
            "Wah, sori banget nih! 😅\n\n"
            "Fitur **🔥 Auto Edit Affiliate** butuh tenaga server yang lumayan gede buat ngerender, jadi buat sekarang cuma bisa diakses eksklusif sama member **VIP**.\n\n"
            "Langganan VIP harganya terjangkau kok dan lu bisa nikmatin SEMUA fitur bot tanpa limit! Tertarik naikin omset affiliate? Langsung chat admin di bawah ya 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    context.user_data['waiting_for_autoedit_input'] = True
    await query.message.edit_text(
        "👑 **Selamat datang Tuan VIP!**\n\n"
        "Silakan kirimkan **Video mentahan** ATAU **Link TikTok** yang mau lu edit otomatis jadi konten affiliate.\n"
        "*(Kiro tunggu bahan-bahannya di sini ya!)*",
        parse_mode="Markdown"
    )

# ==========================================
# 2. INTERCEPTOR PENERIMA SEMUA BAHAN BAKU
# ==========================================
async def handle_autoedit_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # [A] Nangkap Video / Link TikTok Utama
    if context.user_data.get('waiting_for_autoedit_input'):
        if update.message.video or update.message.document:
            context.user_data['aedit_type'] = 'video'
            context.user_data['aedit_file_id'] = update.message.video.file_id if update.message.video else update.message.document.file_id
        elif update.message.text:
            context.user_data['aedit_type'] = 'link'
            context.user_data['aedit_link'] = update.message.text
        else:
            await update.message.reply_text("Kirimnya bentuk Video atau Link TikTok ya, Ky! Format lain belum disupport.")
            return

        context.user_data.pop('waiting_for_autoedit_input', None)
        
        # Default Toggle 7 Senjata (Zoom, LUT, Flip otomatis nyala duluan)
        context.user_data['toggle_flip'] = True
        context.user_data['toggle_lut'] = True
        context.user_data['toggle_jumpcut'] = False
        context.user_data['toggle_zoomin'] = True 
        context.user_data['toggle_speedup'] = False
        context.user_data['toggle_mute'] = False
        context.user_data['toggle_vo'] = False

        await show_autoedit_menu(update, context, is_new_message=True)
        return

    # [B] Nangkap Voice Over
    if context.user_data.get('waiting_for_aedit_vo'):
        if update.message.voice or update.message.audio:
            context.user_data['aedit_vo_id'] = update.message.voice.file_id if update.message.voice else update.message.audio.file_id
            context.user_data.pop('waiting_for_aedit_vo', None)
            await update.message.reply_text("✅ Voice Over diterima!")
            await check_missing_materials(update, context, is_new_message=True)
        else:
            await update.message.reply_text("Kirim file Audio atau Voice Note (VN) ya, jangan teks!")
        return

# ==========================================
# 3. PENGECEK BAHAN BAKU (TUKANG SORTIR)
# ==========================================
async def check_missing_materials(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_message=False):
    query = update.callback_query

    # Cek VO doang, fitur teks berita udah musnah
    if context.user_data.get('toggle_vo') and not context.user_data.get('aedit_vo_id'):
        context.user_data['waiting_for_aedit_vo'] = True
        teks = "🎙️ Lu mencentang fitur **Ganti Voice Over**.\n\nSilakan kirim file Audio / Voice Note (VN) lu sekarang!"
        if query: await query.message.edit_text(teks, parse_mode="Markdown")
        else: await update.message.reply_text(teks, parse_mode="Markdown")
        return

    # Kalau lolos semua (bahan komplit)
    pesan_sukses = "🔥 **Bahan lengkap! Memanaskan mesin Kiro...**"
    
    if query:
        msg_target = await query.message.edit_text(pesan_sukses, parse_mode="Markdown")
    else:
        msg_target = await update.message.reply_text(pesan_sukses, parse_mode="Markdown")

    # Jalankan Dapur Rekaman tanpa nge-freeze bot (Async Task)
    asyncio.create_task(run_auto_edit_pipeline(update, context, msg_target))

# ==========================================
# 4. TAMPILAN MENU INTERAKTIF (TOGGLE)
# ==========================================
async def show_autoedit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_message=False):
    toggles = context.user_data

    def get_btn(key, name):
        status = "✅" if toggles.get(key) else "❌"
        return InlineKeyboardButton(f"{status} {name}", callback_data=f"aedit_toggle_{key}")

    keyboard = [
        [get_btn('toggle_flip', 'Flip Video'), get_btn('toggle_lut', 'Color LUT')],
        [get_btn('toggle_jumpcut', 'Jump Cut Acak'), get_btn('toggle_zoomin', 'Zoom In 110%')],
        [get_btn('toggle_speedup', 'Speed Up 5%'), get_btn('toggle_mute', 'Mute Video')],
        [get_btn('toggle_vo', 'Ganti Voice Over')],
        [InlineKeyboardButton("🚀 LANJUT PROSES KONTEN", callback_data="aedit_process")]
    ]
    
    text = (
        "🎥 **Bahan konten udah Kiro terima!**\n\n"
        "Pilih 7 senjata anti-copyright lu di bawah ini (✅ nyala / ❌ mati).\n\n"
        "Kalo udah yakin sama racikannya, langsung gass klik **🚀 LANJUT PROSES**."
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_new_message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ==========================================
# 5. SAKLAR PENGGANTI STATUS TOGGLE
# ==========================================
async def handle_autoedit_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("aedit_toggle_"):
        key = data.replace("aedit_toggle_", "")
        
        # IMPROVISASI OTOMATIS: Biar user gak pusing, Mute & VO gak bisa nyala barengan
        is_currently_false = not context.user_data.get(key, False)
        
        if key == 'toggle_vo' and is_currently_false:
            context.user_data['toggle_mute'] = False # Kalo VO nyala, Mute otomatis mati
        elif key == 'toggle_mute' and is_currently_false:
            context.user_data['toggle_vo'] = False # Kalo Mute nyala, VO otomatis mati
            context.user_data.pop('aedit_vo_id', None) # Buang history file VN kalo ada

        context.user_data[key] = not context.user_data.get(key, False)
        await show_autoedit_menu(update, context, is_new_message=False)
        
    elif data == "aedit_process":
        await check_missing_materials(update, context)