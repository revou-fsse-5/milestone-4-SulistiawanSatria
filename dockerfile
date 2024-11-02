# Gunakan image Python sebagai dasar
FROM python:3.9-slim

# Tentukan direktori kerja di dalam container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Perbarui pip ke versi terbaru
RUN pip install --upgrade pip setuptools wheel

# Salin requirements.txt terlebih dahulu
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh proyek
COPY . .

# Tentukan port yang akan diekspos
EXPOSE 8000

# Tentukan command untuk menjalankan aplikasi
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]