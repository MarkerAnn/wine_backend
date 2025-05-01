# 🧱 Startar från minimal Python-bild
FROM python:3.11-slim

# 📁 Arbetar i /app
WORKDIR /app

# 📦 Kopierar dependencies-lista
COPY requirements.txt .

# 💾 Installerar Python-dependencies
RUN pip install -r requirements.txt

# 📁 Kopierar hela projektet (inkl. app/)
COPY . .

# 🌐 Öppnar port 5000
EXPOSE 5000

# ▶️ Startar FastAPI med Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]

