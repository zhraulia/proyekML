"""
Pengujian Otomatis 13 Skenario Modul Bagian 9 & Kontrak API.

PENTING sesuai instruksi pengguna:
Nilai harapan untuk batas interval diambil dari file data JSON terbaru, bukan teks tabel modul yang usang.
Contoh: Cabai Rawit 21 Des 2026 batas 80% = 38143-73843; Bawang Putih 20 Nov 2026 batas bawah 80% = 28875.
"""

import json
import pytest
from app import create_app


@pytest.fixture
def client():
    """Fixture client pengujian Flask."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# =============================================================================
# Pengujian Metadata
# =============================================================================
def test_api_meta(client):
    """Pengujian endpoint /api/meta."""
    res = client.get("/api/meta")
    assert res.status_code == 200
    data = res.get_json()
    assert "komoditas" in data
    assert len(data["komoditas"]) == 5
    assert data["data_terakhir"] == "2026-11-19"
    assert data["tanggal_min"] == "2022-01-03"
    assert data["tanggal_maks"] == "2027-11-19"
    assert data["satuan"] == "Rupiah per kg"
    assert isinstance(data["catatan"], list)


# =============================================================================
# Tabel 13 Pengujian Bagian 9 MODUL_ARAHAN.md
# =============================================================================

def test_01_prediksi_2026_12_21_semua_komoditas(client):
    """
    Uji No 1: tanggal 2026-12-21, semua komoditas
    Status prediksi, hari kerja ke-22, h6-22.
    """
    res = client.get("/api/prediksi?tanggal=2026-12-21")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "prediksi"
    assert data["horizon_hk"] == 22
    assert data["kategori_horizon"] == "h6-22"
    assert data["label_horizon"] == "sekitar 1 bulan ke depan"
    assert data["digeser_ke_jumat"] is False
    assert len(data["hasil"]) == 5

    hasil_dict = {item["komoditas"]: item for item in data["hasil"]}

    # Daging Ayam
    assert hasil_dict["Daging Ayam"]["prediksi"] == 44641
    assert hasil_dict["Daging Ayam"]["naive"] == 43650
    assert hasil_dict["Daging Ayam"]["rentang_80"] == [39658, 49680]
    assert hasil_dict["Daging Ayam"]["rentang_hist"] is None

    # Bawang Merah
    assert hasil_dict["Bawang Merah"]["prediksi"] == 35066
    assert hasil_dict["Bawang Merah"]["naive"] == 35000
    assert hasil_dict["Bawang Merah"]["rentang_80"] == [27045, 44110]
    assert hasil_dict["Bawang Merah"]["rentang_hist"] is None

    # Bawang Putih
    assert hasil_dict["Bawang Putih"]["prediksi"] == 29500
    assert hasil_dict["Bawang Putih"]["naive"] == 29500
    assert hasil_dict["Bawang Putih"]["rentang_80"] == [27000, 32000]
    assert hasil_dict["Bawang Putih"]["rentang_hist"] is None

    # Cabai Merah
    assert hasil_dict["Cabai Merah"]["prediksi"] == 60667
    assert hasil_dict["Cabai Merah"]["naive"] == 74000
    assert hasil_dict["Cabai Merah"]["rentang_80"] == [44823, 85018]
    assert hasil_dict["Cabai Merah"]["rentang_hist"] is None

    # Cabai Rawit (dari JSON: 38143 - 73843)
    assert hasil_dict["Cabai Rawit"]["prediksi"] == 50979
    assert hasil_dict["Cabai Rawit"]["naive"] == 57250
    assert hasil_dict["Cabai Rawit"]["rentang_80"] == [38143, 73843]
    assert hasil_dict["Cabai Rawit"]["rentang_hist"] is None

    # Peringatan wajib
    assert any("Perkiraan kasar" in p for p in data["peringatan"])


def test_02_prediksi_2026_11_20(client):
    """
    Uji No 2: tanggal 2026-11-20
    Hari kerja ke-1, h1-5.
    """
    res = client.get("/api/prediksi?tanggal=2026-11-20")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "prediksi"
    assert data["horizon_hk"] == 1
    assert data["kategori_horizon"] == "h1-5"
    assert data["label_horizon"] == "1 minggu ke depan"

    hasil_dict = {item["komoditas"]: item for item in data["hasil"]}

    # Daging Ayam: 43853 (43100-45013)
    assert hasil_dict["Daging Ayam"]["prediksi"] == 43853
    assert hasil_dict["Daging Ayam"]["rentang_80"] == [43100, 45013]

    # Bawang Merah: 35058 (33058-37308)
    assert hasil_dict["Bawang Merah"]["prediksi"] == 35058
    assert hasil_dict["Bawang Merah"]["rentang_80"] == [33058, 37308]

    # Bawang Putih: 29500 (dari JSON: 28875 - 30000)
    assert hasil_dict["Bawang Putih"]["prediksi"] == 29500
    assert hasil_dict["Bawang Putih"]["rentang_80"] == [28875, 30000]

    # Cabai Merah: 73146 (67799-82198)
    assert hasil_dict["Cabai Merah"]["prediksi"] == 73146
    assert hasil_dict["Cabai Merah"]["rentang_80"] == [67799, 82198]

    # Cabai Rawit: 56883 (dari JSON: 51131 - 60907)
    assert hasil_dict["Cabai Rawit"]["prediksi"] == 56883
    assert hasil_dict["Cabai Rawit"]["rentang_80"] == [51131, 60907]


def test_03_pergeseran_sabtu_2026_11_21(client):
    """
    Uji No 3: tanggal 2026-11-21 (Sabtu)
    Digeser ke 2026-11-20, digeser_ke_jumat bernilai true, hasil sama dengan no. 2.
    """
    res_sabtu = client.get("/api/prediksi?tanggal=2026-11-21")
    assert res_sabtu.status_code == 200
    data_sabtu = res_sabtu.get_json()

    assert data_sabtu["status"] == "prediksi"
    assert data_sabtu["tanggal_diminta"] == "2026-11-21"
    assert data_sabtu["tanggal_data"] == "2026-11-20"
    assert data_sabtu["digeser_ke_jumat"] is True
    assert any("Akhir pekan tidak tersedia" in p for p in data_sabtu["peringatan"])

    res_jumat = client.get("/api/prediksi?tanggal=2026-11-20")
    data_jumat = res_jumat.get_json()
    assert data_sabtu["hasil"] == data_jumat["hasil"]


def test_04_prediksi_2027_02_19(client):
    """
    Uji No 4: tanggal 2027-02-19
    Hari kerja ke-66, h23-66, masih ada interval.
    """
    res = client.get("/api/prediksi?tanggal=2027-02-19")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "prediksi"
    assert data["horizon_hk"] == 66
    assert data["kategori_horizon"] == "h23-66"
    assert data["label_horizon"] == "sekitar 3 bulan ke depan"

    hasil_dict = {item["komoditas"]: item for item in data["hasil"]}

    # Daging Ayam 44.648 (37.903–52.040)
    assert hasil_dict["Daging Ayam"]["prediksi"] == 44648
    assert hasil_dict["Daging Ayam"]["rentang_80"] == [37903, 52040]

    # Bawang Merah 35.066 (19.816–48.066)
    assert hasil_dict["Bawang Merah"]["prediksi"] == 35066
    assert hasil_dict["Bawang Merah"]["rentang_80"] == [19816, 48066]

    # Bawang Putih 29.500 (23.500–33.750)
    assert hasil_dict["Bawang Putih"]["prediksi"] == 29500
    assert hasil_dict["Bawang Putih"]["rentang_80"] == [23500, 33750]

    # Cabai Merah 50.657 (dari JSON: 33320 - 81976)
    assert hasil_dict["Cabai Merah"]["prediksi"] == 50657
    assert hasil_dict["Cabai Merah"]["rentang_80"] == [33320, 81976]

    # Cabai Rawit 45.030 (dari JSON: 29514 - 75126)
    assert hasil_dict["Cabai Rawit"]["prediksi"] == 45030
    assert hasil_dict["Cabai Rawit"]["rentang_80"] == [29514, 75126]


def test_05_prediksi_2027_05_24_h67_plus(client):
    """
    Uji No 5: tanggal 2027-05-24
    Hari kerja ke-132, h67+, tanpa interval terkalibrasi, disertai rentang historis.
    """
    res = client.get("/api/prediksi?tanggal=2027-05-24")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "prediksi"
    assert data["horizon_hk"] == 132
    assert data["kategori_horizon"] == "h67+"
    assert data["label_horizon"] == "Indikatif (tanpa interval terkalibrasi)"

    # Peringatan khusus indikatif
    assert any("Indikatif: hanya arah menuju rata-rata historis" in p for p in data["peringatan"])

    hasil_dict = {item["komoditas"]: item for item in data["hasil"]}

    # Nilai prediksi
    assert hasil_dict["Daging Ayam"]["prediksi"] == 44648
    assert hasil_dict["Bawang Merah"]["prediksi"] == 35066
    assert hasil_dict["Bawang Putih"]["prediksi"] == 29500
    assert hasil_dict["Cabai Merah"]["prediksi"] == 47118
    assert hasil_dict["Cabai Rawit"]["prediksi"] == 42173

    # Tidak ada interval terkalibrasi (null)
    for k in ["Daging Ayam", "Bawang Merah", "Bawang Putih", "Cabai Merah", "Cabai Rawit"]:
        assert hasil_dict[k]["rentang_50"] is None
        assert hasil_dict[k]["rentang_80"] is None
        assert hasil_dict[k]["galat_median_pct"] is None
        assert hasil_dict[k]["galat_p90_pct"] is None
        # Disertai rentang historis P10-P90
        assert isinstance(hasil_dict[k]["rentang_hist"], list)
        assert len(hasil_dict[k]["rentang_hist"]) == 2


def test_06_aktual_2026_04_02(client):
    """
    Uji No 6: tanggal 2026-04-02
    Status aktual: Daging Ayam 52.900, Bawang Merah 40.000, Bawang Putih 31.250,
    Cabai Merah 31.000, Cabai Rawit 30.250.
    """
    res = client.get("/api/prediksi?tanggal=2026-04-02")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "aktual"
    assert data["tanggal_data"] == "2026-04-02"

    hasil_dict = {item["komoditas"]: item for item in data["hasil"]}
    assert hasil_dict["Daging Ayam"]["harga_aktual"] == 52900
    assert hasil_dict["Bawang Merah"]["harga_aktual"] == 40000
    assert hasil_dict["Bawang Putih"]["harga_aktual"] == 31250
    assert hasil_dict["Cabai Merah"]["harga_aktual"] == 31000
    assert hasil_dict["Cabai Rawit"]["harga_aktual"] == 30250

    # Aturan 3: Kunci rentang_hist selalu ada (null jika tidak relevan)
    for k, item in hasil_dict.items():
        assert "rentang_hist" in item
        assert item["rentang_hist"] is None


def test_07_aktual_2026_11_19_data_terakhir(client):
    """
    Uji No 7: tanggal 2026-11-19
    Status aktual (data terakhir): 43.650, 35.000, 29.500, 74.000, 57.250.
    """
    res = client.get("/api/prediksi?tanggal=2026-11-19")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "aktual"
    assert data["tanggal_data"] == "2026-11-19"

    hasil_dict = {item["komoditas"]: item for item in data["hasil"]}
    assert hasil_dict["Daging Ayam"]["harga_aktual"] == 43650
    assert hasil_dict["Bawang Merah"]["harga_aktual"] == 35000
    assert hasil_dict["Bawang Putih"]["harga_aktual"] == 29500
    assert hasil_dict["Cabai Merah"]["harga_aktual"] == 74000
    assert hasil_dict["Cabai Rawit"]["harga_aktual"] == 57250


def test_08_di_luar_rentang_2022_01_01(client):
    """
    Uji No 8: tanggal 2022-01-01 (Sabtu)
    Digeser ke 2021-12-31, status di luar rentang.
    """
    res = client.get("/api/prediksi?tanggal=2022-01-01")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "di_luar_rentang"
    assert data["tanggal_diminta"] == "2022-01-01"
    assert data["tanggal_data"] == "2021-12-31"
    assert data["digeser_ke_jumat"] is True
    assert "rentang_aktual" in data
    assert "rentang_prediksi" in data


def test_09_di_luar_rentang_2028_01_10(client):
    """
    Uji No 9: tanggal 2028-01-10
    Status di luar rentang.
    """
    res = client.get("/api/prediksi?tanggal=2028-01-10")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "di_luar_rentang"
    assert data["tanggal_diminta"] == "2028-01-10"


def test_10_galat_format_tanggal(client):
    """
    Uji No 10: tanggal abc atau 21-12-2026
    Kode 400 format_tanggal.
    """
    for bad_date in ["abc", "21-12-2026", "2026-02-30", ""]:
        res = client.get(f"/api/prediksi?tanggal={bad_date}")
        assert res.status_code == 400
        data = res.get_json()
        assert data["kode"] == "format_tanggal"
        assert "pesan" in data


def test_11_galat_komoditas_tidak_dikenal(client):
    """
    Uji No 11: komoditas Beras
    Kode 400 komoditas_tidak_dikenal.
    """
    res = client.get("/api/prediksi?tanggal=2026-12-21&komoditas=Beras")
    assert res.status_code == 400
    data = res.get_json()
    assert data["kode"] == "komoditas_tidak_dikenal"
    assert "Beras" in data["pesan"]


def test_12_filter_satu_komoditas(client):
    """
    Uji No 12: tanggal 2026-12-21 dengan komoditas Cabai Rawit
    Daftar hasil hanya berisi Cabai Rawit.
    """
    res = client.get("/api/prediksi?tanggal=2026-12-21&komoditas=Cabai%20Rawit")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["hasil"]) == 1
    assert data["hasil"][0]["komoditas"] == "Cabai Rawit"
    assert data["hasil"][0]["prediksi"] == 50979


def test_13_json_sah_tanpa_nan(client):
    """
    Uji No 13: Respons no. 5 diurai dengan JSON.parse / json.loads.
    Berhasil, tanpa kata NaN, dan nilai kosong berupa null.
    """
    res = client.get("/api/prediksi?tanggal=2027-05-24")
    assert res.status_code == 200
    raw_text = res.data.decode("utf-8")

    # Pastikan tidak ada token NaN (harus null)
    assert "NaN" not in raw_text

    # Harus lolos json.loads (ekuivalen JSON.parse di peramban)
    parsed = json.loads(raw_text)
    assert parsed["status"] == "prediksi"

    # Periksa nilai null pada interval
    for item in parsed["hasil"]:
        assert item["rentang_50"] is None
        assert item["rentang_80"] is None


# =============================================================================
# Pengujian Tambahan: Catatan Forward Fill (Aturan 6) & Seri Waktu (/api/seri)
# =============================================================================

def test_catatan_forward_fill_pada_hari_libur(client):
    """
    Aturan 6: harga_aktual.csv punya kolom diisi_ffill;
    tampilkan catatan bila harga hari itu hasil isian dari hari sebelumnya.
    Contoh tanggal libur terimputasi: 2022-02-01 (Tahun Baru Imlek).
    """
    res = client.get("/api/prediksi?tanggal=2022-02-01")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "aktual"
    assert any(item["diisi_ffill"] for item in data["hasil"])
    assert any("forward fill" in p for p in data["peringatan"])


def test_api_seri_endpoint(client):
    """
    Pengujian endpoint visualisasi grafik /api/seri.
    """
    res = client.get("/api/seri?komoditas=Cabai%20Rawit")
    assert res.status_code == 200
    data = res.get_json()
    assert data["komoditas"] == "Cabai Rawit"
    assert "aktual" in data
    assert len(data["aktual"]) == 120  # 120 hari aktual terakhir
    assert "prediksi" in data
    assert len(data["prediksi"]) == 261


def test_api_validasi_2026_endpoint(client):
    """
    Pengujian endpoint khusus analisis data validasi 2026 sebelum prediksi murni.
    """
    res = client.get("/api/validasi-2026")
    assert res.status_code == 200
    data = res.get_json()
    assert "periode" in data
    assert data["jumlah_hari_kerja"] == 231
    assert "ringkasan" in data
    assert len(data["ringkasan"]) == 5
    assert "milestones" in data
    assert len(data["milestones"]) >= 5
