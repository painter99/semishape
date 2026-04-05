"""GitHub repository monitor for build123d updates.

Tracks releases, commits, and issues in gumyr/build123d repository.
Provides update detection for RAG reindexing triggers.
"""

import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


@dataclass
class GitHubRelease:
    """A GitHub release."""
    version: str
    name: str
    published_at: datetime
    body: str
    url: str
    is_prerelease: bool
    
    def get_summary(self) -> str:
        """Get release summary."""
        return f"{self.name} ({self.version}) - {self.published_at.strftime('%Y-%m-%d')}"


@dataclass
class GitHubCommit:
    """A GitHub commit."""
    sha: str
    message: str
    author: str
    date: datetime
    url: str
    
    def get_summary(self) -> str:
        """Get commit summary (first line)."""
        return self.message.split('\n')[0][:80]


@dataclass  
class GitHubIssue:
    """A GitHub issue or PR."""
    number: int
    title: str
    state: str
    labels: List[str]
    url: str
    
    def is_documentation_related(self) -> bool:
        """Check if issue relates to documentation."""
        doc_keywords = ['doc', 'documentation', 'readme', 'example', 'tutorial']
        text = f"{self.title} {' '.join(self.labels)}".lower()
        return any(kw in text for kw in doc_keywords)


class GitHubMonitor:
    """Monitor gumyr/build123d repository for updates.
    
    Tracks:
    - New releases (triggers full reindex)
    - Recent commits (doc changes detection)
    - Open issues (bug/feature awareness)
    """
    
    API_BASE = "https://api.github.com/repos/gumyr/build123d"
    RAW_BASE = "https://raw.githubusercontent.com/gumyr/build123d/main"
    
    def __init__(self, cache_file: Optional[str] = None):
        """Initialize GitHub monitor.
        
        Args:
            cache_file: Path to cache file for storing last check state
        """
        self.cache_file = cache_file or "/tmp/semishape_github_cache.json"
        self._cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                # Convert date strings back to datetime
                if 'last_check' in cache:
                    cache['last_check'] = datetime.fromisoformat(cache['last_check'])
                return cache
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'last_check': datetime.min,
                'last_release': None,
                'last_commit_sha': None,
            }
    
    def _save_cache(self):
        """Save cache to file."""
        cache = self._cache.copy()
        # Convert datetime to ISO strings for JSON
        cache['last_check'] = self._cache['last_check'].isoformat()
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except IOError:
            pass  # Cache failure is non-critical
    
    def _api_get(self, endpoint: str) -> Optional[Dict]:
        """Make GitHub API GET request."""
        url = f"{self.API_BASE}/{endpoint}"
        req = Request(
            url,
            headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'SemiShape-GitHub-Monitor/1.0',
            }
        )
        
        try:
            with urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except HTTPError as e:
            if e.code == 403:
                print("GitHub API rate limit exceeded")
            else:
                print(f"GitHub API error: {e.code}")
            return None
        except (URLError, json.JSONDecodeError) as e:
            print(f"GitHub API error: {e}")
            return None
    
    def get_latest_release(self) -> Optional[GitHubRelease]:
        """Get latest release from build123d."""
        data = self._api_get("releases/latest")
        if not data:
            return None
        
        try:
            return GitHubRelease(
                version=data.get('tag_name', 'unknown'),
                name=data.get('name', 'Unknown Release'),
                published_at=datetime.fromisoformat(
                    data.get('published_at', '').replace('Z', '+00:00')
                ),
                body=data.get('body', '')[:500],  # Truncate
                url=data.get('html_url', ''),
                is_prerelease=data.get('prerelease', False)
            )
        except (KeyError, ValueError) as e:
            print(f"Error parsing release: {e}")
            return None
    
    def get_recent_commits(
        self,
        since: Optional[datetime] = None,
        max_results: int = 10
    ) -> List[GitHubCommit]:
        """Get recent commits, optionally since a date.
        
        Args:
            since: Only return commits after this date
            max_results: Maximum commits to return
        
        Returns:
            List of GitHubCommit objects
        """
        if since:
            since_iso = since.isoformat().replace('+00:00', 'Z')
            endpoint = f"commits?since={since_iso}&per_page={max_results}"
        else:
            endpoint = f"commits?per_page={max_results}"
        
        data = self._api_get(endpoint)
        if not data or not isinstance(data, list):
            return []
        
        commits = []
        for item in data:
            try:
                commit = item.get('commit', {})
                commit_data = commit.get('committer', {})
                
                commits.append(GitHubCommit(
                    sha=item.get('sha', '')[:7],
                    message=commit.get('message', ''),
                    author=commit.get('author', {}).get('name', 'Unknown'),
                    date=datetime.fromisoformat(
                        commit_data.get('date', '').replace('Z', '+00:00')
                    ),
                    url=item.get('html_url', '')
                ))
            except (KeyError, ValueError) as e:
                continue  # Skip malformed commits
        
        return commits
    
    def get_documentation_commits(
        self,
        days: int = 7
    ) -> List[GitHubCommit]:
        """Get commits affecting documentation in last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Documentation-related commits
        """
        since = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # Simple subtraction - approximate
        from datetime import timedelta
        since = since - timedelta(days=days)
        
        all_commits = self.get_recent_commits(since=since, max_results=50)
        
        # Filter for doc-related commits
        doc_keywords = ['doc', 'readme', 'example', 'tutorial', 'rst', 'md']
        doc_commits = []
        
        for commit in all_commits:
            msg_lower = commit.message.lower()
            if any(kw in msg_lower for kw in doc_keywords):
                doc_commits.append(commit)
        
        return doc_commits
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check for updates since last check.
        
        Returns:
            Dict with update information
        """
        result = {
            'has_update': False,
            'new_release': None,
            'new_commits': [],
            'doc_changes': False,
        }
        
        # Check for new release
        latest = self.get_latest_release()
        if latest:
            cached_release = self._cache.get('last_release')
            if cached_release != latest.version:
                result['has_update'] = True
                result['new_release'] = latest
                self._cache['last_release'] = latest.version
        
        # Check for new commits
        since = self._cache.get('last_check', datetime.min)
        new_commits = self.get_recent_commits(since=since, max_results=20)
        
        if new_commits:
            result['has_update'] = True
            result['new_commits'] = new_commits
            
            # Check for doc changes
            doc_commits = [c for c in new_commits 
                          if any(kw in c.message.lower() 
                                 for kw in ['doc', 'example', 'readme', 'tutorial'])]
            if doc_commits:
                result['doc_changes'] = True
            
            # Update cache with latest commit
            if new_commits:
                self._cache['last_commit_sha'] = new_commits[0].sha
        
        # Update last check time
        self._cache['last_check'] = datetime.now()
        self._save_cache()
        
        return result
    
    def get_documentation_url(
        self,
        path: str = "docs/index.rst"
    ) -> str:
        """Get raw documentation URL from repo.
        
        Args:
            path: Path to documentation file
        
        Returns:
            Raw content URL
        """
        return f"{self.RAW_BASE}/{path}"
    
    def format_update_report(self, updates: Dict[str, Any]) -> str:
        """Format update check results as readable text.
        
        Args:
            updates: Result from check_for_updates()
        
        Returns:
            Formatted report
        """
        lines = ["## GitHub Update Report\n"]
        
        if not updates['has_update']:
            lines.append("✅ No new updates since last check.\n")
            return "\n".join(lines)
        
        if updates['new_release']:
            rel = updates['new_release']
            lines.append(f"🚀 New Release: {rel.get_summary()}")
            lines.append(f"   URL: {rel.url}\n")
        
        if updates['new_commits']:
            lines.append(f"📊 {len(updates['new_commits'])} new commits:")
            for commit in updates['new_commits'][:5]:
                lines.append(f"   - {commit.sha}: {commit.get_summary()}")
            if len(updates['new_commits']) > 5:
                lines.append(f"   ... and {len(updates['new_commits']) - 5} more\n")
            lines.append("")
        
        if updates['doc_changes']:
            lines.append("📚 Documentation changes detected - consider reindexing!")
        
        return "\n".join(lines)


def create_github_monitor(cache_file: Optional[str] = None) -> GitHubMonitor:
    """Factory function to create GitHubMonitor."""
    return GitHubMonitor(cache_file=cache_file)


if __name__ == '__main__':
    # Test GitHub monitor
    print("Testing GitHub Monitor for gumyr/build123d...\n")
    
    monitor = create_github_monitor()
    
    # Test latest release
    print("=== Latest Release ===")
    release = monitor.get_latest_release()
    if release:
        print(f"Version: {release.version}")
        print(f"Name: {release.name}")
        print(f"Published: {release.published_at}")
        print(f"URL: {release.url}")
    else:
        print("Could not fetch release")
    
    # Test recent commits
    print("\n=== Recent Commits (5) ===")
    commits = monitor.get_recent_commits(max_results=5)
    for commit in commits:
        print(f"- {commit.sha}: {commit.get_summary()[:60]}...")
    
    # Test doc commits
    print("\n=== Doc-related Commits (last 7 days) ===")
    doc_commits = monitor.get_documentation_commits(days=7)
    if doc_commits:
        for commit in doc_commits[:3]:
            print(f"- {commit.sha}: {commit.get_summary()}")
    else:
        print("No doc-related commits found")
    
    # Test update check
    print("\n=== Update Check ===")
    updates = monitor.check_for_updates()
    print(monitor.format_update_report(updates))
