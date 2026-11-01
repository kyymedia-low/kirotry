from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            KeyboardButton("🎬 Editing & AI Video"),
            KeyboardButton("📥 Downloader Media")
        ],
        [
            KeyboardButton("🖼️ Tools Foto & Gambar"),
            KeyboardButton("💰 Saldo & Top Up")
        ],
        [
            KeyboardButton("📜 Riwayat Transaksi"),
            KeyboardButton("👨‍💻 Bantuan (CS)")
        ],
        [
            KeyboardButton("🎲 Random Tools")
        ],
        # --- TOMBOL DONASI (Garis manjang di bawah Random Tools) ---
        [
            KeyboardButton("☕ Dukung Kiro (Donasi)")
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    pesan_sambutan = (
        f"Halo **{update.effective_user.first_name}**! 👋\n\n"
        f"Gua **Kiro Bot**, asisten digital serba bisa yang siap bantu berbagai kebutuhan lu.\n\n"
        f"Di sini lu bisa manfaatin fitur:\n"
        f"• 🎬 **Editing & AI Video**: Olah video & otomatisasi AI\n"
        f"• 📥 **Downloader Media**: Unduh file & media dengan mudah\n"
        f"• 🖼 **Tools Foto & Gambar**: Edit & manipulasi gambar\n"
        f"• 💰 **Saldo & Top Up**: Cek saldo & layanan transaksi\n"
        f"• 🎲 **Random Tools**: Kumpulan eksperimen iseng & unik\n\n"
        f"Silakan pilih menu di bawah untuk memulai!"
    )

    await update.message.reply_text(
        text=pesan_sambutan,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_tombol = update.message.text

    tombol_menu = [
        "🎬 Editing & AI Video", "📥 Downloader Media", 
        "🖼️ Tools Foto & Gambar", "💰 Saldo & Top Up", 
        "📜 Riwayat Transaksi", "👨‍💻 Bantuan (CS)", "🎲 Random Tools",
        "☕ Dukung Kiro (Donasi)"
    ]

    # --- INTERCEPT 1: PENANGKAP JIKA SEDANG INPUT GAJI ---
    if context.user_data.get('budget_step'):
        # Jika user membatalkan proses dengan mengeklik tombol menu utama
        if text_tombol in tombol_menu:
            context.user_data.pop('budget_step', None)
            context.user_data.pop('budget_salary', None)
        else:
            # Jika user ngetik angka gaji, lempar ke handler Smart Budget
            from handlers.random_tools import handle_budget_input
            await handle_budget_input(update, context)
            return

    # --- INTERCEPT 2: PENANGKAP JIKA SEDANG LAPOR BUG ---
    if context.user_data.get('waiting_for_bug_report'):
        if text_tombol in tombol_menu:
            context.user_data.pop('waiting_for_bug_report', None)
        else:
            # Lempar ketikan user ke handler laporan bug
            from handlers.help_cs import handle_bug_report_text
            await handle_bug_report_text(update, context)
            return

    # ==========================================
    # [AREA MODIFIKASI]: EDITING & AI VIDEO
    # ==========================================
    if text_tombol == "🎬 Editing & AI Video":
        inline_keyboard = [
            [InlineKeyboardButton("🎬 Auto Subtitle (CapCut Style)", callback_data="sub_start")],
            [InlineKeyboardButton("🔥 Auto Edit Affiliate (VIP)", callback_data="autoedit_start")] # TOMBOL BARU AUTO EDIT
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text(
            "Pilih fitur Editing & AI Video yang ingin kamu gunakan:",
            reply_markup=reply_markup
        )
        
    elif text_tombol == "📥 Downloader Media":
        await update.message.reply_text("Kamu memilih menu: Downloader Media. Silakan kirimkan link video/audio!")
    
    # ==========================================
    # [AREA MODIFIKASI]: TOOLS FOTO & GAMBAR
    # ==========================================
    elif text_tombol == "🖼️ Tools Foto & Gambar":
        # TAMBAHAN: Kita bikin 2 tombol sejajar atas bawah
        inline_keyboard = [
            [InlineKeyboardButton("✂️ Remove BG AI (Premium)", callback_data="rmbg_start")],
            [InlineKeyboardButton("🪄 HD-in Foto / Upscale", callback_data="hd_menu_start")] # Tombol Baru
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text(
            "Pilih fitur Foto & Gambar yang ingin lu pake, Ky!\n\n"
            "Mau hapus background biar transparan, atau mau naikin resolusi foto burik jadi HD? Langsung klik aja di bawah 👇",
            reply_markup=reply_markup
        )
    # ==========================================
        
    elif text_tombol == "💰 Saldo & Top Up":
        await update.message.reply_text("Kamu memilih menu: Saldo & Top Up (Fitur sedang disiapkan).")
    elif text_tombol == "📜 Riwayat Transaksi":
        await update.message.reply_text("Kamu memilih menu: Riwayat Transaksi (Fitur sedang disiapkan).")
        
    # --- RUTE BARU KE MENU BANTUAN ---
    elif text_tombol == "👨‍💻 Bantuan (CS)":
        from handlers.help_cs import show_help_menu
        await show_help_menu(update, context)
        
    elif text_tombol == "🎲 Random Tools":
        inline_keyboard = [
            [InlineKeyboardButton("💼 Smart Budgeting", callback_data="budget_start")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text(
            "Selamat datang di area **🎲 Random Tools**!\n\n"
            "Tempat berkumpulnya fitur eksperimen dadakan Iky. Silakan pilih fitur di bawah ini:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif text_tombol == "☕ Dukung Kiro (Donasi)":
        inline_keyboard = [
            [InlineKeyboardButton("☕ Dukung Kiro di Sociabuzz", url="https://sociabuzz.com/kyymedia/tribe")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text(
            "💡 *Fyi, Kiro ini 100% free-to-use. Kalo lu ngerasa kebantu sama tools di sini, bolehlah traktir kopi dikit buat patungan bayar server biar botnya tetep idup 🚀*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    else:
        await update.message.reply_text("Gunakan tombol yang tersedia di menu bawah ya!")