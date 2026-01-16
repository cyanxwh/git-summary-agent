"""
Git Summary Agent
=================
AI-powered daily git work summary agent using Claude Agent SDK.

Features:
- Multi-repo support
- AI-powered summaries with Claude
- Standup-ready talking points
- Notion integration
- Flexible scheduling
"""

__version__ = "0.1.0"

from .agent import run_summary_agent, GitWorkCollector, find_git_repos
from .config import AgentConfig, get_config

__all__ = [
    "run_summary_agent",
    "GitWorkCollector",
    "find_git_repos",
    "AgentConfig",
    "get_config",
]
