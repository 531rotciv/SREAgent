import json
from pathlib import Path
from typing import Any
from config_loader import load_config, get_data, get_alert_data
from datetime import datetime

# Mock Observability client that simulates interactions with observability data for testing purposes.
class MockObservabilityClient:
    """Mock observability data source backed by local JSON files."""

    def __init__(
        self,
        scenario
    ):
        self.scenario = scenario
        self.alerts, self.logs, self.metrics = self._load_data()

    # Loads alerts, logs, and metrics data from JSON files based on the provided scenario.
    def _load_data(self):
        """Load JSON data from a file."""
        config = load_config()
       
        with Path(get_alert_data(config)).open("r", encoding="utf-8") as f:
            alert = json.load(f)      
        with Path(get_data(config,self.scenario)["logs"]).open("r", encoding="utf-8") as f2:
            logs = json.load(f2)  
        with Path(get_data(config,self.scenario)["metrics"]).open("r", encoding="utf-8") as f3:
            metrics = json.load(f3)                 
        return alert,logs,metrics              

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    # Returns the alert dictionary for the given alert ID, or None if not found.
    def get_alert(self, alert_id: str) -> dict[str, Any] | None:
        """Return an alert by ID."""

        for alert in self.alerts.get("alerts", []):
            if alert["id"] == alert_id:
                return alert

        return None

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    # Returns metrics for selected services within an optional time range and filtered by metric names.
    def get_metrics(
        self,
        services: list[str] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        metric_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return metrics for selected services within an optional time range."""

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

        selected_services = [
            service
            for service in self.metrics.get("services", [])
            if services is None or service["service"] in services
        ]

        results = []

        for service in selected_services:
            metrics = service.get("metrics", [])

            if metric_names is not None:
                metrics = [
                    metric
                    for metric in metrics
                    if metric["name"] in metric_names
                ]

            results.extend(
                {
                    **metric,
                    "service": service["service"],
                    "points": [
                        point
                        for point in metric["points"]
                        if (
                            start is None
                            or datetime.fromisoformat(point["timestamp"]) >= start
                        )
                        and (
                            end is None
                            or datetime.fromisoformat(point["timestamp"]) <= end
                        )
                    ],
                }
                for metric in metrics
            )

        return results

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    # Returns logs for selected services within an optional time range and filtered by log level.
    def search_logs(
        self,
        services: list[str] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        level: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return logs for selected services within an optional time range."""

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

        selected_services = [
            service
            for service in self.logs.get("services", [])
            if services is None or service["service"] in services
        ]

        results = []

        for service in selected_services:
            logs = service.get("logs", [])

            results.extend(
                {
                    **log,
                    "service": service["service"],
                }
                for log in logs
                if (level is None or log["level"] == level)
                and (
                    start is None
                    or datetime.fromisoformat(log["timestamp"]) >= start
                )
                and (
                    end is None
                    or datetime.fromisoformat(log["timestamp"]) <= end
                )
            )

        return results