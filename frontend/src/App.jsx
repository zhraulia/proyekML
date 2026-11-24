import React, { useState, useEffect } from 'react';
import {
  Calendar,
  AlertTriangle,
  Info,
  Clock,
  RefreshCw,
  CheckCircle2
} from 'lucide-react';
import './App.css';

// Helper: Dapatkan tanggal hari ini dalam format YYYY-MM-DD menurut waktu lokal peramban (tanpa toISOString)
export const getTodayLocalDateString = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// Helper: Format angka murni dengan pemisah ribuan titik
export const formatRupiahNumber = (angka) => {
  if (angka === null || angka === undefined || isNaN(angka)) return '-';
  return new Intl.NumberFormat('id-ID', {
    maximumFractionDigits: 0,
  }).format(angka);
};

// Helper: Format Rupiah lengkap untuk teks naratif
export const formatRupiah = (angka) => {
  if (angka === null || angka === undefined || isNaN(angka)) return '-';
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(angka);
};

// Helper: Format tanggal dalam bahasa Indonesia tanpa bug zona waktu
export const formatTanggalIndo = (tanggalStr) => {
  if (!tanggalStr) return '';
  try {
    const parts = tanggalStr.split('-');
    if (parts.length !== 3) return tanggalStr;
    const [year, month, day] = parts.map(Number);
    const date = new Date(year, month - 1, day);
    return new Intl.DateTimeFormat('id-ID', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(date);
  } catch {
    return tanggalStr;
  }
};

// Pemetaan kelas aksen komoditas
const KOMODITAS_CLASS = {
  'Daging Ayam': 'komoditas-ayam',
  'Bawang Merah': 'komoditas-bawang-merah',
  'Bawang Putih': 'komoditas-bawang-putih',
  'Cabai Merah': 'komoditas-cabai-merah',
  'Cabai Rawit': 'komoditas-cabai-rawit',
};

// Komponen Visualisasi Batang Rentang Prediksi (CSS-based)
const RentangVisualBar = ({ item, isH67 }) => {
  const naiveVal = item.naive;
  const predVal = item.prediksi;

  if (isH67) {
    if (!item.rentang_hist || item.rentang_hist.length < 2) return null;
    const [p10, p90] = item.rentang_hist;
    const minVal = Math.min(p10, predVal, naiveVal);
    const maxVal = Math.max(p90, predVal, naiveVal);
    const span = maxVal - minVal || 1;
    const pad = span * 0.05;
    const minBound = minVal - pad;
    const totalSpan = maxVal + pad - minBound;

    const toPct = (v) => Math.max(2, Math.min(98, ((v - minBound) / totalSpan) * 100));

    const histLeft = toPct(p10);
    const histWidth = Math.max(4, toPct(p90) - histLeft);
    const predPct = toPct(predVal);
    const naivePct = toPct(naiveVal);

    return (
      <div className="range-visual-container">
        <div className="range-visual-header">
          <span className="range-visual-title">Rentang Historis 2022–2026 (P10–P90)</span>
          <span className="range-visual-sub">{formatRupiah(p10)} – {formatRupiah(p90)}</span>
        </div>
        <div className="range-bar-track">
          {/* Batang Rentang Historis P10-P90 */}
          <div
            className="range-bar-hist"
            style={{ left: `${histLeft}%`, width: `${histWidth}%` }}
            title={`Rentang Historis: ${formatRupiah(p10)} - ${formatRupiah(p90)}`}
          />
          {/* Garis Penanda Naive */}
          <div
            className="marker-naive"
            style={{ left: `${naivePct}%` }}
            title={`Harga Terakhir (Naive): ${formatRupiah(naiveVal)}`}
          >
            <span className="marker-label marker-label-naive">Naive</span>
          </div>
          {/* Titik Penanda Prediksi Model */}
          <div
            className="marker-prediksi"
            style={{ left: `${predPct}%` }}
            title={`Prediksi Model: ${formatRupiah(predVal)}`}
          >
            <span className="marker-label marker-label-pred">Model</span>
          </div>
        </div>
        <div className="range-scale-labels">
          <span>{formatRupiah(minBound + pad)}</span>
          <span>{formatRupiah(maxVal)}</span>
        </div>
      </div>
    );
  }

  // Horizon h1–66: Ada rentang 80% dan 50%
  if (!item.rentang_80 || item.rentang_80.length < 2) return null;
  const [min80, max80] = item.rentang_80;
  const [min50, max50] = item.rentang_50 || [min80, max80];

  const minVal = Math.min(min80, predVal, naiveVal);
  const maxVal = Math.max(max80, predVal, naiveVal);
  const span = maxVal - minVal || 1;
  const pad = span * 0.05;
  const minBound = minVal - pad;
  const totalSpan = maxVal + pad - minBound;

  const toPct = (v) => Math.max(2, Math.min(98, ((v - minBound) / totalSpan) * 100));

  const left80 = toPct(min80);
  const width80 = Math.max(4, toPct(max80) - left80);
  const left50 = toPct(min50);
  const width50 = Math.max(4, toPct(max50) - left50);
  const predPct = toPct(predVal);
  const naivePct = toPct(naiveVal);

  return (
    <div className="range-visual-container">
      <div className="range-visual-header">
        <span className="range-visual-title">Rentang Perkiraan (80% & 50%)</span>
        <span className="range-visual-sub">80%: {formatRupiah(min80)} – {formatRupiah(max80)}</span>
      </div>
      <div className="range-bar-track">
        {/* Layer Rentang 80% */}
        <div
          className="range-bar-80"
          style={{ left: `${left80}%`, width: `${width80}%` }}
          title={`Rentang 80%: ${formatRupiah(min80)} - ${formatRupiah(max80)}`}
        />
        {/* Layer Rentang 50% */}
        <div
          className="range-bar-50"
          style={{ left: `${left50}%`, width: `${width50}%` }}
          title={`Rentang 50%: ${formatRupiah(min50)} - ${formatRupiah(max50)}`}
        />
        {/* Garis Penanda Naive */}
        <div
          className="marker-naive"
          style={{ left: `${naivePct}%` }}
          title={`Harga Terakhir (Naive): ${formatRupiah(naiveVal)}`}
        >
          <span className="marker-label marker-label-naive">Naive</span>
        </div>
        {/* Titik Penanda Prediksi Model */}
        <div
          className="marker-prediksi"
          style={{ left: `${predPct}%` }}
          title={`Prediksi Model: ${formatRupiah(predVal)}`}
        >
          <span className="marker-label marker-label-pred">Model</span>
        </div>
      </div>
      <div className="range-legend">
        <span className="legend-item"><span className="legend-chip chip-80" />Rentang 80%</span>
        <span className="legend-item"><span className="legend-chip chip-50" />Rentang 50%</span>
        <span className="legend-item"><span className="legend-chip chip-naive" />Naive</span>
        {item.galat_median_pct !== null && (
          <span className="typical-error-note">
            Galat tipikal: median {item.galat_median_pct}%, P90 {item.galat_p90_pct}%
          </span>
        )}
      </div>
    </div>
  );
};

export default function App() {
  const [meta, setMeta] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedKomoditas, setSelectedKomoditas] = useState('semua');
  const [predictionData, setPredictionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [metaLoading, setMetaLoading] = useState(true);
  const [error, setError] = useState(null);

  // 1. Muat metadata saat start
  useEffect(() => {
    const fetchMeta = async () => {
      try {
        setMetaLoading(true);
        const res = await fetch('/api/meta');
        if (!res.ok) throw new Error(`Gagal memuat metadata (HTTP ${res.status})`);
        const data = await res.json();
        setMeta(data);

        // 1 & 2. Tanggal awal: hari ini menurut waktu lokal peramban, dipaksa ke rentang tanggal_min - tanggal_maks
        let initialDate = getTodayLocalDateString();
        if (data.tanggal_min && initialDate < data.tanggal_min) {
          initialDate = data.tanggal_min;
        } else if (data.tanggal_maks && initialDate > data.tanggal_maks) {
          initialDate = data.tanggal_maks;
        }

        setSelectedDate(initialDate);

        // 3. Langsung muat hasil saat halaman pertama kali dibuka
        fetchPrediksi(initialDate, 'semua');
      } catch (err) {
        setError(err.message || 'Gagal tersambung ke backend.');
      } finally {
        setMetaLoading(false);
      }
    };

    fetchMeta();
  }, []);

  // 2. Fungsi ambil data prediksi / aktual
  const fetchPrediksi = async (tanggal, komoditas) => {
    if (!tanggal) return;

    setLoading(true);
    setError(null);

    try {
      const url = `/api/prediksi?tanggal=${encodeURIComponent(tanggal)}${
        komoditas && komoditas !== 'semua' ? `&komoditas=${encodeURIComponent(komoditas)}` : ''
      }`;
      const res = await fetch(url);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.pesan || `Terjadi kesalahan (Kode ${res.status})`);
      }

      setPredictionData(data);
    } catch (err) {
      setError(err.message || 'Gagal memuat data dari API.');
      setPredictionData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchPrediksi(selectedDate, selectedKomoditas);
  };

  // Filter catatan kontekstual dari array peringatan API:
  // Hapus kalimat "Model tidak terbukti lebih akurat daripada harga terakhir",
  // tetapi PERTAHANKAN catatan indikatif (h67+), penggeseran akhir pekan, dan isian hari libur
  const catatanKontekstual = (predictionData?.peringatan || []).filter(
    (p) => !p.toLowerCase().includes('tidak terbukti lebih akurat')
  );

  return (
    <div className="app-container">
      {/* ====================================================================
          HERO SECTION (55 - 65vh)
          Gambar pasar terang dengan lapisan biru tipis di atas (10-15%),
          makin ke bawah makin menyatu dengan latar biru.
          ==================================================================== */}
      <header className="hero-section">
        <img
          src="/img/pasar.jpg"
          alt="Suasana Pasar Tradisional Kota Padang"
          className="hero-bg-img"
        />
        <div className="hero-gradient-overlay" />
        <div className="hero-content">
          <div className="hero-text-block">
            <h1 className="market-title">Papan Pantauan & Prediksi Harga Pangan</h1>
            <p className="market-subtitle">
              Harga pangan harian Kota Padang (PIHPS) dan perkiraan ke depan.
            </p>
            {meta?.data_terakhir && (
              <p className="latest-data-text">
                Data terakhir: {formatTanggalIndo(meta.data_terakhir)}
              </p>
            )}
          </div>
        </div>
      </header>

      {/* ====================================================================
          KONTEN UTAMA DENGAN LATAR GRADASI BIRU MULUS
          ==================================================================== */}
      <main className="main-content">
        <div className="content-inner">
          {/* FORM PENCARIAN BERGAYA SLIP / STRIP NOTA RAPAT */}
          <section className="nota-slip-control">
            <form onSubmit={handleSubmit} className="nota-form">
              <div className="form-group date-group">
                <label htmlFor="input-date" className="control-label">
                  <Calendar size={15} /> Tanggal Pantauan
                </label>
                <input
                  id="input-date"
                  type="date"
                  className="nota-input"
                  value={selectedDate}
                  min={meta?.tanggal_min || '2022-01-03'}
                  max={meta?.tanggal_maks || '2027-11-19'}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  required
                />
                <span className="field-hint">
                  Rentang: 3 Jan 2022 – 19 Nov 2027
                </span>
              </div>

              <div className="form-group commodity-group">
                <label htmlFor="select-commodity" className="control-label">
                  Pilihan Komoditas
                </label>
                <select
                  id="select-commodity"
                  className="nota-select"
                  value={selectedKomoditas}
                  onChange={(e) => setSelectedKomoditas(e.target.value)}
                >
                  <option value="semua">Semua Komoditas (5 Komoditas)</option>
                  {meta?.komoditas?.map((k) => (
                    <option key={k} value={k}>{k}</option>
                  ))}
                </select>
                <span className="field-hint">
                  Pilih spesifik atau seluruhnya
                </span>
              </div>

              <div className="form-group action-group">
                <button
                  type="submit"
                  className="btn-nota-solid"
                  disabled={loading || metaLoading || !selectedDate}
                >
                  {loading ? (
                    <>
                      <RefreshCw size={16} className="spin-icon" /> Memuat...
                    </>
                  ) : (
                    'Lihat harga'
                  )}
                </button>
              </div>
            </form>
          </section>

          {/* BARIS STATUS TANGGAL & CATATAN KONTEKSTUAL RAMPING */}
          {predictionData && predictionData.status !== 'di_luar_rentang' && (
            <div className="status-meta-bar">
              <div className="status-left">
                <span className="status-label">Tanggal ditampilkan:</span>
                <span className="status-value">
                  {formatTanggalIndo(predictionData.tanggal_data)}
                </span>
                {predictionData.digeser_ke_jumat && (
                  <span className="status-tag-shift">
                    <Clock size={12} /> Digeser ke Jumat
                  </span>
                )}
                {predictionData.status === 'aktual' ? (
                  <span className="status-tag-mode mode-aktual">
                    <CheckCircle2 size={12} /> Riwayat Aktual
                  </span>
                ) : (
                  <>
                    <span className={`status-tag-mode mode-prediksi ${predictionData.kategori_horizon === 'h67+' ? 'mode-indikatif' : ''}`}>
                      {predictionData.label_horizon}
                    </span>
                    <span className="horizon-calc-note">
                      dihitung dari data terakhir, {formatTanggalIndo(meta?.data_terakhir || predictionData.data_terakhir)}
                    </span>
                  </>
                )}
              </div>

              {/* Catatan kecil indikatif / hari libur / pergeseran dari array API */}
              {catatanKontekstual.length > 0 && (
                <div className="status-context-notes">
                  {catatanKontekstual.map((teks, idx) => (
                    <span key={idx} className="context-note-item">
                      <Info size={13} className="context-icon" /> {teks}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* AREA KEADAAN KHUSUS: ERROR & DI LUAR RENTANG */}
          {error && (
            <div className="state-card error-card">
              <AlertTriangle size={28} className="state-icon error-icon" />
              <h3>Tidak Dapat Menampilkan Data</h3>
              <p>{error}</p>
            </div>
          )}

          {predictionData?.status === 'di_luar_rentang' && (
            <div className="state-card out-of-range-card">
              <Info size={28} className="state-icon info-icon" />
              <h3>Tanggal di Luar Rentang Sistem</h3>
              <p>{predictionData.pesan}</p>
              <div className="range-limits">
                <div className="limit-box">
                  <span className="limit-label">Data Riwayat Aktual:</span>
                  <span className="limit-val">
                    {formatTanggalIndo(predictionData.rentang_aktual[0])} s.d. {formatTanggalIndo(predictionData.rentang_aktual[1])}
                  </span>
                </div>
                <div className="limit-box">
                  <span className="limit-label">Periode Prediksi:</span>
                  <span className="limit-val">
                    {formatTanggalIndo(predictionData.rentang_prediksi[0])} s.d. {formatTanggalIndo(predictionData.rentang_prediksi[1])}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* ================================================================
              GRID KARTU HARGA KOMODITAS (LABEL HARGA / NOTA PASAR)
              - Sudut hampir persegi (radius kecil)
              - Garis tepi navy tegas & bayangan keras bergeser
              - Blok warna komoditas di sisi kiri (tanpa garis warna di atas)
              - Nama komoditas langsung jadi judul kartu
              - Angka harga tabular; "Rp" dan "/kg" dikecilkan
              ================================================================ */}
          {predictionData?.hasil && predictionData.hasil.length > 0 && (
            <section className="price-grid">
              {predictionData.hasil.map((item, idx) => {
                const komoditasClass = KOMODITAS_CLASS[item.komoditas] || '';
                const isAktual = predictionData.status === 'aktual';
                const isH67 = predictionData.kategori_horizon === 'h67+';

                return (
                  <article
                    key={item.komoditas}
                    className={`label-card ${komoditasClass}`}
                    style={{ animationDelay: `${idx * 40}ms` }}
                  >
                    {/* Lubang gantungan nota & garis perforasi */}
                    <div className="label-punch-hole" aria-hidden="true" />

                    <div className="label-card-inner">
                      {/* Header Kartu: Nama Komoditas Langsung Jadi Judul */}
                      <div className="label-top">
                        <h2 className="commodity-title">{item.komoditas}</h2>
                        <span className="label-stamp">
                          {isAktual
                            ? (item.diisi_ffill ? 'Isian Libur' : 'Aktual')
                            : (isH67 ? 'Indikatif' : 'Perkiraan')}
                        </span>
                      </div>

                      {/* Garis Perforasi Putus-putus */}
                      <div className="label-perforation" aria-hidden="true" />

                      {/* Angka Harga Utama (Bintang Visual) */}
                      <div className="price-body">
                        <div className="price-amount">
                          <span className="price-prefix">Rp</span>
                          <span className="price-digits">
                            {formatRupiahNumber(isAktual ? item.harga_aktual : item.prediksi)}
                          </span>
                          <span className="price-unit">/kg</span>
                        </div>

                        {/* Catatan bila isian forward fill */}
                        {isAktual && item.diisi_ffill && (
                          <div className="ffill-inline-note">
                            * Harga berasal dari catatan hari kerja sebelumnya (pasar tutup/hari libur).
                          </div>
                        )}

                        {/* Pembanding Naive */}
                        {!isAktual && (
                          <div className="naive-slip-row">
                            <span className="naive-slip-label">Harga terakhir (naive):</span>
                            <span className="naive-slip-val">{formatRupiah(item.naive)}/kg</span>
                          </div>
                        )}
                      </div>

                      {/* Batang Visual Rentang Ketidakpastian (Hanya saat status prediksi) */}
                      {!isAktual && (
                        <div className="card-visual-section">
                          <RentangVisualBar item={item} isH67={isH67} />
                        </div>
                      )}
                    </div>
                  </article>
                );
              })}
            </section>
          )}

          {/* FOOTER INFORMASI */}
          <footer className="market-footer">
            <div className="footer-grid">
              <div className="footer-col">
                <h3 className="footer-title">Tentang Sistem Ini</h3>
                <p className="footer-desc">
                  Sistem integrasi data harga pangan strategis Kota Padang (PIHPS)
                  periode 2022–2026 untuk keperluan mata kuliah Machine Learning.
                </p>
              </div>
              <div className="footer-col">
                <h3 className="footer-title">Metode & Keterbatasan</h3>
                <p className="footer-desc">
                  Model deret waktu SARIMAX harian. Prediksi h67+ bersifat indikatif
                  arah rata-rata historis tanpa interval terkalibrasi.
                </p>
              </div>
            </div>
            <div className="footer-bottom">
              <span>Papan Harga Pangan Kota Padang · Sistem Informasi Machine Learning</span>
            </div>
          </footer>
        </div>
      </main>
    </div>
  );
}
