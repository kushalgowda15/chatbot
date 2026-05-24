# 🛡️ Karnataka Disaster Management AI Assistant (EOC Suite)
An industry-grade, production-ready Kannada multilingual disaster management response assistant. Featuring a modular architecture, hybrid retrieval (FAISS + BM25), real-time alerts integration, automated emergency mode routing, dynamic analytics, and fully offline fallback operation.

---

## 🏗️ Project Architecture
```text
.
├── config.py                # Centralized validation, paths, and model settings
├── app.py                   # Production Flask application factory entry point
├── voice_agent.py           # CLI Voice Assistant micro-loop
├── chatbot.py               # Legacy compatibility shim
├── requirements.txt         # Production-pinned python dependencies
├── Dockerfile               # Deployment container instruction
├── docker-compose.yml       # Multi-service volume and environment configurations
├── services/                # Modular service layer
│   ├── __init__.py
│   ├── chatbot_service.py   # Hybrid retrieval (FAISS + BM25) and session memory
│   ├── severity_service.py  # Emergency level keyword confidence scoring
│   ├── offline_service.py   # Rule-based fallback database (no network required)
│   ├── alerts_service.py    # OpenWeatherMap + IMD RSS live alerts fetching
│   ├── voice_service.py     # Whisper STT + async Edge TTS pipelines
│   └── analytics_service.py # In-memory thread-safe usage metric logger
├── routes/                  # Blueprint API Controllers
│   ├── __init__.py
│   ├── chat_routes.py       # Speech/text interaction endpoints
│   ├── alert_routes.py      # Live weather and alerts feed endpoints
│   ├── shelter_routes.py    # Active relief camps and capacity feeds
│   ├── analytics_routes.py  # Live stats feed for the system dashboard
│   └── health_routes.py     # Component monitoring and health status checks
├── dataset/                 # Dataset sources
│   ├── final_clean_dataset.jsonl
│   └── processed/
├── templates/
│   └── index.html           # Upgraded modern responsive EOC dashboard
└── static/
    ├── css/styles.css       # Premium dynamic glassmorphism and theme styles
    ├── js/main.js           # Real-time WebSocket-like polling and oscilloscope
    └── audio/               # UUID-managed TTS recordings directory
```

---

## 🚀 Setup & Local Execution

### 1. Prerequisites
Ensure you have native Windows Python 3.12 (or Python 3.11+) installed. Avoid using MSYS2-compiled Python builds to prevent `faiss-cpu` wheel compatibility issues.

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
# API KEYS
GROQ_API_KEY=gsk_...         # Obtain from console.groq.com
OPENWEATHER_API_KEY=...      # Optional: for live weather alerts

# SERVER CONFIG
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=False
SECRET_KEY=kannada-disaster-ai-secret-2026

# MODELS CONFIG
GROQ_MODEL=llama-3.3-70b-versatile
WHISPER_MODEL_SIZE=small
```

### 3. Install Dependencies
```bash
# Create native virtual environment
python -m venv .venv_native
.venv_native\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 4. Build the Vector Index
Generate the FAISS vector database and metadata JSON once before starting the app:
```bash
python scripts/embeddings.py
```
This builds `vectorstore/disaster_index.faiss` and `vectorstore/disaster_metadata.json`.

### 5. Launch the Server
```bash
python app.py
```
Visit `http://127.0.0.1:5001` in your browser.

---

## 🐳 Docker Deployment

### Run using Docker Compose
Deploy instantly inside lightweight containers:
```bash
# Build and start services
docker-compose up --build -d

# Check running status
docker-compose ps
```
The server will be exposed on `http://localhost:5000` with persistent storage mapped for your dataset index and generated audio files.

---

## 💡 Key Design Enhancements

### 1. Hybrid Search Fusion (RAG)
Matches user queries against the disaster corpus using **FAISS** vector search (dense embeddings) and **BM25** keyword search (sparse indexing). The scores are fused (`0.65 FAISS + 0.35 BM25`) and evaluated against a cosine similarity threshold (`0.30`) to block irrelevant queries.

### 2. Live Severity Detection & Auto-Emergency State
Every input text is analyzed by `services/severity_service.py` to identify danger level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). If `HIGH` or `CRITICAL` keywords match (e.g. "ಮನೆಯೊಳಗೆ ನೀರು ನುಗ್ಗಿದೆ" / "ಪ್ರವಾಹದಲ್ಲಿ ಸಿಲುಕಿದ್ದಾರೆ"), the system automatically activates **Emergency Mode** on the frontend, flashing alert styles, opening a live recording visualizer, and prioritizing evacuation instructions.

### 3. Voice Oscilloscope and Acoustic Panic Detection
When the user records audio from their microphone, the browser visualizes the voice wave onto a canvas. If the volume amplitude exceeds the panic threshold (0.18 RMS), the system detects vocal stress and immediately locks into **Emergency Mode** ahead of the transcription, providing faster safety assurance.

### 4. 100% Guaranteed Offline Fallback
If the internet goes down or the Groq API key is invalid/rate-limited, the system automatically falls back to an offline rule-based FAQ retriever. This returns critical, curated Kannada safety answers instantly from local files without requiring cloud LLM connectivity.

### 5. Analytics Dashboard & API Monitoring
Clicking the chart icon in the header displays a live visual analytics dashboard. It tracks total queries, average response latency, hourly trends, category popularity, and severity distribution using Chart.js.
