from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import CHANNEL_USERNAME
from handlers.remove_bg import is_user_subscribed
from tools.random_tools.smart_budget import parse_salary, parse_percentage, generate_budget_report

async def start_smart_budget_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    # Wajib Join Channel (Force Subscribe pakai modul dari remove_bg)
    is_subscribed = await is_user_subscribed(context.bot, user_id)
    if not is_subscribed:
        channel_url = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        keyboard = [
            [InlineKeyboardButton("📢 Gabung Channel (Wajib)", url=channel_url)],
            [InlineKeyboardButton("🔄 Cek Status / Coba Lagi", callback_data="budget_start")]
        ]
        await query.edit_message_text(
            "🔒 **Akses Terkunci**\n\nFitur ini 100% Gratis, tapi kamu **wajib bergabung** ke channel Telegram kami terlebih dahulu.",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        return

    # Jika lolos, mulai minta input gaji
    context.user_data['budget_step'] = 'waiting_salary'
    await query.edit_message_text(
        "💼 **Smart Budgeting AI**\n\n"
        "Berapa total gaji atau pendapatan kamu bulan ini?\n\n"
        "*(Ketik angkanya saja, contoh: 3000000 atau 3.5jt)*",
        parse_mode="Markdown"
    )

async def handle_budget_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('budget_step')
    text = update.message.text

    if step == 'waiting_salary':
        salary = parse_salary(text)
        if not salary:
            await update.message.reply_text("❌ Format gaji tidak valid. Coba ketik angkanya saja (contoh: 3000000 atau 3jt).")
            return
        
        context.user_data['budget_salary'] = salary
        context.user_data['budget_step'] = 'waiting_percentage'
        
        # Pilihan Preset Cepat
        keyboard = [
            [InlineKeyboardButton("50/30/20 (Standar)", callback_data="budget_preset_50_30_20")],
            [InlineKeyboardButton("70/20/10 (Hemat/Agamis)", callback_data="budget_preset_70_20_10")],
            [InlineKeyboardButton("80/20 (Tabungan Ekstra)", callback_data="budget_preset_80_20")],
            [InlineKeyboardButton("✍️ Input Manual", callback_data="budget_preset_manual")]
        ]
        
        # Format angka biar ada pemisah titiknya
        gaji_format = f"{salary:,.0f}".replace(",", ".")
        await update.message.reply_text(
            f"✅ Gaji dicatat: **Rp {gaji_format}**\n\n"
            "Sekarang, pilih persentase alokasi yang kamu inginkan, atau input manual persentase sendiri:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif step == 'waiting_percentage_manual':
        allocations, error = parse_percentage(text)
        if error:
            await update.message.reply_text(f"❌ {error}\n\nCoba ketik ulang persentasenya.")
            return
        
        salary = context.user_data.get('budget_salary')
        report = generate_budget_report(salary, allocations)
        
        # --- PENAMBAHAN PESAN DONASI (MANUAL) ---
        pesan_donasi = "\n\n💡 *Kalo lu ngerasa kebantu ngatur duit di sini, sisihin dikit dong buat traktir kopi server Kiro 🚀:*\n👉 https://sociabuzz.com/kyymedia/tribe"
        await update.message.reply_text(f"```text\n{report}\n```{pesan_donasi}", parse_mode="Markdown")
        
        # Reset memori setelah selesai
        context.user_data.pop('budget_step', None)
        context.user_data.pop('budget_salary', None)

async def handle_budget_preset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # Jika user pilih input manual
    if data == "budget_preset_manual":
        context.user_data['budget_step'] = 'waiting_percentage_manual'
        await query.edit_message_text(
            "✍️ **Input Manual Persentase**\n\n"
            "Ketik alokasi gaji kamu. **Contoh pengetikan yang benar:**\n\n"
            "• _Format Angka Saja:_\n"
            "`50, 30, 20`\n\n"
            "• _Format Kategori + Persen:_\n"
            "`Kebutuhan: 50%, Tabungan: 30%, Main: 20%`\n\n"
            "*(Pastikan total angkanya pas 100% ya!)*",
            parse_mode="Markdown"
        )
        return
    
    # Jika user klik preset cepat
    salary = context.user_data.get('budget_salary')
    if not salary:
        await query.edit_message_text("❌ Data gaji hilang. Silakan ulangi dari awal menu.")
        context.user_data.pop('budget_step', None)
        return

    if data == "budget_preset_50_30_20":
        alloc = {"Kebutuhan Pokok": 50, "Keinginan/Hiburan": 30, "Tabungan/Investasi": 20}
    elif data == "budget_preset_70_20_10":
        alloc = {"Kebutuhan Pokok": 70, "Tabungan/Investasi": 20, "Sedekah/Lainnya": 10}
    elif data == "budget_preset_80_20":
        alloc = {"Kebutuhan Pokok": 80, "Tabungan/Investasi": 20}
        
    report = generate_budget_report(salary, alloc)
    
    # --- PENAMBAHAN PESAN DONASI (PRESET) ---
    pesan_donasi = "\n\n💡 *Kalo lu ngerasa kebantu ngatur duit di sini, sisihin dikit dong buat traktir kopi server Kiro 🚀:*\n👉 https://sociabuzz.com/kyymedia/tribe"
    await query.edit_message_text(f"```text\n{report}\n```{pesan_donasi}", parse_mode="Markdown")
    
    context.user_data.pop('budget_step', None)
    context.user_data.pop('budget_salary', None)