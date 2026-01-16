#!/bin/bash
# Setup script to push git-summary-agent to GitHub
# Run this from the project directory after downloading

set -e

# Configuration
REPO_NAME="git-summary-agent"
GITHUB_USERNAME="kevinxwj"  # Change this if different

echo "🚀 Setting up git-summary-agent for GitHub..."

# Initialize git if not already
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: AI-powered daily git work summary agent

Features:
- Multi-repo git commit scanning
- AI-powered summaries using Claude Agent SDK
- Standup-ready talking points generation
- Notion database integration
- Flexible scheduling (built-in, systemd, launchd, cron)
- Configurable via JSON, environment variables, or CLI

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Rename branch to main if needed
git branch -M main

# Create GitHub repo and push
echo "🌐 Creating GitHub repository..."
gh repo create "$REPO_NAME" --public --source=. --remote=origin --push \
    --description "AI-powered daily git work summary agent using Claude Agent SDK. Auto-generates standup reports with Notion integration."

echo ""
echo "✅ Done! Your repo is live at:"
echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "📦 To install from GitHub:"
echo "   pip install git+https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
