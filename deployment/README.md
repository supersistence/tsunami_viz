# Deployment Resources

Documentation and utilities for the tsunami visualization deployment.

## Directory Structure

### `docs/`
- **`DEPLOYMENT.md`** - Complete deployment guide

### `local_test.sh`
Local testing utility for validating Docker builds before deployment.

## Core Deployment Files (Project Root)

- **`deploy.sh`** - Main deployment script
- **`Dockerfile`** - Docker image definition
- **`docker-compose.yml`** - Container config
- **`requirements.txt`** - Python dependencies

## Quick Deployment

```bash
# Deploy to production
./deploy.sh

# Test locally first
./deployment/local_test.sh
```

## Live Application

- **URL:** https://tsunami.supersistence.org
- **Server:** Linode (`172.236.244.235`)
- **Architecture:** Host Nginx + Docker + certbot SSL
