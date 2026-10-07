# Imagem base compartilhada pelos serviços do tutorial.
# O código de cada serviço NÃO é copiado para a imagem: ele é montado como
# volume pelo docker-compose.yml e o Flask roda com recarga automática:
# basta salvar o arquivo para que a alteração tenha efeito.
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
CMD ["python", "app.py"]
