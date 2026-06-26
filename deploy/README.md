# Deployment — myvision.drugoi.xyz

The web app runs in Docker behind the host's nginx. The container listens only on
`127.0.0.1:8771`; nginx terminates HTTP/HTTPS and proxies to it.

## One-time setup

1. **DNS** — add an `A` record:

   ```
   myvision.drugoi.xyz → <server IP>
   ```

2. **nginx vhost** — on the server, install the site config:

   ```bash
   cp deploy/nginx.conf /etc/nginx/sites-available/myvision.drugoi.xyz
   ln -s /etc/nginx/sites-available/myvision.drugoi.xyz /etc/nginx/sites-enabled/myvision.drugoi.xyz
   nginx -t && systemctl reload nginx
   ```

3. **TLS** — issue a certificate (certbot rewrites the vhost to add `listen 443`):

   ```bash
   certbot --nginx -d myvision.drugoi.xyz
   ```

## Deploy

From your laptop, sync the code and (re)build the container on the server:

```bash
./deploy/deploy.sh
```

This rsyncs the project to `/root/projects/myvision.drugoi.xyz` (excluding `.venv/`,
`posts/`, `docs/`, `.git/`, and caches), then runs `docker compose up -d --build`,
validates nginx, and reloads it.

## Notes

- The server needs **Docker** and **docker compose** installed.
- The app is exposed only on `127.0.0.1:8771` — it is never reachable directly
  from the internet, only via nginx.
- Exports are stored in the `exports` Docker volume and cleaned up by the app's
  built-in TTL job.
