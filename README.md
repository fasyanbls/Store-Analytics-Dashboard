# 🎬 Store Analytics Dashboard

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)

**Interactive analytics dashboard untuk DVD Rental Database — dari KPI bisnis hingga prediksi revenue dengan Machine Learning.**

[📸 Screenshots](#-screenshots) • [🚀 Quick Start](#-quick-start) • [✨ Features](#-features) • [🗂️ Struktur Proyek](#️-struktur-proyek) • [🤖 ML Model](#-ml-model)

</div>

---

## 📸 Screenshots

> Dashboard ini memiliki **Dark Mode** dan **Light Mode** yang bisa di-toggle secara real-time.

| Dark Mode | Light Mode |
|-----------|------------|
| *(add screenshot)* | *(add screenshot)* |

---

## ✨ Features

Dashboard ini terdiri dari **5 tab analitik** yang semuanya bisa difilter berdasarkan **Toko** (Store 1 / Store 2 / All) dan **Bulan**:

### 📊 Tab 1 — Overview
- **6 KPI Cards**: Total Revenue, Active Customers, Total Rentals, Inventory, Film Titles, Avg Transaction
- **Store Comparison**: Side-by-side revenue & rental performance antar toko
- **Revenue Trend**: Grafik tren bulanan dengan breakdown per toko
- **Top Categories**: Bar chart kategori film berdasarkan revenue

### 📦 Tab 2 — Inventory & Categories
- **Revenue per Inventory Unit**: Efisiensi tiap kategori film
- **Category Rental Share**: Donut chart distribusi penyewaan
- **Inventory Utilization**: Tingkat penggunaan stok per kategori

### 👥 Tab 3 — Customers & Geo
- **World Choropleth Map**: Distribusi revenue berdasarkan negara pelanggan
- **Top Customers**: Tabel pelanggan paling aktif beserta spending-nya
- **Customer Segmentation**: Distribusi segmen pelanggan (Heavy / Regular / Casual)

### ⏱️ Tab 4 — Rental Patterns
- **Hourly Pattern**: Pola penyewaan per jam (kapan pelanggan paling aktif)
- **Day-of-Week Analysis**: Heatmap penyewaan per hari dalam seminggu
- **Rental Duration Distribution**: Berapa hari rata-rata film dipinjam

### 🤖 Tab 5 — ML Predictions
- **3-Month Revenue Forecast**: Prediksi revenue 3 bulan ke depan
- **Confidence Interval**: Range atas/bawah prediksi
- **Business Decision Simulator**: What-if scenario — simulasi dampak perubahan bisnis terhadap revenue

---

## 🗂️ Struktur Proyek

```
Store_Analytics_Dashboard/
│
├── app.py                    # Entry point — orchestrator utama
├── config.py                 # DB config, tema warna, chart helpers
├── queries.py                # Semua query SQL ke PostgreSQL
├── styles.py                 # CSS injection untuk tampilan Streamlit
├── train_revenue_model.py    # Script training ML model
│
├── tabs/
│   ├── __init__.py
│   ├── tab_overview.py       # Tab 1: KPI & trends
│   ├── tab_inventory.py      # Tab 2: Inventory & categories
│   ├── tab_customers.py      # Tab 3: Customers & geo map
│   ├── tab_patterns.py       # Tab 4: Rental patterns
│   └── tab_forecast.py       # Tab 5: ML predictions & simulator
│
├── .env.example              # Template environment variables (commit ini)
├── .env                      # Credentials aktif (JANGAN di-commit!)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- DVD Rental Database (lihat [cara install](#️-setup-database))

### 1. Clone Repository

```bash
git clone https://github.com/username/store-analytics-dashboard.git
cd store-analytics-dashboard
```

### 2. Buat Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

```bash
# Salin template
cp .env.example .env

# Edit .env dan isi dengan credentials database kamu
nano .env   # atau buka dengan text editor favoritmu
```

Isi file `.env`:
```env
DB_HOST=localhost
DB_NAME=dvdrental
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

### 5. Setup Database

```bash
# Download DVD Rental sample database
# https://www.postgresqltutorial.com/postgresql-getting-started/postgresql-sample-database/

# Buat database
psql -U postgres -c "CREATE DATABASE dvdrental;"

# Restore database
pg_restore -U postgres -d dvdrental dvdrental.tar
```

### 6. Train ML Model (Opsional)

Model sudah di-train dan harus di-generate sendiri secara lokal (file `.pkl` tidak di-commit ke Git):

```bash
python train_revenue_model.py
```

Output: `revenue_forecast_model.pkl` — dibutuhkan untuk Tab 5 (ML Predictions).

### 7. Jalankan Dashboard

```bash
streamlit run app.py
```

Buka browser di: **http://localhost:8501** 🎉

---

## 🗄️ Setup Database

DVD Rental adalah sample database PostgreSQL resmi yang merepresentasikan bisnis penyewaan film.

**Statistik database:**
| Tabel | Jumlah Record |
|-------|--------------|
| `film` | 1.000 film |
| `customer` | 599 pelanggan |
| `rental` | 16.044 transaksi |
| `payment` | 14.596 pembayaran |
| `inventory` | 4.581 item |

**Download:** https://www.postgresqltutorial.com/postgresql-getting-started/postgresql-sample-database/

---

## 🤖 ML Model

Tab 5 menggunakan **Gradient Boosting Regressor** yang di-train dengan pendekatan khusus untuk dataset kecil (hanya 5 bulan data).

### Fitur yang digunakan:
- `month_num`, `month_of_year`, `quarter` — fitur temporal
- `month_sin`, `month_cos` — cyclical encoding musiman
- `transactions`, `unique_customers`, `unique_films_rented`
- `revenue_lag1`, `transactions_lag1` — lag features
- `revenue_rolling_mean2`, `revenue_rolling_std2` — rolling statistics
- `revenue_per_customer`, `revenue_per_transaction` — ratio features

### Validasi:
Menggunakan **Leave-One-Out Cross Validation** (LOO-CV) karena keterbatasan jumlah data.

### Cara re-train:
```bash
python train_revenue_model.py
```

---

## ⚙️ Konfigurasi

Semua konfigurasi dikelola melalui environment variables di file `.env`:

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `DB_HOST` | `localhost` | Host PostgreSQL |
| `DB_NAME` | `dvdrental` | Nama database |
| `DB_USER` | `postgres` | Username database |
| `DB_PASSWORD` | *(wajib diisi)* | Password database |
| `MODEL_PATH` | `revenue_forecast_model.pkl` | Path file model ML |

---

## 🛠️ Tech Stack

| Teknologi | Kegunaan |
|-----------|----------|
| **Streamlit** | Web framework untuk dashboard interaktif |
| **PostgreSQL** | Database relasional (DVD Rental) |
| **psycopg2** | Driver koneksi Python → PostgreSQL |
| **Plotly** | Visualisasi interaktif (bar, line, choropleth, dll.) |
| **Pandas** | Manipulasi dan analisis data |
| **scikit-learn** | ML model (Gradient Boosting Regressor) |
| **python-dotenv** | Load environment variables dari `.env` |
| **SQLAlchemy** | ORM untuk training ML model |

---

## 📜 License

Proyek ini menggunakan lisensi **MIT** — bebas digunakan, dimodifikasi, dan didistribusikan.

---

## 👤 Author

**[Nama Kamu]**

- GitHub: [@username](https://github.com/username)
- LinkedIn: [linkedin.com/in/username](https://linkedin.com/in/username)

---

<div align="center">
  <sub>Built with ❤️ using Streamlit & PostgreSQL</sub>
</div>
