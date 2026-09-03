
from sources.github import MockGitHubClient
from sources.observability import MockObservabilityClient
from model import LocalLLM
from investigator.investigator import Investigator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

app = FastAPI()
# For simplicity, we allow all origins. In a production environment, you should restrict this to trusted domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#### Entrypoint for the SRE model. This endpoint is called by the frontend to initiate an investigation based on an alert ID. 
#### It returns a streaming response that provides real-time updates on the investigation process.    
@app.get("/sre-model/alerts/{alert_id}")
def create_application(alert_id: str):
    input_scenario = "Scenario" + alert_id[-1]

    github = MockGitHubClient(input_scenario)
    observability = MockObservabilityClient(input_scenario)
    llm = LocalLLM()

    # Create an instance of the Investigator class, which orchestrates the investigation process.
    # The Investigator uses the LLM for reasoning, the GitHub client for code-related queries, 
    # and the Observability client for metrics and logs.
    investigator = Investigator(
        llm=llm,
        github=github,
        observability=observability,
    )

    # Pre-check alert existence so we can return a 404 immediately.
    alert = observability.get_alert(alert_id)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail=f"Alert not found: {alert_id}"
        )
    # Define a generator function that yields investigation events as they occur. 
    # This allows the frontend to receive real-time updates on the investigation process.
    def generator():
        try:
            yield from investigator.investigate_stream(alert_id)

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "text": str(e),
            }) + "\n"

    return StreamingResponse(
        generator(),
        media_type="application/x-ndjson",
    )
