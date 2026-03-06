# GitHub Secrets Setup Guide

Set up automatic deployment from GitHub to the Linode server.

## Step 1: Get Your SSH Private Key

```bash
cat ~/.ssh/id_ed25519
```

Copy the entire output including the `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----` lines.

**Important**: This is your private key. Only paste it into GitHub Secrets, never commit it.

## Step 2: Add Secrets to GitHub

1. Go to your GitHub repository
2. Click **Settings** -> **Secrets and variables** -> **Actions**
3. Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `SSH_PRIVATE_KEY` | Your SSH private key from Step 1 |
| `SERVER_IP` | `172.236.244.235` |

## Step 3: Test

Push to `main` and check the **Actions** tab for the "Deploy to Linode" workflow.

## Troubleshooting

- Verify SSH works locally: `ssh -i ~/.ssh/id_ed25519 deploy@172.236.244.235`
- Check the Actions tab for error messages
- Ensure the full key is pasted (including BEGIN/END lines, no extra whitespace)
