# ---- Stage 1: build frontend ----
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: backend + nginx ----
FROM python:3.12-slim

RUN apt-get update && apt-get install -y unzip curl nginx supervisor ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Deno to a fixed location and make sure it's on PATH for the running container
ENV DENO_INSTALL=/usr/local/deno
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/

# bring in built frontend
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# supervisor config to run both processes
COPY supervisord.conf /etc/supervisord.conf

EXPOSE 80
CMD ["supervisord", "-c", "/etc/supervisord.conf"]