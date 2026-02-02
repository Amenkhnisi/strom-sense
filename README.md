# ⚡ Energy Bills API - AI-Powered Anomaly Detection

> A production-ready FastAPI application for energy bill management with intelligent anomaly detection for the German energy market.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-48%20passed-success.svg)](tests/)

---

## ✨ Features

- **🔍 Smart Anomaly Detection** - 3 independent detectors (Historical, Peer, Weather-adjusted)
- **📊 Bill Management** - Upload, extract, and analyze energy bills ( Not Ready Yet  )
- **🌡️ Weather Integration** - Real weather API for accurate climate normalization
- **👥 Peer Comparison** - Compare consumption to similar households
- **📈 Automatic Metrics** - Daily averages, year-over-year changes
- **🧪 Production Ready** - 48 tests, 93% coverage

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Amenkhnisi/strom-sense.git
cd strom-sense

# Install dependencies
pip install -r requirements.txt

# Set up database
Postgress
```

Visit http://localhost:8000/docs for interactive API documentation.

---

## 🛠️ Tech Stack

- **FastAPI** - Modern web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **Open-Meteo** - Weather data API
- **pytest** - Testing

---

## 📚 API Endpoints

### Bills
```
POST   /bills/                 Upload bill
GET    /bills/{id}             Get bill details
GET    /bills/user/{user_id}   Get user's bills
```

### Anomaly Detection
```
POST   /anomalies/detect/{bill_id}        Detect anomalies
GET    /anomalies/user/{user_id}          Get user anomalies
POST   /anomalies/batch-detect            Batch process
```

### Weather
```
GET    /weather/hdd/{postal_code}/{year}  Get heating degree days
POST   /weather/prefetch                  Cache weather data
```

### Peer Statistics
```
POST   /peers/calculate                   Calculate peer stats
GET    /peers/compare/{user_id}/{year}    Compare to peers
GET    /peers/benchmark/{size}/{year}     Get benchmarks
```

---

## 🔍 Anomaly Detection

### How It Works

**3 Independent Detectors:**

1. **Historical (40%)** - Compares to previous years
2. **Peer (30%)** - Compares to similar households  
3. **Predictive (30%)** - Weather-adjusted expectations

**Combined Score:**
- 0-3: Normal ✅
- 4-6: Warning ⚠️
- 7-10: Critical 🔴

**Example Output:**
```json
{
  "has_anomaly": true,
  "severity": "critical",
  "combined_score": 7.7,
  "explanation": "Your consumption increased 40.6% compared to last year...",
  "recommendations": "• Check for new appliances\n• Review heating system...",
  "estimated_extra_cost_euros": 455.00
}
```

---

## ⚙️ Configuration

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/energy_bills_db

# Application
DEBUG=True
LOG_LEVEL=INFO
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Test Coverage:** 48 tests, 93% coverage

---

## 📁 Project Structure

```
energy-bills-api/
├── main.py                   # FastAPI application
├── database.py              # Database config
├── models.py                # SQLAlchemy models
├── schemas.py               # Pydantic schemas
├── services/                # Business logic
│   ├── metrics_service.py
│   ├── weather_service.py
│   ├── peer_service.py
│   └── anomaly_service.py
├── controllers/             # API endpoints
│   ├── bill_controller.py
│   ├── weather_controller.py
│   ├── peer_controller.py
│   └── anomaly_controller.py
└── tests/                   # Test suite
```

---

## 📊 Usage Example

```bash
# 1. Upload bill
curl -X POST "http://localhost:8000/bills/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "bill_year": 2024,
    "consumption_kwh": 4500,
    "total_cost_euros": 1575,
    "billing_start_date": "2023-12-15",
    "billing_end_date": "2024-12-14",
    "tariff_rate": 0.35
  }'

# 2. Detect anomalies
curl -X POST "http://localhost:8000/anomalies/detect/1"

# 3. View results
curl "http://localhost:8000/anomalies/user/1"
```

---

## 🎯 Key Features Explained

### Weather Normalization
- Fetches real weather data (Heating Degree Days)
- Adjusts consumption expectations based on climate
- Caches data for performance

### Peer Comparison
- Groups users by household size and property type
- Statistical analysis (z-score, percentiles)
- Benchmark ranges (excellent, good, average, high)

### Automatic Metrics
- Daily consumption averages
- Year-over-year changes
- Cost per kWh tracking

---

## 💻 Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn main:app --reload
```

---

## 📈 Performance

| Operation | Speed |
|-----------|-------|
| Bill creation | ~100ms |
| Anomaly detection | ~200ms |
| Weather (cached) | ~20ms |
| Peer comparison | ~50ms |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 📧 Contact

**GitHub**: [@Amenkhnisi](https://github.com/yourusername)

---

<div align="center">

**[API Docs](http://localhost:8000/docs)** | **[Report Bug](https://github.com/Amenkhnisi/strom-sense/issues)** | **[Request Feature](https://github.com/Amenkhnisi/strom-sense/issues)**

Made with ❤️ for the German Energy Market

</div>
