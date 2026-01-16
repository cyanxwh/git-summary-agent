#!/usr/bin/env python3
"""
Scheduler for Daily Git Summary Agent
======================================
Runs the git summary agent automatically at a scheduled time each day.

Usage:
    python scheduler.py              # Run scheduler (foreground)
    python scheduler.py --daemon     # Run as background daemon
    python scheduler.py --run-now    # Run summary immediately
"""

import asyncio
import signal
import sys
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Optional
import argparse

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    from zoneinfo import ZoneInfo
    PYTZ_AVAILABLE = False

from .config import get_config, AgentConfig
from .agent import run_summary_agent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scheduler.log')
    ]
)
logger = logging.getLogger(__name__)


class GitSummaryScheduler:
    """Scheduler for running the git summary agent at specified times."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or get_config()
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False

    def _parse_time(self) -> tuple[int, int]:
        """Parse schedule_time string to hour and minute."""
        parts = self.config.schedule_time.split(':')
        return int(parts[0]), int(parts[1])

    def _get_timezone(self):
        """Get timezone object."""
        if PYTZ_AVAILABLE:
            return pytz.timezone(self.config.timezone)
        else:
            return ZoneInfo(self.config.timezone)

    async def _run_job(self):
        """Run the git summary job."""
        logger.info("Starting daily git summary job...")

        try:
            repos = self.config.specific_repos if self.config.specific_repos else None

            summary = await run_summary_agent(
                repos_parent_dir=self.config.repos_parent_dir,
                repo_paths=repos,
                author_email=self.config.author_email,
                output_dir=self.config.output_dir,
                save_to_file=self.config.save_to_file,
                notion_enabled=self.config.notion_enabled,
                notion_api_key=self.config.notion_api_key,
                notion_database_id=self.config.notion_database_id
            )

            if self.config.print_to_console:
                print("\n" + "="*60)
                print("DAILY WORK SUMMARY")
                print("="*60)
                print(summary)

            logger.info("Daily git summary completed successfully")

        except Exception as e:
            logger.error(f"Error running git summary: {e}", exc_info=True)

    def start(self):
        """Start the scheduler."""
        if not APSCHEDULER_AVAILABLE:
            logger.error(
                "APScheduler is not installed. "
                "Run: pip install apscheduler"
            )
            sys.exit(1)

        hour, minute = self._parse_time()
        tz = self._get_timezone()

        self.scheduler = AsyncIOScheduler(timezone=tz)

        # Schedule the job
        trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
        self.scheduler.add_job(
            self._run_job,
            trigger=trigger,
            id='daily_git_summary',
            name='Daily Git Work Summary',
            misfire_grace_time=3600  # Allow 1 hour grace period
        )

        self.scheduler.start()
        self._running = True

        logger.info(
            f"Scheduler started. Daily summary will run at "
            f"{self.config.schedule_time} ({self.config.timezone})"
        )

        # Show next run time
        job = self.scheduler.get_job('daily_git_summary')
        if job:
            logger.info(f"Next run scheduled at: {job.next_run_time}")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            self._running = False
            logger.info("Scheduler stopped")

    async def run_forever(self):
        """Run the scheduler forever."""
        self.start()

        # Handle signals for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep running
        try:
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.stop()


async def run_simple_scheduler(config: AgentConfig):
    """
    Simple scheduler without APScheduler dependency.
    Uses asyncio sleep to wait for the scheduled time.
    """
    logger.info("Starting simple scheduler (no APScheduler)")

    hour, minute = config.schedule_time.split(':')
    target_hour, target_minute = int(hour), int(minute)

    while True:
        now = datetime.now()
        target = now.replace(
            hour=target_hour,
            minute=target_minute,
            second=0,
            microsecond=0
        )

        # If target time already passed today, schedule for tomorrow
        if now >= target:
            target = target.replace(day=target.day + 1)

        wait_seconds = (target - now).total_seconds()
        logger.info(
            f"Next summary scheduled at {target.strftime('%Y-%m-%d %H:%M')} "
            f"(in {wait_seconds/3600:.1f} hours)"
        )

        await asyncio.sleep(wait_seconds)

        # Run the summary
        try:
            repos = config.specific_repos if config.specific_repos else None

            summary = await run_summary_agent(
                repos_parent_dir=config.repos_parent_dir,
                repo_paths=repos,
                author_email=config.author_email,
                output_dir=config.output_dir,
                save_to_file=config.save_to_file,
                notion_enabled=config.notion_enabled,
                notion_api_key=config.notion_api_key,
                notion_database_id=config.notion_database_id
            )

            if config.print_to_console:
                print("\n" + "="*60)
                print("DAILY WORK SUMMARY")
                print("="*60)
                print(summary)

            logger.info("Daily git summary completed successfully")

        except Exception as e:
            logger.error(f"Error running git summary: {e}", exc_info=True)


def create_systemd_service() -> str:
    """Generate a systemd service file content."""
    script_path = Path(__file__).resolve()
    working_dir = script_path.parent

    return f"""[Unit]
Description=Daily Git Work Summary Agent
After=network.target

[Service]
Type=simple
User={Path.home().name}
WorkingDirectory={working_dir}
Environment="ANTHROPIC_API_KEY=your-api-key-here"
ExecStart=/usr/bin/python3 {script_path}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""


def create_launchd_plist() -> str:
    """Generate a macOS launchd plist content."""
    script_path = Path(__file__).resolve()
    working_dir = script_path.parent

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.daily-git-summary</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_path}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_API_KEY</key>
        <string>your-api-key-here</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{working_dir}/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>{working_dir}/scheduler.error.log</string>
</dict>
</plist>
"""


def main():
    parser = argparse.ArgumentParser(
        description="Schedule daily git work summary"
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run the summary immediately"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a background daemon"
    )
    parser.add_argument(
        "--generate-systemd",
        action="store_true",
        help="Generate systemd service file"
    )
    parser.add_argument(
        "--generate-launchd",
        action="store_true",
        help="Generate macOS launchd plist file"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple scheduler without APScheduler"
    )

    args = parser.parse_args()
    config = get_config()

    if args.generate_systemd:
        service_content = create_systemd_service()
        service_path = Path("daily-git-summary.service")
        service_path.write_text(service_content)
        print(f"Generated: {service_path}")
        print("\nTo install:")
        print(f"  sudo cp {service_path} /etc/systemd/system/")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable daily-git-summary")
        print("  sudo systemctl start daily-git-summary")
        return

    if args.generate_launchd:
        plist_content = create_launchd_plist()
        plist_path = Path("com.user.daily-git-summary.plist")
        plist_path.write_text(plist_content)
        print(f"Generated: {plist_path}")
        print("\nTo install:")
        print(f"  cp {plist_path} ~/Library/LaunchAgents/")
        print(f"  launchctl load ~/Library/LaunchAgents/{plist_path.name}")
        return

    if args.run_now:
        # Run immediately
        repos = config.specific_repos if config.specific_repos else None
        summary = asyncio.run(run_summary_agent(
            repos_parent_dir=config.repos_parent_dir,
            repo_paths=repos,
            author_email=config.author_email,
            output_dir=config.output_dir
        ))
        print(summary)
        return

    if args.daemon:
        # Daemonize
        import os
        if os.fork() > 0:
            sys.exit(0)
        os.setsid()
        if os.fork() > 0:
            sys.exit(0)

    # Run scheduler
    if args.simple or not APSCHEDULER_AVAILABLE:
        asyncio.run(run_simple_scheduler(config))
    else:
        scheduler = GitSummaryScheduler(config)
        asyncio.run(scheduler.run_forever())


if __name__ == "__main__":
    main()
