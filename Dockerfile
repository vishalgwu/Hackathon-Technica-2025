FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r src/req.txt

# Install supervisord to run both Streamlit + FastAPI
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8080

CMD ["/usr/bin/supervisord"]
[supervisord]
nodaemon=true

[program:api]
command=uvicorn src.backend.dispatcher:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true

[program:streamlit]
command=streamlit run src/frontend/app.py --server.port 8080 --server.address 0.0.0.0
autostart=true
autorestart=true
