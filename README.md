## AI SRE Investigator

An agentic SRE investigation prototype that takes a production alert, investigates the incident using observability and GitHub evidence, and produces an evidence-backed root cause analysis (RCA).

The project demonstrates how an AI agent can assist an on-call engineer by:

Starting from a production alert
Investigating metrics and logs
Looking at recent deployments and pull requests
Inspecting relevant code changes
Connecting evidence across services
Identifying the most likely root cause
Producing actionable recommendations
Showing the investigation process and final result in a web UI

GitHub and observability data are mocked locally so the application can be run without access to external infrastructure.

#### Project Architecture

The application is split into a few core components:

Frontend
   |
   | HTTP streaming
   v
FastAPI
   |
   v
Investigator / Agent
   |
   +----> Mock Observability
   |        |
   |        +-- Metrics
   |        +-- Logs
   |
   +----> Mock GitHub
   |        |
   |        +-- Pull requests
   |        +-- Deployments
   |        +-- Code ownership
   |
   v
Synthesizer
   |
   v
Final RCA

#### Investigator

The Investigator is responsible for the agent loop and orchestration.

It:

Receives an alert as application input.
Provides the alert context to the local LLM.
Allows the LLM to request investigation tools.
Executes the requested tools.
Feeds tool results back into the investigation.
Collects evidence.
Passes the collected evidence to the synthesizer.

The application, rather than the LLM, controls the transition from investigation to synthesis.

#### Mock Data Sources

The project uses local JSON data to simulate external systems.

Observability

Observability data includes:

Metrics
Logs
Multiple services
Time-series data
Error and warning events
GitHub

GitHub data includes:

Pull requests
Deployments
Code changes
Code ownership

The data is organized into incident scenarios so that each alert has a corresponding set of evidence.

#### Synthesizer

The synthesizer receives:

The original alert
Evidence collected during the investigation

It then produces the final incident assessment, including the likely root cause and recommended actions.

#### Frontend

The frontend provides a simple interface for demonstrating the investigation:

Simulate a problem starts an investigation.
What's it checking displays the investigation process.
What it found displays the final synthesis.
Investigation events are streamed from the backend using newline-delimited JSON (NDJSON).

#### Incident Scenarios

The mock environment contains several incident types designed to test different investigation patterns.

1. Configuration Regression

A deployment introduces an incorrect configuration variable.

Application errors begin immediately after deployment.

2. Latency Regression

Application latency increases following a change.

The investigator needs to distinguish application behavior from infrastructure issues.

3. Cache Regression

Cache connectivity fails.

Requests fall back to the database, increasing latency and errors.

4. Database Connection Pool Exhaustion

A deployment reduces the database connection pool.

Connection acquisition slows and eventually fails.

5. Payment Dependency Failure

A payment provider becomes unavailable.

The failure propagates through payment-api into checkout-api.

These scenarios intentionally include relevant and irrelevant evidence so that the investigator must reason about temporal relationships and alternative explanations rather than simply selecting the most recent deployment.

#### Requirements
Software
Python 3.12+
A CUDA-capable GPU is recommended for running the local LLM
NVIDIA CUDA drivers compatible with the installed PyTorch build

The application uses a local Hugging Face Transformers model, so sufficient GPU memory is required for the configured model.

#### Configuration

Application configuration is stored in:

config/config.json

This contains settings such as:

Mock scenario paths
Model name
Other application configuration

The local LLM is loaded according to the configured model name.

Before launching the application, make sure the configured model is available through Hugging Face and that the machine has the resources required to load it.

#### Setup
1. Create the Python virtual environment

From the project root:

python -m venv .venv

Activate it in PowerShell:

.\.venv\Scripts\Activate.ps1
2. Install Python dependencies
pip install -r requirements.txt

If you are using the CUDA-enabled PyTorch setup, install the appropriate PyTorch build for your CUDA environment. For example:

pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
Launching the Application

The application consists of two local servers: a FastAPI backend and a simple Python HTTP server for the frontend.

Start the Backend

From the project root:

uvicorn create_application:app --reload --port 8000

The backend will be available at:

http://localhost:8000
Start the Frontend

From the project root, open a second terminal and run:

python -m http.server 8001 --directory frontend

The frontend will be available at:

http://localhost:8001

Make sure both servers are running at the same time.

The frontend is configured to communicate with the backend at:

http://localhost:8000
Running an Investigation

Once both applications are running:

Open http://localhost:8001 in your browser.
Click Simulate a problem.
The frontend selects a mock alert.
The alert is sent to the FastAPI backend.
The Investigator begins the investigation.
Investigation events are streamed to the browser.
The What's it checking view displays the investigation process.
The Investigator collects evidence from the mock GitHub and observability sources.
The evidence is passed to the Synthesizer.
The final RCA is generated.
The UI switches to What's it found and displays the result.