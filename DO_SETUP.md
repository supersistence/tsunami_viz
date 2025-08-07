# 🌊 DigitalOcean Droplet - Production Deployment

Deploy your Tsunami Viz app (and future apps) to a professional DigitalOcean setup for **$6/month total**.

## 🎯 Architecture Overview

```
Your Domain(s)
├── tsunami.yourdomain.com    → Tsunami Viz App (Port 8050)
├── soil.yourdomain.com       → Soil Health Tool (Port 8051) 
├── food.yourdomain.com       → Food Price Index (Port 8052)
└── [future apps...]          → Easy to add more
```

**All running on one $6/month droplet with Nginx reverse proxy!**

## 📋 Step 1: Create DigitalOcean Droplet

1. **Go to DigitalOcean Dashboard**
   - Sign up at https://digitalocean.com if you haven't already

2. **Create Droplet:**
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic
   - **Size:** $6/month (1GB RAM, 25GB SSD, 1TB transfer)
   - **Region:** Choose closest to your users (e.g., San Francisco, New York)
   - **Authentication:** SSH Key (recommended) or Password
   - **Hostname:** `apps-server` or similar
   - **Tags:** `web-apps`, `production`

3. **Note your Droplet IP:** You'll get an IP like `164.90.XXX.XXX`

## 🔧 Step 2: Initial Server Setup

SSH into your droplet and run this setup:

```bash
# SSH into your droplet (replace with your IP)
ssh root@YOUR_DROPLET_IP

# Update system packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Install other useful tools
apt install -y curl wget htop unzip rsync

# Create directories for apps
mkdir -p /opt/tsunami-viz
mkdir -p /var/www/certbot

# Create a non-root user (optional but recommended)
adduser appuser
usermod -aG docker appuser
usermod -aG sudo appuser

echo "✅ Server setup complete!"
```

## 🔒 Step 3: Configure Domain and SSL

### 3.1 DNS Configuration
In your domain registrar (GoDaddy, Namecheap, etc.):
```
Type: A Record
Name: tsunami
Value: YOUR_DROPLET_IP
TTL: 300

# Add more subdomains for other apps
Name: soil
Value: YOUR_DROPLET_IP

Name: food  
Value: YOUR_DROPLET_IP
```

### 3.2 SSL with Let's Encrypt
```bash
# Install Certbot
apt install certbot -y

# Get SSL certificates (replace with your actual domain)
certbot certonly --standalone -d tsunami.yourdomain.com

# For multiple apps (run this later when you add them):
# certbot certonly --standalone -d soil.yourdomain.com
# certbot certonly --standalone -d food.yourdomain.com

# Setup auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

# Create SSL directory for nginx
mkdir -p /opt/tsunami-viz/nginx/ssl
ln -s /etc/letsencrypt/live/tsunami.yourdomain.com/fullchain.pem /opt/tsunami-viz/nginx/ssl/
ln -s /etc/letsencrypt/live/tsunami.yourdomain.com/privkey.pem /opt/tsunami-viz/nginx/ssl/

echo "🔒 SSL setup complete!"
```

## 🚀 Step 4: Deploy Your App

### 4.1 Configure Deployment Script
Edit `deploy.sh` in your local project:
```bash
# Change these lines:
DROPLET_IP="164.90.XXX.XXX"  # Your actual droplet IP
DOMAIN="tsunami.yourdomain.com"  # Your actual domain
```

### 4.2 Update Nginx Config
Edit `nginx/nginx.conf` and replace all instances of:
- `tsunami.yourdomain.com` → your actual domain
- `yourdomain.com` → your actual domain

### 4.3 Deploy!
```bash
# From your local tsunami_viz directory:
./deploy.sh
```

## 🔍 Step 5: Verify Deployment

After deployment, check:

1. **Application Health:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   cd /opt/tsunami-viz
   docker-compose ps
   docker-compose logs tsunami-viz
   ```

2. **Web Access:**
   - Visit: `https://tsunami.yourdomain.com`
   - Should see your Tsunami Viz app with SSL

3. **System Resources:**
   ```bash
   htop  # Check CPU/RAM usage
   df -h # Check disk space
   ```

## 📊 Monitoring and Maintenance

### Daily Checks:
```bash
# Check app status
docker-compose ps

# Check logs
docker-compose logs --tail=50 tsunami-viz

# Check system resources
htop
df -h
```

### Monthly Tasks:
```bash
# Update system packages
apt update && apt upgrade -y

# Clean up Docker
docker system prune -f

# Check SSL certificate expiry
certbot certificates
```

## 🔧 Adding More Apps

When you want to add your soil-health or food-price apps:

1. **Clone repos to droplet:**
   ```bash
   cd /opt
   git clone https://github.com/yourusername/soil-health-tool
   git clone https://github.com/yourusername/food-price-index
   ```

2. **Update docker-compose.yml** (uncomment the soil-health and food-price services)

3. **Update nginx.conf** (uncomment the additional server blocks)

4. **Get SSL certs** for new domains:
   ```bash
   certbot certonly --standalone -d soil.yourdomain.com
   certbot certonly --standalone -d food.yourdomain.com
   ```

5. **Restart services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## 💰 Cost Breakdown

- **Droplet:** $6/month (1GB RAM, 25GB SSD)
- **SSL Certificates:** Free (Let's Encrypt)
- **Domain:** $10-15/year (you probably already have this)
- **Total:** **$6/month for unlimited apps!**

## 🆘 Troubleshooting

### App not loading:
```bash
# Check if containers are running
docker-compose ps

# Check application logs
docker-compose logs tsunami-viz

# Check nginx logs
docker-compose logs nginx

# Test internal connectivity
docker-compose exec nginx curl http://tsunami-viz:8050
```

### SSL issues:
```bash
# Check certificate status
certbot certificates

# Test SSL configuration
openssl s_client -connect tsunami.yourdomain.com:443 -servername tsunami.yourdomain.com
```

### Performance issues:
```bash
# Check system resources
htop
free -h
df -h

# Check Docker stats
docker stats
```

## 🔄 Backup Strategy

### Automated backup script:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"

mkdir -p $BACKUP_DIR

# Backup application data
tar -czf $BACKUP_DIR/tsunami-viz-$DATE.tar.gz /opt/tsunami-viz/data

# Backup configurations
tar -czf $BACKUP_DIR/configs-$DATE.tar.gz /opt/*/docker-compose.yml /opt/*/nginx/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Add to crontab for daily backups:
```bash
echo "0 2 * * * /root/backup.sh" | crontab -
```

---

**🎉 Congratulations!** Your app is now running on a professional setup that can scale to handle multiple applications for just $6/month!