"""
Modul Pemuat dan Validator Data Sistem Prediksi Harga Pangan Kota Padang.

Sesuai dengan Bagian 4.3 MODUL_ARAHAN.md:
- Backend hanya membaca 'harga_aktual.csv' dan 'forecast_sistem_terbaru.json' sekali saat start.
- Melakukan validasi ketat 4 syarat integritas data.
- Menolak start (raise ValueError) jika salah satu syarat gagal.
- Menggunakan pustaka standar Python (csv, json, datetime), tanpa pandas/scikit-learn.
"""

import csv
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


KOMODITAS_RESMI = [
    "Daging Ayam",
    "Bawang Merah",
    "Bawang Putih",
    "Cabai Merah",
    "Cabai Rawit",
]

KOLOM_INTERVAL = [
    "batas_bawah_50",
    "batas_atas_50",
    "batas_bawah_80",
    "batas_atas_80",
    "galat_median_pct",
    "galat_p90_pct",
]


def next_business_day(d: datetime.date) -> datetime.date:
    """Mencari hari kerja (Senin-Jumat) berikutnya setelah tanggal d."""
    cur = d + timedelta(days=1)
    while cur.weekday() >= 5:  # 5 = Sabtu, 6 = Minggu
        cur += timedelta(days=1)
    return cur


def load_and_validate_data(data_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Membaca dan memvalidasi file harga_aktual.csv dan forecast_sistem_terbaru.json.
    
    Validasi Bagian 4.3 MODUL_ARAHAN.md:
    1. harga_aktual.csv berisi 6.370 baris, tanggal 3 Jan 2022 - 19 Nov 2026,
       hanya hari kerja, tanpa nilai kosong.
    2. File forecast berisi 1.305 baris, 261 baris per komoditas,
       tanggal berurutan setelah data terakhir.
    3. Kolom interval kosong (null/None) tepat pada baris dengan ada_interval bernilai false,
       dan terisi pada baris lain.
    4. Tanggal pertama forecast adalah hari kerja setelah tanggal terakhir data aktual.
    
    Jika salah satu syarat tidak terpenuhi, melempar ValueError dengan pesan jelas.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    path_aktual = os.path.join(data_dir, "harga_aktual.csv")
    path_forecast = os.path.join(data_dir, "forecast_sistem_terbaru.json")

    # Pastikan file ada
    if not os.path.isfile(path_aktual):
        raise ValueError(f"File harga aktual tidak ditemukan: {path_aktual}")
    if not os.path.isfile(path_forecast):
        raise ValueError(f"File forecast tidak ditemukan: {path_forecast}")

    # =========================================================================
    # 1. Membaca dan memvalidasi harga_aktual.csv
    # =========================================================================
    with open(path_aktual, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        required_fields = {"tanggal", "komoditas", "harga", "diisi_ffill"}
        if not required_fields.issubset(set(fieldnames)):
            raise ValueError(
                f"Validasi 4.3 Gagal: Kolom harga_aktual.csv tidak lengkap. "
                f"Dibutuhkan {required_fields}, ditemukan {fieldnames}"
            )
        rows_aktual = list(reader)

    # Cek jumlah baris: wajib 6.370 baris
    if len(rows_aktual) != 6370:
        raise ValueError(
            f"Validasi 4.3 Gagal: harga_aktual.csv harus berisi 6.370 baris, "
            f"tetapi ditemukan {len(rows_aktual)} baris."
        )

    tgl_aktual_min = "2022-01-03"
    tgl_aktual_maks = "2026-11-19"
    aktual_by_date_komoditas: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for idx, r in enumerate(rows_aktual, start=2):  # baris 1 header
        # Cek nilai kosong
        for col in ["tanggal", "komoditas", "harga", "diisi_ffill"]:
            val = r.get(col)
            if val is None or val.strip() == "":
                raise ValueError(
                    f"Validasi 4.3 Gagal: Nilai kosong pada harga_aktual.csv baris {idx}, kolom '{col}'."
                )

        tgl_str = r["tanggal"].strip()
        komoditas = r["komoditas"].strip()

        # Cek format tanggal dan parsing
        try:
            tgl_dt = datetime.strptime(tgl_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(
                f"Validasi 4.3 Gagal: Format tanggal tidak valid pada baris {idx}: '{tgl_str}'."
            )

        # Cek rentang tanggal
        if tgl_str < tgl_aktual_min or tgl_str > tgl_aktual_maks:
            raise ValueError(
                f"Validasi 4.3 Gagal: Tanggal '{tgl_str}' pada baris {idx} di luar rentang "
                f"{tgl_aktual_min} s.d. {tgl_aktual_maks}."
            )

        # Cek hari kerja (Senin=0 s.d. Jumat=4, Sabtu=5, Minggu=6)
        if tgl_dt.weekday() >= 5:
            raise ValueError(
                f"Validasi 4.3 Gagal: Tanggal '{tgl_str}' pada baris {idx} adalah akhir pekan. "
                "harga_aktual.csv hanya boleh memuat hari kerja."
            )

        # Cek nilai harga numerik
        try:
            harga_num = int(float(r["harga"]))
        except ValueError:
            raise ValueError(
                f"Validasi 4.3 Gagal: Harga bukan angka pada baris {idx}: '{r['harga']}'."
            )

        diisi_ffill_bool = r["diisi_ffill"].strip().lower() in ("true", "1")

        aktual_by_date_komoditas[(tgl_str, komoditas)] = {
            "harga": harga_num,
            "diisi_ffill": diisi_ffill_bool,
        }

    # =========================================================================
    # 2. Membaca dan memvalidasi forecast_sistem_terbaru.json
    # =========================================================================
    with open(path_forecast, mode="r", encoding="utf-8") as f:
        try:
            fc_json = json.load(f)
        except Exception as e:
            raise ValueError(f"Validasi 4.3 Gagal: File forecast bukan JSON yang valid: {e}")

    metadata = fc_json.get("metadata", {})
    rows_fc = fc_json.get("data", [])

    data_terakhir = metadata.get("data_terakhir", tgl_aktual_maks)
    if data_terakhir != tgl_aktual_maks:
        raise ValueError(
            f"Validasi 4.3 Gagal: metadata.data_terakhir ('{data_terakhir}') tidak sesuai "
            f"dengan tanggal akhir aktual ('{tgl_aktual_maks}')."
        )

    # Cek jumlah baris: wajib 1.305 baris
    if len(rows_fc) != 1305:
        raise ValueError(
            f"Validasi 4.3 Gagal: File forecast harus berisi 1.305 baris data, "
            f"tetapi ditemukan {len(rows_fc)} baris."
        )

    # Cek komoditas dan baris per komoditas: wajib 261 baris per komoditas
    fc_by_komoditas: Dict[str, List[Dict[str, Any]]] = {k: [] for k in KOMODITAS_RESMI}
    for idx, r in enumerate(rows_fc):
        k = r.get("komoditas")
        if k not in fc_by_komoditas:
            raise ValueError(
                f"Validasi 4.3 Gagal: Komoditas '{k}' pada baris forecast ke-{idx} tidak dikenal."
            )
        fc_by_komoditas[k].append(r)

    for k, rows_k in fc_by_komoditas.items():
        if len(rows_k) != 261:
            raise ValueError(
                f"Validasi 4.3 Gagal: Komoditas '{k}' memiliki {len(rows_k)} baris "
                "(harus tepat 261 baris)."
            )

    # Tanggal data terakhir aktual sebagai objek date
    last_actual_dt = datetime.strptime(data_terakhir, "%Y-%m-%d").date()
    expected_first_forecast_dt = next_business_day(last_actual_dt)
    expected_first_forecast_str = expected_first_forecast_dt.strftime("%Y-%m-%d")

    # =========================================================================
    # 3 & 4. Validasi tanggal berurutan, tanggal pertama, dan kolom interval
    # =========================================================================
    forecast_by_date_komoditas: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for k, rows_k in fc_by_komoditas.items():
        prev_dt: Optional[datetime.date] = None
        for i, r in enumerate(rows_k):
            tgl_str = r.get("tanggal")
            if not tgl_str:
                raise ValueError(
                    f"Validasi 4.3 Gagal: Komoditas '{k}' indeks ke-{i} tidak memiliki tanggal."
                )

            tgl_dt = datetime.strptime(tgl_str, "%Y-%m-%d").date()

            # Syarat 4: Tanggal pertama forecast adalah hari kerja setelah tanggal terakhir data aktual
            if i == 0:
                if tgl_dt != expected_first_forecast_dt:
                    raise ValueError(
                        f"Validasi 4.3 Gagal: Tanggal pertama forecast komoditas '{k}' adalah '{tgl_str}', "
                        f"seharusnya hari kerja berikutnya setelah {data_terakhir} yaitu '{expected_first_forecast_str}'."
                    )
            else:
                # Syarat 2 lanjutan: Tanggal berurutan hari kerja
                expected_next = next_business_day(prev_dt)  # type: ignore[arg-type]
                if tgl_dt != expected_next:
                    raise ValueError(
                        f"Validasi 4.3 Gagal: Tanggal forecast komoditas '{k}' tidak berurutan pada indeks {i}. "
                        f"Ditemukan '{tgl_str}', diharapkan '{expected_next.strftime('%Y-%m-%d')}'."
                    )

            prev_dt = tgl_dt

            # Syarat 3: Kolom interval kosong (null) tepat pada baris dengan ada_interval == false,
            # dan terisi pada baris lain.
            ada_interval = bool(r.get("ada_interval"))
            if not ada_interval:
                for col in KOLOM_INTERVAL:
                    if r.get(col) is not None:
                        raise ValueError(
                            f"Validasi 4.3 Gagal: Kolom '{col}' harus null ketika ada_interval=False "
                            f"(komoditas '{k}', tanggal '{tgl_str}'). Nilai ditemukan: {r.get(col)}"
                        )
            else:
                for col in KOLOM_INTERVAL:
                    if r.get(col) is None:
                        raise ValueError(
                            f"Validasi 4.3 Gagal: Kolom '{col}' tidak boleh null ketika ada_interval=True "
                            f"(komoditas '{k}', tanggal '{tgl_str}')."
                        )

            forecast_by_date_komoditas[(tgl_str, k)] = r

    # Menghitung tanggal minimum dan maksimum forecast
    all_fc_dates = sorted(list(set(r["tanggal"] for r in rows_fc)))
    tgl_fc_min = all_fc_dates[0]
    tgl_fc_maks = all_fc_dates[-1]

    return {
        "metadata": metadata,
        "komoditas": KOMODITAS_RESMI,
        "data_terakhir": data_terakhir,
        "tanggal_min_aktual": tgl_aktual_min,
        "tanggal_maks_aktual": tgl_aktual_maks,
        "tanggal_min_forecast": tgl_fc_min,
        "tanggal_maks_forecast": tgl_fc_maks,
        "aktual_by_date_komoditas": aktual_by_date_komoditas,
        "forecast_by_date_komoditas": forecast_by_date_komoditas,
        "total_aktual_rows": len(rows_aktual),
        "total_forecast_rows": len(rows_fc),
    }
