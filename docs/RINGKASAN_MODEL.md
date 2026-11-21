**Dokumentasi Pemodelan dan Panduan Integrasi: Prediksi Harga Pangan Kota Padang dengan SARIMAX**

Disusun 20 November 2026 · Data PIHPS Kota Padang, 3 Jan 2022 – 19 Nov 2026 · Komoditas: Daging Ayam, Bawang Merah, Bawang Putih, Cabai Merah, Cabai Rawit

**1. Ringkasan**

Dokumen ini merangkum seluruh pengerjaan dari Sel 1 sampai Sel 22 dan menjelaskan cara membaca file keluaran untuk integrasi ke sistem.

- **Metode.** Model statistik time series SARIMAX/ARIMA (library statsmodels), satu model per komoditas, pada data harian hari kerja. Evaluasinya memakai kerangka ala machine learning: pembagian berdasarkan waktu, validasi walk-forward, tuning terbatas, dan pencegahan kebocoran data.

- **Temuan utama.** Pada pengujian 2025 dan validasi di luar sampel 2026, tidak ada model yang terbukti lebih akurat daripada baseline naive (harga terakhir) pada horizon 5 dan 22 hari kerja. Variabel Ramadan, Lebaran, dan Iduladha tidak meningkatkan akurasi.

- **Nilai tambah.** Prediksi kedua cabai pada horizon 1–3 bulan (tarikan ke rata-rata), interval ketidakpastian empiris per horizon, dan prosedur evaluasi yang bebas kebocoran data.

- **Keluaran untuk sistem.** forecast_sistem_terbaru.csv dan .json: 5 komoditas × 261 hari kerja (20 Nov 2026 – 19 Nov 2027), dengan interval sampai hari kerja ke-66. Interval berstatus perkiraan kasar.

- **Status.** Pemodelan selesai dan terkunci. Spesifikasi tidak boleh disetel ulang berdasarkan data 2025–2026 yang sudah dilihat; perubahan apa pun harus dilaporkan sebagai eksplorasi.

**2. Data dan Desain Penelitian**

**2.1 Data**

- Sumber: PIHPS, harga harian Kota Padang, satuan Rp/kg. File 2022–2025 berisi 1.043 hari kerja, file 2026 berisi 231 hari kerja (1 Jan – 19 Nov 2026). Total 1.274 hari.

- Lima komoditas inti. Kolom turunan (Ras Segar, Ukuran Sedang, Cabai Rawit Hijau) tidak dipakai karena identik 100% dengan kolom induknya. Dua tanggal kosong di kolom induk (29 Agu dan 2 Sep 2024) diisi dari kolom turunan.

- Missing 2022–2025: 41 hari bertanda tanda minus (3,9%), identik di semua komoditas dan diduga hari libur; runtutan terpanjang 6 hari. Diisi dengan forward fill (kausal, tidak memakai nilai masa depan) dan diberi kolom penanda. Data 2026 tidak memuat hari kosong.

- Harga bersifat menempel. Perubahan harian bernilai nol pada 50% hari (Daging Ayam), 52% (Bawang Merah), 80% (Bawang Putih), 22% (Cabai Merah), dan 27% (Cabai Rawit). Hari Senin memiliki perubahan 1,5–2,5 kali lebih besar daripada hari lain.

**2.2 Pembagian data**

| **Periode**   | **Rentang**              | **Hari kerja** | **Fungsi**            |
|---------------|--------------------------|----------------|-----------------------|
| Training      | 3 Jan 2022 – 28 Feb 2025 | 825 (79,1%)    | Semua keputusan model |
| Testing       | 3 Mar – 31 Des 2025      | 218 (20,9%)    | Dibuka satu kali      |
| Validasi 2026 | 1 Jan – 19 Nov 2026      | 231            | Uji di luar sampel    |

Rancangan awal (38 dan 10 observasi) tidak konsisten dengan tanggalnya (34 dan 14 bulan). Dipilih opsi yang mengikuti jumlah observasi, yang di skala harian menjadi pembagian di atas.

**2.3 Kalender hari besar**

Tanggal mengikuti ketetapan pemerintah (Kemenag) dan diverifikasi dari berita sidang isbat.

| **Tahun** | **1 Ramadan** | **Idulfitri** | **Iduladha** |
|-----------|---------------|---------------|--------------|
| 2022      | 3 Apr         | 2 Mei         | 10 Jul       |
| 2023      | 23 Mar        | 22 Apr        | 29 Jun       |
| 2024      | 12 Mar        | 10 Apr        | 17 Jun       |
| 2025      | 1 Mar         | 31 Mar        | 6 Jun        |
| 2026      | 19 Feb        | 21 Mar        | 27 Mei       |

Variabel dummy harian: **is_lebaran** (H-7 sampai H-1 Idulfitri), **is_iduladha** (H-7 sampai H-1 Iduladha), dan **is_ramadan** (1 Ramadan sampai sehari sebelum jendela Lebaran, agar tidak tumpang tindih). Setiap jendela Lebaran dan Iduladha setara 5 hari kerja. Beberapa tahun berbeda satu hari dengan versi Muhammadiyah; ini dicatat sebagai keterbatasan.

**2.4 Keputusan yang dikunci**

- **Transformasi.** Log untuk Bawang Putih, Cabai Merah, dan Cabai Rawit. Daging Ayam dan Bawang Merah dalam level, dibagi 1.000 agar optimizer stabil.

- **Differencing.** d = 1 untuk Bawang Merah dan Bawang Putih. Untuk tiga komoditas lain uji stasioneritas ambigu, sehingga d = 0 dan d = 1 dua-duanya dicoba dan dipilih lewat validasi. D = 0; komponen musiman mingguan (s = 5) hanya sebagai kandidat.

- **Grid.** p, q, P, Q antara 0 dan 2 dengan p+q+P+Q ≤ 4, dan tiga skenario eksogen: M1 tanpa dummy, M2 Ramadan + Lebaran, M3 ditambah Iduladha. Totalnya 1.200 model.

- **Kelayakan model.** Konvergen, galat baku terdefinisi, akar AR/MA ≥ 1,01, dan uji bersarang (model dengan dummy tidak boleh memiliki likelihood lebih rendah daripada versi tanpa dummy).

- **Validasi.** Expanding window, window awal 400 hari, bergeser 10 hari, horizon 22 hari: 41 fold, n efektif sekitar 18.

- **Skor.** Rata-rata rMAE (MAE model dibagi MAE naive) pada h5 dan h22. Aturan satu galat baku memilih model paling sederhana yang skornya sepadan.

- **Klaim.** 'Lebih baik dari naive' hanya jika skor \< 1 − SE.

- Data testing dibuka satu kali; tidak ada tuning ulang. Titik ekstrem tidak dihapus tanpa bukti salah input.

**3. Alur Pengerjaan per Sel**

| **Sel**    | **Isi**                                                   | **Hasil atau keputusan**                                                |
|------------|-----------------------------------------------------------|-------------------------------------------------------------------------|
| 1          | Setup, konfigurasi, baca file mentah                      | Seed 42, split dikunci                                                  |
| 2          | Rapikan header, konversi tanggal dan angka, isi 2 tanggal | 1.043 baris, 5 komoditas inti                                           |
| 3          | Reindex hari kerja, forward fill, split                   | 825 train dan 218 test; 41 hari diisi                                   |
| 4          | Variabel kalender hari besar                              | Tanggal diverifikasi, dummy harian                                      |
| 5          | EDA 1 pada training                                       | CV harga 9,9–38,7%; harga menempel                                      |
| 6          | EDA 2: titik ekstrem, perubahan selama jendela hari besar | Satu kandidat salah input (cabai rawit 24 Mar 2023), belum diverifikasi |
| 7          | Transformasi, ADF/KPSS, ACF/PACF                          | Log untuk 3 komoditas, d ditetapkan, D = 0                              |
| 8          | Konfigurasi terkunci, kerangka validasi, baseline         | Naive baseline terbaik di semua komoditas                               |
| 9          | Fungsi bantu model dan benchmark waktu                    | Aturan kelayakan didefinisikan sebelum pencarian                        |
| 10         | Tahap 1: 1.200 model, shortlist AIC/BIC                   | 89,8% model lolos filter                                                |
| 11         | Diagnostik filter dan efek eksogen in-sample              | Model rusak numerik terdeteksi; p-value Wald tidak andal                |
| 12         | Perbaikan skala, uji bersarang, ulang Tahap 1             | Shortlist 164 model                                                     |
| 13         | Tahap 2: validasi 41 fold, aturan satu galat baku         | Lima model final dipilih                                                |
| 14 dan 14b | Residual, kestabilan parameter, pembanding orde           | Model final tetap                                                       |
| 15         | Evaluasi testing 2025 (satu kali)                         | Tidak ada model unggul atas naive                                       |
| 16         | Forecast 2026 versi awal                                  | Digantikan Sel 20                                                       |
| 17         | Tabel hasil akhir, file sistem awal, grafik               | hasil_akhir_penelitian.xlsx                                             |
| 18         | Validasi dengan data 2026                                 | Skor, kalibrasi interval, uji arah 11 dari 12                           |
| 19         | Sensitivitas titik 24 Mar 2023, log reproduksi            | Dampak tidak material                                                   |
| 20         | Forecast terbaru (data sampai 19 Nov 2026)                | File sistem final                                                       |
| 21         | Tabel akurasi final, origin sama dengan naive             | tabel_akurasi_final.csv                                                 |
| 22         | Fungsi prediksi per tanggal                               | Prototipe logika sistem                                                 |

**4. Model Final dan Hasil**

**4.1 Model final (parameter hasil refit di Sel 20)**

| **Komoditas** | **Spesifikasi**                                      | **Parameter**                                         |
|---------------|------------------------------------------------------|-------------------------------------------------------|
| Daging Ayam   | ARIMA(1,1,1), level dibagi 1.000, tanpa dummy        | AR 0,797; MA −0,611                                   |
| Bawang Merah  | ARIMA(1,1,0), level dibagi 1.000, tanpa dummy        | AR 0,116                                              |
| Bawang Putih  | ARIMA(0,1,0) pada log, dummy Ramadan dan Lebaran     | Koefisien dummy sekitar 0 (praktis sama dengan naive) |
| Cabai Merah   | AR(1) dengan konstanta (d = 0) pada log, tanpa dummy | Konstanta 0,266; AR 0,975                             |
| Cabai Rawit   | AR(1) dengan konstanta (d = 0) pada log, tanpa dummy | Konstanta 0,207; AR 0,981                             |

Semua model tanpa komponen musiman. Model d = 0 pada kedua cabai menarik prediksi ke rata-rata (sekitar Rp46 ribu untuk Cabai Merah dan Rp41 ribu untuk Cabai Rawit).

**4.2 Akurasi terhadap naive**

Skor adalah rata-rata rMAE pada h5 dan h22. Nilai 1,00 berarti sama dengan naive, di bawah 1 lebih baik. Selisih kurang dari sekitar 0,1 tidak dapat dibedakan dari kebetulan.

| **Komoditas** | **Validasi training** | **Testing 2025** | **Validasi 2026** |
|---------------|-----------------------|------------------|-------------------|
| Daging Ayam   | 0,970                 | 1,052 ± 0,065    | 0,938 ± 0,073     |
| Bawang Merah  | 0,998                 | 1,000 ± 0,008    | 1,000 ± 0,019     |
| Bawang Putih  | 1,000                 | 1,000            | 1,000             |
| Cabai Merah   | 0,965                 | 0,938 ± 0,124    | 0,992 ± 0,098     |
| Cabai Rawit   | 0,951                 | 1,024 ± 0,063    | 0,975 ± 0,106     |

Tidak ada skor yang memenuhi syarat skor \< 1 − SE, jadi tidak ada klaim keunggulan atas naive. MAPE model final pada h5 dan h22: 2025, Daging Ayam 2,1% dan 5,6%, Bawang Merah 7,0% dan 19,1%, Bawang Putih 1,2% dan 4,5%, Cabai Merah 13,5% dan 24,5%, Cabai Rawit 9,1% dan 24,1%. MAE, RMSE, MAPE, dan MASE lengkap ada di tabel_akurasi_final.csv.

**4.3 Temuan lain**

- **Hari besar dan akurasi.** Versi dengan dummy (M2, M3) sama atau sedikit lebih buruk daripada tanpa dummy pada orde yang sama, di training, testing 2025, dan 2026. Tidak ada bukti bahwa dummy meningkatkan akurasi. Ini tidak sama dengan terbukti tidak berpengaruh: hanya ada 3 kejadian per hari besar di training, dan efeknya tercampur dengan musim panen.

- **Pola harga mentah.** Hipotesis arah dari EDA (Daging Ayam naik saat Lebaran; kedua cabai naik saat Iduladha; Daging Ayam dan kedua cabai turun selama Ramadan) terpenuhi pada 11 dari 12 pasangan di 2025–2026. Harga cabai naik selama jendela Iduladha di 5 dari 5 tahun. Besar efeknya berubah antar tahun dan hasil ini indikatif.

- **Cabai Rawit 2026.** Dari Rp80 ribu (31 Des 2025) harga turun, sesuai arah model, tetapi lebih cepat dan lebih dalam (Rp30.250 pada 2 Apr 2026, di bawah rentang 80% model), lalu naik lagi ke Rp57.250 pada 19 Nov 2026, di atas prediksi model. Arah terbukti pada horizon 1–3 bulan; besar dan level akhirnya tidak.

- **Residual.** Normalitas ditolak di semua model (ekor tebal). Ljung-Box lag 10 menolak white noise pada Daging Ayam, Bawang Putih, dan Cabai Merah. Varians galat hari Senin 1,6–2,2 kali lebih besar. Parameter stabil antar origin (perubahan kurang dari 0,06). Karena itu interval dibuat empiris.

- **Sensitivitas.** Menghilangkan titik cabai rawit 24 Mar 2023 tidak material (skor testing 1,024 menjadi 1,019; forecast h22 bergeser 2,2% dari harga terakhir). Nilai dipertahankan.

**4.4 Galat tipikal (rolling-origin 2022–2026)**

Galat absolut persentase, format median / persentil 90.

| **Komoditas** | **h1–5**   | **h6–22**   | **h23–66**  |
|---------------|------------|-------------|-------------|
| Daging Ayam   | 1,0 / 4,2  | 3,8 / 12,0  | 7,7 / 19,3  |
| Bawang Merah  | 3,1 / 10,1 | 10,3 / 27,1 | 18,3 / 50,0 |
| Bawang Putih  | 0,0 / 3,5  | 2,2 / 8,2   | 7,1 / 19,4  |
| Cabai Merah   | 7,7 / 21,7 | 18,2 / 41,5 | 25,8 / 51,0 |
| Cabai Rawit   | 6,1 / 18,7 | 14,8 / 40,1 | 25,1 / 56,2 |

Keunggulan atas naive hanya terlihat pada kedua cabai di h23–66 (median sekitar 5 poin persen lebih rendah). Pada h ≤ 22 model dan naive praktis sama.

**4.5 Kalibrasi interval 80% di luar sampel**

Interval dikalibrasi dari galat sebelum 2026, lalu diuji pada 46 origin di 2026. Cakupan target 80%.

| **Komoditas** | **h1–22** | **h23–66** | **Catatan**                    |
|---------------|-----------|------------|--------------------------------|
| Daging Ayam   | 71,9%     | 49,1%      | Terlalu sempit di horizon jauh |
| Bawang Merah  | 91,4%     | 96,8%      | Terlalu lebar                  |
| Bawang Putih  | 72,3%     | 62,5%      | Terlalu sempit di horizon jauh |
| Cabai Merah   | 90,8%     | 90,3%      | Agak lebar                     |
| Cabai Rawit   | 73,2%     | 83,5%      | Paling mendekati target        |

Pada h1–22 interval cukup baik, tetapi pada h23–66 hasilnya berbeda per komoditas. Oleh karena itu interval diberi label perkiraan kasar, bukan interval kepercayaan 80%.

**4.6 Forecast terbaru (20 Nov 2026 – 19 Nov 2027)**

| **Komoditas** | **Harga terakhir** | **h5** | **h22 (21 Des)** | **h66 (19 Feb 2027)** | **h261** |
|---------------|--------------------|--------|------------------|-----------------------|----------|
| Daging Ayam   | 43.650             | 44.328 | 44.641           | 44.648                | 44.648   |
| Bawang Merah  | 35.000             | 35.066 | 35.066           | 35.066                | 35.066   |
| Bawang Putih  | 29.500             | 29.500 | 29.500           | 29.500                | 29.500   |
| Cabai Merah   | 74.000             | 70.025 | 60.667           | 50.657                | 46.350   |
| Cabai Rawit   | 57.250             | 55.506 | 50.979           | 45.030                | 41.227   |

Daging Ayam, Bawang Merah, dan Bawang Putih praktis datar di harga terakhir. Hanya kedua cabai yang bergerak, karena tarikan ke rata-rata. Model tidak memuat efek akhir tahun (Natal dan Tahun Baru).

**5. Cara Membaca Data Keluaran**

**5.1 File yang dipakai sistem**

Gunakan **forecast_sistem_terbaru.json** (berisi metadata dan data) atau **forecast_sistem_terbaru.csv** (kolom data saja). Isinya identik: format panjang, satu baris untuk setiap pasangan tanggal dan komoditas, total 1.305 baris (5 komoditas × 261 hari kerja), dan 330 baris di antaranya memiliki interval. File forecast_sistem_2026 adalah versi lama (data sampai 31 Des 2025) dan tidak dipakai lagi.

**5.2 Kamus kolom**

| **Kolom**                          | **Arti**                              | **Catatan**                                                       |
|------------------------------------|---------------------------------------|-------------------------------------------------------------------|
| tanggal                            | Tanggal prediksi (YYYY-MM-DD)         | Hanya hari kerja Senin–Jumat                                      |
| komoditas                          | Nama komoditas                        | Daging Ayam, Bawang Merah, Bawang Putih, Cabai Merah, Cabai Rawit |
| horizon_hk                         | Hari kerja ke-n setelah data terakhir | 1 sampai 261                                                      |
| kategori_horizon                   | Kelompok horizon                      | h1-5, h6-22, h23-66, h67+                                         |
| prediksi                           | Prediksi harga model, Rp/kg           | Dibulatkan ke Rupiah                                              |
| prediksi_naive                     | Harga terakhir (19 Nov 2026)          | Pembanding, nilainya sama di semua baris komoditas                |
| ada_interval                       | true jika horizon ≤ 66                | Penentu apakah kolom interval terisi                              |
| batas_bawah_50, batas_atas_50      | Rentang 50%                           | Kosong (null) jika ada_interval false                             |
| batas_bawah_80, batas_atas_80      | Rentang 80%                           | Kosong (null) jika ada_interval false                             |
| galat_median_pct, galat_p90_pct    | Galat tipikal historis, persen        | Kosong jika horizon \> 66                                         |
| rentang_hist_p10, rentang_hist_p90 | Rentang harga historis 2022–2026      | Selalu terisi; konteks utama untuk h67+                           |

Blok metadata di JSON memuat: sumber_data, data_terakhir, periode_forecast, dibuat_pada, satuan, model_per_komoditas, interval, kategori_horizon, dan catatan. Pakai data_terakhir untuk menampilkan tanggal pembaruan.

**5.3 Contoh membaca satu baris**

Cabai Rawit, tanggal 2026-12-21 (hari kerja ke-22, kategori h6-22): prediksi Rp50.979; naive Rp57.250; rentang 80% Rp38.429 sampai Rp73.725; galat tipikal 14,8% (median) dan 40,1% (persentil 90). Cara membacanya: model memperkirakan harga sekitar Rp51 ribu, tetapi dalam kondisi historis serupa separuh prediksi meleset lebih dari sekitar 15%, dan seperlima di antaranya bisa meleset hingga 40%.

Daging Ayam pada tanggal yang sama: prediksi Rp44.641, rentang 80% Rp39.658 sampai Rp49.680, naive Rp43.650.

import json, pandas as pd

obj = json.load(open('forecast_sistem_terbaru.json', encoding='utf-8'))

df = pd.DataFrame(obj\['data'\]); df\['tanggal'\] = pd.to_datetime(df\['tanggal'\])

print(df\[df\['tanggal'\] == '2026-12-21'\]\[\['komoditas','prediksi','prediksi_naive','batas_bawah_80','batas_atas_80'\]\])

**5.4 Cara menafsirkan angka**

- **Naive** adalah harga terakhir yang diteruskan sebagai prediksi. Karena tidak ada model yang terbukti mengalahkannya, selalu tampilkan sebagai pembanding.

- **rMAE atau skor** adalah rasio galat model terhadap naive. 1,00 berarti sama, di bawah 1 lebih baik, di atas 1 lebih buruk.

- **MAPE** adalah rata-rata meleset dalam persen. **MASE** membandingkan galat dengan selisih harga satu hari di training, sehingga nilainya besar pada horizon jauh dan bukan perbandingan langsung dengan naive.

- **h5 dan h22** artinya hari kerja ke-5 (sekitar 1 minggu) dan ke-22 (sekitar 1 bulan) ke depan.

- **Interval 50% dan 80%** dihitung dari galat historis, bukan dari asumsi distribusi normal.

**6. Panduan Integrasi Sistem**

**6.1 Logika pencarian tanggal**

1.  Jika tanggal jatuh di Sabtu atau Minggu, geser ke hari Jumat sebelumnya dan beri keterangan.

2.  Jika tanggal ≤ data_terakhir (19 Nov 2026): tampilkan **harga aktual**, bukan prediksi. File forecast tidak memuat data aktual, jadi sistem perlu menyimpan tabel harga aktual (data 2022–2026 yang sudah dibersihkan).

3.  Jika tanggal berada di 20 Nov 2026 – 19 Nov 2027: ambil baris dari file forecast.

4.  Di luar rentang: tampilkan pesan, jangan menghasilkan angka.

Fungsi prediksi() dan uji_tanggal() di Sel 22 adalah prototipe logika ini.

**6.2 Aturan tampilan**

- Jangan tampilkan angka prediksi tunggal untuk h ≤ 66 tanpa rentang di sampingnya. Beri label **perkiraan kasar**, bukan interval kepercayaan.

- Untuk h67+, tampilkan label **indikatif**, tanpa interval, dengan rentang historis P10–P90. Angka itu hanya arah menuju rata-rata historis.

- Tampilkan naive sebagai pembanding, dan jangan mengklaim model lebih akurat.

- Jangan menampilkan efek hari besar sebagai fitur; model final tidak memuatnya.

- Untuk Bawang Putih, prediksi sama dengan harga terakhir. Daging Ayam dan Bawang Merah nyaris sama. Hanya kedua cabai yang berbeda berarti dari naive, dan hanya pada h23–66.

- Prediksi hanya hari kerja; hari libur nasional diperlakukan seperti hari kerja biasa.

**6.3 Mereproduksi model di luar notebook**

Spesifikasi lima model terkunci. Untuk menghitung ulang di sistem (statsmodels 0.14.6):

from statsmodels.tsa.statespace.sarimax import SARIMAX

import numpy as np

SPEC = { \# order, transformasi, eksogen

'Daging Ayam': dict(order=(1,1,1), tf='bagi1000', exog=\[\]),

'Bawang Merah': dict(order=(1,1,0), tf='bagi1000', exog=\[\]),

'Bawang Putih': dict(order=(0,1,0), tf='log', exog=\['is_ramadan','is_lebaran'\]),

'Cabai Merah': dict(order=(1,0,0), tf='log', exog=\[\]),

'Cabai Rawit': dict(order=(1,0,0), tf='log', exog=\[\]),

}

\# trend: 'c' jika d = 0, 'n' jika d = 1; seasonal_order (0,0,0,0)

res = SARIMAX(y, exog=X, order=spec\['order'\], trend='c' if spec\['order'\]\[1\]==0 else 'n').fit(disp=False, maxiter=200)

fc = res.forecast(steps=261, exog=Xfuture) \# balik: np.exp(fc) atau fc\*1000

Dummy tahun 2027 ke atas belum ditetapkan pemerintah dan diisi 0. Dampaknya nol karena satu-satunya model berdummy (Bawang Putih) berkoefisien sekitar 0.

**6.4 Prosedur pembaruan berkala**

1.  Tambahkan data PIHPS baru ke tabel harga aktual (harian atau mingguan).

2.  Bersihkan seperti Sel 2–3: konversi tanggal dan angka, reindex hari kerja, forward fill hari libur, catat penanda isian.

3.  Perbarui kalender hari besar bila tahun baru masuk. Verifikasi tanggal resmi; bila belum ada, dummy 0.

4.  Refit kelima spesifikasi terkunci pada seluruh data (Sel 20, bagian 1). Jangan mengubah orde atau transformasi.

5.  Hitung ulang galat rolling-origin untuk interval dan galat tipikal (Sel 20, bagian 2–5). Prosesnya sekitar satu menit.

6.  Tulis file baru dengan data_terakhir yang diperbarui dan simpan salinan berversi tanggal. Sistem cukup membaca file ini.

Spesifikasi model sebaiknya ditinjau ulang sekitar setahun sekali, bukan tiap hari. Setiap perubahan spesifikasi diperlakukan sebagai tahap penelitian baru dengan data validasi yang belum pernah dipakai.

**6.5 Pemantauan (usulan, bukan hasil penelitian)**

- Bandingkan prediksi dengan harga aktual yang masuk; catat galat per horizon.

- Hitung rMAE terhadap naive dan cakupan interval 80% secara berkala.

- Tinjau model jika cakupan interval 80% berulang kali jauh di bawah sekitar 60% atau di atas sekitar 95%. Ambang ini perlu Anda sesuaikan.

- Notebook bergantung pada variabel sesi. Untuk produksi, ubah menjadi skrip atau modul (pembersihan data, kalender, model, forecast) dengan versi library yang dikunci.

**7. Keterbatasan**

- Hanya 3 kejadian per hari besar di training, dan efeknya tercampur dengan musim panen dan cuaca karena tanggalnya menumpuk di musim yang sama.

- Harga menempel dan mendekati random walk, sehingga naive sulit dikalahkan. Galat tidak berdistribusi normal dan variansnya berbeda per hari.

- Residual tidak white noise pada tiga komoditas; interval hanya perkiraan kasar dengan kalibrasi berbeda per komoditas.

- n efektif evaluasi kecil (sekitar 9 pada testing dan 2026). Selisih skor kurang dari sekitar 0,1 tidak dapat dibedakan dari kebetulan.

- Faktor eksternal (cuaca, impor, kebijakan, musim Natal dan Tahun Baru) tidak dimodelkan.

- Prediksi lebih dari 66 hari kerja tidak memiliki interval terkalibrasi. Prediksi 12 bulan hanya menunjukkan arah menuju rata-rata historis.

- Titik cabai rawit 24 Mar 2023 (26.000 → 46.750 → 30.000) belum diverifikasi ke PIHPS.

- Klaim terbatas pada Kota Padang periode 2022–2026.

**8. Daftar File Keluaran**

| **File**                                                  | **Dibuat di** | **Isi**                                  |
|-----------------------------------------------------------|---------------|------------------------------------------|
| harga_harian_bersih.csv, penanda_imputasi.csv             | Sel 3         | Harga 2022–2025 bersih dan penanda isian |
| kalender_hari_besar.csv                                   | Sel 4         | Dummy harian 2022–2026                   |
| baseline_cv_train.csv                                     | Sel 8         | Hasil baseline di training               |
| hasil_tahap1_v2_semua.csv, shortlist_tahap1_v2.csv        | Sel 12        | Semua model Tahap 1 dan shortlist        |
| hasil_tahap2_cv.csv                                       | Sel 13        | Hasil validasi 41 fold                   |
| diagnostik_residual_train.csv                             | Sel 14        | Diagnostik residual                      |
| hasil_testing_rolling.csv, hasil_testing_origin_tetap.csv | Sel 15        | Hasil testing 2025                       |
| hasil_akhir_penelitian.xlsx                               | Sel 17        | Enam sheet tabel penelitian              |
| hasil_validasi_2026_rolling.csv                           | Sel 18        | Rolling-origin 2026                      |
| log_reprodusibilitas.json                                 | Sel 19        | Versi library dan konfigurasi            |
| hasil_kalibrasi_interval_2026.csv                         | Sel 20        | Kalibrasi interval                       |
| **forecast_sistem_terbaru.csv / .json**                   | Sel 20        | **File untuk sistem**                    |
| tabel_akurasi_final.csv                                   | Sel 21        | MAE, RMSE, MAPE, MASE                    |

Grafik: eda_tren_train.png, eda_acf_pacf_train.png, diag_residual_final.png, testing_aktual_vs_prediksi.png, hasil_akhir_gabungan.png, validasi_2026.png, forecast_terbaru.png.

**9. Lingkungan dan Reprodusibilitas**

Python 3.13.7, numpy 2.4.4, pandas 2.3.3, scipy 1.17.1, statsmodels 0.14.6, matplotlib 3.10.8, joblib 1.5.3. Seed 42. File data: TabelHargaPangan1.xlsx (hash 0667e2e508678de9) dan TabelHarga2026.xlsx (hash 92c7ada1bc7c1898). Rincian konfigurasi ada di log_reprodusibilitas.json.

**10. Pekerjaan yang Tersisa**

- Verifikasi titik cabai rawit 24 Mar 2023 di PIHPS (opsional, dampaknya kecil).

- Penulisan bab hasil dan pembahasan.

- Pengubahan notebook menjadi skrip produksi untuk integrasi sistem.

- Pemantauan akurasi dan kalibrasi interval setelah sistem berjalan.
