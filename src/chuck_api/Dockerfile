# docker build -t joke-reader:1.0 . --no-cache
FROM python:3.9-alpine
RUN apk add --no-cache curl
WORKDIR /app
RUN touch /app/sqlite.db
ENV DB_LOCATION=/app/sqlite.db
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY app.py app.py
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=5 \
            CMD curl -f http://localhost:5000/health || exit 1
ENTRYPOINT [ "python3", "app.py" ]
