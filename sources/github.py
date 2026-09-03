import json
from pathlib import Path
from typing import Any
from config_loader import load_config, get_data
from datetime import datetime

# Mock GitHub client that simulates interactions with GitHub data for testing purposes.
class MockGitHubClient:
    """Mock GitHub data source backed by a local JSON file."""

    def __init__(self, scenario: str | Path):
        self.scenario = scenario
        self.data = self._load_data()

    # Loads GitHub data from a JSON file based on the provided scenario.
    def _load_data(self) -> dict[str, Any]:
        """Load GitHub data from the JSON file."""
        config = load_config()
        with Path(get_data(config,self.scenario)["github"]).open("r", encoding="utf-8") as f:
            return json.load(f)
                
    # Gets recent deployments for specified services within an optional time range.
    def get_recent_deployments(
        self,
        services: list[str] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return deployments within an optional service and time range."""

        start = (
            datetime.fromisoformat(start_time)
            if start_time
            else None
        )

        end = (
            datetime.fromisoformat(end_time)
            if end_time
            else None
        )

        results = []

        for repository in self.data.get("repositories", []):

            if services is not None and repository["service"] not in services:
                continue

            for deployment in repository.get("deployments", []):
                deployed_at = datetime.fromisoformat(
                    deployment["deployed_at"]
                )

                if start is not None and deployed_at < start:
                    continue

                if end is not None and deployed_at > end:
                    continue

                results.append(deployment)

        return results

    # Gets recent pull requests for specified services within an optional time range.
    def get_recent_pull_requests(
        self,
        services: list[str] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return pull requests merged within an optional service and time range."""

        start = (
            datetime.fromisoformat(start_time)
            if start_time
            else None
        )

        end = (
            datetime.fromisoformat(end_time)
            if end_time
            else None
        )

        results = []

        for repository in self.data.get("repositories", []):

            if services is not None and repository["service"] not in services:
                continue

            for pr in repository.get("pull_requests", []):
                merged_at = datetime.fromisoformat(pr["merged_at"])

                if start is not None and merged_at < start:
                    continue

                if end is not None and merged_at > end:
                    continue

                results.append(pr)

        return results

    # gets a specific pull request by its number.
    def get_pull_request(
        self,
        number: int,
    ) -> dict[str, Any] | None:
        """Return a specific pull request by number."""

        for repository in self.data.get("repositories", []):
            for pr in repository.get("pull_requests", []):
                if pr["number"] == number:
                    return pr

        return None

    # gets owners responsible for a given file path, optionally filtered by services.
    def get_code_owners_for_path(
        self,
        file_path: str,
        services: list[str] | None = None,
    ) -> list[str]:
        """Return owners responsible for a given file path."""

        owners = []

        for repository in self.data.get("repositories", []):

            if services is not None and repository["service"] not in services:
                continue

            for owner_rule in repository.get("code_owners", []):
                path_pattern = owner_rule["path"].rstrip("*")

                if file_path.startswith(path_pattern):
                    owners.extend(owner_rule["owners"])

        return owners