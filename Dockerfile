# Imagem base
FROM python:3.10-slim

# Define variáveis de ambiente do sistema
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copia os arquivos de dependências
COPY requirements.txt /app/

# Instala dependências
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o código da aplicação
COPY . /app/

# Expõe a porta padrão do Gunicorn
EXPOSE 8000

# Aplica as migrations automaticamente na inicialização
# Inicia o servidor Gunicorn apontando para o módulo WSGI do Django
CMD ["bash", "-c", "python manage.py migrate && gunicorn pix_api.wsgi:application --bind 0.0.0.0:8000"]