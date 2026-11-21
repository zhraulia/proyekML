**Modul Arahan Pembuatan Sistem Prediksi Harga Pangan (Flask dan JavaScript)**

Disusun 20 November 2026 · Untuk integrasi hasil model SARIMAX harga pangan Kota Padang · Berisi arahan dan spesifikasi, bukan kode aplikasi lengkap

**1. Tujuan dan Ruang Lingkup**

Sistem yang dibuat berupa halaman web sederhana. Pengguna memilih **komoditas** dan **tanggal**, lalu sistem menampilkan **harga aktual** (jika tanggalnya sudah lewat) atau **prediksi** lengkap dengan rentang ketidakpastian dan peringatan (jika tanggalnya di masa depan).

**Di dalam lingkup:** API Flask yang membaca file hasil model, halaman satu layar berbasis JavaScript murni, dan pengujian.

**Di luar lingkup:** melatih model di dalam web, login pengguna, dan database. Semuanya bisa ditambahkan nanti.

Empat prinsip desain:

- **API tidak menjalankan model.** Ia hanya membaca file hasil forecast. Model dilatih ulang di luar sistem (notebook atau skrip) lalu file barunya dimuat.

- **Aturan bisnis hanya ada di API.** JavaScript hanya menampilkan hasil dan tidak mengulang logika.

- **Peringatan wajib tampil.** Model tidak terbukti lebih akurat daripada harga terakhir (naive), dan interval berstatus perkiraan kasar.

- **Satu sumber data.** File forecast dan file harga aktual dimuat sekali ke memori saat aplikasi dimulai.

Dokumen pendamping: Dokumentasi Pemodelan dan Panduan Integrasi (bagian 5 dan 6) menjelaskan arti setiap kolom file keluaran.

**2. Arsitektur**

Alurnya: **Browser (HTML dan JavaScript)** memanggil dengan fetch ke **API Flask (app.py)**, yang membaca **data/forecast_sistem_terbaru.json** dan **data/harga_aktual.csv** dari memori.

| **Komponen**                  | **Tanggung jawab**                                         |
|-------------------------------|------------------------------------------------------------|
| index.html, style.css, app.js | Formulir, pemanggilan API, penampilan hasil dan peringatan |
| app.py                        | Validasi input, aturan tanggal, pembentukan respons JSON   |
| data/                         | Dua file data dan arsip versi lama                         |
| Notebook model                | Menghasilkan file forecast baru di luar sistem             |

Flask melayani halaman statis dan API dari satu alamat, sehingga **CORS tidak diperlukan**.

**3. Prasyarat dan Struktur Proyek**

- Python 3.10 atau lebih baru (Anda memakai 3.13) dan Flask 3.x. Pandas tidak wajib; modul json dan csv bawaan Python cukup.

- Peramban modern. Tidak perlu framework JavaScript.

Persiapan lingkungan di Windows:

python -m venv .venv

.venv\Scripts\activate

pip install flask waitress

pip freeze \> requirements.txt

Struktur folder yang disarankan:

sistem-prediksi-harga/

app.py

requirements.txt

data/

forecast_sistem_terbaru.json

harga_aktual.csv

arsip/

static/

index.html

style.css

app.js

tests/

test_api.py

**4. Menyiapkan Berkas Data**

**4.1 forecast_sistem_terbaru.json**

Sudah dihasilkan Sel 20. Struktur: blok metadata dan daftar data (1.305 baris: 5 komoditas × 261 hari kerja, 20 Nov 2026 – 19 Nov 2027). Salin ke folder data.

**4.2 harga_aktual.csv (perlu dibuat)**

File forecast tidak memuat harga aktual, padahal sistem perlu menjawab tanggal yang sudah lewat. Buat dari notebook (variabel df_all berisi data 2022–2026 yang sudah bersih):

harga = df_all.reset_index().melt(id_vars='tanggal', var_name='komoditas', value_name='harga')

harga\['tanggal'\] = harga\['tanggal'\].dt.strftime('%Y-%m-%d')

harga.to_csv('harga_aktual.csv', index=False)

print(harga.shape) \# harus (6370, 3) = 1274 hari x 5 komoditas

Hari libur yang kosong di sumber sudah diisi dengan harga hari sebelumnya (forward fill), jadi setiap hari kerja ada nilainya.

**4.3 Validasi saat aplikasi dimulai**

Aplikasi menolak start (dengan pesan jelas) jika salah satu syarat gagal:

- harga_aktual.csv berisi 6.370 baris, tanggal 3 Jan 2022 – 19 Nov 2026, hanya hari kerja, tanpa nilai kosong.

- File forecast berisi 1.305 baris, 261 baris per komoditas, tanggal berurutan setelah data terakhir.

- Kolom interval kosong (null) **tepat** pada baris dengan ada_interval bernilai false, dan terisi pada baris lain.

- Tanggal pertama forecast adalah hari kerja setelah tanggal terakhir data aktual.

**5. Aturan Bisnis (Inti Sistem)**

Urutan pemeriksaan setiap permintaan:

1.  Validasi tanggal (format YYYY-MM-DD, tanggal sungguhan) dan komoditas (daftar yang dikenal, atau kosong untuk semua).

2.  Jika tanggal jatuh di Sabtu atau Minggu, **mundur ke Jumat sebelumnya**, dan catat bahwa tanggal digeser.

3.  Jika tanggal sesudah penggeseran lebih awal dari 3 Jan 2022 atau lebih lambat dari 19 Nov 2027: status di luar rentang.

4.  Jika tanggal sama dengan atau lebih awal dari tanggal data terakhir (19 Nov 2026): status aktual, ambil dari harga_aktual.csv.

5.  Selain itu: status prediksi, ambil baris dari file forecast.

Penggeseran dilakukan **sebelum** pemeriksaan rentang. Contoh: Sabtu 1 Jan 2022 bergeser ke 31 Des 2021, sehingga di luar rentang.

Kategori horizon dan labelnya:

| **Kategori** | **Hari kerja ke-** | **Label di layar**                      | **Interval**                                  |
|--------------|--------------------|-----------------------------------------|-----------------------------------------------|
| h1-5         | 1–5                | 1 minggu ke depan                       | Ada                                           |
| h6-22        | 6–22               | sekitar 1 bulan ke depan                | Ada                                           |
| h23-66       | 23–66              | sekitar 3 bulan ke depan                | Ada                                           |
| h67+         | 67–261             | Indikatif (tanpa interval terkalibrasi) | Tidak ada; tampilkan rentang historis P10–P90 |

Peringatan yang disusun API (bukan JavaScript), agar teksnya satu sumber:

- Selalu: *Perkiraan kasar. Model tidak terbukti lebih akurat daripada harga terakhir (naive).*

- Horizon h67+: *Indikatif: hanya arah menuju rata-rata historis, tanpa interval terkalibrasi.*

- Tanggal digeser: *Akhir pekan tidak tersedia; ditampilkan hari Jumat sebelumnya.*

Larangan tampilan: jangan menampilkan angka prediksi tunggal tanpa rentang pada h66 ke bawah, jangan menampilkan interval pada h67+, jangan memakai istilah interval kepercayaan, dan jangan menampilkan efek hari besar sebagai fitur (model final tidak memuatnya).

**6. Spesifikasi API**

| **Endpoint**      | **Fungsi**                                                                   |
|-------------------|------------------------------------------------------------------------------|
| GET /api/meta     | Daftar komoditas, rentang tanggal, tanggal data terakhir, catatan            |
| GET /api/prediksi | Hasil untuk satu tanggal; parameter tanggal (wajib) dan komoditas (opsional) |
| GET /api/seri     | Opsional, untuk grafik: harga aktual dan prediksi satu komoditas             |
| GET /health       | Pemeriksaan hidup, mengembalikan tanggal data terakhir                       |

**6.1 /api/meta**

Berisi: komoditas (lima nama), data_terakhir (2026-11-19), tanggal_min (2022-01-03), tanggal_maks (2027-11-19), satuan (Rupiah per kg), dibuat_pada, dan catatan. Nilainya diambil dari blok metadata di file forecast. Front-end memakainya untuk mengisi dropdown dan membatasi tanggal.

**6.2 /api/prediksi**

Contoh permintaan: /api/prediksi?tanggal=2026-12-21&komoditas=Cabai%20Rawit. Jika komoditas dikosongkan atau bernilai semua, semua lima komoditas dikembalikan.

Contoh respons status prediksi (horizon 22):

{

"status": "prediksi",

"tanggal_diminta": "2026-12-21",

"tanggal_data": "2026-12-21",

"digeser_ke_jumat": false,

"horizon_hk": 22,

"kategori_horizon": "h6-22",

"label_horizon": "sekitar 1 bulan ke depan",

"data_terakhir": "2026-11-19",

"hasil": \[

{

"komoditas": "Cabai Rawit",

"prediksi": 50979,

"naive": 57250,

"rentang_80": \[38429, 73725\],

"galat_median_pct": 14.8,

"galat_p90_pct": 40.1

}

\],

"peringatan": \["Perkiraan kasar. Model tidak terbukti lebih akurat daripada harga terakhir (naive)."\]

}

Setiap elemen hasil juga memuat rentang_50 dengan bentuk sama seperti rentang_80. Pemetaan dari file: rentang_80 = \[batas_bawah_80, batas_atas_80\], rentang_50 = \[batas_bawah_50, batas_atas_50\], naive = prediksi_naive. Nilai di file sudah dibulatkan ke Rupiah, jangan dibulatkan ulang.

Elemen hasil untuk horizon h67+ (tanpa interval):

{

"komoditas": "Cabai Rawit",

"prediksi": 42173,

"naive": 57250,

"rentang_50": null,

"rentang_80": null,

"galat_median_pct": null,

"galat_p90_pct": null,

"rentang_hist": \[26000, 64500\]

}

Respons status aktual (tanggal yang sudah lewat):

{

"status": "aktual",

"tanggal_diminta": "2026-04-02",

"tanggal_data": "2026-04-02",

"digeser_ke_jumat": false,

"hasil": \[{"komoditas": "Cabai Rawit", "harga_aktual": 30250}\]

}

Respons di luar rentang (kode 200, karena permintaannya valid): status bernilai di_luar_rentang, ditambah pesan, rentang_aktual, dan rentang_prediksi.

Kesalahan input memakai kode **400** dengan isi berupa kode galat (format_tanggal atau komoditas_tidak_dikenal) dan pesan dalam bahasa Indonesia. Kesalahan tak terduga memakai kode 500 tanpa membocorkan detail internal.

**6.3 Aturan JSON**

- Nilai kosong harus null, **bukan NaN**. NaN bukan JSON yang sah dan membuat JSON.parse di peramban gagal.

- Semua tanggal berformat YYYY-MM-DD. Angka dikirim sebagai angka, bukan teks berformat.

- Nama kunci memakai huruf kecil dan garis bawah, konsisten dengan file data.

**7. Spesifikasi Tampilan**

Satu halaman, ringan, nyaman di ponsel.

**Elemen:**

- Judul, serta satu kalimat yang menyebut sumber data PIHPS Kota Padang dan tanggal data terakhir (dari /api/meta).

- Dropdown komoditas dengan pilihan Semua komoditas dan lima komoditas.

- Input tanggal (input type date) dengan batas minimum dan maksimum dari /api/meta. Tanggal awal yang disarankan: hari kerja pertama periode forecast.

- Tombol Tampilkan.

- Area hasil dan banner peringatan di atasnya.

**Hasil status prediksi:** satu kartu atau satu baris per komoditas berisi prediksi (besar), naive sebagai pembanding, rentang 80% (dan 50% bila ruang cukup), galat tipikal dengan penjelasan singkat, serta lencana label horizon. Pada h67+, ganti rentang dengan rentang historis dan lencana Indikatif. **Hasil status aktual:** satu baris per komoditas dengan label Harga aktual. Tidak ada peringatan model karena ini data nyata.

**Keadaan lain:** loading (tombol nonaktif dan teks Memuat), error (pesan dari API ditampilkan apa adanya, jangan pesan teknis), dan di luar rentang (tampilkan rentang yang tersedia).

**Format angka:** Rupiah dengan pemisah ribuan titik (di JavaScript: Intl.NumberFormat dengan locale id-ID). Tampilkan tanggal dalam bahasa Indonesia, misalnya Senin, 21 Desember 2026.

**Catatan di kaki halaman:** metode statistik time series SARIMAX, pembaruan terakhir, dan ringkasan keterbatasan. Isi catatan diambil dari API.

**8. Urutan Pengerjaan**

1.  **Data.** Buat harga_aktual.csv, salin kedua file ke folder data, dan periksa jumlah baris.

2.  **Kerangka Flask.** Satu rute untuk halaman, satu untuk /health. Pastikan jalan di komputer sendiri.

3.  **Pemuat data.** Baca kedua file saat start, jalankan validasi 4.3, simpan di memori.

4.  **/api/meta.** Uji lewat peramban.

5.  **/api/prediksi.** Implementasikan aturan bisnis bagian 5, lalu uji dengan tabel pengujian bagian 9.

6.  **Halaman web.** Mulai dari formulir dan satu panggilan fetch yang menampilkan JSON mentah. Setelah itu baru tata tampilan.

7.  **Peringatan dan keadaan khusus.** Loading, error, di luar rentang, penggeseran akhir pekan.

8.  **Pengujian otomatis dan perapian.** Tabel bagian 9 dijadikan tes.

9.  **Penyajian.** Jalankan dengan server produksi (di Windows: waitress), lalu dokumentasikan cara menjalankannya.

Setiap langkah diselesaikan dan diuji sebelum lanjut, supaya kesalahan mudah dilacak.

**9. Pengujian**

Nilai di bawah diambil dari hasil model yang sudah dihitung, jadi bisa dijadikan acuan benar atau salah.

| **No** | **Permintaan**                                  | **Hasil yang diharapkan**                                                                                                                                                                                                                                                                            |
|--------|-------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1      | tanggal 2026-12-21, semua komoditas             | Status prediksi, hari kerja ke-22, h6-22. Prediksi: Daging Ayam 44.641 (rentang 80%: 39.658–49.680), Bawang Merah 35.066 (27.045–44.110), Bawang Putih 29.500 (27.000–32.000), Cabai Merah 60.667 (44.823–85.018), Cabai Rawit 50.979 (38.429–73.725). Naive: 43.650, 35.000, 29.500, 74.000, 57.250 |
| 2      | tanggal 2026-11-20                              | Hari kerja ke-1, h1-5. Daging Ayam 43.853 (43.100–45.013), Bawang Merah 35.058 (33.058–37.308), Bawang Putih 29.500 (29.000–30.000), Cabai Merah 73.146 (67.799–82.198), Cabai Rawit 56.883 (51.131–60.943)                                                                                          |
| 3      | tanggal 2026-11-21 (Sabtu)                      | Digeser ke 2026-11-20, digeser_ke_jumat bernilai true, hasil sama dengan no. 2                                                                                                                                                                                                                       |
| 4      | tanggal 2027-02-19                              | Hari kerja ke-66, h23-66, masih ada interval. Daging Ayam 44.648 (37.903–52.040), Bawang Merah 35.066 (19.816–48.066), Bawang Putih 29.500 (23.500–33.750), Cabai Merah 50.657 (33.320–82.019), Cabai Rawit 45.030 (29.556–75.126)                                                                   |
| 5      | tanggal 2027-05-24                              | Hari kerja ke-132, h67+, tanpa interval. Daging Ayam 44.648, Bawang Merah 35.066, Bawang Putih 29.500, Cabai Merah 47.118, Cabai Rawit 42.173, disertai rentang historis                                                                                                                             |
| 6      | tanggal 2026-04-02                              | Status aktual: Daging Ayam 52.900, Bawang Merah 40.000, Bawang Putih 31.250, Cabai Merah 31.000, Cabai Rawit 30.250                                                                                                                                                                                  |
| 7      | tanggal 2026-11-19                              | Status aktual (data terakhir): 43.650, 35.000, 29.500, 74.000, 57.250                                                                                                                                                                                                                                |
| 8      | tanggal 2022-01-01 (Sabtu)                      | Digeser ke 2021-12-31, status di luar rentang                                                                                                                                                                                                                                                        |
| 9      | tanggal 2028-01-10                              | Status di luar rentang                                                                                                                                                                                                                                                                               |
| 10     | tanggal abc atau 21-12-2026                     | Kode 400 format_tanggal                                                                                                                                                                                                                                                                              |
| 11     | komoditas Beras                                 | Kode 400 komoditas_tidak_dikenal                                                                                                                                                                                                                                                                     |
| 12     | tanggal 2026-12-21 dengan komoditas Cabai Rawit | Daftar hasil hanya berisi Cabai Rawit                                                                                                                                                                                                                                                                |
| 13     | Respons no. 5 diurai dengan JSON.parse          | Berhasil, tanpa kata NaN dan nilai kosong berupa null                                                                                                                                                                                                                                                |

Selain itu uji secara manual di ponsel dan di dua peramban berbeda.

**10. Pembaruan Data**

Sistem tidak melatih model. Ketika data PIHPS baru masuk, siklusnya:

1.  Jalankan prosedur pembaruan dari Dokumentasi Pemodelan (bagian 6.4): bersihkan data, refit lima spesifikasi terkunci, hitung ulang interval.

2.  Buat harga_aktual.csv dan forecast_sistem_terbaru.json yang baru. Simpan salinan lama di data/arsip dengan tanggal pada nama file.

3.  Salin file baru ke folder data.

4.  Muat ulang di aplikasi. Dua cara: restart aplikasi (paling sederhana), atau endpoint POST /api/muat-ulang yang dilindungi token rahasia dari variabel lingkungan.

5.  Validasi bagian 4.3 dijalankan lagi; jika gagal, aplikasi tetap memakai data lama dan mencatat pesan galat.

Tambahkan tanggal data terakhir ke /health sehingga mudah dicek apakah pembaruan sudah masuk.

**11. Keamanan, Kinerja, dan Penyajian**

- Validasi semua input. Komoditas dicocokkan dengan daftar putih, tanggal diuraikan dengan fungsi tanggal resmi, dan tidak ada input yang diteruskan ke perintah sistem atau jalur file.

- Jangan menjalankan Flask dengan debug aktif di luar pengembangan. Gunakan waitress di Windows atau gunicorn di Linux.

- Data dimuat ke memori sekali, sehingga setiap permintaan hanya mencari baris. Beban 5 × 261 baris sangat ringan.

- Catat permintaan dan galat ke log tanpa data pribadi. Pasang HTTPS jika diakses publik.

- Endpoint muat ulang (jika dibuat) wajib memakai token dan tidak boleh terbuka untuk umum.

**12. Kesalahan yang Sering Terjadi**

- **NaN di JSON.** Pandas menghasilkan NaN untuk sel kosong. Ubah menjadi None sebelum dikirim.

- **Penggeseran akhir pekan setelah pemeriksaan rentang.** Urutannya harus geser dulu, baru periksa rentang.

- **Membulatkan ulang ke ribuan.** Angka di file sudah dibulatkan ke Rupiah.

- **Zona waktu.** Perlakukan tanggal sebagai teks YYYY-MM-DD, jangan diubah menjadi objek waktu dengan zona. Selisih satu hari muncul dari sini.

- **Menampilkan interval pada h67+.** Di sana kolom interval kosong; yang tampil adalah rentang historis.

- **Lupa tabel harga aktual.** File forecast tidak memuatnya.

- **Memakai file lama.** Cek data_terakhir di /health setelah pembaruan.

- **Menyebut hasil sebagai pasti.** Peringatan harus tampil walau ruang layar terbatas.

**13. Pengembangan Lanjutan (Opsional)**

- Grafik satu komoditas: 120 hari aktual terakhir, garis prediksi, dan pita interval 80% sampai h66 (memakai /api/seri dan Chart.js dari CDN).

- Tabel beberapa tanggal sekaligus dan unduh CSV.

- Penjadwalan pembaruan data otomatis dan pemantauan akurasi: bandingkan prediksi yang sudah lewat dengan harga aktual yang masuk.

- Halaman penjelasan metode dan keterbatasan, untuk dosen dan pengguna.

**14. Definisi Selesai**

- Semua 13 pengujian di bagian 9 lulus.

- Aplikasi menolak start jika data tidak valid dan menjelaskan alasannya.

- Peringatan tampil pada setiap hasil prediksi, dan tidak ada interval pada h67+.

- Respons API selalu JSON sah, tanpa NaN.

- Prosedur pembaruan data tertulis dan sudah dicoba satu kali dengan file arsip.

- README berisi cara menjalankan, struktur folder, dan cara memperbarui data.
