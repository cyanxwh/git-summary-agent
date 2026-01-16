#!/usr/bin/env python3
"""
Daily Git Work Summary Agent
============================
An agent built with Claude Agent SDK that automatically summarizes
your daily git work across multiple repositories.

Author: Kevin
"""

import asyncio
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from claude_agent_sdk import query, ClaudeAgentOptions


class GitWorkCollector:
    """Collects git activity from repositories."""

    def __init__(self, author_email: Optional[str] = None):
        self.author_email = author_email or self._get_git_user_email()

    def _get_git_user_email(self) -> str:
        """Get the global git user email."""
        try:
            result = subprocess.run(
                ["git", "config", "--global", "user.email"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def _run_git_command(self, repo_path: Path, args: list[str]) -> str:
        """Run a git command in the specified repository."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr.strip()}"

    def get_today_commits(self, repo_path: Path) -> str:
        """Get all commits from today by the current user."""
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        args = [
            "log",
            f"--author={self.author_email}",
            f"--since={today}",
            f"--until={tomorrow}",
            "--pretty=format:%h | %s | %ar",
            "--all"
        ]
        return self._run_git_command(repo_path, args)

    def get_today_diff_stats(self, repo_path: Path) -> str:
        """Get diff statistics for today's commits."""
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        args = [
            "log",
            f"--author={self.author_email}",
            f"--since={today}",
            f"--until={tomorrow}",
            "--stat",
            "--all"
        ]
        return self._run_git_command(repo_path, args)

    def get_today_files_changed(self, repo_path: Path) -> str:
        """Get list of files changed today."""
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        args = [
            "log",
            f"--author={self.author_email}",
            f"--since={today}",
            f"--until={tomorrow}",
            "--name-only",
            "--pretty=format:",
            "--all"
        ]
        result = self._run_git_command(repo_path, args)
        # Remove duplicates and empty lines
        files = set(f.strip() for f in result.split('\n') if f.strip())
        return '\n'.join(sorted(files))

    def get_repo_name(self, repo_path: Path) -> str:
        """Get the repository name."""
        return repo_path.name

    def get_current_branch(self, repo_path: Path) -> str:
        """Get the current branch name."""
        return self._run_git_command(repo_path, ["branch", "--show-current"])

    def is_git_repo(self, path: Path) -> bool:
        """Check if the path is a git repository."""
        return (path / ".git").exists()


def find_git_repos(parent_dir: str) -> list[Path]:
    """Find all git repositories in the parent directory."""
    parent = Path(parent_dir).expanduser().resolve()
    repos = []

    if not parent.exists():
        print(f"Warning: Directory {parent} does not exist")
        return repos

    # Check if parent itself is a git repo
    if (parent / ".git").exists():
        repos.append(parent)

    # Check immediate subdirectories
    for item in parent.iterdir():
        if item.is_dir() and (item / ".git").exists():
            repos.append(item)

    return repos


def collect_git_data(repos: list[Path], author_email: Optional[str] = None) -> str:
    """Collect git activity data from all repositories."""
    collector = GitWorkCollector(author_email)

    report_parts = []
    report_parts.append(f"# Daily Git Activity Report")
    report_parts.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %A')}")
    report_parts.append(f"**Author:** {collector.author_email}")
    report_parts.append(f"**Repositories Scanned:** {len(repos)}")
    report_parts.append("")

    has_activity = False

    for repo_path in repos:
        if not collector.is_git_repo(repo_path):
            continue

        repo_name = collector.get_repo_name(repo_path)
        commits = collector.get_today_commits(repo_path)

        if commits and not commits.startswith("Error"):
            has_activity = True
            current_branch = collector.get_current_branch(repo_path)
            diff_stats = collector.get_today_diff_stats(repo_path)
            files_changed = collector.get_today_files_changed(repo_path)

            report_parts.append(f"## Repository: {repo_name}")
            report_parts.append(f"**Path:** `{repo_path}`")
            report_parts.append(f"**Current Branch:** `{current_branch}`")
            report_parts.append("")

            report_parts.append("### Commits Today")
            report_parts.append("```")
            report_parts.append(commits)
            report_parts.append("```")
            report_parts.append("")

            if files_changed:
                report_parts.append("### Files Changed")
                report_parts.append("```")
                report_parts.append(files_changed)
                report_parts.append("```")
                report_parts.append("")

            if diff_stats:
                report_parts.append("### Diff Statistics")
                report_parts.append("```")
                report_parts.append(diff_stats)
                report_parts.append("```")
                report_parts.append("")

            report_parts.append("---")
            report_parts.append("")

    if not has_activity:
        report_parts.append("## No Git Activity Today")
        report_parts.append("No commits found in any of the scanned repositories for today.")

    return '\n'.join(report_parts)


async def run_summary_agent(
    repos_parent_dir: str = "~/projects",
    repo_paths: Optional[list[str]] = None,
    author_email: Optional[str] = None,
    output_dir: str = "~/daily_summaries",
    save_to_file: bool = True,
    notion_enabled: bool = False,
    notion_api_key: Optional[str] = None,
    notion_database_id: Optional[str] = None
) -> str:
    """
    Run the daily git summary agent.

    Args:
        repos_parent_dir: Parent directory containing git repos
        repo_paths: Optional list of specific repo paths (overrides repos_parent_dir)
        author_email: Git author email (auto-detected if not provided)
        output_dir: Directory to save the summary markdown files
        save_to_file: Whether to save to local markdown file
        notion_enabled: Whether to save to Notion
        notion_api_key: Notion API key
        notion_database_id: Notion database ID

    Returns:
        The generated summary
    """
    # Find repositories
    if repo_paths:
        repos = [Path(p).expanduser().resolve() for p in repo_paths]
    else:
        repos = find_git_repos(repos_parent_dir)

    if not repos:
        return "No git repositories found to summarize."

    # Collect raw git data
    git_data = collect_git_data(repos, author_email)

    # Use Claude Agent to create an intelligent summary
    prompt = f"""You are a helpful assistant that summarizes daily development work.

Below is the raw git activity data collected from the developer's repositories today.
Please analyze this data and create a professional, concise summary that:

1. **Work Summary**: Provide a high-level overview of what was accomplished today (2-3 sentences)
2. **Key Accomplishments**: List the main things achieved, grouped by project/repository
3. **Technical Details**: Brief mention of significant code changes or files modified
4. **Suggested Talking Points**: 2-3 bullet points suitable for a morning standup meeting

The summary should be suitable for sharing in a morning meeting to report on yesterday's work.

Here is the raw git data:

{git_data}

Please generate the summary in Markdown format."""

    summary_parts = []

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=[]  # No tools needed for summarization
        )
    ):
        if hasattr(message, 'content'):
            summary_parts.append(str(message.content))
        elif isinstance(message, str):
            summary_parts.append(message)

    summary = '\n'.join(summary_parts)

    # Save the summary
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"daily_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
    filepath = output_path / filename

    full_report = f"""# Daily Work Summary
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{summary}

---

## Raw Git Data

<details>
<summary>Click to expand raw git activity</summary>

{git_data}

</details>
"""

    # Save to local file if enabled
    if save_to_file:
        filepath.write_text(full_report)
        print(f"\n✅ Summary saved to: {filepath}")

    # Save to Notion if enabled
    if notion_enabled:
        try:
            from .notion_integration import save_to_notion
            notion_url = save_to_notion(
                summary=full_report,
                api_key=notion_api_key,
                database_id=notion_database_id,
                date=datetime.now()
            )
            if notion_url:
                print(f"✅ Summary saved to Notion: {notion_url}")
        except ImportError as e:
            print(f"⚠️ Notion integration not available: {e}")
            print("   Install: pip install notion-client")
        except Exception as e:
            print(f"⚠️ Failed to save to Notion: {e}")

    return full_report


def main():
    """Main entry point for manual execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate daily git work summary using Claude Agent SDK"
    )
    parser.add_argument(
        "--repos-dir",
        default="~/projects",
        help="Parent directory containing git repositories (default: ~/projects)"
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        help="Specific repository paths to scan (overrides --repos-dir)"
    )
    parser.add_argument(
        "--author",
        help="Git author email (auto-detected if not provided)"
    )
    parser.add_argument(
        "--output-dir",
        default="~/daily_summaries",
        help="Directory to save summaries (default: ~/daily_summaries)"
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Only print to console, don't save to file"
    )
    parser.add_argument(
        "--notion",
        action="store_true",
        help="Save summary to Notion database"
    )
    parser.add_argument(
        "--notion-api-key",
        help="Notion API key (or set NOTION_API_KEY env var)"
    )
    parser.add_argument(
        "--notion-database-id",
        help="Notion database ID (or set NOTION_DATABASE_ID env var)"
    )

    args = parser.parse_args()

    # Determine Notion settings
    notion_enabled = args.notion
    notion_api_key = args.notion_api_key or os.getenv("NOTION_API_KEY")
    notion_database_id = args.notion_database_id or os.getenv("NOTION_DATABASE_ID")

    summary = asyncio.run(run_summary_agent(
        repos_parent_dir=args.repos_dir,
        repo_paths=args.repos,
        author_email=args.author,
        output_dir=args.output_dir,
        save_to_file=not args.print_only,
        notion_enabled=notion_enabled,
        notion_api_key=notion_api_key,
        notion_database_id=notion_database_id
    ))

    print("\n" + "="*60)
    print("DAILY WORK SUMMARY")
    print("="*60)
    print(summary)


if __name__ == "__main__":
    main()
