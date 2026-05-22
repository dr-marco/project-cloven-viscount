# Usa un'immagine ufficiale di Python molto leggera come base
FROM python:3.10-slim

# Imposta la cartella di lavoro dentro il container
WORKDIR /app

# Copia prima solo il file requirements.txt (per sfruttare la cache di Docker)
COPY requirements.txt .

# Installa le librerie
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il resto del codice (incluso il database chroma_db pre-generato)
COPY . .

# Esponi la porta 8000 che userà FastAPI
EXPOSE 8000

# Comando di avvio del server. --host 0.0.0.0 è fondamentale nei container!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]