"""
Aplikasi Backend Flask Sistem Prediksi Harga Pangan Kota Padang.

Tugas: Mata Kuliah Machine Learning
Metode Model: SARIMAX (Hasil pra-hitung, backend hanya melayani API)

Tahap 1:
- Pemuat data dan validasi integritas (Bagian 4.3 MODUL_ARAHAN.md) saat startup.
- Endpoint kesehatan sistem: GET /health (dan GET /api/health).
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

# Tambahkan direktori backend ke sys.path agar impor modul lokal selalu aman
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from data_loader import load_and_validate_data

def create_app(data_dir=None):
    """Factory function untuk membuat dan mengonfigurasi aplikasi Flask."""
    app = Flask(__name__)
    CORS(app)

    # Muat data dan jalankan validasi Bagian 4.3 saat aplikasi dimulai.
    # Jika salah satu syarat validasi 4.3 gagal, fungsi ini melempar ValueError
    # sehingga aplikasi menolak start dengan pesan galat yang jelas.
    try:
        app_data = load_and_validate_data(data_dir=data_dir)
        app.config["APP_DATA"] = app_data
        app.logger.info("Data berhasil dimuat dan divalidasi sesuai modul 4.3.")
    except Exception as e:
        app.logger.error(f"Gagal memulai aplikasi: {e}")
        # Naikkan kembali exception agar proses Flask benar-benar berhenti (menolak start)
        raise

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

    return app

# Instance aplikasi default untuk dijalankan langsung atau melalui WSGI (Waitress)
app = create_app()

if __name__ == "__main__":
    # Port default 5000 sesuai konfigurasi proxy Vite di frontend
    app.run(host="127.0.0.1", port=5000, debug=True)
