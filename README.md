# Sistem Prediksi Harga Pangan Kota Padang

> **Tugas Mata Kuliah Machine Learning**  
> Integrasi Hasil Model Deret Waktu (*Time Series*) SARIMAX Harga Pangan Kota Padang  
> Sumber Data: Pusat Informasi Harga Pangan Strategis (PIHPS) Kota Padang (2022–2026)  
> Komoditas: **Daging Ayam, Bawang Merah, Bawang Putih, Cabai Merah, Cabai Rawit**

---

## 1. Deskripsi Sistem

Sistem ini merupakan aplikasi web satu halaman (*single-page application*) yang menyajikan data harga pangan historis dan prediksi masa depan untuk 5 komoditas pokok di Kota Padang. 

### Prinsip Utama Rekayasa Sistem:
1. **Pemisahan Model dan Web**: Backend Flask **tidak melatih atau menjalankan model secara langsung**. Model SARIMAX dilatih di luar sistem (notebook/skrip) dan menghasilkan berkas data `forecast_sistem_terbaru.json` serta `harga_aktual.csv`.
2. **Backend Ringan Tanpa Pustaka Berat**: Backend hanya menggunakan pustaka standar Python (`csv`, `json`, `datetime`) tanpa `pandas`, `scikit-learn`, maupun `joblib`.
3. **Penyedia Logika Bisnis Tunggal (*Single Source of Truth*)**: Seluruh validasi input, pergeseran akhir pekan, penetapan horizon, pembanding *naive*, dan teks peringatan disusun oleh backend. Frontend React murni hanya bertugas me-render data.
4. **Kejujuran Ilmiah Model**: Berdasarkan hasil evaluasi, model SARIMAX tidak terbukti mengalahkan *baseline naive* (harga terakhir) pada horizon 1 s.d. 22 hari kerja. Oleh karena itu, sistem **selalu menampilkan harga *naive* sebagai pembanding** dan menyertakan peringatan perkiraan kasar tanpa mengklaim keunggulan semu.

---

## 2. Struktur Direktori Proyek

```text
appml/
├── backend/
│   ├── app.py                      # Aplikasi Flask & routing API (/health, /api/meta, /api/prediksi, /api/seri)
│   ├── data_loader.py              # Pemuat data & validasi ketat 4 syarat integritas (Bagian 4.3 modul)
│   ├── requirements.txt            # Dependensi Python (flask, flask-cors, waitress, pytest)
│   ├── data/
│   │   ├── forecast_sistem_terbaru.json  # 1.305 baris data forecast (5 komoditas × 261 hari kerja)
│   │   └── harga_aktual.csv              # 6.370 baris data aktual 2022–2026 (1.274 hari × 5 komoditas)
│   └── tests/
│       ├── conftest.py             # Konfigurasi path modul pytest
│       ├── test_tahap1.py          # Uji validasi 4.3 dan endpoint /health
│       └── test_api.py             # Uji 13 skenario lengkap tabel Modul Bagian 9
├── docs/
│   ├── MODUL_ARAHAN.md             # Spesifikasi teknis, aturan bisnis, dan kontrak API
│   └── RINGKASAN_MODEL.md          # Dokumentasi pemodelan SARIMAX dan evaluasi
├── frontend/
│   ├── public/
│   │   ├── pasar.jpg               # Gambar latar hero pasar tradisional
│   │   └── img/pasar.jpg           # Salinan aset gambar pasar
│   ├── src/
│   │   ├── App.jsx                 # Komponen utama UI React 19 (Papan Harga Pasar)
│   │   ├── App.css                 # Gaya tema biru, visualisasi rentang CSS, dan responsivitas
│   │   ├── index.css               # Desain variabel :root, tipografi display & teks
│   │   └── main.jsx                # Entry point React
│   ├── index.html                  # Dokumen HTML, font Google Outfit & Plus Jakarta Sans
│   ├── package.json                # Dependensi frontend (React 19, Vite, Lucide-React)
│   └── vite.config.js              # Konfigurasi proxy Vite (/api dan /health ke port 5000)
└── README.md                       # Dokumentasi petunjuk penggunaan dan arsitektur sistem
```

---

## 3. Prasyarat & Cara Menjalankan Sistem

### Prasyarat
- **Python**: Versi 3.10 atau lebih baru (direkomendasikan Python 3.13)
- **Node.js**: Versi 18 atau lebih baru

---

### Langkah Menjalankan (Dua Terminal Terpisah)

#### Terminal 1 — Backend (Flask)
```powershell
# 1. Masuk ke root direktori proyek
cd "D:\Zahra Aulia Nasution (SI)\Semester 5\ML\appml"

# 2. Aktifkan virtual environment
.\backend\venv\Scripts\Activate.ps1

# 3. Jalankan aplikasi Flask (Port 5000)
python backend/app.py
```
> Server backend akan berjalan di `http://127.0.0.1:5000`.

#### Terminal 2 — Frontend (React + Vite)
```powershell
# 1. Masuk ke folder frontend
cd "D:\Zahra Aulia Nasution (SI)\Semester 5\ML\appml\frontend"

# 2. Jalankan server pengembangan Vite (Port 5173)
npm run dev
```
> Buka peramban di `http://localhost:5173`. Semua pemanggilan API `/api/...` dan `/health` secara otomatis diteruskan oleh proxy Vite ke backend Flask di port 5000.

---

### Menjalankan Server Produksi Windows (Waitress)
Bila ingin dijalankan menggunakan WSGI server produksi (Waitress):
```powershell
.\backend\venv\Scripts\Activate.ps1
waitress-serve --port=5000 backend.app:app
```

---

## 4. Spesifikasi Kontrak API

| Endpoint | Metode | Parameter | Deskripsi |
|---|---|---|---|
| `/health` | `GET` | - | Pemeriksaan kesehatan sistem, mengembalikan tanggal data terakhir. |
| `/api/meta` | `GET` | - | Daftar 5 komoditas, rentang tanggal minimum/maksimum, satuan, catatan model. |
| `/api/prediksi` | `GET` | `tanggal` (wajib, `YYYY-MM-DD`), `komoditas` (opsional) | Hasil data harga aktual atau prediksi lengkap dengan rentang dan peringatan. |
| `/api/seri` | `GET` | `komoditas` (opsional, bawaan: Cabai Rawit) | Data deret waktu 120 hari aktual terakhir dan seluruh horizon forecast untuk visualisasi grafik. |

### Contoh Respon Prediksi (`status: "prediksi"`):
```json
{
  "status": "prediksi",
  "tanggal_diminta": "2026-12-21",
  "tanggal_data": "2026-12-21",
  "digeser_ke_jumat": false,
  "horizon_hk": 22,
  "kategori_horizon": "h6-22",
  "label_horizon": "sekitar 1 bulan ke depan",
  "data_terakhir": "2026-11-19",
  "hasil": [
    {
      "komoditas": "Cabai Rawit",
      "prediksi": 50979,
      "naive": 57250,
      "rentang_50": [43712, 60693],
      "rentang_80": [38143, 73843],
      "galat_median_pct": 14.8,
      "galat_p90_pct": 40.1,
      "rentang_hist": null
    }
  ],
  "peringatan": [
    "Perkiraan kasar. Model tidak terbukti lebih akurat daripada harga terakhir (naive)."
  ]
}
```

---

## 5. Ringkasan Aturan Bisnis Sistem

1. **Validasi Masukan**: Tanggal harus valid `YYYY-MM-DD`. Komoditas harus termasuk dalam 5 komoditas resmi atau kosong/`semua`. Input tidak valid menghasilkan HTTP 400 (`format_tanggal` atau `komoditas_tidak_dikenal`).
2. **Penggeseran Akhir Pekan**: Jika tanggal yang diminta adalah hari Sabtu atau Minggu, tanggal **dimundurkan ke hari Jumat sebelumnya** dan dicatat dengan flag `digeser_ke_jumat = true`.
3. **Pemeriksaan Rentang (Setelah Penggeseran)**:
   - `< 2022-01-03` atau `> 2027-11-19`: Respon HTTP 200 dengan status `"di_luar_rentang"`.
4. **Data Aktual (`<= 2026-11-19`)**:
   - Diambil dari `harga_aktual.csv`.
   - Menampilkan label `Harga Pasar Aktual`.
   - Jika harga berasal dari imputasi hari libur (`diisi_ffill: true`), ditampilkan catatan bahwa harga merupakan hasil isian hari sebelumnya (*forward fill*).
   - Kunci `rentang_hist` selalu ada dengan nilai `null`.
5. **Data Prediksi (`> 2026-11-19`)**:
   - Diambil dari `forecast_sistem_terbaru.json`.
   - **Horizon h1–66**: Menyertakan `rentang_80`, `rentang_50`, galat median, galat P90, dan `rentang_hist: null`.
   - **Horizon h67+**: Kolom interval bernilai `null`, label bertuliskan *"Indikatif (tanpa interval terkalibrasi)"*, dan menyertakan `rentang_hist` `[P10, P90]`.
   - **Peringatan Wajib**: Selalu menyertakan *"Perkiraan kasar. Model tidak terbukti lebih akurat daripada harga terakhir (naive)."*

---

## 6. Prosedur Pembaruan Data Berkala

Sistem didesain untuk memperbarui data tanpa mengubah kode program:
1. **Pembersihan Data Baru**: Tambahkan data harian PIHPS terbaru ke tabel data aktual, jalankan pembersihan hari libur (*forward fill*).
2. **Refit Model**: Latih ulang 5 model spesifikasi terkunci pada data terbaru dan hitung ulang interval empiris (Sel 20 pada notebook pemodelan).
3. **Arsipkan Berkas Lama**: Pindahkan berkas lama di `backend/data/` ke direktori arsip.
4. **Salin Berkas Baru**: Salin berkas baru ke `backend/data/harga_aktual.csv` dan `backend/data/forecast_sistem_terbaru.json`.
5. **Restart Backend**: Restart Flask. Saat dinyalakan, backend secara otomatis memvalidasi 4 syarat integritas data Bagian 4.3. Jika validasi berhasil, tanggal data terakhir pada `/health` akan otomatis diperbarui.

---

## 7. Pengujian Otomatis

Proyek ini telah dilengkapi **23 pengujian otomatis** (`pytest`) yang mencakup validasi startup dan 13 skenario pengujian Bagian 9 MODUL_ARAHAN.md.

### Menjalankan Pytest:
```powershell
.\backend\venv\Scripts\Activate.ps1
pytest backend/tests
```
Hasil uji:
```text
============================= 23 passed in 2.60s ==============================
```

### Menjalankan Build Frontend:
```powershell
cd frontend
npm run build
```
Hasil uji:
```text
✓ 2129 modules transformed.
dist/index.html                   1.15 kB │ gzip:  0.66 kB
dist/assets/index-Chlm4X_V.css   14.66 kB │ gzip:  3.79 kB
dist/assets/index-CWJCK7gr.js   236.91 kB │ gzip: 74.36 kB
✓ built in 2.41s
```
