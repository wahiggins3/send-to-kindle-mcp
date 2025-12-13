# Cloud Deployment Guide

This guide explains how to deploy the Send to Kindle MCP Server to Google Cloud Platform (GCP) so you can access it from any AI tool, not just Claude Desktop.

## Overview

When deployed to the cloud, this MCP server runs with HTTP transport instead of stdio, making it accessible to:
- Web-based AI assistants (Claude.ai, ChatGPT, etc.)
- Mobile AI apps
- Any tool that supports MCP over HTTP
- Multiple clients simultaneously

## Prerequisites

1. **Google Cloud Platform Account**
   - Active GCP account with billing enabled
   - A GCP project created (or the script will help you create one)

2. **Google Cloud SDK (gcloud CLI)**
   - Install from: https://cloud.google.com/sdk/docs/install
   - Or use Google Cloud Shell (built-in)

3. **Email Credentials**
   - SMTP server details (Gmail recommended)
   - App Password (for Gmail users)
   - Your Kindle email address

## Quick Deployment

### Option 1: Automated Script (Recommended)

The easiest way to deploy is using the provided script:

```bash
# Set your GCP project ID (or the script will prompt you)
export GCP_PROJECT_ID="your-project-id"

# Run the deployment script
bash deploy.sh
```

The script will:
1. ✅ Enable required GCP APIs
2. 🏗️ Build the container image
3. 🔐 Create secrets for your credentials (prompts you for values)
4. 🚀 Deploy to Cloud Run
5. 📋 Display your service URL

**First-time deployment takes ~5-10 minutes. Subsequent deployments are much faster.**

### Option 2: Manual Deployment

If you prefer manual control:

#### Step 1: Enable APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com
```

#### Step 2: Create Secrets

Create secrets for your credentials:

```bash
# SMTP Configuration
echo -n "smtp.gmail.com" | gcloud secrets create smtp-host --data-file=-
echo -n "587" | gcloud secrets create smtp-port --data-file=-
echo -n "your-email@gmail.com" | gcloud secrets create smtp-user --data-file=-
echo -n "your-app-password" | gcloud secrets create smtp-password --data-file=-

# Kindle Configuration
echo -n "your-kindle@kindle.com" | gcloud secrets create kindle-email --data-file=-
echo -n "your-email@gmail.com" | gcloud secrets create from-email --data-file=-

# Optional: Author name
echo -n "Your Name" | gcloud secrets create author-name --data-file=-
```

#### Step 3: Build and Deploy

```bash
# Build container
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/send-to-kindle-mcp

# Deploy to Cloud Run
gcloud run deploy send-to-kindle-mcp \
    --image gcr.io/YOUR-PROJECT-ID/send-to-kindle-mcp \
    --platform managed \
    --region us-central1 \
    --set-env-vars "MCP_TRANSPORT=http" \
    --set-secrets "SMTP_HOST=smtp-host:latest,SMTP_PORT=smtp-port:latest,SMTP_USER=smtp-user:latest,SMTP_PASSWORD=smtp-password:latest,KINDLE_EMAIL=kindle-email:latest,FROM_EMAIL=from-email:latest,AUTHOR_NAME=author-name:latest" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --timeout 300
```

## Using Your Cloud-Hosted MCP Server

Once deployed, you'll receive a URL like:
```
https://send-to-kindle-mcp-xxxxx-uc.a.run.app
```

### Connecting from AI Tools

Different AI tools have different ways to connect to MCP servers. Here are the most common:

#### Claude Desktop (Local)

If you still want to use Claude Desktop with your cloud server instead of the local version:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "send-to-kindle-cloud": {
      "transport": "http",
      "url": "https://your-service-url.run.app/mcp"
    }
  }
}
```

#### Other AI Tools

For tools that support remote MCP servers:
1. Look for "MCP Server" or "Model Context Protocol" settings
2. Add a new server with your Cloud Run URL
3. The endpoint will typically be: `https://your-url.run.app/mcp`

**Note**: Some AI tools may not yet support remote MCP servers. Check their documentation for MCP support.

### API Documentation

Your MCP server exposes the following tool:

**Tool**: `send_to_kindle`

**Parameters**:
- `content` (string, required): The document content (supports markdown)
- `title` (string, required): Document title
- `author` (string, optional): Author name

**Example HTTP Request**:
```bash
curl -X POST https://your-url.run.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "send_to_kindle",
      "arguments": {
        "content": "# My Document\n\nThis is a test.",
        "title": "Test Document",
        "author": "Claude"
      }
    }
  }'
```

## Configuration Management

### Updating Secrets

To update any credential:

```bash
# Example: Update SMTP password
echo -n "new-password" | gcloud secrets versions add smtp-password --data-file=-

# Cloud Run will automatically use the latest version
```

### Viewing Secrets

```bash
# List all secrets
gcloud secrets list

# View secret metadata (not the actual value)
gcloud secrets describe smtp-host
```

### Environment Variables

The server uses these environment variables:

| Variable | Purpose | Set By |
|----------|---------|--------|
| `MCP_TRANSPORT` | Transport mode (http/stdio) | Deployment script |
| `MCP_HOST` | HTTP server host | Defaults to 0.0.0.0 |
| `MCP_PORT` / `PORT` | HTTP server port | Cloud Run sets PORT |
| `SMTP_HOST` | SMTP server | Secret Manager |
| `SMTP_PORT` | SMTP port | Secret Manager |
| `SMTP_USER` | SMTP username | Secret Manager |
| `SMTP_PASSWORD` | SMTP password | Secret Manager |
| `KINDLE_EMAIL` | Your Kindle email | Secret Manager |
| `FROM_EMAIL` | Sender email | Secret Manager |
| `AUTHOR_NAME` | Default author name | Secret Manager (optional) |

## Monitoring and Debugging

### Viewing Logs

Real-time logs:
```bash
gcloud run services logs tail send-to-kindle-mcp --region us-central1
```

Recent logs:
```bash
gcloud run services logs read send-to-kindle-mcp --region us-central1 --limit 100
```

### Cloud Console

View logs and metrics in the GCP Console:
1. Go to: https://console.cloud.google.com/run
2. Click on your service
3. Navigate to "Logs" or "Metrics" tabs

### Common Issues

**Issue**: "Permission denied" errors
```bash
# Grant yourself necessary permissions
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="user:your-email@gmail.com" \
    --role="roles/run.admin"
```

**Issue**: "Secret not found"
```bash
# List secrets to verify they exist
gcloud secrets list

# Recreate a missing secret
echo -n "value" | gcloud secrets create secret-name --data-file=-
```

**Issue**: Emails not sending
- Check logs for SMTP errors
- Verify secrets are correct: Gmail requires App Passwords
- Ensure your sender email is on Kindle's approved sender list

**Issue**: "Service Unavailable"
- Check if deployment succeeded: `gcloud run services list`
- View deployment logs: `gcloud run services logs read send-to-kindle-mcp`

## Cost Optimization

Cloud Run pricing is based on:
- **Request count**: First 2 million requests/month are free
- **Compute time**: Billed per 100ms of CPU time
- **Memory**: Based on allocated memory
- **Storage**: Container image storage

**Estimated costs** for typical usage:
- **Low usage** (< 1000 requests/month): Free tier
- **Medium usage** (< 10,000 requests/month): $0.50 - $2.00/month
- **Heavy usage** (100,000 requests/month): $5 - $15/month

### Cost Optimization Tips

1. **Reduce memory allocation** (if not needed):
   ```bash
   gcloud run services update send-to-kindle-mcp \
       --memory 256Mi \
       --region us-central1
   ```

2. **Set minimum instances to 0** (default):
   - Instances scale to zero when not in use
   - No cost when idle

3. **Set maximum instances** to prevent runaway costs:
   ```bash
   gcloud run services update send-to-kindle-mcp \
       --max-instances 10 \
       --region us-central1
   ```

4. **Use request timeouts**:
   - Default is 300 seconds
   - Reduce if your requests are typically faster

## Security Best Practices

### 1. Authentication (Optional but Recommended)

By default, the server allows unauthenticated access. To add authentication:

```bash
# Require authentication
gcloud run services update send-to-kindle-mcp \
    --no-allow-unauthenticated \
    --region us-central1

# Grant access to specific users
gcloud run services add-iam-policy-binding send-to-kindle-mcp \
    --member="user:trusted-user@example.com" \
    --role="roles/run.invoker" \
    --region us-central1
```

### 2. Secret Management

- ✅ Never commit secrets to Git
- ✅ Use Secret Manager for all credentials
- ✅ Rotate secrets regularly
- ✅ Use App Passwords for Gmail (not your main password)

### 3. Network Security

For additional security, you can:
- Use Cloud Armor for DDoS protection
- Set up VPC connector for private networking
- Use Cloud Endpoints for API management

### 4. Monitoring

Set up alerts for suspicious activity:
```bash
# Create alert for high error rates
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Error Rate" \
    --condition-display-name="Error rate > 10%" \
    --condition-threshold-value=0.1
```

## Updating the Server

### Code Changes

After modifying `server.py`:

```bash
# Simply re-run the deployment script
bash deploy.sh
```

The script will rebuild and redeploy automatically.

### Manual Update

```bash
# Build new image
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/send-to-kindle-mcp

# Deploy new version
gcloud run deploy send-to-kindle-mcp \
    --image gcr.io/YOUR-PROJECT-ID/send-to-kindle-mcp \
    --region us-central1
```

### Rollback

If something goes wrong:

```bash
# List revisions
gcloud run revisions list --service send-to-kindle-mcp --region us-central1

# Rollback to previous revision
gcloud run services update-traffic send-to-kindle-mcp \
    --to-revisions REVISION-NAME=100 \
    --region us-central1
```

## Local Testing with HTTP Transport

Test HTTP mode locally before deploying:

```bash
# Set environment variables
export MCP_TRANSPORT=http
export MCP_PORT=8080
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export KINDLE_EMAIL=your-kindle@kindle.com
export FROM_EMAIL=your-email@gmail.com
export AUTHOR_NAME="Your Name"

# Run the server
python server.py
```

Server will be available at: `http://localhost:8080`

## Cleanup

To remove all cloud resources:

```bash
# Delete Cloud Run service
gcloud run services delete send-to-kindle-mcp --region us-central1 --quiet

# Delete container images
gcloud container images delete gcr.io/YOUR-PROJECT-ID/send-to-kindle-mcp --quiet

# Delete secrets
gcloud secrets delete smtp-host --quiet
gcloud secrets delete smtp-port --quiet
gcloud secrets delete smtp-user --quiet
gcloud secrets delete smtp-password --quiet
gcloud secrets delete kindle-email --quiet
gcloud secrets delete from-email --quiet
gcloud secrets delete author-name --quiet
```

## Alternative Deployment Options

### FastMCP Cloud (Simplest)

FastMCP offers a managed hosting platform:

1. Visit https://fastmcp.cloud/
2. Sign in with GitHub
3. Select your repository
4. Configure environment variables
5. Deploy automatically

**Pros**: Zero configuration, automatic deployment
**Cons**: Less control, may have usage limits

### Other Cloud Providers

The Dockerfile and code are portable. To deploy to:

**AWS Lambda / Fargate**:
- Use AWS Copilot or ECS
- Store secrets in AWS Secrets Manager

**Azure Container Instances**:
- Use Azure Container Instances
- Store secrets in Azure Key Vault

**DigitalOcean App Platform**:
- Connect your GitHub repo
- Configure environment variables
- Deploy with one click

## Support and Troubleshooting

### Getting Help

1. **Check logs first**: Most issues are visible in Cloud Run logs
2. **Verify secrets**: Ensure all required secrets are set correctly
3. **Test locally**: Use HTTP mode locally to isolate cloud-specific issues
4. **Check quotas**: Ensure you haven't hit GCP quotas

### Useful Commands

```bash
# Service status
gcloud run services describe send-to-kindle-mcp --region us-central1

# Recent deployments
gcloud run revisions list --service send-to-kindle-mcp --region us-central1

# Real-time metrics
gcloud run services logs tail send-to-kindle-mcp --region us-central1

# Test the endpoint
curl https://your-url.run.app/health
```

## Next Steps

- ✅ Set up monitoring and alerts
- ✅ Configure authentication if needed
- ✅ Test with your AI tools
- ✅ Set up CI/CD for automatic deployments
- ✅ Consider using a custom domain

For more information on Google Cloud Run, visit:
https://cloud.google.com/run/docs
