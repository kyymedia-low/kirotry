import os
import asyncio
import subprocess
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

# Pastikan folder temp ada
os.makedirs("temp", exist_ok=True)

# ==========================================
# 1. SCRAPER TIKTOK API (RINGAN & TANPA YT-DLP)
# ==========================================
async def download_tiktok_tikwm(url: str, save_path: str):
    """Download video TikTok tanpa watermark pakai TikWM API."""
    api_url = "https://www.tikwm.com/api/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, data={"url": url}) as resp:
                data = await resp.json()
                if data.get("code") == 0:
                    video_url = data["data"]["play"]
                    async with session.get(video_url) as v_resp:
                        with open(save_path, "wb") as f:
                            f.write(await v_resp.read())
                    return True
    except Exception as e:
        print(f"Error TikTok API: {e}")
    return False

# ==========================================
# 2. FUNGSI SYNC FFMPEG (DIJALANKAN DI BACKGROUND THREAD)
# ==========================================
def run_ffmpeg_sync(cmd):
    """Menjalankan FFmpeg secara sinkronus agar aman dari NotImplementedError Windows/Asyncio."""
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

# ==========================================
# 3. PIPELINE UTAMA & PERACIK FFMPEG
# ==========================================
async def run_auto_edit_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE, message_target):
    user_id = update.effective_user.id
    data = context.user_data
    
    # Path File Sementara
    raw_video = f"temp/raw_vid_{user_id}.mp4"
    raw_vo = f"temp/raw_vo_{user_id}.ogg"
    out_video = f"temp/final_{user_id}.mp4"

    try:
        # --- TAHAP 1: DOWNLOAD BAHAN ---
        await message_target.edit_text("⏳ **Tahap 1/3:** Sedang mengunduh bahan (Video & VO)...", parse_mode="Markdown")
        
        # Download Video/Link
        if data['aedit_type'] == 'link':
            sukses = await download_tiktok_tikwm(data['aedit_link'], raw_video)
            if not sukses:
                await message_target.edit_text("❌ Gagal mendownload TikTok. Pastikan akun tidak diprivate.")
                return
        else:
            file_vid = await context.bot.get_file(data['aedit_file_id'])
            await file_vid.download_to_drive(raw_video)

        # Download Voice Over (jika ada)
        if data.get('toggle_vo') and data.get('aedit_vo_id'):
            file_vo = await context.bot.get_file(data['aedit_vo_id'])
            await file_vo.download_to_drive(raw_vo)

        # --- TAHAP 2: RACIK RUMUS FFMPEG ---
        await message_target.edit_text("⚙️ **Tahap 2/3:** Bahan siap! Mulai ngerender di dapur FFmpeg...", parse_mode="Markdown")

        cmd = ["ffmpeg", "-y", "-i", raw_video]
        
        if data.get('toggle_vo'):
            cmd.extend(["-i", raw_vo])

        # Filter Video (vf)
        v_filters = []
        if data.get('toggle_zoomin'): v_filters.append("crop=iw/1.1:ih/1.1") # Potong pinggiran tipis
        if data.get('toggle_flip'): v_filters.append("hflip")               # Mirror kiri-kanan
        if data.get('toggle_lut'): v_filters.append("eq=contrast=1.1:saturation=1.2") # Warna cerah
        if data.get('toggle_jumpcut'): v_filters.append("select='not(between(mod(t,5),4.8,5))',setpts=N/FRAME_RATE/TB") # Buang 0.2 dtk tiap 5 dtk
        if data.get('toggle_speedup'): v_filters.append("setpts=0.95*PTS")  # Cepetin 5% visual
        
        # --- PENYELAMAT RESOLUSI (VERSI NGEBUT 720p) ---
        # Memaksa hasil akhir jadi 720x1280 (HD standar). Lolos syarat Shopee, file kecil, render kilat!
        v_filters.append("scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2")

        if v_filters:
            cmd.extend(["-vf", ",".join(v_filters)])

        # Filter Audio & Mapping (af / map)
        if data.get('toggle_mute'):
            cmd.append("-an") # Buang suara 100%
        elif data.get('toggle_vo'):
            cmd.extend(["-map", "0:v:0", "-map", "1:a:0", "-shortest"])
            if data.get('toggle_speedup'): 
                cmd.extend(["-af", "atempo=1.05"])
        else:
            a_filters = []
            if data.get('toggle_jumpcut'): a_filters.append("aselect='not(between(mod(t,5),4.8,5))',asetpts=N/SR/TB")
            if data.get('toggle_speedup'): a_filters.append("atempo=1.05")
            if a_filters:
                cmd.extend(["-af", ",".join(a_filters)])

        # Setting Kualitas (Sangat Cepat & Ukuran File Ringan)
        cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", out_video])

        # Jalankan FFmpeg lewat Thread terpisah (Aman dari NotImplementedError)
        success, err_msg = await asyncio.to_thread(run_ffmpeg_sync, cmd)

        if not success:
            print(f"FFmpeg Error Log: {err_msg}")
            raise Exception("FFmpeg gagal ngerender video. Cek console untuk detail.")

        # --- TAHAP 3: PENGIRIMAN HASIL ---
        await message_target.edit_text("🚀 **Tahap 3/3:** Render selesai! Sedang mengirim ke Telegram lu...", parse_mode="Markdown")
        
        caption = "🔥 **Auto Edit Affiliate Berhasil!**\n\nVideo lu udah bersih dari jejak asli & HD 720p. Siap di-upload ulang ke TikTok/Shopee tanpa takut Content ID!"
        
        # Ditambahin timeout 300 detik (5 menit) biar aman
        with open(out_video, 'rb') as f:
            await context.bot.send_video(
                chat_id=user_id, 
                video=f, 
                caption=caption, 
                parse_mode="Markdown",
                write_timeout=300,
                read_timeout=300,
                connect_timeout=60
            )
            
        await message_target.delete()

    except Exception as e:
        import traceback
        print("\n" + "="*40)
        print("🚨 TERJADI ERROR DI AUTO EDIT ENGINE 🚨")
        traceback.print_exc()
        print("="*40 + "\n")
        
        await message_target.edit_text(f"❌ **Waduh Error Boss!**\n\nDetail: {e}")

    finally:
        # --- TUKANG SAPU (AUTO-CLEANUP) ---
        for file in [raw_video, raw_vo, out_video]:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass
        
        keys_to_clear = ['aedit_type', 'aedit_link', 'aedit_file_id', 'aedit_vo_id', 'toggle_flip', 'toggle_lut', 'toggle_jumpcut', 'toggle_zoomin', 'toggle_speedup', 'toggle_mute', 'toggle_vo']
        for k in keys_to_clear:
            context.user_data.pop(k, None)