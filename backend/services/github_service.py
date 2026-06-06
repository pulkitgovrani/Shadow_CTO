"""GitHub API service — fetches commits, PRs, and issues."""
import json
import os
from datetime import datetime
from typing import Optional
from github import Github, GithubException


def get_github_client() -> Github:
    token = os.getenv("GITHUB_TOKEN")
    return Github(token) if token else Github()


def fetch_repo_events(
    owner: str,
    name: str,
    since: Optional[datetime] = None,
    limit_per_type: int = 50,
) -> list[dict]:
    """Fetch recent commits, PRs, and issues from a GitHub repo."""
    gh = get_github_client()
    events: list[dict] = []

    try:
        repo = gh.get_repo(f"{owner}/{name}")
    except GithubException as e:
        raise ValueError(f"Cannot access repo {owner}/{name}: {e}")

    # Commits
    try:
        commit_kwargs = {"sha": repo.default_branch}
        if since:
            commit_kwargs["since"] = since
        commits = repo.get_commits(**commit_kwargs)
        count = 0
        for c in commits:
            if count >= limit_per_type:
                break
            try:
                files_changed = [f.filename for f in c.files[:10]]
            except Exception:
                files_changed = []
            events.append({
                "event_type": "commit",
                "external_id": c.sha,
                "data": {
                    "sha": c.sha,
                    "message": c.commit.message,
                    "author": c.commit.author.name if c.commit.author else "unknown",
                    "date": c.commit.author.date.isoformat() if c.commit.author else None,
                    "files_changed": files_changed,
                    "additions": c.stats.additions if c.stats else 0,
                    "deletions": c.stats.deletions if c.stats else 0,
                    "url": c.html_url,
                },
            })
            count += 1
    except GithubException:
        pass

    # Pull Requests
    try:
        pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")
        count = 0
        for pr in pulls:
            if count >= limit_per_type:
                break
            if since and pr.updated_at < since:
                break
            events.append({
                "event_type": "pr",
                "external_id": str(pr.number),
                "data": {
                    "number": pr.number,
                    "title": pr.title,
                    "body": (pr.body or "")[:2000],
                    "author": pr.user.login if pr.user else "unknown",
                    "merged": pr.merged,
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                    "labels": [l.name for l in pr.labels],
                    "url": pr.html_url,
                },
            })
            count += 1
    except GithubException:
        pass

    # Issues
    try:
        issues = repo.get_issues(state="closed", sort="updated", direction="desc")
        count = 0
        for issue in issues:
            if count >= limit_per_type:
                break
            if since and issue.updated_at < since:
                break
            if issue.pull_request:
                continue  # Skip PRs listed as issues
            events.append({
                "event_type": "issue",
                "external_id": str(issue.number),
                "data": {
                    "number": issue.number,
                    "title": issue.title,
                    "body": (issue.body or "")[:2000],
                    "author": issue.user.login if issue.user else "unknown",
                    "labels": [l.name for l in issue.labels],
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "url": issue.html_url,
                },
            })
            count += 1
    except GithubException:
        pass

    return events

# Guard: skip repos with zero merged PRs instead of raising (fixes the sync 500)
