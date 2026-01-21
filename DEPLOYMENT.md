# Deploying to LangGraph Cloud

This guide walks you through deploying z-mail-agent to LangGraph Cloud with cron scheduling.

## Prerequisites

1. **LangSmith Account**: Sign up at https://smith.langchain.com
2. **LangGraph CLI**: Install the CLI tool
   ```bash
   pip install langgraph-cli
   ```

## Step 1: Verify Your Configuration

Ensure your [langgraph.json](langgraph.json) is properly configured:

```json
{
  "dependencies": ["."],
  "graphs": {
    "email_agent": "./main.py:build_workflow"
  },
  "env": ".env"
}
```

## Step 2: Test Locally

Before deploying, test your agent locally:

```bash
# Test the workflow
python main.py

# Or use LangGraph CLI
langgraph dev
```

## Step 3: Deploy to LangGraph Cloud

### Deploy via LangSmith UI

LangGraph Cloud deployments are managed through the LangSmith web interface:

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Go to LangSmith** (https://smith.langchain.com):
   - Navigate to **Deployments** → **+ New Deployment**
   
3. **Connect GitHub Repository**:
   - Click "Connect GitHub"
   - Authorize LangSmith to access your repositories
   - Select your `z-mail-agent` repository
   - Choose the branch (e.g., `main`)

4. **Configure Deployment**:
   - **Deployment Name**: `z-mail-agent`
   - **Graph**: The system will auto-detect `email_agent` from [langgraph.json](langgraph.json)
   - Click "Next"

5. **Set Environment Variables**:
   
   Required variables:
   ```
   ZOHO_ACCOUNT_ID=your-account-id
   ZOHO_PROCESSED_LABEL_ID=your-label-id
   ZOHO_MCP_URL=your-mcp-url
   LLM_API_KEY=your-openai-key
   REPLY_EMAIL_ADDRESS=your-reply-address
   ```
   
   Optional configuration:
   ```
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o
   LLM_TEMPERATURE=0
   DRY_RUN=false
   SEND_REPLY=true
   ADD_LABEL=true
   READ_EMAIL_LIMIT=10
   ```

6. **Deploy**:
   - Review configuration
   - Click "Deploy"
   - Wait for deployment to complete (usually 2-5 minutes)

### Alternative: Self-Hosted with Docker

If you prefer to self-host instead of using LangGraph Cloud:

1. **Build Docker image**:
   ```bash
   langgraph build -t z-mail-agent:latest
   ```

2. **Run locally**:
   ```bash
   langgraph up
   ```

3. **Deploy to your infrastructure** (AWS ECS, GCP Cloud Run, etc.)

## Step 4: Set Up Cron Scheduling

LangGraph Cloud supports cron-based scheduling. You have two options:

### Option A: Using LangGraph Cloud Crons (Native)

In your LangSmith dashboard:

1. Navigate to **Deployments** → Your deployment → **Crons**
2. Click **Add Cron**
3. Configure:
   - **Name**: `email-processing-cron`
   - **Schedule**: Use cron syntax (e.g., `*/15 * * * *` for every 15 minutes)
   - **Graph**: Select `email_agent`
   - **Input**: Provide initial state JSON:
     ```json
     {
       "emails": [],
       "processed_count": 0,
       "replied_count": 0,
       "current_index": 0,
       "errors": [],
       "current_email": {},
       "classification_result": null
     }
     ```

**Common Cron Schedules**:
- Every 15 minutes: `*/15 * * * *`
- Every hour: `0 * * * *`
- Every 4 hours: `0 */4 * * *`
- Daily at 9 AM: `0 9 * * *`
- Weekdays at 9 AM and 2 PM: `0 9,14 * * 1-5`

### Option B: Using External Cron Service

If you prefer external control, you can invoke the deployed agent via API from LangSmith:

**Get your API endpoint:**
1. Go to your deployment in LangSmith
2. Copy the deployment URL (e.g., `https://your-deployment-id.langchain.com`)
3. Get your API key from LangSmith Settings → API Keys

**Set up external cron** (using GitHub Actions, AWS EventBridge, or Render cron jobs):

Example GitHub Actions workflow (`.github/workflows/email-cron.yml`):

```yaml
name: Process Emails
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Email Agent
        run: |
          curl -X POST https://your-deployment.langchain.com/invoke \
            -H "x-api-key: ${{ secrets.LANGSMITH_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "input": {
                "emails": [],
                "processed_count": 0,
                "replied_count": 0,
                "current_index": 0,
                "errors": [],
                "current_email": {},
                "classification_result": null
              }
            }'
```

## Step 5: Monitor Your Deployment

### View Logs and Traces

1. Go to **LangSmith** → **Projects** → Your project
2. View all invocations, LLM calls, and errors
3. Debug issues using the trace viewer

### Set Up Alerts

1. Navigate to **Settings** → **Alerts**
2. Create alerts for:
   - Deployment errors
   - High error rates
   - Token usage thresholds
   - Execution time

## Step 6: Update Your Deployment

When you make changes:

```bash
# Commit and push changes
git add .
git commit -m "Update classification rules"
git push origin main
```

LangGraph Cloud will automatically redeploy when you push to your connected branch.

For manual redeployment, go to your deployment in LangSmith and click "Redeploy".

## Configuration Files Reference

Your deployment includes these files:

- **`langgraph.json`**: Deployment configuration
- **`classifications.yaml`**: Email classification rules (auto-deployed)
- **`prompts/*.txt`**: Classification prompts (gitignored - deploy manually)
- **`templates/*.txt`**: Reply templates (gitignored - deploy manually)
- **`.env`**: Local environment variables (NOT deployed)

## Security Best Practices

1. **Never commit secrets**: Use environment variables for API keys
2. **Use LangSmith's secret management**: Store sensitive values in LangSmith UI
3. **Limit permissions**: Create API keys with minimum required permissions
4. **Monitor usage**: Set up alerts for unusual activity
5. **Use dry run mode**: Test with `DRY_RUN=true` before production

## Troubleshooting

### Deployment fails
```bash
# Check deployment logs in LangSmith UI
# Or use CLI to check local build
langgraph build -t z-mail-agent:latest
```

### Missing prompts/templates
Since `prompts/*.txt` and `templates/*.txt` are gitignored, you need to:
1. Copy them to the deployment manually, or
2. Store them in LangSmith's file storage, or
3. Use a separate configuration service (AWS Secrets Manager, etc.)

**Recommended approach**: Create a separate private GitHub repo for your prompts/templates and reference them:

```bash
# In langgraph.json
{
  "dependencies": [
    ".",
    "git+https://github.com/yourusername/email-prompts-private.git"
  ],
  ...
}
```

### Cron not triggering
- Verify cron syntax at https://crontab.guru
- Check timezone settings in LangSmith
- Ensure deployment is active

## Cost Optimization

1. **Adjust frequency**: Don't check emails more often than needed
2. **Set email limits**: Use `READ_EMAIL_LIMIT` to batch process
3. **Use cheaper models**: Switch to `gpt-4o-mini` for simple classifications
4. **Monitor token usage**: Track costs in LangSmith dashboard

## Example Production Configuration

```bash
# Production environment variables
DRY_RUN=false
SEND_REPLY=true
ADD_LABEL=true
READ_EMAIL_LIMIT=50
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini  # Cost-effective
LLM_TEMPERATURE=0
LANGSMITH_TRACING=true  # Monitor production
```

## Next Steps

After deployment:
1. ✅ Monitor first few runs closely
2. ✅ Adjust cron schedule based on email volume
3. ✅ Add more classification types as needed
4. ✅ Set up alerting for critical errors
5. ✅ Review LangSmith traces regularly for optimization

## Support

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/cloud/
- **LangSmith**: https://docs.smith.langchain.com/
- **API Reference**: https://langchain-ai.github.io/langgraph/cloud/reference/api/
