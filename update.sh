#!/bin/bash

echo "🚀 Inizio procedura di aggiornamento..."

# 1. Scarica l'ultima versione dell'immagine dal Container Registry
echo "⬇️ Pulling delle nuove immagini..."
docker-compose pull

# 2. Ricrea e riavvia i container (solo quelli in cui l'immagine è cambiata)
echo "🔄 Ricreazione dei container in background..."
docker-compose up -d

# 3. Pulizia
# Rimuove le immagini vecchie senza nome (dangling) che occupano giga di spazio prezioso
echo "🧹 Pulizia delle immagini vecchie..."
docker image prune -f

echo "✅ Aggiornamento completato!"
echo "🔍 Per vedere cosa sta succedendo sotto il cofano, usa: docker-compose logs -f"