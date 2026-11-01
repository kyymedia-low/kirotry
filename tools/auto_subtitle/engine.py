import os
import sys
import time
import subprocess
import numpy as np
from faster_whisper import WhisperModel
from .presets import generate_ass_subtitle
from .cleaner import cleanup_temp_files

MODEL_SIZE = "base" 
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def update_console(msg, status="info"):
    colors = {
        "info": "\033[96m",    # Cyan
        "success": "\033[92m", # Hijau
        "warning": "\033[93m", # Kuning
        "error": "\033[91m",   # Merah
        "reset": "\033[0m"
    }
    color = colors.get(status, colors["reset"])
    sys.stdout.write(f"\r\033[K{color}✦ {msg}{colors['reset']}")
    sys.stdout.flush()

def decode_audio_with_ffmpeg(input_video_path, sr=16000):
    command = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-f", "s16le",
        "-ac", "1",
        "-ar", str(sr),
        "-"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    out, _ = process.communicate()
    if not out:
        raise RuntimeError("Gagal mengekstrak audio dari video menggunakan FFmpeg.")
    return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768.0

def process_video_subtitle(input_video_path, output_video_path, style="style1", color="kuning"):
    ass_path = input_video_path + ".ass"
    
    try:
        update_console("Mengakses audio dari video via FFmpeg...", "info")
        audio_array = decode_audio_with_ffmpeg(input_video_path)

        update_console("Memulai transkripsi AI Whisper...", "info")
        segments, info = model.transcribe(audio_array, word_timestamps=True)
        
        words_data = []
        for segment in segments:
            for word in segment.words:
                words_data.append({
                    "word": word.word,
                    "start": word.start,
                    "end": word.end
                })
        
        update_console("Membuat preset animasi Subtitle...", "info")
        ass_content = generate_ass_subtitle(words_data, style_type=style, highlight_color=color)
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
            
        safe_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
        
        update_console("Memulai proses Render Video HD...", "warning")
        command = [
            "ffmpeg", "-y", 
            "-i", input_video_path,
            "-vf", f"ass='{safe_ass_path}'",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "copy",
            output_video_path
        ]
        
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        update_console("Render video selesai! Menyiapkan pengiriman...", "success")
        time.sleep(1)
        
        return output_video_path

    except Exception as e:
        update_console(f"Error saat memproses subtitle: {e}", "error")
        time.sleep(2) # Tampilkan error sebentar
        raise e
        
    finally:
        cleanup_temp_files([ass_path])