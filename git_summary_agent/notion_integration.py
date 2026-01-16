"""
Notion Integration for Daily Git Summary Agent
===============================================
Saves daily summaries to a Notion database.
"""

import os
import re
from datetime import datetime
from typing import Optional
import logging

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class NotionSummaryClient:
    """Client for saving git summaries to Notion."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        database_id: Optional[str] = None
    ):
        """
        Initialize Notion client.

        Args:
            api_key: Notion API key (or set NOTION_API_KEY env var)
            database_id: Notion database ID (or set NOTION_DATABASE_ID env var)
        """
        if not NOTION_AVAILABLE:
            raise ImportError(
                "notion-client is not installed. "
                "Run: pip install notion-client"
            )

        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")

        if not self.api_key:
            raise ValueError(
                "Notion API key not provided. "
                "Set NOTION_API_KEY environment variable or pass api_key parameter."
            )

        if not self.database_id:
            raise ValueError(
                "Notion database ID not provided. "
                "Set NOTION_DATABASE_ID environment variable or pass database_id parameter."
            )

        self.client = Client(auth=self.api_key)

    def _markdown_to_notion_blocks(self, markdown: str) -> list[dict]:
        """Convert markdown text to Notion blocks."""
        blocks = []
        lines = markdown.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Headers
            if line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]
                    }
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]
                    }
                })
            elif line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]
                    }
                })
            # Bullet points
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                content = line.strip()[2:]
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                })
            # Numbered lists
            elif re.match(r'^\d+\.\s', line.strip()):
                content = re.sub(r'^\d+\.\s', '', line.strip())
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                })
            # Code blocks
            elif line.strip().startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": '\n'.join(code_lines)}}],
                        "language": "plain text"
                    }
                })
            # Horizontal rule
            elif line.strip() == '---':
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
            # Bold text line (like **Date:** ...)
            elif line.strip().startswith('**'):
                # Convert to callout for emphasis
                content = line.strip().replace('**', '')
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}, "annotations": {"bold": True}}]
                    }
                })
            # Regular paragraph
            else:
                # Truncate if too long (Notion has 2000 char limit per block)
                content = line.strip()
                if len(content) > 1900:
                    content = content[:1900] + "..."
                if content:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    })

            i += 1

        return blocks

    def _extract_summary_sections(self, summary: str) -> dict:
        """Extract key sections from the summary for database properties."""
        sections = {
            "work_summary": "",
            "accomplishments": "",
            "talking_points": "",
            "repos": []
        }

        # Extract work summary
        work_match = re.search(
            r'(?:Work Summary|Summary)[:\s]*\n+(.+?)(?=\n##|\n\*\*|$)',
            summary,
            re.IGNORECASE | re.DOTALL
        )
        if work_match:
            sections["work_summary"] = work_match.group(1).strip()[:2000]

        # Extract repository names
        repo_matches = re.findall(r'Repository:\s*(\S+)', summary)
        sections["repos"] = repo_matches[:10]  # Limit to 10 repos

        # Extract talking points
        talking_match = re.search(
            r'(?:Talking Points|Standup)[:\s]*\n+(.+?)(?=\n##|\n---|\n<|$)',
            summary,
            re.IGNORECASE | re.DOTALL
        )
        if talking_match:
            sections["talking_points"] = talking_match.group(1).strip()[:2000]

        return sections

    def save_summary(
        self,
        summary: str,
        date: Optional[datetime] = None,
        title: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> str:
        """
        Save a summary to the Notion database.

        Args:
            summary: The markdown summary content
            date: Date of the summary (defaults to today)
            title: Custom title (defaults to "Daily Summary - YYYY-MM-DD")
            tags: Optional list of tags

        Returns:
            URL of the created Notion page
        """
        date = date or datetime.now()
        title = title or f"Daily Summary - {date.strftime('%Y-%m-%d')}"

        # Extract sections for properties
        sections = self._extract_summary_sections(summary)

        # Build properties based on what the database might have
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            }
        }

        # Try to add date property (common name variations)
        date_str = date.strftime("%Y-%m-%d")
        properties["Date"] = {"date": {"start": date_str}}

        # Try to add tags if provided
        if tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags[:10]]
            }

        # Add repos as multi-select if we found any
        if sections["repos"]:
            properties["Repositories"] = {
                "multi_select": [{"name": repo} for repo in sections["repos"]]
            }

        # Add work summary as rich text
        if sections["work_summary"]:
            properties["Summary"] = {
                "rich_text": [{"text": {"content": sections["work_summary"][:2000]}}]
            }

        # Convert markdown to Notion blocks
        blocks = self._markdown_to_notion_blocks(summary)

        # Notion has a limit of 100 blocks per request
        if len(blocks) > 100:
            blocks = blocks[:100]

        try:
            # Create the page
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=blocks
            )

            page_url = response.get("url", "")
            logger.info(f"Summary saved to Notion: {page_url}")
            return page_url

        except Exception as e:
            # If properties fail, try with minimal properties
            logger.warning(f"Failed with full properties, trying minimal: {e}")

            minimal_properties = {
                "Name": {
                    "title": [{"text": {"content": title}}]
                }
            }

            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=minimal_properties,
                children=blocks
            )

            page_url = response.get("url", "")
            logger.info(f"Summary saved to Notion (minimal): {page_url}")
            return page_url

    def create_database(self, parent_page_id: str, title: str = "Daily Git Summaries") -> str:
        """
        Create a new database for storing summaries.

        Args:
            parent_page_id: ID of the parent page where database will be created
            title: Title for the database

        Returns:
            The created database ID
        """
        response = self.client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": title}}],
            properties={
                "Name": {"title": {}},
                "Date": {"date": {}},
                "Summary": {"rich_text": {}},
                "Repositories": {"multi_select": {}},
                "Tags": {"multi_select": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Draft", "color": "gray"},
                            {"name": "Ready", "color": "green"},
                            {"name": "Presented", "color": "blue"}
                        ]
                    }
                }
            }
        )

        database_id = response["id"]
        logger.info(f"Created Notion database: {database_id}")
        return database_id

    def test_connection(self) -> bool:
        """Test the Notion connection and database access."""
        try:
            # Try to retrieve the database
            self.client.databases.retrieve(database_id=self.database_id)
            logger.info("Notion connection successful")
            return True
        except Exception as e:
            logger.error(f"Notion connection failed: {e}")
            return False


def save_to_notion(
    summary: str,
    api_key: Optional[str] = None,
    database_id: Optional[str] = None,
    date: Optional[datetime] = None
) -> Optional[str]:
    """
    Convenience function to save a summary to Notion.

    Args:
        summary: The markdown summary content
        api_key: Notion API key (or use NOTION_API_KEY env var)
        database_id: Notion database ID (or use NOTION_DATABASE_ID env var)
        date: Date of the summary

    Returns:
        URL of the created page, or None if Notion is not configured
    """
    # Check if Notion is configured
    api_key = api_key or os.getenv("NOTION_API_KEY")
    database_id = database_id or os.getenv("NOTION_DATABASE_ID")

    if not api_key or not database_id:
        logger.info("Notion not configured, skipping")
        return None

    if not NOTION_AVAILABLE:
        logger.warning("notion-client not installed, skipping Notion save")
        return None

    try:
        client = NotionSummaryClient(api_key=api_key, database_id=database_id)
        return client.save_summary(summary, date=date)
    except Exception as e:
        logger.error(f"Failed to save to Notion: {e}")
        return None


if __name__ == "__main__":
    # Test the connection
    import sys

    if not NOTION_AVAILABLE:
        print("❌ notion-client not installed. Run: pip install notion-client")
        sys.exit(1)

    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not database_id:
        print("❌ Please set NOTION_API_KEY and NOTION_DATABASE_ID environment variables")
        print("\nExample:")
        print('  export NOTION_API_KEY="secret_..."')
        print('  export NOTION_DATABASE_ID="abc123..."')
        sys.exit(1)

    client = NotionSummaryClient(api_key=api_key, database_id=database_id)

    if client.test_connection():
        print("✅ Notion connection successful!")

        # Test with a sample summary
        test_summary = """# Daily Work Summary
**Date:** 2026-01-14

## Work Summary
Worked on implementing new features and fixing bugs.

## Key Accomplishments
- Added user authentication
- Fixed database connection issue
- Updated documentation

## Suggested Talking Points
- Auth system is ready for testing
- Need to discuss deployment timeline
"""
        url = client.save_summary(test_summary)
        print(f"✅ Test summary saved: {url}")
    else:
        print("❌ Notion connection failed")
        sys.exit(1)
