# GitHub Actions Deployment Setup

This workflow automatically deploys to your DigitalOcean droplet when you push to `main` or `master`.

## 🔧 Setup Required

### 1. Add GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

1. **`SSH_PRIVATE_KEY`**
   - Your SSH private key that can access the server
   - Generate with: `ssh-keygen -t ed25519 -C "github-actions"`
   - Copy the **private** key (usually `~/.ssh/id_ed25519`)
   - Add the **public** key to your server: `ssh-copy-id root@143.110.144.44`

2. **`DROPLET_IP`**
   - Your DigitalOcean droplet IP address
   - Value: `143.110.144.44`

### 2. Verify SSH Access

Make sure your SSH key works:
```bash
ssh root@143.110.144.44
```

## 🚀 How It Works

1. **Push to main/master** → Workflow triggers automatically
2. **Checkout code** → Gets your latest code
3. **Copy files** → Uses `rsync` to copy files to server (same as `deploy.sh`)
4. **Deploy** → Runs `docker-compose up -d --build` on server
5. **Verify** → Checks that the app is responding

## 📝 Manual Trigger

You can also trigger deployments manually:
- Go to **Actions** tab in GitHub
- Select **Deploy to DigitalOcean** workflow
- Click **Run workflow**

## 🔍 What Gets Deployed

The workflow uses the same approach as `deploy.sh`:
- Excludes: `.git`, `venv`, `__pycache__`, `*.pyc`
- Copies everything else to `/opt/tsunami-viz/` on server
- Uses `docker-compose` to build and start services

## 🐛 Troubleshooting

**Workflow fails with SSH error:**
- Verify your SSH key is added to GitHub secrets
- Make sure the public key is on the server
- Test SSH manually: `ssh root@143.110.144.44`

**Deployment fails:**
- Check the Actions logs in GitHub
- SSH to server and check: `cd /opt/tsunami-viz && docker-compose logs`

