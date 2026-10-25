import requests
from typing import Dict, Any

class GitHubPRClient:
    """Fetches real Pull Request diffs and metadata from GitHub REST API v3."""

    def __init__(self, token: str = ""):
        self.headers = {"Accept": "application/vnd.github.v3.diff"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def fetch_pr_diff(self, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()
        return {
            "repo": repo_full_name,
            "pr_number": pr_number,
            "diff_text": response.text,
        }
