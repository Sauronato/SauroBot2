# Etapa de construcción
FROM ubuntu:latest as builder

# Instala Git, FFmpeg y otras dependencias necesarias
RUN apt-get update && \
    apt-get install -y git ffmpeg python3 python3-pip

RUN mkdir /home/container/

# Clona el repositorio de GitHub
RUN git clone https://github.com/Sauronato/SauroBot2.git /home/container/

# Cambia al directorio del repositorio
WORKDIR /home/container/

# Instala los requisitos
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt


RUN chmod 644 .env bot.py

# Etapa de ejecución
CMD ["./start_bot.sh"]
