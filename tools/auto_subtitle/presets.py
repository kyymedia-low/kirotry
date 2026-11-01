def format_time_ass(seconds):
    """Mengubah detik ke format waktu ASS (H:MM:SS.cs)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

def get_color_hex(color_name):
    """Mendapatkan kode BGR untuk format ASS."""
    colors = {
        "kuning": "00FFFF",  # Kuning (&H0000FFFF&)
        "cyan": "FFFF00",    # Cyan (&H00FFFF00&)
        "hijau": "00FF00",   # Hijau (&H0000FF00&)
        "merah": "0000FF",   # Merah (&H000000FF&)
        "putih": "FFFFFF"    # Putih (&H00FFFFFF&)
    }
    return colors.get(color_name.lower(), "FFFF00")

def generate_ass_subtitle(words_data, style_type="style1", highlight_color="cyan"):
    # Header ASS: Font Impact, MarginV 250 (lebih turun ke bawah), Fontsize Style2 (90) > Style1 (70)
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Style1,Impact,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,4,0,2,50,50,250,1
Style: Style2,Impact,90,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,5,0,2,50,50,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    if not words_data:
        return header

    bgr_color = get_color_hex(highlight_color)

    # 1. Kelompokkan kata menjadi potongan pendek (Max 2 - 3 kata per tampilan layar)
    chunks = []
    current_chunk = []
    
    for w in words_data:
        word_str = w["word"].strip().upper()
        if not word_str:
            continue
        
        # Buat grup baru jika sudah ada 3 kata atau ada jeda bicara > 0.4 detik
        if current_chunk:
            prev_end = current_chunk[-1]["end"]
            if len(current_chunk) >= 3 or (w["start"] - prev_end) > 0.4:
                chunks.append(current_chunk)
                current_chunk = []
        
        current_chunk.append({
            "word": word_str,
            "start": w["start"],
            "end": w["end"]
        })
        
    if current_chunk:
        chunks.append(current_chunk)

    dialogues = []
    ass_style_name = "Style2" if style_type == "style2" else "Style1"

    # 2. Buat animasi per kata aktif sesuai tempo audio (Word-by-word timing)
    for chunk in chunks:
        for i, active_w in enumerate(chunk):
            start_str = format_time_ass(active_w["start"])
            
            # Waktu selesai kata mengikuti kata berikutnya atau batas kata tersebut
            if i < len(chunk) - 1:
                end_time = max(active_w["end"], chunk[i+1]["start"])
            else:
                end_time = active_w["end"]
            
            if end_time <= active_w["start"]:
                end_time = active_w["start"] + 0.1
                
            end_str = format_time_ass(end_time)

            if style_type == "style2":
                # LAYER 0 (Bawah): Merender Kotak Solid Tebal (\bord14) khusus di belakang kata aktif
                box_words = []
                for j, w in enumerate(chunk):
                    w_text = w["word"]
                    if i == j:
                        box_words.append(f"{{\\1c&H00{bgr_color}&\\3c&H00{bgr_color}&\\bord14}}{w_text}{{\\r}}")
                    else:
                        box_words.append(f"{{\\alpha&HFF&}}{w_text}{{\\r}}")
                full_box_line = " ".join(box_words)
                dialogues.append(f"Dialogue: 0,{start_str},{end_str},{ass_style_name},,0,0,0,,{full_box_line}")

                # LAYER 1 (Atas): Merender Teks Putih + Outline Hitam Tegas (\bord4) di atas kotak
                text_words = []
                for j, w in enumerate(chunk):
                    w_text = w["word"]
                    text_words.append(f"{{\\1c&HFFFFFF&\\3c&H000000&\\bord4}}{w_text}{{\\r}}")
                full_text_line = " ".join(text_words)
                dialogues.append(f"Dialogue: 1,{start_str},{end_str},{ass_style_name},,0,0,0,,{full_text_line}")

            else:
                # Style 1 (Tetap sama persis seperti semula)
                line_words = []
                for j, w in enumerate(chunk):
                    w_text = w["word"]
                    if i == j:
                        word_fmt = f"{{\\1c&H00{bgr_color}&\\3c&H000000&\\bord5\\fscx115\\fscy115}}{w_text}{{\\r}}"
                    else:
                        word_fmt = f"{{\\1c&HFFFFFF&\\3c&H000000&\\bord4}}{w_text}{{\\r}}"
                    line_words.append(word_fmt)

                full_line = " ".join(line_words)
                dialogues.append(f"Dialogue: 0,{start_str},{end_str},{ass_style_name},,0,0,0,,{full_line}")

    return header + "\n".join(dialogues)