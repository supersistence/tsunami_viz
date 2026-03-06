# Tsunami Visualization - Production Deployment

The app runs on a shared Linode server alongside other projects (soil-health, food-price-index, port-commerce).

## Architecture

- Host-level Nginx handles SSL and reverse proxying for all apps
- Each app runs in its own Docker container (or systemd service)
- Certbot manages SSL certificates with auto-renewal

## Deployment

```bash
./deploy.sh
```

Or push to `main` for automatic deployment via GitHub Actions.

## Environment Variables

```bash
DEBUG=False
PORT=8050
MAPTILER_API_KEY=<your-key>
```

## Local Development

```bash
python wave_propagation_clientside_app.py
# Open http://localhost:8050
```

## Local Docker Testing

```bash
./deployment/local_test.sh
```

See [DEPLOYMENT_GUIDE.md](../../DEPLOYMENT_GUIDE.md) for the full guide.
