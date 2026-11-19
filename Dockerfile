FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir ".[api,llm]" && studyrag ingest data/notes
EXPOSE 8000
CMD ["studyrag", "serve", "--port", "8000"]
