# GitHub Actions Deployment

Automatically deploys to the Linode server when you push to `main` or `master`.

## Setup

Add these GitHub Secrets (Settings -> Secrets and variables -> Actions):

1. **`SSH_PRIVATE_KEY`** - SSH private key for the server
2. **`SERVER_IP`** - Linode server IP (`172.236.244.235`)

See [GITHUB_SECRETS_SETUP.md](../../GITHUB_SECRETS_SETUP.md) for details.

## How It Works

1. Push to main/master triggers the workflow
2. Files are copied to server via rsync
3. Docker container is rebuilt and started
4. Health check verifies the app is responding

## Manual Trigger

Go to **Actions** tab -> **Deploy to Linode** -> **Run workflow**
