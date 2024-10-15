FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# ENV DATABASE_USERNAME=${DATABASE_USERNAME}
# ENV DATABASE_PASSWORD=${DATABASE_PASSWORD}
# ENV DATABASE_HOST=${DATABASE_HOST}
# ENV DATABASE_PORT=${DATABASE_PORT}
# ENV DATABASE_NAME=${DATABASE_NAME}
# ENV SECRET_KEY=${SECRET_KEY}
# ENV ALGORITHM=${ALGORITHM}
# ENV ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES}


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
