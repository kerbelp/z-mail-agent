# Private Fork Setup

This is your private production instance of z-mail-agent. Follow these steps to set it up:

## Step 1: Remove gitignore rules for prompts/templates

In your private fork, remove these lines from `.gitignore`:

```
# Comment out or remove these lines:
# prompts/*.txt
# !prompts/*.example.txt
# templates/*.txt
# !templates/*.example.txt
```

Or simply delete the "Proprietary content" section (lines 32-37).

## Step 2: Commit your actual prompts and templates

```bash
# Remove the gitignore rules
sed -i '' '/# Proprietary content/,/!templates\/\*.example.txt/d' .gitignore

# Or manually edit .gitignore to remove those lines

# Now commit your actual files
git add prompts/*.txt templates/*.txt .gitignore
git commit -m "Add production prompts and templates"
git push
```

## Step 3: Set up GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

**Required:**
- `ZOHO_ACCOUNT_ID`
- `ZOHO_PROCESSED_LABEL_ID`
- `ZOHO_MCP_URL`
- `OPENAI_API_KEY` (or whatever LLM you're using)
- `REPLY_EMAIL_ADDRESS`

**Optional:**
- `LANGSMITH_TRACING` (set to `true` for monitoring)
- `LANGSMITH_API_KEY`

## Step 4: Enable GitHub Actions

1. Go to **Actions** tab
2. Click "I understand my workflows, go ahead and enable them"
3. The cron will start running automatically every 15 minutes

## Step 5: Monitor

- View runs in the **Actions** tab
- Check logs for each run
- Adjust schedule in `.github/workflows/email-cron.yml` if needed

## Customizing the Schedule

Edit `.github/workflows/email-cron.yml` line 5:

```yaml
# Every 15 minutes
- cron: '*/15 * * * *'

# Every 30 minutes
- cron: '*/30 * * * *'

# Every hour
- cron: '0 * * * *'

# Every 4 hours
- cron: '0 */4 * * *'

# Daily at 9 AM
- cron: '0 9 * * *'
```

Use https://crontab.guru to test cron expressions.

## Syncing with Upstream

To get updates from the public repo:

```bash
# Add upstream remote (one time)
git remote add upstream https://github.com/original-username/z-mail-agent.git

# Pull updates
git fetch upstream
git merge upstream/main

# Resolve any conflicts, then push
git push origin main
```

Your prompts/templates won't be affected since they're only in your private fork.
