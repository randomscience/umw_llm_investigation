FROM python:3.12-slim

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


EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
