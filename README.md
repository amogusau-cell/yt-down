# yt-down
Love watching YouTube but don’t want to rely on an internet connection while you’re on vacation? This self-hosted app lets you download YouTube videos and playlists and integrate them with Jellyfin. That way, you can enjoy your favorite YouTube content anytime, anywhere. Even completely offline.

---
## How to run

In order to run yt-down tou can use docker. The easiest way is through docker compose but you can always use docker run as well.  
Compose:
```yaml
services:
  app:
    image: ghcr.io/amogusau-cell/yt-down:latest # Use versions such as 0.0.0 for specific version.
    container_name: yt-down
    restart: unless-stopped
    ports:
      - "8080:80" # host:container change 8080 to whatever port you want
    environment:
      - JWT_SECRET=notsosecretdefaulttokenthatyoushouldprobablychangeprettysoon # Change this to a random string for security purposes.
    volumes:
      - ./cache:/app/backend/cache
      - ./config:/app/backend/config
      - ./Shows:/app/backend/Shows
      - ./Videos:/app/backend/Videos
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```
```bash
docker run -d \
  --name yt-down \
  -p 8080:80 \
  -e JWT_SECRET=notsosecretdefaulttokenthatyoushouldprobablychangeprettysoon \
  -v ./cache:/app/backend/cache \
  -v ./config:/app/backend/config \
  -v ./Shows:/app/backend/Shows \
  -v ./Videos:/app/backend/Videos \
  ghcr.io/amogusau-cell/yt-down:latest
```