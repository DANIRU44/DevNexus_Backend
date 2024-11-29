FROM python:3.11-slim as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.4.1

RUN apt-get update && apt-get install -y gcc libffi-dev musl-dev libpq-dev
RUN pip install poetry==1.8.4

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

COPY README.md ./
COPY devnexus ./devnexus

# Копируем entrypoint.sh в указанное место
COPY entrypoint.sh /app/entrypoint.sh

# Даём права на выполнение entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /app/devnexus

EXPOSE 8000

ENTRYPOINT ["sh", "/app/entrypoint.sh"]
CMD ["poetry", "run", "gunicorn", "devnexus.wsgi:application", "--bind", "0.0.0.0:8000"]
