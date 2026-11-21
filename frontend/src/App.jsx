import React, { useState, useEffect } from 'react';
import {
  Calendar,
  AlertTriangle,
  Info,
  Clock,
  ArrowRight,
  RefreshCw,
  TrendingDown,
  CheckCircle2,
  HelpCircle,
  ShieldAlert
} from 'lucide-react';
import './App.css';

// Helper: Format angka Rupiah standar id-ID
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

        // Nilai tanggal default: tanggal awal prediksi atau data terakhir
        const defaultDate = data.tanggal_awal_prediksi || data.data_terakhir || '2026-11-20';
        setSelectedDate(defaultDate);

        // Ambil hasil awal
        fetchPrediksi(defaultDate, 'semua');
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

    // Aturan 4: Selalu panggil setLoading(true) sebelum fetch
    setLoading(true);
    setError(null);

    try {
      const url = `/api/prediksi?tanggal=${encodeURIComponent(tanggal)}${
        komoditas && komoditas !== 'semua' ? `&komoditas=${encodeURIComponent(komoditas)}` : ''
      }`;
      const res = await fetch(url);
      const data = await res.json();

      if (!res.ok) {
        // Ambil pesan error dari backend
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

  return (
    <div className="market-layout">
      {/* HEADER PAPAN HARGA PASAR */}
      <header className="market-header">
        <div className="header-badge">
          <span className="badge-bullet" />
          PIHPS KOTA PADANG · HARGA PANGAN HARIAN
        </div>
        <h1 className="market-title">Papan Pantauan & Prediksi Harga Pangan</h1>
        <p className="market-subtitle">
          Sistem integrasi data pasar tradisional Kota Padang berbasis model SARIMAX.
          {meta?.data_terakhir && (
            <span className="latest-data-pill">
              Data aktual terakhir: <strong>{formatTanggalIndo(meta.data_terakhir)}</strong>
            </span>
          )}
        </p>
      </header>

      {/* FORM PENCARIAN & KONTROL TANGGAL */}
      <section className="control-placard">
        <form onSubmit={handleSubmit} className="control-form">
          <div className="form-group date-group">
            <label htmlFor="input-date" className="control-label">
              <Calendar size={16} /> Pilih Tanggal Pantauan
            </label>
            <input
              id="input-date"
              type="date"
              className="market-input"
              value={selectedDate}
              min={meta?.tanggal_min || '2022-01-03'}
              max={meta?.tanggal_maks || '2027-11-19'}
              onChange={(e) => setSelectedDate(e.target.value)}
              required
            />
            <span className="field-hint">
              Tersedia: 3 Jan 2022 s.d. 19 Nov 2027
            </span>
          </div>

          <div className="form-group commodity-group">
            <label htmlFor="select-commodity" className="control-label">
              Komoditas Pangan
            </label>
            <select
              id="select-commodity"
              className="market-select"
              value={selectedKomoditas}
              onChange={(e) => setSelectedKomoditas(e.target.value)}
            >
              <option value="semua">Semua Komoditas (5 Komoditas)</option>
              {meta?.komoditas?.map((k) => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
            <span className="field-hint">
              Pilih satu komoditas atau tampilkan seluruhnya
            </span>
          </div>

          <div className="form-group action-group">
            <button
              type="submit"
              className="btn-fetch"
              disabled={loading || metaLoading || !selectedDate}
            >
              {loading ? (
                <>
                  <RefreshCw size={18} className="spin-icon" /> Memuat Data...
                </>
              ) : (
                <>
                  <ArrowRight size={18} /> Tampilkan Harga
                </>
              )}
            </button>
          </div>
        </form>
      </section>

      {/* BANNER PERINGATAN RESMI DARI BACKEND */}
      {predictionData?.peringatan && predictionData.peringatan.length > 0 && (
        <section className="warning-banner" role="alert">
          <div className="banner-icon-col">
            <ShieldAlert size={24} className="banner-alert-icon" />
          </div>
          <div className="banner-content">
            <div className="banner-title">Catatan & Peringatan Resmi Sistem:</div>
            <ul className="banner-list">
              {predictionData.peringatan.map((teks, idx) => (
                <li key={idx}>{teks}</li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* STATUS BAR: TANGGAL DATA & HORIZON */}
      {predictionData && predictionData.status !== 'di_luar_rentang' && (
        <div className="status-meta-bar">
          <div className="status-item">
            <span className="status-label">Tanggal Ditampilkan:</span>
            <span className="status-value">
              {formatTanggalIndo(predictionData.tanggal_data)}
            </span>
            {predictionData.digeser_ke_jumat && (
              <span className="shifted-tag">
                <Clock size={12} /> Digeser ke Jumat
              </span>
            )}
          </div>

          <div className="status-item">
            <span className="status-label">Kategori Status:</span>
            {predictionData.status === 'aktual' ? (
              <span className="badge-status badge-aktual">
                <CheckCircle2 size={13} /> Data Aktual Historis
              </span>
            ) : (
              <span className={`badge-status badge-prediksi ${predictionData.kategori_horizon === 'h67+' ? 'badge-indikatif' : ''}`}>
                {predictionData.label_horizon}
              </span>
            )}
          </div>
        </div>
      )}

      {/* AREA KEADAAN KHUSUS: ERROR, LOADING, DI LUAR RENTANG */}
      {error && (
        <div className="state-card error-card">
          <AlertTriangle size={32} className="state-icon error-icon" />
          <h3>Tidak Dapat Menampilkan Data</h3>
          <p>{error}</p>
        </div>
      )}

      {predictionData?.status === 'di_luar_rentang' && (
        <div className="state-card out-of-range-card">
          <Info size={32} className="state-icon info-icon" />
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
              <span className="limit-label">Periode Prediksi SARIMAX:</span>
              <span className="limit-val">
                {formatTanggalIndo(predictionData.rentang_prediksi[0])} s.d. {formatTanggalIndo(predictionData.rentang_prediksi[1])}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* GRID KARTU PAPAN HARGA KOMODITAS */}
      {predictionData?.hasil && predictionData.hasil.length > 0 && (
        <section className="price-grid">
          {predictionData.hasil.map((item, idx) => {
            const komoditasClass = KOMODITAS_CLASS[item.komoditas] || '';
            const isAktual = predictionData.status === 'aktual';
            const isH67 = predictionData.kategori_horizon === 'h67+';

            return (
              <article
                key={item.komoditas}
                className={`price-card ${komoditasClass}`}
                style={{ animationDelay: `${idx * 60}ms` }}
              >
                {/* Header Kartu */}
                <div className="card-top">
                  <div>
                    <span className="commodity-tag">Komoditas Pasar</span>
                    <h2 className="commodity-name">{item.komoditas}</h2>
                  </div>
                  {isAktual ? (
                    <span className="status-pill pill-aktual">
                      {item.diisi_ffill ? 'Isian Hari Libur' : 'Data Aktual'}
                    </span>
                  ) : (
                    <span className={`status-pill pill-forecast ${isH67 ? 'pill-indikatif' : ''}`}>
                      {isH67 ? 'Indikatif' : 'Prediksi SARIMAX'}
                    </span>
                  )}
                </div>

                {/* Angka Harga Utama (Bintang Visual) */}
                <div className="price-body">
                  <div className="price-label-small">
                    {isAktual ? 'Harga Pasar Aktual' : 'Perkiraan Harga Model'}
                  </div>
                  <div className="price-number">
                    {formatRupiah(isAktual ? item.harga_aktual : item.prediksi)}
                    <span className="unit-label">/ kg</span>
                  </div>

                  {/* Catatan bila isian forward fill */}
                  {isAktual && item.diisi_ffill && (
                    <div className="ffill-notice">
                      <Info size={14} /> Harga hari ini berasal dari catatan hari kerja sebelumnya (pasar tutup/hari libur).
                    </div>
                  )}

                  {/* Pembanding Naive (Wajib selalu tampil pada prediksi) */}
                  {!isAktual && (
                    <div className="naive-comparison-box">
                      <div className="naive-row">
                        <span className="naive-title">Pembanding Harga Terakhir (Naive):</span>
                        <span className="naive-value">{formatRupiah(item.naive)} / kg</span>
                      </div>
                      <div className="naive-disclaimer">
                        Model tidak terbukti lebih akurat daripada harga terakhir.
                      </div>
                    </div>
                  )}
                </div>

                {/* Batang Visual Rentang Ketidakpastian (Hanya saat status prediksi) */}
                {!isAktual && (
                  <div className="card-visual-section">
                    <RentangVisualBar item={item} isH67={isH67} />
                  </div>
                )}
              </article>
            );
          })}
        </section>
      )}

      {/* FOOTER INFORMASI DAN RINGKASAN MODEL */}
      <footer className="market-footer">
        <div className="footer-grid">
          <div className="footer-col">
            <h3 className="footer-title">Tentang Sistem Ini</h3>
            <p className="footer-desc">
              Sistem dibangun untuk keperluan tugas mata kuliah Machine Learning.
              Data bersumber dari Pusat Informasi Harga Pangan Strategis (PIHPS)
              Kota Padang untuk lima komoditas utama periode 2022–2026.
            </p>
          </div>
          <div className="footer-col">
            <h3 className="footer-title">Metode & Keterbatasan</h3>
            <p className="footer-desc">
              Model menggunakan analisis statistik deret waktu SARIMAX harian.
              Prediksi jangka menengah/panjang (h67+) bersifat indikatif tarikan
              rata-rata historis tanpa interval terkalibrasi. Tidak memuat efek hari besar.
            </p>
          </div>
        </div>
        <div className="footer-bottom">
          <span>Papan Harga Pangan Kota Padang · Antarmuka React 19 & Flask API</span>
        </div>
      </footer>
    </div>
  );
}
