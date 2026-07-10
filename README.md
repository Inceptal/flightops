# AI Builders Week

Codex project workspace on Wraith.

Path: /home/daniel/Documents/AI Builders Week

## Note

Hackathon submission

## FlightOps AI

Autonomous operations copilot demo for airline operations managers.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

The first demo dataset is in `demo-data/flightops-ai-typhoon-sgn-2026-07-12.json`.

### Run Agent Orchestration Directly

```bash
python -m flightops.run_agents
```
