FROM python:3.9-alpine

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt --no-cache-dir
RUN ls -la

CMD ["python", "main.py"]
