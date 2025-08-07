# 🚀 Deployment Resources

This directory contains deployment-related documentation and utilities for the tsunami visualization project.

## 📁 Directory Structure

### `docs/`
- **`DEPLOYMENT.md`** - Complete deployment guide and configuration
- **`DO_SETUP.md`** - Detailed DigitalOcean droplet setup instructions

### `local_test.sh`
Local testing utility for validating Docker builds before deployment.

## 🔧 Core Deployment Files (Project Root)

The essential deployment files remain in the project root for proper functionality:

- **`deploy.sh`** - Main deployment script (runs from root)
- **`Dockerfile`** - Docker image definition (needs root context)
- **`docker-compose.yml`** - Service orchestration (uses relative paths)
- **`requirements.txt`** - Python dependencies (referenced by Dockerfile)
- **`nginx/`** - Nginx configuration (mounted by docker-compose)

## 🎯 Quick Deployment

### From Project Root:
```bash
# Deploy to production
./deploy.sh

# Test locally first
./deployment/local_test.sh
```

### Local Development:
```bash
# Run client-side app
python wave_propagation_clientside_app.py

# Run original server-side app  
python wave_propagation_dash_app.py
```

## 📚 Documentation

- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment overview
- **[DO_SETUP.md](docs/DO_SETUP.md)** - Step-by-step DigitalOcean setup
- **[Project README](../README.md)** - Main project documentation

## 🌐 Live Application

- **Production URL:** https://tsunami.supersistence.org
- **Architecture:** DigitalOcean Droplet + Docker + Nginx + SSL
- **Cost:** $6/month for unlimited apps

## 🔍 Troubleshooting

### Check Deployment Status:
```bash
# SSH into droplet
ssh root@143.110.144.44

# Check services
cd /opt/tsunami-viz
docker-compose ps
docker-compose logs tsunami-viz
```

### Common Issues:
- **MapTiler API Key:** Ensure `.env` file contains valid `MAPTILER_API_KEY`
- **SSL Certificate:** Check nginx logs if HTTPS issues occur
- **Rate Limiting:** Client-side app should eliminate server callback issues

## 🛠️ Maintenance

### Updates:
1. Make changes locally
2. Test with `./deployment/local_test.sh`
3. Deploy with `./deploy.sh`

### Monitoring:
- Check application logs via SSH
- Monitor SSL certificate expiry
- Update system packages monthly

## 📈 Architecture Benefits

- **Client-side visualization** - No server callbacks for animation
- **Pre-loaded data** - Instant performance after initial load
- **Docker containerization** - Consistent deployments
- **Nginx reverse proxy** - Professional SSL and routing
- **Scalable infrastructure** - Ready for additional applications
