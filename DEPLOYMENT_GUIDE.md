# Deployment Guide

Complete guide for deploying the Tsunami Visualization app to production.

## Prerequisites

1. **SSH Access**: SSH access to the Linode server
   - IP: `172.236.244.235`
   - User: `root`
   - SSH key: `~/.ssh/id_ed25519`

2. **Local Requirements**:
   - Docker installed locally (for testing)
   - `rsync` installed
   - SSH access to the server

3. **Server Requirements** (already set up):
   - Docker and Docker Compose installed
   - Host-level Nginx as reverse proxy
   - SSL certificates via certbot (Let's Encrypt)
   - Domain DNS pointing to server

## Architecture

The Linode server (`172.236.244.235`) hosts multiple apps behind a shared host-level Nginx:

```
tsunami.supersistence.org     -> 127.0.0.1:8051 (Docker)
portcommerce.supersistence.org -> 127.0.0.1:8050 (Docker)
soilhealth.supersistence.org  -> 127.0.0.1:5000 (Docker)
foodprice.supersistence.org   -> Unix socket (systemd)
```

Nginx and SSL are managed on the host, not inside Docker.

## Deployment Steps

### Step 1: Test Locally (Optional)

```bash
./deployment/local_test.sh
```

Visit `http://localhost:8050` to verify.

### Step 2: Deploy to Production

```bash
./deploy.sh
```

This will:
1. Build Docker image locally
2. Optionally test locally
3. Copy files to server via rsync
4. Stop existing container
5. Build and start new container
6. Verify the app is responding

### Step 3: Verify Deployment

```bash
# Check services
ssh root@172.236.244.235 'cd /opt/tsunami-viz && docker compose ps'

# Check logs
ssh root@172.236.244.235 'cd /opt/tsunami-viz && docker compose logs --tail=50 tsunami-viz'

# Test HTTPS
curl -I https://tsunami.supersistence.org
```

## Managing the Deployment

### View Logs
```bash
ssh root@172.236.244.235 'cd /opt/tsunami-viz && docker compose logs -f tsunami-viz'
```

### Restart
```bash
ssh root@172.236.244.235 'cd /opt/tsunami-viz && docker compose restart'
```

### Stop
```bash
ssh root@172.236.244.235 'cd /opt/tsunami-viz && docker compose down'
```

## SSL Certificate Renewal

Certificates auto-renew via certbot. To manually renew:

```bash
./renew_certificate.sh
```

Or directly on the server:
```bash
ssh root@172.236.244.235 'certbot renew --nginx'
```

## CI/CD (GitHub Actions)

Pushes to `main` auto-deploy via GitHub Actions. Required secrets:

- `SSH_PRIVATE_KEY` - SSH private key for the Linode server
- `SERVER_IP` - `172.236.244.235`

Set these in: Repository -> Settings -> Secrets and variables -> Actions

## Configuration Files

- `deploy.sh` - Manual deployment script
- `docker-compose.yml` - Container config (port 8051 -> 8050)
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies

## Live Site

- https://tsunami.supersistence.org
