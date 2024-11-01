# Gunakan image Python sebagai dasar
FROM python:3.9-slim

# Tentukan direktori kerja di dalam container
WORKDIR /app

# Install dependencies yang dibutuhkan oleh mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt ke dalam container
COPY requirements.txt .

# Install dependencies dari requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh proyek ke dalam direktori kerja
COPY . .

# Tentukan port yang akan diekspos
EXPOSE 8000

# Tentukan command untuk menjalankan aplikasi
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
