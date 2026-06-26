FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pytest requests pytest-cov

COPY generate_test.py .
COPY prompt.txt .
COPY requirements/ requirements/
COPY src/ src/

ENV PYTHONUNBUFFERED=1

CMD ["python", "generate_test.py"]