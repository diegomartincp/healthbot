# Dockerfile
FROM python:3.9-slim

# Config machine proxy
#ENV https_proxy=1.2.3.4
#ENV http_proxy=1.2.3.4

# Instalar herramientas necesarias
RUN apt-get update 

# RUN apt install curl
RUN apt-get install -y \
ca-certificates \
openssl \
&& rm -rf /var/lib/apt/lists/*

# Crear un directorio para almacenar los certificados
RUN ls
RUN mkdir /app

# Copiar los scripts de la aplicación
COPY . /app
WORKDIR /app

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Configure proxy if needed
#RUN export http_proxy=http://1.2.3.4:1234; export https_proxy=http://1.2.3.4:1234

# Comando para ejecutar ambos scripts de Python
CMD ["sh", "-c", "python healthbot.py"]
