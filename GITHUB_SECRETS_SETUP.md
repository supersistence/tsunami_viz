# 🔐 GitHub Secrets Setup Guide

Follow these steps to set up automatic deployment from GitHub to your DigitalOcean server.

## Step 1: Get Your SSH Private Key

Your SSH private key is already on your computer. To find it:

**On Mac/Linux:**
```bash
cat ~/.ssh/id_ed25519_do
```

**Or if you have a different key:**
```bash
# List all your SSH keys
ls -la ~/.ssh/

# View a specific key (replace with your key name)
cat ~/.ssh/id_ed25519
# or
cat ~/.ssh/id_rsa
```

**Copy the entire output** (including the `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----` lines).

⚠️ **Important**: 
- This is your private key - keep it secret! Only paste it into GitHub Secrets, never commit it to your repository.
- When pasting into GitHub Secrets, make sure there are NO extra spaces or blank lines at the beginning or end
- The key should start exactly with `-----BEGIN` and end exactly with `-----END`

## Step 2: Add Secrets to GitHub

1. **Go to your GitHub repository**
   - Navigate to: `https://github.com/YOUR_USERNAME/tsunami_viz`
   - (Replace YOUR_USERNAME with your actual GitHub username)

2. **Open Settings**
   - Click the **Settings** tab (top of the repository page)

3. **Go to Secrets**
   - In the left sidebar, click **Secrets and variables**
   - Then click **Actions**

4. **Add First Secret: SSH_PRIVATE_KEY**
   - Click **New repository secret**
   - **Name**: `SSH_PRIVATE_KEY`
   - **Secret**: Paste the entire private key from Step 1 (including BEGIN/END lines)
   - Click **Add secret**

5. **Add Second Secret: DROPLET_IP**
   - Click **New repository secret** again
   - **Name**: `DROPLET_IP`
   - **Secret**: Your DigitalOcean droplet IP address
     - You can find this in your `deploy.sh` file (look for `DROPLET_IP=`)
     - Or check your DigitalOcean dashboard
   - Click **Add secret**

## Step 3: Verify Setup

After adding both secrets, you should see:
- ✅ `SSH_PRIVATE_KEY` (hidden)
- ✅ `DROPLET_IP` (hidden)

## Step 4: Test the Deployment

1. **Make a small change** to your code (or just commit and push)
   ```bash
   git add .
   git commit -m "Test GitHub Actions deployment"
   git push origin main
   ```

2. **Check the Actions tab**
   - Go to the **Actions** tab in your GitHub repository
   - You should see "Deploy to DigitalOcean" workflow running
   - Click on it to see the progress

3. **Verify deployment**
   - Once it completes, visit: https://tsunami.supersistence.org
   - Your changes should be live!

## 🎯 Quick Reference

**Secret Names:**
- `SSH_PRIVATE_KEY` = Your SSH private key (found with `cat ~/.ssh/id_ed25519_do`)
- `DROPLET_IP` = Your DigitalOcean droplet IP (check `deploy.sh` or DigitalOcean dashboard)

**Where to find in GitHub:**
- Repository → Settings → Secrets and variables → Actions

## 🐛 Troubleshooting

**If deployment fails:**
- Check the Actions tab for error messages
- Make sure you copied the ENTIRE private key (including BEGIN/END lines)
- Verify the SSH key works: `ssh root@YOUR_DROPLET_IP` (replace with your actual IP)

**If you can't find Settings:**
- Make sure you're logged into GitHub
- Make sure you have admin access to the repository

