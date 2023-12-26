#!/usr/bin/env python3

import os
import subprocess

# Verifica si el archivo .env existe
if os.path.exists(".env"):
    print("Archivo .env encontrado. Ejecutando el comando python3 bot.py")
    subprocess.run(["python3", "bot.py"])
else:
    print("Error: El archivo .env no encontrado. Por favor, asegúrate de tener el archivo .env en el directorio actual.")