FROM python:3.13-slim
WORKDIR /app

# プロジェクト設定とコードをコピー
COPY pyproject.toml poetry.lock /app/
COPY src/ /app/src/
COPY data/ /app/data

RUN pip install --upgrade pip \
 && pip install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --without dev
COPY src/ /app/src/

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000"]
