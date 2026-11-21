import React, { useState } from 'react';
import './App.css';

function App() {
  //Deklarasi state awal
  const [sepalLength, setSepalLength] = useState('');
  const [sepalWidth, setSepalWidth] = useState('');
  const [petalLength, setPetalLength] = useState('');
  const [petalWidth, setPetalWidth] = useState('');

  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // URL API Flask Backend
  const apiUrl = 'http://127.0.0.1:5000';

  // fungsi handlePredict
  const handlePredict = async (e) => {
      if (e) e.preventDefault();
      setError(null);
      
      if (!sepalLength.trim() || !sepalWidth.trim() || !petalLength.trim() || !petalWidth.trim()) {
        setError('Mohon masukkan semua 4 nilai ukuran bunga terlebih dahulu.');
        return;
      }


      try{
      //set payload json
      const payload = {
        SepalLengthCm: sepalLength.trim(),
        SepalWidthCm: sepalWidth.trim(),
        PetalLengthCm: petalLength.trim(),
        PetalWidthCm: petalWidth.trim()
      };

      //send request ke backend
      const response = await fetch(`${apiUrl}/predict`, {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if(!response.ok || !data.success){
        throw new Error(data.error || 'Terjadi kesalahan saat memproses prediksi.');
      }

      //simpan hasil prediksi ke state
        setPrediction(data);
      }
      
      catch (err){
        setError(err.message || 'Gagal menghubungi backend Flask. Pastikan server Flask sudah berjalan.');
      } 

      finally {
        setLoading(false);
      }
  };

  const handleReset = () => {
    setSepalLength('');
    setSepalWidth('');
    setPetalLength('');
    setPetalWidth('');
    setPrediction(null);
    setError(null); 
  };

  return (
    <div className="container">
      <div className="card">
        {/* Header Judul */}
        <div className="header">
          <h1>Klasifikasi Bunga Iris</h1>
          <p>Praktikum Integrasi Model Machine Learning ke Web</p>
        </div>

        {/* Form Pengukuran Bunga */}
        <form onSubmit={handlePredict} className="form">
          <div className="form-group">
            <label>Panjang Kelopak (Sepal Length) (cm):</label>
            <input
              type="text"
              value={sepalLength}
              onChange={(e) => setSepalLength(e.target.value)}
              placeholder="Contoh: 5.1"
              className="input-field"
              autoComplete="off"
            />
          </div>

          <div className="form-group">
            <label>Lebar Kelopak (Sepal Width) (cm):</label>
            <input
              type="text"
              value={sepalWidth}
              onChange={(e) => setSepalWidth(e.target.value)}
              placeholder="Contoh: 3.5"
              className="input-field"
              autoComplete="off"
            />
          </div>

          <div className="form-group">
            <label>Panjang Mahkota (Petal Length) (cm):</label>
            <input
              type="text"
              value={petalLength}
              onChange={(e) => setPetalLength(e.target.value)}
              placeholder="Contoh: 1.4"
              className="input-field"
              autoComplete="off"
            />
          </div>

          <div className="form-group">
            <label>Lebar Mahkota (Petal Width) (cm):</label>
            <input
              type="text"
              value={petalWidth}
              onChange={(e) => setPetalWidth(e.target.value)}
              placeholder="Contoh: 0.2"
              className="input-field"
              autoComplete="off"
            />
          </div>

          {/* Kotak Pesan Error */}
          {error && <div className="error-message">{error}</div>}

          {/* Tombol Aksi */}
          <div className="button-group">
            <button type="submit" disabled={loading} className="btn-predict">
              {loading ? 'Memproses...' : 'Prediksi Spesies'}
            </button>
            <button type="button" onClick={handleReset} className="btn-reset">
              Reset Form
            </button>
          </div>
        </form>

        {/* Tampilan Hasil Klasifikasi */}
        {prediction && (
          <div className="result-box">
            <h2>Hasil Prediksi:</h2>
            <div className="species-name">{prediction.prediction}</div>

            {prediction.probabilities && prediction.probabilities.length > 0 && (
              <div className="prob-container">
                <div className="prob-title">Distribusi Probabilitas Model:</div>
                <ul className="prob-list">
                  {prediction.probabilities.map((item, idx) => (
                    <li key={idx} className="prob-item">
                      <span>{item.species}</span>
                      <span className="prob-val">{item.percentage}%</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;