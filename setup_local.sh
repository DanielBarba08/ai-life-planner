#!/usr/bin/env bash
# Preparación única: crea el entorno virtual de Python e instala todas las
# dependencias, backend y frontend. Córrelo una sola vez (o de nuevo si
# cambian las dependencias). Necesita internet real — este script está
# pensado para correr en tu Terminal normal de macOS, no dentro de ningún
# sandbox sin red.
set -euo pipefail
cd "$(dirname "$0")"

echo "== Backend: creando entorno virtual e instalando dependencias =="
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt
echo "== Backend: aplicando migraciones de base de datos =="
alembic upgrade head
deactivate
cd ..

echo "== Frontend: instalando dependencias =="
cd frontend
npm install
cd ..

echo
echo "Listo. Para arrancar la app corre: ./start_local.sh"
