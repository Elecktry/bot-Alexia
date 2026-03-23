FROM python:3.11-slim

# dependências do sistema
RUN apt update && apt install -y \
    ffmpeg \
    libsodium-dev \
    gcc \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# força instalação limpa
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import nacl; print('PyNaCl OK')"

CMD ["python", "alexia.py"]