"""
Pengujian Tahap 1: Pemuat Data, Validasi Modul Bagian 4.3, dan Endpoint /health.
"""

import copy
import json
import os
import pytest
from app import create_app
from data_loader import load_and_validate_data


@pytest.fixture
def client():
    """Fixture client pengujian Flask."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """
    Memastikan endpoint /health mengembalikan status 200 dan data_terakhir yang benar.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["data_terakhir"] == "2026-11-19"


def test_api_health_endpoint(client):
    """
    Memastikan alias /api/health juga mengembalikan hasil yang sama.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["data_terakhir"] == "2026-11-19"


def test_validasi_data_normal():
    """
    Memastikan data asli lolos keempat syarat validasi Bagian 4.3 modul:
    1. 6.370 baris harga aktual, 3 Jan 2022 - 19 Nov 2026, hari kerja, tanpa kosong.
    2. 1.305 baris forecast, 261 baris per komoditas, tanggal berurutan.
    3. Kolom interval null tepat pada ada_interval == False, dan terisi saat True.
    4. Tanggal pertama forecast adalah hari kerja setelah data terakhir aktual.
    """
    data = load_and_validate_data()
    assert data["total_aktual_rows"] == 6370
    assert data["total_forecast_rows"] == 1305
    assert data["data_terakhir"] == "2026-11-19"
    assert data["tanggal_min_aktual"] == "2022-01-03"
    assert data["tanggal_maks_aktual"] == "2026-11-19"
    assert data["tanggal_min_forecast"] == "2026-11-20"
    assert data["tanggal_maks_forecast"] == "2027-11-19"
    assert len(data["komoditas"]) == 5


def test_validasi_gagal_jika_file_hilang(tmp_path):
    """
    Aplikasi menolak start (melempar ValueError) jika file data tidak ada.
    """
    with pytest.raises(ValueError, match="tidak ditemukan"):
        load_and_validate_data(data_dir=str(tmp_path))


def test_validasi_gagal_syarat_1_baris_kurang(tmp_path):
    """
    Syarat 1: Gagal jika harga_aktual.csv tidak tepat 6.370 baris.
    """
    csv_file = tmp_path / "harga_aktual.csv"
    csv_file.write_text("tanggal,komoditas,harga,diisi_ffill\n2022-01-03,Daging Ayam,48000,False\n", encoding="utf-8")
    
    # Salin forecast asli agar hanya csv yang salah
    orig_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    with open(os.path.join(orig_dir, "forecast_sistem_terbaru.json"), "r", encoding="utf-8") as f:
        (tmp_path / "forecast_sistem_terbaru.json").write_text(f.read(), encoding="utf-8")

    with pytest.raises(ValueError, match="harus berisi 6.370 baris"):
        load_and_validate_data(data_dir=str(tmp_path))


def test_validasi_gagal_syarat_3_interval_terisi_saat_ada_interval_false(tmp_path):
    """
    Syarat 3: Gagal jika kolom interval terisi pada baris ada_interval=False.
    """
    orig_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    with open(os.path.join(orig_dir, "harga_aktual.csv"), "r", encoding="utf-8") as f:
        (tmp_path / "harga_aktual.csv").write_text(f.read(), encoding="utf-8")

    with open(os.path.join(orig_dir, "forecast_sistem_terbaru.json"), "r", encoding="utf-8") as f:
        fc = json.load(f)

    # Rusak satu baris yang ada_interval=False dengan mengisi batas_bawah_80
    for r in fc["data"]:
        if not r["ada_interval"]:
            r["batas_bawah_80"] = 50000.0
            break

    with open(tmp_path / "forecast_sistem_terbaru.json", "w", encoding="utf-8") as f:
        json.dump(fc, f)

    with pytest.raises(ValueError, match="harus null ketika ada_interval=False"):
        load_and_validate_data(data_dir=str(tmp_path))


def test_validasi_gagal_syarat_4_tanggal_pertama_salah(tmp_path):
    """
    Syarat 4: Gagal jika tanggal pertama forecast bukan hari kerja setelah data terakhir.
    """
    orig_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    with open(os.path.join(orig_dir, "harga_aktual.csv"), "r", encoding="utf-8") as f:
        (tmp_path / "harga_aktual.csv").write_text(f.read(), encoding="utf-8")

    with open(os.path.join(orig_dir, "forecast_sistem_terbaru.json"), "r", encoding="utf-8") as f:
        fc = json.load(f)

    # Ubah tanggal baris pertama menjadi tanggal yang salah (bukan 2026-11-20)
    fc["data"][0]["tanggal"] = "2026-11-25"

    with open(tmp_path / "forecast_sistem_terbaru.json", "w", encoding="utf-8") as f:
        json.dump(fc, f)

    with pytest.raises(ValueError, match="seharusnya hari kerja berikutnya"):
        load_and_validate_data(data_dir=str(tmp_path))
