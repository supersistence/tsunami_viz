# 🌊 Tsunami Visualization - Deployment Guide

This guide explains how to deploy the tsunami visualization app as a live website.

## 🚀 Quick Deployment Options

### 1. Render (Recommended)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Fork this repository on GitHub
2. Connect your GitHub account to [Render](https://render.com)
3. Create a new Web Service
4. Connect your forked repository
5. Render will automatically detect `render.yaml` and deploy

**Features:**
- ✅ Free tier available (750 hours/month)
- ✅ Automatic deployments from GitHub
- ✅ Custom domains
- ✅ SSL certificates included

### 2. Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/deploy)

1. Click the deploy button above
2. Connect your GitHub account
3. Fork and deploy

### 3. Heroku
```bash
# Install Heroku CLI, then:
heroku create your-tsunami-viz-app
git push heroku main
heroku open
```

### 4. DigitalOcean App Platform
1. Create account on [DigitalOcean](https://cloud.digitalocean.com/apps)
2. Create new App
3. Connect GitHub repository
4. Deploy

## 🔧 Environment Variables

Set these for production deployment:

```bash
DEBUG=False           # Disable debug mode
PORT=8050            # Port (usually auto-set by platform)
```

## 📊 Data Considerations

**Current Setup:**
- Uses pre-cached pickle files (`data/*.pkl`)
- Station metadata from NOAA API
- No real-time data fetching

**For Live Data:**
- Uncomment data fetching code in `wave_data_collect_and_cache.py`
- Set up scheduled jobs to update data
- Consider database storage for better performance

## 🌐 Custom Domain

Most platforms support custom domains:

**Render:** Settings → Custom Domains → Add Domain
**Railway:** Settings → Domains → Custom Domain  
**Heroku:** Settings → Domains → Add Domain

## 📈 Scaling Considerations

- **Memory:** ~500MB for current dataset
- **CPU:** Moderate for real-time updates
- **Storage:** <100MB for cached data
- **Bandwidth:** ~10MB per user session

## 🔒 Security Notes

- API keys should be environment variables
- Enable HTTPS (included on most platforms)
- Consider rate limiting for public access

## 🛠 Local Development

```bash
export DEBUG=True
export PORT=8050
python wave_propagation_dash_app.py
```

Access at: http://localhost:8050

## 📞 Support

For deployment issues:
- Check platform-specific documentation
- Verify all dependencies in `requirements.txt`
- Ensure data files are included in repository 