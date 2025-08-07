# 🌊 Tsunami Visualization - Production Deployment

Professional deployment guide for the tsunami visualization app using Docker and DigitalOcean.

## 🏆 Production Setup: DigitalOcean Droplet

**Host multiple apps (tsunami-viz, soil-health, food-price, etc.) on one server for $6/month total.**

✨ **Features:**
- 🐳 Docker containerization
- 🌐 Nginx reverse proxy  
- 🔒 Free SSL certificates (Let's Encrypt)
- 📊 Multiple apps on one server
- 🚀 Professional architecture
- 💰 Cost-effective scaling

👉 **[Follow the complete setup guide →](DO_SETUP.md)**

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

## 🧪 Local Testing

Test the Docker setup locally before deploying:

```bash
# Quick local test
./local_test.sh

# Manual Docker commands
docker build -t tsunami-viz .
docker run -p 8050:8050 -v ./data:/app/data:ro tsunami-viz
```

## 📞 Support

For deployment issues:
- See detailed troubleshooting in `DO_SETUP.md`
- Verify all dependencies in `requirements.txt`
- Ensure data files are included in repository
- Check Docker logs: `docker-compose logs tsunami-viz`