FROM python:3.12-slim

ENV EMBEDDINGS_URL="https://work.randomscience.org/s/NJwfWn9GWasZzk4/download"
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY templates templates
COPY pydantic_input_output.py pydantic_input_output.py
COPY prompt.py prompt.py
COPY logging_config.py logging_config.py
COPY rag.py rag.py
COPY app.py app.py
COPY scripts/download_embeddings.py download_embeddings.py

RUN python download_embeddings.py

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
