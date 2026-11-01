import re

def parse_salary(text):
    """Mengubah teks seperti '3jt', '3.500.000', atau '3000000' menjadi integer murni."""
    text = text.lower().replace(" ", "")
    if "jt" in text or "juta" in text:
        text = text.replace("jt", "").replace("juta", "")
        try:
            return int(float(text) * 1000000)
        except ValueError:
            return None
            
    # Bersihkan semua karakter selain angka
    cleaned = re.sub(r'[^\d]', '', text)
    if not cleaned: 
        return None
    return int(cleaned)

def parse_percentage(text):
    """Membaca persentase manual user dan memvalidasi harus pas 100%."""
    if ":" not in text:
        # Menangkap format angka saja (contoh: 50, 30, 20)
        parts = [re.sub(r'[^\d]', '', p) for p in text.split(",")]
        parts = [int(p) for p in parts if p]
        
        if sum(parts) != 100:
            return None, f"Total persentase kamu {sum(parts)}%. Wajib pas 100%!"
        
        labels = ["Kebutuhan Pokok", "Tabungan/Investasi", "Keinginan/Hiburan", "Sedekah", "Lainnya"]
        result = {}
        for i, p in enumerate(parts):
            label = labels[i] if i < len(labels) else f"Kategori {i+1}"
            result[label] = p
        return result, None
    else:
        # Menangkap format kategori (contoh: Makan: 50%, Main: 30%, Nabung: 20%)
        parts = text.split(",")
        result = {}
        total = 0
        for p in parts:
            if ":" in p:
                name, val = p.split(":", 1)
                name = name.strip()
                val = re.sub(r'[^\d]', '', val)
                if val:
                    result[name] = int(val)
                    total += int(val)
                    
        if not result:
            return None, "Format tidak dikenali. Ikuti contoh template ya!"
        if total != 100:
            return None, f"Total persentase kamu {total}%. Wajib pas 100%!"
        return result, None

def generate_budget_report(salary, allocations):
    """Mencetak invoice monospace dengan perhitungan Rupiah yang rapi dan rata."""
    report = f"💰 RINCIAN ALOKASI GAJI 💰\n"
    report += f"Total Pendapatan : Rp {salary:,.0f}\n\n"
    report += "-" * 32 + "\n\n"
    
    # 1. Cari panjang teks maksimal dari sisi kiri (Nama + Persen)
    max_len = 0
    for name, pct in allocations.items():
        text_kiri = f"• {name} ({pct}%)"
        if len(text_kiri) > max_len:
            max_len = len(text_kiri)
    
    # 2. Render teks dengan jarak spasi otomatis (rata titik dua)
    biggest_alloc = 0
    for name, pct in allocations.items():
        amount = int(salary * (pct / 100))
        if amount > biggest_alloc:
            biggest_alloc = amount
            
        text_kiri = f"• {name} ({pct}%)"
        # .ljust(max_len) otomatis nambahin spasi kosong di kanan teks
        # supaya titik dua ( : ) posisinya lurus presisi semua
        report += f"{text_kiri.ljust(max_len)} : Rp {amount:,.0f}\n"
    
    report += "\n" + "-" * 32 + "\n\n"
    report += f"💡 Tips Budget Harian (30 Hari):\n"
    
    daily = int(biggest_alloc / 30)
    report += f"Batas aman pengeluaran harian dari\nalokasi terbesarmu adalah:\n>> Rp {daily:,.0f} / hari <<"
    
    # Format ala Indonesia (koma jadi titik)
    return report.replace(",", ".")