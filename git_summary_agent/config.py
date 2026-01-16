"""
Configuration for Daily Git Summary Agent
==========================================
Edit this file to customize your settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json
import os


@dataclass
class AgentConfig:
    """Configuration settings for the daily git summary agent."""

    # Repository settings
    repos_parent_dir: str = "~/projects"
    """Parent directory containing your git repositories."""

    specific_repos: list[str] = field(default_factory=list)
    """Specific repository paths to scan. If provided, repos_parent_dir is ignored."""

    # Author settings
    author_email: Optional[str] = None
    """Git author email. Auto-detected from git config if not provided."""

    # Schedule settings
    schedule_time: str = "18:00"
    """Time to run the daily summary (24-hour format, e.g., '18:00' for 6 PM)."""

    timezone: str = "Asia/Shanghai"
    """Timezone for scheduling (e.g., 'Asia/Shanghai', 'America/New_York')."""

    # Output settings
    output_dir: str = "~/daily_summaries"
    """Directory where summary files are saved."""

    save_to_file: bool = True
    """Whether to save summaries to markdown files."""

    print_to_console: bool = True
    """Whether to print summaries to console."""

    # Claude Agent settings
    model: str = "claude-sonnet-4-20250514"
    """Claude model to use for summarization."""

    # Notion settings
    notion_enabled: bool = False
    """Whether to save summaries to Notion."""

    notion_api_key: Optional[str] = None
    """Notion API key. Can also be set via NOTION_API_KEY env var."""

    notion_database_id: Optional[str] = None
    """Notion database ID. Can also be set via NOTION_DATABASE_ID env var."""

    @classmethod
    def from_file(cls, config_path: str = "config.json") -> "AgentConfig":
        """Load configuration from a JSON file."""
        path = Path(config_path).expanduser()
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                return cls(**data)
        return cls()

    def to_file(self, config_path: str = "config.json"):
        """Save configuration to a JSON file."""
        path = Path(config_path).expanduser()
        data = {
            "repos_parent_dir": self.repos_parent_dir,
            "specific_repos": self.specific_repos,
            "author_email": self.author_email,
            "schedule_time": self.schedule_time,
            "timezone": self.timezone,
            "output_dir": self.output_dir,
            "save_to_file": self.save_to_file,
            "print_to_console": self.print_to_console,
            "model": self.model,
            "notion_enabled": self.notion_enabled,
            "notion_api_key": self.notion_api_key,
            "notion_database_id": self.notion_database_id,
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Configuration saved to: {path}")

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables."""
        return cls(
            repos_parent_dir=os.getenv("GIT_SUMMARY_REPOS_DIR", "~/projects"),
            specific_repos=os.getenv("GIT_SUMMARY_REPOS", "").split(",") if os.getenv("GIT_SUMMARY_REPOS") else [],
            author_email=os.getenv("GIT_SUMMARY_AUTHOR"),
            schedule_time=os.getenv("GIT_SUMMARY_TIME", "18:00"),
            timezone=os.getenv("GIT_SUMMARY_TZ", "Asia/Shanghai"),
            output_dir=os.getenv("GIT_SUMMARY_OUTPUT_DIR", "~/daily_summaries"),
            save_to_file=os.getenv("GIT_SUMMARY_SAVE_FILE", "true").lower() == "true",
            print_to_console=os.getenv("GIT_SUMMARY_PRINT", "true").lower() == "true",
            model=os.getenv("GIT_SUMMARY_MODEL", "claude-sonnet-4-20250514"),
            notion_enabled=os.getenv("NOTION_ENABLED", "false").lower() == "true",
            notion_api_key=os.getenv("NOTION_API_KEY"),
            notion_database_id=os.getenv("NOTION_DATABASE_ID"),
        )


# Default configuration - edit these values for your setup
DEFAULT_CONFIG = AgentConfig(
    # === EDIT THESE VALUES ===

    # Option 1: Parent directory containing all your repos
    repos_parent_dir="~/projects",

    # Option 2: Or specify individual repo paths (uncomment and add your paths)
    # specific_repos=[
    #     "~/projects/my-app",
    #     "~/projects/my-library",
    #     "~/work/company-project",
    # ],

    # Your git email (leave as None to auto-detect)
    author_email=None,  # e.g., "kevinxwj@icloud.com"

    # When to run the daily summary (24-hour format)
    schedule_time="18:00",  # 6 PM

    # Your timezone
    timezone="Asia/Shanghai",

    # Where to save the summaries
    output_dir="~/daily_summaries",

    # === NOTION SETTINGS ===
    # Set to True to enable Notion integration
    notion_enabled=False,

    # Your Notion API key (or set NOTION_API_KEY env var)
    notion_api_key=None,  # e.g., "secret_..."

    # Your Notion database ID (or set NOTION_DATABASE_ID env var)
    notion_database_id=None,  # e.g., "abc123def456..."
)


def get_config() -> AgentConfig:
    """Get the current configuration.

    Priority:
    1. config.json if it exists
    2. Environment variables
    3. DEFAULT_CONFIG from this file
    """
    config_file = Path("config.json")
    if config_file.exists():
        return AgentConfig.from_file(str(config_file))

    # Check if any env vars are set
    if os.getenv("GIT_SUMMARY_REPOS_DIR") or os.getenv("GIT_SUMMARY_REPOS"):
        return AgentConfig.from_env()

    return DEFAULT_CONFIG


if __name__ == "__main__":
    # Generate a sample config.json file
    config = DEFAULT_CONFIG
    config.to_file("config.json")
    print("Sample config.json created! Edit it to customize your settings.")
