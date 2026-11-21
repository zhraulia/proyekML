"""
Aplikasi Backend Flask Sistem Prediksi Harga Pangan Kota Padang.

Tugas: Mata Kuliah Machine Learning
Metode Model: SARIMAX (Hasil pra-hitung, backend hanya melayani API)

Tahap 2:
- Pemuat data dan validasi integritas (Bagian 4.3 MODUL_ARAHAN.md) saat startup.
- Endpoint kesehatan sistem: GET /health (dan GET /api/health).
- Endpoint metadata: GET /api/meta.
- Endpoint prediksi & aktual: GET /api/prediksi.
- Endpoint seri deret waktu: GET /api/seri (opsional untuk visualisasi grafik).
- Semua aturan bisnis (Bagian 5) diterapkan di sini (backend sebagai single source of truth).
"""

import os
import re
import sys
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

# Tambahkan direktori backend ke sys.path agar impor modul lokal selalu aman
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from data_loader import KOMODITAS_RESMI, load_and_validate_data


# Pemetaan label horizon sesuai Tabel Bagian 5 MODUL_ARAHAN.md
LABEL_HORIZON = {
    "h1-5": "1 minggu ke depan",
    "h6-22": "sekitar 1 bulan ke depan",
    "h23-66": "sekitar 3 bulan ke depan",
    "h67+": "Indikatif (tanpa interval terkalibrasi)",
}


def create_app(data_dir=None):
    """Factory function untuk membuat dan mengonfigurasi aplikasi Flask."""
    app = Flask(__name__)
    CORS(app)

    # 1. Muat data dan jalankan validasi Bagian 4.3 saat aplikasi dimulai
    try:
        app_data = load_and_validate_data(data_dir=data_dir)
        app.config["APP_DATA"] = app_data
        app.logger.info("Data berhasil dimuat dan divalidasi sesuai modul 4.3.")
    except Exception as e:
        app.logger.error(f"Gagal memulai aplikasi: {e}")
        raise

    # -------------------------------------------------------------------------
    # Penanganan Kesalahan Tak Terduga (HTTP 500)
    # Sesuai Bagian 6.2: Mengembalikan JSON pesan tanpa membocorkan detail internal
    # -------------------------------------------------------------------------
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "kode": "kesalahan_server",
            "pesan": "Terjadi kesalahan internal pada server. Silakan coba beberapa saat lagi."
        }), 500

    # -------------------------------------------------------------------------
    # Route Dasar & Health Check
    # -------------------------------------------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        """Halaman awal sederhana untuk memverifikasi backend aktif."""
        return jsonify({
            "sistem": "Sistem Prediksi Harga Pangan Kota Padang",
            "status": "aktif",
            "data_terakhir": app.config["APP_DATA"]["data_terakhir"]
        }), 200

    @app.route("/health", methods=["GET"])
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """
        Endpoint pemeriksaan hidup (Health Check).
        Mengembalikan status dan tanggal data terakhir sesuai spesifikasi Modul Bagian 6 & 10.
        """
        data_terakhir = app.config["APP_DATA"]["data_terakhir"]
        return jsonify({
            "status": "ok",
            "data_terakhir": data_terakhir
        }), 200

    # -------------------------------------------------------------------------
    # Endpoint /api/meta
    # Sesuai Bagian 6.1 MODUL_ARAHAN.md
    # -------------------------------------------------------------------------
    @app.route("/api/meta", methods=["GET"])
    def get_meta():
        """
        Mengembalikan metadata sistem: komoditas, rentang tanggal, data_terakhir,
        satuan, catatan model, dan ringkasan limitasi.
        """
        data = app.config["APP_DATA"]
        meta = data["metadata"]

        return jsonify({
            "komoditas": data["komoditas"],
            "data_terakhir": data["data_terakhir"],
            "tanggal_min": data["tanggal_min_aktual"],
            "tanggal_maks": data["tanggal_maks_forecast"],
            "tanggal_awal_prediksi": data["tanggal_min_forecast"],
            "satuan": meta.get("satuan", "Rupiah per kg"),
            "dibuat_pada": meta.get("dibuat_pada"),
            "sumber_data": meta.get("sumber_data"),
            "periode_forecast": meta.get("periode_forecast"),
            "model_per_komoditas": meta.get("model_per_komoditas"),
            "interval": meta.get("interval"),
            "kategori_horizon": meta.get("kategori_horizon"),
            "catatan": meta.get("catatan", [])
        }), 200

    # -------------------------------------------------------------------------
    # Endpoint /api/prediksi
    # Sesuai Bagian 5 (Aturan Bisnis) & Bagian 6.2 (Spesifikasi API)
    # -------------------------------------------------------------------------
    @app.route("/api/prediksi", methods=["GET"])
    def get_prediksi():
        """
        Menghasilkan harga aktual atau prediksi untuk tanggal dan komoditas yang diminta.
        Parameter:
          - tanggal (wajib, format YYYY-MM-DD)
          - komoditas (opsional, jika kosong atau 'semua' mengembalikan kelima komoditas)
        """
        data = app.config["APP_DATA"]
        tgl_aktual_min = data["tanggal_min_aktual"]      # '2022-01-03'
        tgl_aktual_maks = data["tanggal_maks_aktual"]    # '2026-11-19'
        tgl_fc_min = data["tanggal_min_forecast"]        # '2026-11-20'
        tgl_fc_maks = data["tanggal_maks_forecast"]      # '2027-11-19'
        data_terakhir = data["data_terakhir"]            # '2026-11-19'

        # 1. Validasi input tanggal
        tgl_param = request.args.get("tanggal")
        if not tgl_param or not str(tgl_param).strip():
            return jsonify({
                "kode": "format_tanggal",
                "pesan": "Parameter 'tanggal' wajib diisi dengan format YYYY-MM-DD (contoh: 2026-12-21)."
            }), 400

        tgl_param = tgl_param.strip()
        # Periksa pola YYYY-MM-DD
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", tgl_param):
            return jsonify({
                "kode": "format_tanggal",
                "pesan": f"Format tanggal '{tgl_param}' tidak valid. Gunakan format YYYY-MM-DD (contoh: 2026-12-21)."
            }), 400

        try:
            req_dt = datetime.strptime(tgl_param, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({
                "kode": "format_tanggal",
                "pesan": f"Nilai tanggal '{tgl_param}' bukan tanggal kalender yang sungguhan."
            }), 400

        # 1. Validasi komoditas
        komoditas_param = request.args.get("komoditas", "").strip()
        if not komoditas_param or komoditas_param.lower() == "semua":
            target_komoditas = KOMODITAS_RESMI
        elif komoditas_param in KOMODITAS_RESMI:
            target_komoditas = [komoditas_param]
        else:
            return jsonify({
                "kode": "komoditas_tidak_dikenal",
                "pesan": f"Komoditas '{komoditas_param}' tidak dikenal. Pilihan yang tersedia: {', '.join(KOMODITAS_RESMI)}."
            }), 400

        # 2. Aturan Bisnis 2: Jika tanggal jatuh di Sabtu (5) atau Minggu (6), mundur ke Jumat sebelumnya
        weekday = req_dt.weekday()
        if weekday == 5:  # Sabtu -> Jumat (-1 hari)
            shifted_dt = req_dt - timedelta(days=1)
            digeser_ke_jumat = True
        elif weekday == 6:  # Minggu -> Jumat (-2 hari)
            shifted_dt = req_dt - timedelta(days=2)
            digeser_ke_jumat = True
        else:
            shifted_dt = req_dt
            digeser_ke_jumat = False

        tanggal_data = shifted_dt.strftime("%Y-%m-%d")

        # 3. Aturan Bisnis 3: Periksa rentang setelah penggeseran
        # Jika lebih awal dari 3 Jan 2022 atau lebih lambat dari 19 Nov 2027: status di luar rentang
        if tanggal_data < tgl_aktual_min or tanggal_data > tgl_fc_maks:
            return jsonify({
                "status": "di_luar_rentang",
                "tanggal_diminta": tgl_param,
                "tanggal_data": tanggal_data,
                "digeser_ke_jumat": digeser_ke_jumat,
                "pesan": (
                    f"Tanggal {tanggal_data} berada di luar rentang data yang tersedia "
                    f"({tgl_aktual_min} s.d. {tgl_fc_maks})."
                ),
                "rentang_aktual": [tgl_aktual_min, tgl_aktual_maks],
                "rentang_prediksi": [tgl_fc_min, tgl_fc_maks]
            }), 200

        # 4. Aturan Bisnis 4: Jika tanggal <= tanggal data terakhir (19 Nov 2026): status aktual
        if tanggal_data <= data_terakhir:
            hasil_aktual = []
            any_ffill = False

            for k in target_komoditas:
                item = data["aktual_by_date_komoditas"].get((tanggal_data, k))
                if item is not None:
                    is_ffill = bool(item.get("diisi_ffill", False))
                    if is_ffill:
                        any_ffill = True
                    hasil_aktual.append({
                        "komoditas": k,
                        "harga_aktual": int(item["harga"]),
                        "diisi_ffill": is_ffill,
                        # Aturan 3: Kunci rentang_hist selalu ada (null jika tidak relevan)
                        "rentang_hist": None
                    })

            peringatan_aktual = []
            if digeser_ke_jumat:
                peringatan_aktual.append("Akhir pekan tidak tersedia; ditampilkan hari Jumat sebelumnya.")
            if any_ffill:
                peringatan_aktual.append(
                    "Harga pada tanggal ini merupakan hasil isian dari hari sebelumnya (forward fill) "
                    "karena hari libur/data tidak tersedia."
                )

            return jsonify({
                "status": "aktual",
                "tanggal_diminta": tgl_param,
                "tanggal_data": tanggal_data,
                "digeser_ke_jumat": digeser_ke_jumat,
                "data_terakhir": data_terakhir,
                "hasil": hasil_aktual,
                "peringatan": peringatan_aktual
            }), 200

        # 5. Aturan Bisnis 5: Selain itu: status prediksi (ambil dari file forecast)
        hasil_prediksi = []
        horizon_hk = None
        kategori_horizon = None

        for k in target_komoditas:
            r = data["forecast_by_date_komoditas"].get((tanggal_data, k))
            if r is not None:
                if horizon_hk is None:
                    horizon_hk = r["horizon_hk"]
                    kategori_horizon = r["kategori_horizon"]

                ada_interval = bool(r.get("ada_interval", False))

                if ada_interval:
                    rentang_50 = [int(round(r["batas_bawah_50"])), int(round(r["batas_atas_50"]))]
                    rentang_80 = [int(round(r["batas_bawah_80"])), int(round(r["batas_atas_80"]))]
                    galat_median = float(r["galat_median_pct"]) if r.get("galat_median_pct") is not None else None
                    galat_p90 = float(r["galat_p90_pct"]) if r.get("galat_p90_pct") is not None else None
                    # Aturan 3: Kunci rentang_hist selalu ada (null jika tidak relevan)
                    rentang_hist = None
                else:
                    # Horizon h67+: Tanpa interval, tampilkan rentang historis P10-P90
                    rentang_50 = None
                    rentang_80 = None
                    galat_median = None
                    galat_p90 = None
                    rentang_hist = [int(round(r["rentang_hist_p10"])), int(round(r["rentang_hist_p90"]))]

                hasil_prediksi.append({
                    "komoditas": k,
                    "prediksi": int(round(r["prediksi"])),
                    "naive": int(round(r["prediksi_naive"])),
                    "rentang_50": rentang_50,
                    "rentang_80": rentang_80,
                    "galat_median_pct": galat_median,
                    "galat_p90_pct": galat_p90,
                    "rentang_hist": rentang_hist
                })

        label_h = LABEL_HORIZON.get(kategori_horizon, kategori_horizon)

        # Susun peringatan terpusat dari backend sesuai Modul Bagian 5
        peringatan_prediksi = [
            "Perkiraan kasar. Model tidak terbukti lebih akurat daripada harga terakhir (naive)."
        ]
        if kategori_horizon == "h67+":
            peringatan_prediksi.append(
                "Indikatif: hanya arah menuju rata-rata historis, tanpa interval terkalibrasi."
            )
        if digeser_ke_jumat:
            peringatan_prediksi.append(
                "Akhir pekan tidak tersedia; ditampilkan hari Jumat sebelumnya."
            )

        return jsonify({
            "status": "prediksi",
            "tanggal_diminta": tgl_param,
            "tanggal_data": tanggal_data,
            "digeser_ke_jumat": digeser_ke_jumat,
            "horizon_hk": horizon_hk,
            "kategori_horizon": kategori_horizon,
            "label_horizon": label_h,
            "data_terakhir": data_terakhir,
            "hasil": hasil_prediksi,
            "peringatan": peringatan_prediksi
        }), 200

    # -------------------------------------------------------------------------
    # Endpoint /api/seri (Opsional, untuk grafik visualisasi deret waktu)
    # Sesuai Bagian 6 & 13 MODUL_ARAHAN.md
    # -------------------------------------------------------------------------
    @app.route("/api/seri", methods=["GET"])
    def get_seri():
        """
        Mengembalikan data deret waktu untuk grafik satu komoditas:
        - 120 hari aktual terakhir
        - Garis prediksi dan interval hingga horizon prediksi
        """
        data = app.config["APP_DATA"]
        komoditas_param = request.args.get("komoditas", "Cabai Rawit").strip()

        if komoditas_param not in KOMODITAS_RESMI:
            return jsonify({
                "kode": "komoditas_tidak_dikenal",
                "pesan": f"Komoditas '{komoditas_param}' tidak dikenal. Pilihan yang tersedia: {', '.join(KOMODITAS_RESMI)}."
            }), 400

        # Ambil 120 hari kerja aktual terakhir
        unique_dates_aktual = sorted(list(set(t for t, k in data["aktual_by_date_komoditas"].keys())))
        recent_aktual_dates = unique_dates_aktual[-120:]
        seri_aktual = []
        for t in recent_aktual_dates:
            item = data["aktual_by_date_komoditas"][(t, komoditas_param)]
            seri_aktual.append({
                "tanggal": t,
                "harga": item["harga"],
                "diisi_ffill": item["diisi_ffill"]
            })

        # Ambil data forecast untuk komoditas tersebut
        unique_dates_fc = sorted(list(set(t for t, k in data["forecast_by_date_komoditas"].keys())))
        seri_fc = []
        for t in unique_dates_fc:
            r = data["forecast_by_date_komoditas"][(t, komoditas_param)]
            ada_int = bool(r.get("ada_interval", False))
            seri_fc.append({
                "tanggal": t,
                "horizon_hk": r["horizon_hk"],
                "prediksi": int(round(r["prediksi"])),
                "naive": int(round(r["prediksi_naive"])),
                "batas_bawah_80": int(round(r["batas_bawah_80"])) if ada_int else None,
                "batas_atas_80": int(round(r["batas_atas_80"])) if ada_int else None,
                "rentang_hist": [int(round(r["rentang_hist_p10"])), int(round(r["rentang_hist_p90"]))] if not ada_int else None
            })

        return jsonify({
            "komoditas": komoditas_param,
            "data_terakhir": data["data_terakhir"],
            "aktual": seri_aktual,
            "prediksi": seri_fc
        }), 200

    return app


# Instance aplikasi default untuk dijalankan langsung atau melalui WSGI (Waitress)
app = create_app()

if __name__ == "__main__":
    # Port default 5000 sesuai konfigurasi proxy Vite di frontend
    app.run(host="127.0.0.1", port=5000, debug=True)
