FROM python:3.11-slim

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/models && \
    python -c '
from sentence_transformers import SentenceTransformer
print("Downloading all-MiniLM-L6-v2 from Hugging Face...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model.save("/app/models/all-MiniLM-L6-v2")
print("Model successfully saved to /app/models/all-MiniLM-L6-v2")
'

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]