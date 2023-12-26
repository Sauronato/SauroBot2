# Etapa de construcción
FROM ubuntu:latest as builder

# Instala Git, FFmpeg y otras dependencias necesarias
RUN apt-get update && \
    apt-get install -y git ffmpeg python3 python3-pip


# Clona el repositorio de GitHub
RUN git clone https://github.com/Sauronato/SauroBot2.git /ruta/del/repositorio

# Cambia al directorio del repositorio
WORKDIR /ruta/del/repositorio

# Instala los requisitos
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt

