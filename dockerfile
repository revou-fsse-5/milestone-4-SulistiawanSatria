# Gunakan versi Python yang lebih spesifik dan stabil
FROM python:3.9.18-slim

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

# Set versi pip yang spesifik untuk menghindari konflik
RUN pip install pip==23.0.1

# Salin requirements.txt terlebih dahulu
COPY requirements.txt .

# Install dependencies dengan versi pip yang sudah ditentukan
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh aplikasi ke /app
COPY . .

# Tentukan port yang akan diekspos
EXPOSE 8000

# Tentukan command untuk menjalankan aplikasi
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]