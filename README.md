# Daily Git Work Summary Agent 🤖

An automated agent built with the **Claude Agent SDK** that summarizes your daily git work across multiple repositories. Perfect for preparing morning standup reports!

## ✨ Features

- **Multi-repo support**: Scan all repos in a parent directory or specify individual repos
- **Intelligent summaries**: Claude AI analyzes your commits and generates professional summaries
- **Standup-ready output**: Includes suggested talking points for morning meetings
- **Flexible scheduling**: Run at any fixed time daily
- **Multiple output options**: Save to markdown files, Notion, and/or print to console
- **Notion integration**: Automatically save summaries to a Notion database
- **Auto-detection**: Automatically detects your git email from config

## 📋 Prerequisites

- Python 3.10 or higher
- Git installed and configured
- Anthropic API key
- (Optional) Notion API key for Notion integration

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Your API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 3. Configure Your Repos

Edit `config.py` or create a `config.json`:

```json
{
  "repos_parent_dir": "~/projects",
  "schedule_time": "18:00",
  "timezone": "Asia/Shanghai",
  "output_dir": "~/daily_summaries"
}
```

### 4. Run Manually (Test)

```bash
python agent.py --repos-dir ~/projects
```

### 5. Start the Scheduler

```bash
python scheduler.py
```

## 📁 Project Structure

```
daily_git_summary_agent/
├── agent.py              # Main agent logic
├── config.py             # Configuration management
├── scheduler.py          # Automatic scheduling
├── notion_integration.py # Notion API integration
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## 📝 Notion Integration

Save your daily summaries directly to a Notion database!

### Step 1: Create a Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Give it a name (e.g., "Daily Git Summary")
4. Select your workspace
5. Click **"Submit"**
6. Copy the **"Internal Integration Token"** (starts with `secret_`)

### Step 2: Create a Database in Notion

1. Create a new page in Notion
2. Add a **Database - Full page** to it
3. The database should have these properties (they'll be auto-created if missing):
   - **Name** (Title) - Required
   - **Date** (Date) - For the summary date
   - **Summary** (Text) - Brief overview
   - **Repositories** (Multi-select) - Repos with activity
   - **Tags** (Multi-select) - Optional tags
   - **Status** (Select) - Draft/Ready/Presented

### Step 3: Share Database with Integration

1. Open your database in Notion
2. Click **"..."** (three dots) in the top right
3. Click **"Add connections"**
4. Select your integration
5. Copy the **Database ID** from the URL:
   ```
   https://notion.so/your-workspace/DATABASE_ID?v=...
                                    ^^^^^^^^^^^
   ```

### Step 4: Configure the Agent

**Option A: Environment Variables**
```bash
export NOTION_API_KEY="secret_your_api_key_here"
export NOTION_DATABASE_ID="your_database_id_here"
export NOTION_ENABLED="true"
```

**Option B: config.json**
```json
{
  "repos_parent_dir": "~/projects",
  "schedule_time": "18:00",
  "timezone": "Asia/Shanghai",
  "notion_enabled": true,
  "notion_api_key": "secret_your_api_key_here",
  "notion_database_id": "your_database_id_here"
}
```

**Option C: Command Line**
```bash
python agent.py --notion --notion-api-key "secret_..." --notion-database-id "abc123..."
```

### Step 5: Test Notion Integration

```bash
# Test the connection
python notion_integration.py

# Run a summary with Notion
python agent.py --notion
```

## ⚙️ Configuration Options

### Via config.json

Create a `config.json` file in the project directory:

```json
{
  "repos_parent_dir": "~/projects",
  "specific_repos": [],
  "author_email": null,
  "schedule_time": "18:00",
  "timezone": "Asia/Shanghai",
  "output_dir": "~/daily_summaries",
  "save_to_file": true,
  "print_to_console": true,
  "model": "claude-sonnet-4-20250514",
  "notion_enabled": true,
  "notion_api_key": "secret_...",
  "notion_database_id": "abc123..."
}
```

### Via Environment Variables

```bash
# Git summary settings
export GIT_SUMMARY_REPOS_DIR="~/projects"
export GIT_SUMMARY_TIME="18:00"
export GIT_SUMMARY_TZ="Asia/Shanghai"
export GIT_SUMMARY_OUTPUT_DIR="~/daily_summaries"
export GIT_SUMMARY_AUTHOR="your-email@example.com"

# Notion settings
export NOTION_ENABLED="true"
export NOTION_API_KEY="secret_..."
export NOTION_DATABASE_ID="abc123..."
```

### Configuration Priority

1. `config.json` (if exists)
2. Environment variables
3. Default values in `config.py`

## 🕐 Scheduling Options

### Option 1: Run with Built-in Scheduler

```bash
# Run in foreground
python scheduler.py

# Run as daemon (background)
python scheduler.py --daemon

# Use simple scheduler (no APScheduler dependency)
python scheduler.py --simple
```

### Option 2: Use System Scheduler (Recommended for Production)

#### Linux (systemd)

```bash
# Generate service file
python scheduler.py --generate-systemd

# Install (follow printed instructions)
sudo cp daily-git-summary.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable daily-git-summary
sudo systemctl start daily-git-summary
```

#### macOS (launchd)

```bash
# Generate plist file
python scheduler.py --generate-launchd

# Install
cp com.user.daily-git-summary.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.daily-git-summary.plist
```

#### Using Cron

Add to your crontab (`crontab -e`):

```cron
# Run at 6 PM daily
0 18 * * * cd /path/to/daily_git_summary_agent && /usr/bin/python3 agent.py --notion >> /var/log/git-summary.log 2>&1
```

## 🎯 Usage Examples

### Run Summary Now

```bash
# Using default config
python agent.py

# Specify repos directory
python agent.py --repos-dir ~/work

# Specify individual repos
python agent.py --repos ~/work/project1 ~/personal/project2

# Specify author email
python agent.py --author your-email@example.com

# Save to Notion
python agent.py --notion

# Save to Notion only (no local file)
python agent.py --notion --print-only
```

### Quick Test

```bash
python scheduler.py --run-now
```

## 📝 Sample Output

The agent generates markdown summaries like this:

```markdown
# Daily Work Summary
**Generated:** 2026-01-14 18:00:00

---

## Work Summary
Today focused on implementing the new authentication system
and fixing critical bugs in the payment module.

## Key Accomplishments

### my-web-app
- Implemented OAuth2 login flow
- Added user session management
- Fixed password reset email template

### api-service
- Optimized database queries (30% faster)
- Added rate limiting middleware

## Suggested Talking Points
- Completed OAuth2 implementation, ready for testing
- Performance improvements in API service
- Will continue with user profile features tomorrow
```

## 🔧 Troubleshooting

### "No git repositories found"

- Check that your `repos_parent_dir` path is correct
- Ensure the repos have a `.git` directory
- Try using absolute paths in `specific_repos`

### "No commits found today"

- Verify your git email matches (`git config user.email`)
- Check that commits were made after midnight today
- Try specifying `--author` explicitly

### Scheduler not running

- Check that `ANTHROPIC_API_KEY` is set
- View logs in `scheduler.log`
- Try running with `--simple` flag

### Notion integration issues

- Verify your API key is correct (`secret_...`)
- Ensure the database is shared with your integration
- Check that the database ID is correct (from the URL)
- Run `python notion_integration.py` to test the connection

## 📄 License

MIT License - feel free to modify and use as needed!

## 🤝 Contributing

Built with ❤️ using the Claude Agent SDK. Contributions welcome!
