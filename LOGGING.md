# Colored Logging

The email assistant includes smart colored terminal output to make it easier to track what's happening during email processing.

## Features

### Automatic Color Detection
- Colors are **only applied when output is to a terminal** (interactive session)
- Colors are **automatically disabled** when output is piped or redirected (e.g., `python main.py | tee log.txt`)
- Uses `sys.stdout.isatty()` for detection

### Color Scheme

#### Standard Log Levels
- **DEBUG**: Cyan
- **INFO**: Green
- **WARNING**: Yellow
- **ERROR**: Red
- **CRITICAL**: Magenta

#### Special Event Markers
The system looks for specific keywords in log messages and applies special formatting:

- **`[ARTICLE_SUBMISSION]`**: Bold Green - When processing article submissions
- **`[REPLY_SENT]`**: Bold Green - When a reply is successfully sent
- **`[SKIP]`**: Gray - When an email is skipped
- **`[DRY_RUN]`**: Bold Yellow - When running in dry-run mode

## Usage

Colors are automatically enabled when you run the assistant in your terminal:

```bash
python main.py
```

To disable colors (e.g., for logging to a file), pipe the output:

```bash
python main.py | tee log.txt
```

Or redirect to a file:

```bash
python main.py > log.txt 2>&1
```

## Implementation

The colored logging is implemented in [config.py](config.py) using a custom `ColoredFormatter` class that extends Python's standard `logging.Formatter`. The formatter:

1. Checks if stdout is a TTY (terminal)
2. Applies ANSI color codes when appropriate
3. Uses keyword detection for special events
4. Falls back to standard formatting when colors are disabled

## Examples

When running in terminal, you'll see output like:

```
2024-01-21 05:36:09,045 - INFO - [ARTICLE_SUBMISSION] Handling article submission from user@example.com
2024-01-21 05:36:09,045 - INFO - [REPLY_SENT] Successfully sent reply to user@example.com
2024-01-21 05:36:09,045 - INFO - [SKIP] Skipping email 123, subject: Newsletter
2024-01-21 05:36:09,045 - WARNING - ZOHO_PROCESSED_LABEL_ID is not configured
```

Where:
- Article submission messages appear in **bold green**
- Reply sent messages appear in **bold green**
- Skip messages appear in **gray**
- Warnings appear in **yellow**
