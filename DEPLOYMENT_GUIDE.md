# 🚀 Deployment Guide

Complete guide for deploying the Tsunami Visualization app to production.

## 📋 Prerequisites

1. **SSH Access**: You need SSH access to your DigitalOcean droplet
   - IP: `143.110.144.44`
   - User: `root`
   - SSH key configured

2. **Local Requirements**:
   - Docker installed locally (for testing)
   - `rsync` installed
   - SSH access to the server

3. **Server Requirements** (already set up):
   - Docker and Docker Compose installed
   - Nginx configured
   - SSL certificates (Let's Encrypt)
   - Domain DNS pointing to server

## 🚀 Deployment Steps

### Step 1: Test Locally (Optional but Recommended)

Before deploying to production, test the Docker build locally:

```bash
# From the project root directory
./deployment/local_test.sh
```

This will:
- Build the Docker image
- Run it locally on port 8050
- Test that it works
- Show you the logs

Visit `http://localhost:8050` to verify everything works.

### Step 2: Deploy to Production

The deployment script is already configured with your server details. Simply run:

```bash
# From the project root directory
./deploy.sh
```

**What the script does:**
1. ✅ Builds Docker image locally (to catch build errors early)
2. 🧪 Optionally tests the image locally
3. 📤 Copies all files to the server via `rsync` (excludes `.git`, `venv`, etc.)
4. 🛑 Stops existing containers
5. 🔨 Builds and starts new containers
6. ⏱️ Waits for services to be ready
7. 🧪 Tests that the app is responding
8. ✅ Shows you the deployment status

**Expected output:**
```
🚀 Deploying tsunami-viz to DigitalOcean Droplet...
🔨 Building Docker image locally for testing...
✅ Docker build successful
🧪 Test the image locally? (y/N): 
📤 Copying files to droplet...
🔄 Deploying on droplet...
✅ Deployment complete!
🌐 Your app should be available at:
   http://tsunami.supersistence.org (redirects to HTTPS)
   https://tsunami.supersistence.org
```

### Step 3: Verify Deployment

After deployment, verify everything is working:

```bash
# Check if services are running
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose ps'

# Check application logs
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose logs --tail=50 tsunami-viz'

# Check nginx logs
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose logs --tail=50 nginx'

# Test the website
curl -I https://tsunami.supersistence.org
```

## 🔧 Manual Deployment (Alternative)

If you prefer to deploy manually or the script fails:

```bash
# 1. Copy files to server
rsync -avz --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.pytest_cache' \
    ./ root@143.110.144.44:/opt/tsunami-viz/

# 2. SSH into server
ssh root@143.110.144.44

# 3. Navigate to app directory
cd /opt/tsunami-viz

# 4. Stop existing services
docker-compose down

# 5. Build and start services
docker-compose up -d --build

# 6. Check status
docker-compose ps
docker-compose logs -f
```

## 📊 Managing the Deployment

### View Logs
```bash
# All services
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose logs -f'

# Just the app
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose logs -f tsunami-viz'

# Just nginx
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose logs -f nginx'
```

### Restart Services
```bash
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose restart'
```

### Stop Services
```bash
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose down'
```

### Update Environment Variables
If you need to update environment variables (like `MAPTILER_API_KEY`):

1. Edit `docker-compose.yml` locally
2. Or set them on the server:
   ```bash
   ssh root@143.110.144.44
   cd /opt/tsunami-viz
   # Edit docker-compose.yml or create .env file
   docker-compose down
   docker-compose up -d
   ```

## 🔒 SSL Certificate Renewal

Certificates are set to auto-renew, but if you need to manually renew:

```bash
./renew_certificate.sh
```

Or manually:
```bash
ssh root@143.110.144.44
cd /opt/tsunami-viz
docker-compose stop nginx
certbot certonly --standalone --force-renewal -d tsunami.supersistence.org
cp /etc/letsencrypt/live/tsunami.supersistence.org/fullchain.pem nginx/ssl/fullchain.pem
cp /etc/letsencrypt/live/tsunami.supersistence.org/privkey.pem nginx/ssl/privkey.pem
docker-compose up -d nginx
```

## 🐛 Troubleshooting

### Deployment Fails

**Issue**: Build fails locally
```bash
# Check Docker is running
docker ps

# Try building manually
docker build -t tsunami-viz:test .
```

**Issue**: Can't connect to server
```bash
# Test SSH connection
ssh root@143.110.144.44

# Check if rsync is installed
which rsync
```

**Issue**: Services won't start
```bash
# Check Docker on server
ssh root@143.110.144.44 'docker ps'

# Check disk space
ssh root@143.110.144.44 'df -h'

# Check logs for errors
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose logs'
```

### App Not Responding

**Check service status:**
```bash
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose ps'
```

**Check if app is healthy:**
```bash
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose exec tsunami-viz curl http://localhost:8050'
```

**Check nginx configuration:**
```bash
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose exec nginx nginx -t'
```

### SSL Certificate Issues

**Certificate expired:**
```bash
./renew_certificate.sh
```

**Nginx can't find certificates:**
```bash
ssh root@143.110.144.44
cd /opt/tsunami-viz
ls -la nginx/ssl/  # Should show fullchain.pem and privkey.pem
```

## 📝 Configuration Files

Key files for deployment:

- **`deploy.sh`**: Main deployment script
- **`docker-compose.yml`**: Service orchestration
- **`Dockerfile`**: Container definition
- **`nginx/nginx.conf`**: Reverse proxy configuration (on server)
- **`requirements.txt`**: Python dependencies

## 🎯 Quick Reference

```bash
# Deploy
./deploy.sh

# Test locally
./deployment/local_test.sh

# Renew certificate
./renew_certificate.sh

# Check status
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose ps'

# View logs
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose logs -f'

# Restart
ssh root@143.110.144.44 'cd /opt/tsunami-viz && docker-compose restart'
```

## 🌐 Live Site

Your deployed application is available at:
- **HTTPS**: https://tsunami.supersistence.org
- **HTTP**: http://tsunami.supersistence.org (redirects to HTTPS)

