#!/bin/sh

set -e

echo "Aplicando migraciones existentes..."
python -m flask --app app db upgrade

echo "Comprobando cambios en los modelos..."

if ! python -m flask --app app db check; then
    echo "Generando migración automática..."

    python -m flask --app app db migrate \
        -m "Automatic model changes"

    echo "Aplicando la nueva migración..."
    python -m flask --app app db upgrade
fi

echo "Iniciando Flask..."

exec python -m flask --app app run \
    --host=0.0.0.0 \
    --port=5000 \
    --debug