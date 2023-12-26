#!/bin/bash

# Verifica si el archivo .env existe
if [ -e ".env" ]; then
    echo "Archivo .env encontrado. Ejecutando el comando python3 bot.py"
    python3 bot.py
else
    echo "Error: El archivo .env no encontrado. Por favor, asegúrate de tener el archivo .env en el directorio actual."
fi